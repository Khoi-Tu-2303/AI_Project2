"""Module C unit tests: DPLLSolver and EntailmentChecker/Classifier vs independent oracles."""

from __future__ import annotations

import random
import time
from pathlib import Path

import pytest

from common.errors import ReasoningFailure
from common.regions import all_cells
from common.types import (
    Classification, Clue, ClueType, CompareOp, KnowledgeBase, Parity, PublicState,
    ReasoningStatus, Region, RegionKind, StateToken, Status, VerdictResult, bool_to_status,
)
from engine.game_engine import GameEngine
from logic.dpll import DPLLSolver, SatStatus, SolveStats, solve_cnf
from logic.encoder import CNFEncoder
from logic.entailment import EntailmentChecker, EntailmentClassifier, EntailmentStats, Uniqueness
from common.puzzle_io import load_puzzle
from common.types import status_to_bool
from tests.oracles import (
    brute_force_cnf_models, classify_public_state_oracle, evaluate_clue_semantic,
    find_satisfying_models,
)

CHAIN = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"


def _satisfies(model, clauses) -> bool:
    return all(any(model[abs(l)] == (l > 0) for l in c) for c in clauses)


# --------------------------------------------------------------------- DPLL

def test_trivial_cases() -> None:
    assert solve_cnf([], 0).is_sat and solve_cnf([], 3).is_sat      # [] is True
    assert solve_cnf([[]], 2).is_unsat                              # [[]] is False
    assert solve_cnf([[1], [-1]], 1).is_unsat
    assert solve_cnf([[1, -1]], 1).is_sat                           # tautology
    r = solve_cnf([[1], [-2]], 3)                                   # model is complete
    assert r.is_sat and set(r.model) == {1, 2, 3} and r.model[1] and not r.model[2]


def test_invalid_input_rejected() -> None:
    for bad in ([[0]], [[3]], [[-3]]):
        with pytest.raises(ValueError):
            DPLLSolver(bad, 2)
    with pytest.raises(ValueError):
        DPLLSolver([[1]], 2).solve([5])
    with pytest.raises(ValueError):
        DPLLSolver([[1]], 2).solve([True])  # bool is not a literal


def test_random_cnf_matches_bruteforce() -> None:
    rng = random.Random(20240601)
    for _ in range(400):
        n = rng.randint(1, 9)
        clauses = [[rng.choice((-1, 1)) * rng.randint(1, n) for _ in range(rng.randint(1, 4))]
                   for _ in range(rng.randint(0, 3 * n))]
        assumptions = [rng.choice((-1, 1)) * v for v in rng.sample(range(1, n + 1), rng.randint(0, min(3, n)))]
        expected = bool(brute_force_cnf_models(clauses, n, assumptions))
        result = solve_cnf(clauses, n, assumptions)
        assert result.is_sat == expected, (clauses, assumptions)
        if result.is_sat:
            assert _satisfies(result.model, clauses)
            assert all(result.model[abs(a)] == (a > 0) for a in assumptions)


def test_solver_is_reusable_across_assumptions() -> None:
    # (A or B) and (-A or B): B forced, A free (PDF example); vars A=1, B=2
    solver = DPLLSolver([[1, 2], [-1, 2]], 2)
    for _ in range(3):  # repeated queries must not leak state
        assert solver.solve([-2]).is_unsat
        assert solver.solve([2]).is_sat
        assert solver.solve([1]).is_sat and solver.solve([-1]).is_sat
        assert solver.solve([1, -1]).is_unsat
        assert solver.solve().is_sat


def test_decision_vars_order_does_not_change_answers() -> None:
    rng = random.Random(7)
    for _ in range(100):
        n = rng.randint(2, 8)
        clauses = [[rng.choice((-1, 1)) * rng.randint(1, n) for _ in range(rng.randint(2, 3))]
                   for _ in range(rng.randint(1, 3 * n))]
        order = rng.sample(range(1, n + 1), rng.randint(0, n))
        assert solve_cnf(clauses, n, decision_vars=order).status is solve_cnf(clauses, n).status


def test_stats_include_backtracks_and_runtime() -> None:
    """Spec 4.3 item 6: decisions, propagations, backtracks and runtime are recorded."""
    # Pigeonhole 7 -> 6 is UNSAT, so the search must explore and backtrack.
    holes, pigeons = 6, 7
    var = lambda p, h: p * holes + h + 1
    clauses = [[var(p, h) for h in range(holes)] for p in range(pigeons)]
    clauses += [[-var(p, h), -var(q, h)] for h in range(holes)
                for p in range(pigeons) for q in range(p + 1, pigeons)]
    result = solve_cnf(clauses, pigeons * holes)
    stats = result.stats
    assert result.is_unsat and stats.decisions > 0 and stats.propagations > 0
    assert stats.backtracks == 2 * stats.decisions  # UNSAT: each explored variable failed on both values
    assert stats.backtracks >= stats.conflicts      # every conflict undoes its branch
    assert stats.runtime_seconds > 0

    # Easy SAT instance: one guess (x1 = False), x2 is forced, nothing is ever undone.
    easy = solve_cnf([[1, 2]], 2).stats
    assert (easy.decisions, easy.conflicts, easy.backtracks) == (1, 0, 0)
    assert easy.runtime_seconds >= 0


def test_deep_recursion_is_safe() -> None:
    """No clauses: every one of the 3000 variables is a decision, so recursion goes 3000 deep."""
    import sys
    before = sys.getrecursionlimit()
    result = solve_cnf([], 3000)
    assert result.is_sat and len(result.model) == 3000 and result.stats.decisions == 3000
    assert sys.getrecursionlimit() == before  # the limit is restored afterwards


def test_deadline_gives_timeout_not_unsat() -> None:
    # Pigeonhole 10->9: far too hard for plain DPLL to finish within the deadline.
    holes, pigeons = 9, 10
    var = lambda p, h: p * holes + h + 1
    clauses = [[var(p, h) for h in range(holes)] for p in range(pigeons)]
    clauses += [[-var(p, h), -var(q, h)] for h in range(holes)
                for p in range(pigeons) for q in range(p + 1, pigeons)]
    solver = DPLLSolver(clauses, pigeons * holes)
    assert solver.solve(deadline=time.monotonic() - 1).status is SatStatus.TIMEOUT
    assert solver.solve(deadline=time.monotonic() + 0.05).status is SatStatus.TIMEOUT
    # solver state is restored after a timeout; an easy query still works afterwards
    assert solver.solve([var(0, 0), var(1, 0)]).is_unsat


# --------------------------------------------------------------- entailment

def _kb(clauses, n=3, aux=0) -> KnowledgeBase:
    return KnowledgeBase(n, tuple(tuple(c) for c in clauses), n * n, aux)


def test_entails_and_classify_cell() -> None:
    kb = _kb([[1, 2], [-1, 2]])  # A1 or B1 / not A1 or B1 -> B1 is criminal, A1 unknown
    checker = EntailmentChecker(kb)
    assert checker.entails(2) and not checker.entails(-2)
    assert not checker.entails(1) and not checker.entails(-1)
    assert checker.classify_cell("B1") is Classification.CRIMINAL
    assert checker.classify_cell("A1") is Classification.UNKNOWN
    with pytest.raises(ValueError):
        checker.entails(10)  # not a primary literal


def test_inconsistent_kb() -> None:
    checker = EntailmentChecker(_kb([[1], [-1]]))
    assert not checker.is_consistent()
    for call in (lambda: checker.classify_cells(["A1"]), lambda: checker.classify_cell("A1")):
        with pytest.raises(ReasoningFailure) as exc:
            call()
        assert exc.value.status is ReasoningStatus.INCONSISTENT


def test_classify_cells_equals_two_query_definition() -> None:
    rng = random.Random(99)
    cells = all_cells(3)
    for _ in range(150):
        clauses = [[rng.choice((-1, 1)) * rng.randint(1, 9) for _ in range(rng.randint(1, 3))]
                   for _ in range(rng.randint(0, 12))]
        checker = EntailmentChecker(_kb(clauses))
        if not checker.is_consistent():
            continue
        fast = checker.classify_cells(cells)
        slow = {c: checker.classify_cell(c) for c in cells}
        models = brute_force_cnf_models(clauses, 9)
        for i, c in enumerate(cells, 1):
            values = {m[i] for m in models}
            want = (Classification.UNKNOWN if len(values) == 2
                    else Classification.CRIMINAL if values == {True} else Classification.INNOCENT)
            assert fast[c] is slow[c] is want, (clauses, c)


def test_solve_stats_add_up() -> None:
    total = SolveStats(1, 2, 3, 4, 0.5) + SolveStats(10, 20, 30, 40, 0.25)
    assert total == SolveStats(11, 22, 33, 44, 0.75)


def test_checker_accumulates_stats_over_queries() -> None:
    clauses = [[1, 2], [-1, 2]]
    checker = EntailmentChecker(_kb(clauses))
    assert checker.stats == EntailmentStats()  # nothing asked yet

    one = DPLLSolver(clauses, 9, decision_vars=range(1, 10)).solve([-2]).stats  # cost of entails(2)
    checker.entails(2)
    checker.entails(2)
    after_two = checker.stats
    assert after_two.sat_calls == checker.queries == 2
    got = after_two.solver
    assert (got.decisions, got.conflicts, got.propagations, got.backtracks) == tuple(
        2 * x for x in (one.decisions, one.conflicts, one.propagations, one.backtracks)
    )
    assert got.runtime_seconds > 0

    checker.entails(2)
    assert after_two.sat_calls == 2 and checker.stats.sat_calls == 3  # earlier snapshot is unchanged


def test_stats_count_even_when_a_query_times_out() -> None:
    checker = EntailmentChecker(_kb([[1, 2]]))
    with pytest.raises(ReasoningFailure):
        checker.classify_cells(["A1"], deadline=time.monotonic() - 1)
    assert checker.stats.sat_calls == 1


def test_classifier_exposes_last_stats() -> None:
    classifier = EntailmentClassifier()
    assert classifier.last_stats is None
    state = GameEngine(classifier).load(CHAIN)

    assert classifier(state).status is ReasoningStatus.READY
    ok = classifier.last_stats
    assert ok.sat_calls >= 2 and ok.solver.propagations > 0 and ok.solver.runtime_seconds > 0

    classifier(state, deadline=time.monotonic() - 1)  # TIMEOUT report still records its stats
    assert classifier.last_stats.sat_calls == 1

    clash = (Clue("a", ClueType.FACT, cells=("B1",), status=Status.CRIMINAL),
             Clue("b", ClueType.FACT, cells=("B1",), status=Status.INNOCENT))
    bad = PublicState("p", StateToken("s", 0), 3, (), {}, {"A1": clash[0], "B1": clash[1]},
                      all_cells(3))
    assert classifier(bad).status is ReasoningStatus.INCONSISTENT
    assert classifier.last_stats.sat_calls == 1


def test_query_log_matches_stats() -> None:
    checker = EntailmentChecker(_kb([[1, 2], [-1, 2]]))
    checker.classify_cells(all_cells(3))
    log = checker.query_log
    assert len(log) == checker.stats.sat_calls == checker.queries
    assert log[0].assumptions == ()  # first query: is the KB itself satisfiable?
    assert all(r.status in (SatStatus.SAT, SatStatus.UNSAT) for r in log)
    total = SolveStats()
    for record in log:
        total = total + record.stats
    assert total == checker.stats.solver  # the log and the totals describe the same calls


def test_classifier_exposes_kb_and_queries() -> None:
    classifier = EntailmentClassifier()
    assert classifier.last_kb is None and classifier.last_queries is None
    classifier(GameEngine(classifier).load(CHAIN))
    kb = classifier.last_kb
    # chain start: clue of A1 gives [2] and the known status of A1 gives [-1]
    assert (kb.num_primary, kb.num_aux, kb.num_clauses) == (9, 0, 2)
    assert len(classifier.last_queries) == classifier.last_stats.sat_calls


def _chain_kb(drop=()):
    """KB from the clues of the 3x3 chain puzzle (all of them, minus the dropped cells)."""
    puzzle = load_puzzle(CHAIN)
    clues = [clue for cell, clue in puzzle.clues.items() if cell not in drop]
    return puzzle, clues, CNFEncoder(3).build_kb(clues, {})


def test_uniqueness_unique_ambiguous_and_contradictory() -> None:
    # all nine clues: exactly the stored solution
    puzzle, _, kb = _chain_kb()
    report = EntailmentChecker(kb).check_uniqueness()
    assert report.status is Uniqueness.UNIQUE and len(report.solutions) == 1
    assert dict(report.solutions[0]) == dict(puzzle.solution)

    # the clue of C3 is the only one that fixes A1: without it there are two solutions
    _, clues, kb = _chain_kb(drop=("C3",))
    report = EntailmentChecker(kb).check_uniqueness()
    assert report.status is Uniqueness.MULTIPLE and len(report.solutions) == 2
    first, second = report.solutions
    assert dict(first) != dict(second)
    for solution in report.solutions:  # both are real solutions of the remaining clues
        assignment = {cell: status_to_bool(status) for cell, status in solution.items()}
        assert all(evaluate_clue_semantic(clue, assignment, 3) for clue in clues)

    # contradictory clues: no solution at all
    clash = [Clue("a", ClueType.FACT, cells=("B1",), status=Status.CRIMINAL),
             Clue("b", ClueType.FACT, cells=("B1",), status=Status.INNOCENT)]
    report = EntailmentChecker(CNFEncoder(3).build_kb(clash, {})).check_uniqueness()
    assert report.status is Uniqueness.NONE and report.solutions == ()


def test_uniqueness_matches_oracle_on_random_3x3_clue_sets() -> None:
    rng = random.Random(4242)
    n, cells = 3, all_cells(3)
    seen = set()
    for trial in range(80):
        solution = {c: rng.random() < 0.5 for c in cells}
        clues, tries, target = [], 0, rng.randint(3, 14)
        while len(clues) < target and tries < 400:
            tries += 1
            clue = _random_clue(rng, len(clues), n)
            try:
                if evaluate_clue_semantic(clue, solution, n):
                    clues.append(clue)
            except Exception:
                continue
        state = PublicState("rnd", StateToken("s", trial), n, (), {},
                            {f"k{i}": c for i, c in enumerate(clues)}, cells)
        models = find_satisfying_models(state)  # brute force; at least the hidden solution
        want = Uniqueness.UNIQUE if len(models) == 1 else Uniqueness.MULTIPLE
        got = EntailmentChecker(CNFEncoder(n).build_kb(clues, {})).check_uniqueness()
        assert got.status is want, (trial, len(models), clues)
        seen.add(got.status)
    assert seen == {Uniqueness.UNIQUE, Uniqueness.MULTIPLE}  # the test exercises both outcomes


def test_timeout_raises_reasoning_failure() -> None:
    checker = EntailmentChecker(_kb([[1, 2]]))
    with pytest.raises(ReasoningFailure) as exc:
        checker.classify_cells(["A1"], deadline=time.monotonic() - 1)
    assert exc.value.status is ReasoningStatus.TIMEOUT


# ------------------------------------------------ classifier vs brute-force oracle

def _random_clue(rng: random.Random, idx: int, n: int) -> Clue:
    cells = all_cells(n)
    kind = rng.choice(list(ClueType))
    row = lambda: Region(RegionKind.ROW, rng.randint(1, n))
    col = lambda: Region(RegionKind.COL, chr(ord("A") + rng.randint(0, n - 1)))
    nb = lambda: Region(RegionKind.NEIGHBORS, rng.choice(cells))
    region = lambda: rng.choice((row, col, nb))()
    cid = f"r{idx}"
    if kind is ClueType.FACT:
        return Clue(cid, kind, cells=(rng.choice(cells),), status=rng.choice(list(Status)))
    if kind in (ClueType.SAME, ClueType.DIFFERENT):
        return Clue(cid, kind, cells=tuple(rng.sample(cells, 2)))
    if kind in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        from common.regions import resolve_region
        r = region()
        return Clue(cid, kind, region=r, k=rng.randint(0, len(resolve_region(r, n))))
    if kind is ClueType.PARITY:
        return Clue(cid, kind, region=region(), parity=rng.choice(list(Parity)))
    return Clue(cid, kind, left=region(), right=region(), op=rng.choice(list(CompareOp)))


def test_classifier_matches_oracle_on_random_3x3_states() -> None:
    rng = random.Random(2025)
    n, cells = 3, all_cells(3)
    classifier = EntailmentClassifier()
    checked = 0
    for trial in range(60):
        solution = {c: rng.random() < 0.5 for c in cells}
        clues, tries = [], 0
        while len(clues) < rng.randint(2, 6) and tries < 200:
            tries += 1
            clue = _random_clue(rng, len(clues), n)
            try:
                if evaluate_clue_semantic(clue, solution, n):
                    clues.append(clue)
            except Exception:
                continue
        known = {c: bool_to_status(solution[c]) for c in rng.sample(cells, rng.randint(0, 3))}
        state = PublicState(
            puzzle_id="rnd", token=StateToken("s", trial), n=n, characters=(),
            known_statuses=known, revealed_clues={f"k{i}": c for i, c in enumerate(clues)},
            unsolved=tuple(c for c in cells if c not in known),
        )
        got, want = classifier(state), classify_public_state_oracle(state)
        assert got.token == state.token
        assert got.status is want.status is ReasoningStatus.READY
        assert dict(got.by_cell) == dict(want.by_cell), [c for c in clues]
        checked += 1
    assert checked == 60


def test_classifier_reports_inconsistent_and_timeout() -> None:
    cells = all_cells(3)
    contradictory = (
        Clue("a", ClueType.FACT, cells=("B1",), status=Status.CRIMINAL),
        Clue("b", ClueType.FACT, cells=("B1",), status=Status.INNOCENT),
    )
    state = PublicState("p", StateToken("s", 0), 3, (), {}, {"A1": contradictory[0], "B1": contradictory[1]},
                        cells)
    report = EntailmentClassifier()(state)
    assert report.status is ReasoningStatus.INCONSISTENT and report.token == state.token
    # A root-level contradiction is a valid proof even past the deadline; an expired
    # deadline on a consistent KB must give TIMEOUT, never a classification.
    consistent = GameEngine(EntailmentClassifier()).load(CHAIN)
    late = EntailmentClassifier()(consistent, deadline=time.monotonic() - 1)
    assert late.status is ReasoningStatus.TIMEOUT and not late.by_cell and late.token == consistent.token


def test_chain_puzzle_end_to_end_with_real_classifier() -> None:
    """Engine + CNFEncoder + DPLL: the 3x3 chain unlocks one cell per step, in row-major order."""
    engine = GameEngine(EntailmentClassifier())
    engine.load(CHAIN)
    expected = [("B1", Status.CRIMINAL), ("C1", Status.INNOCENT), ("A2", Status.CRIMINAL),
                ("B2", Status.INNOCENT), ("C2", Status.CRIMINAL), ("A3", Status.INNOCENT),
                ("B3", Status.CRIMINAL), ("C3", Status.INNOCENT)]
    for cell, verdict in expected:
        state = engine.get_public_state()
        report = EntailmentClassifier()(state)
        forced = [c for c in state.unsolved if report.by_cell[c] is not Classification.UNKNOWN]
        assert forced == [cell]  # exactly the next link of the chain is forced
        wrong = Status.INNOCENT if verdict is Status.CRIMINAL else Status.CRIMINAL
        assert engine.submit_verdict(cell, wrong).result is VerdictResult.CONTRADICTED
        assert engine.submit_verdict(cell, verdict).result is VerdictResult.ACCEPTED
    assert engine.is_complete()


def test_not_provable_when_nothing_is_forced() -> None:
    engine = GameEngine(EntailmentClassifier())
    state = engine.load(CHAIN)
    # Only A1's clue is public, so C3 is not provable yet.
    assert engine.submit_verdict("C3", Status.INNOCENT).result is VerdictResult.NOT_PROVABLE
    assert engine.get_public_state().token == state.token
