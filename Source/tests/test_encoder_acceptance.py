"""Real G-B checks, also called by the verification runner (no fixtures)."""

import itertools
import random
from pathlib import Path
import pytest

from common.errors import ClueError
from common.regions import all_cells
from common.types import Clue, ClueType, CompareOp, Parity, Region, RegionKind, Status
from logic.encoder import CNFEncoder
from logic.evaluator import SemanticEvaluator
from logic.varmap import VarMap
from tests.oracles import brute_force_cnf_models, evaluate_clue_semantic


def _assignments(n=3):
    for values in itertools.product((False, True), repeat=n*n):
        yield dict(zip(all_cells(n), values))


def _circuit_holds(clauses, assignment, varmap):
    """Project a reified acyclic circuit by unit propagation of fixed inputs.

    Auxiliaries must be determined; unresolved clauses fail the test. Small
    cases additionally use the independent brute-force CNF oracle below.
    """
    values = {varmap.var(c): v for c, v in assignment.items()}
    pending = [list(c) for c in clauses]
    while pending:
        reduced, units = [], []
        for clause in pending:
            if any(abs(lit) in values and values[abs(lit)] == (lit > 0) for lit in clause):
                continue
            remaining = [lit for lit in clause if abs(lit) not in values]
            if not remaining:
                return False
            reduced.append(remaining)
            if len(remaining) == 1:
                units.append(remaining[0])
        if not reduced:
            return True
        assert units, "Unresolved circuit with all primary inputs fixed"
        for lit in units:
            if abs(lit) in values and values[abs(lit)] != (lit > 0):
                return False
            values[abs(lit)] = lit > 0
        pending = reduced
    return True


def _check_clue(clue, assignments=None, n=3):
    encoder, evaluator = CNFEncoder(n), SemanticEvaluator(n)
    clauses = encoder.encode_clue(clue)
    assert all(type(lit) is int and 1 <= abs(lit) <= encoder.varmap.num_vars
               for clause in clauses for lit in clause)
    for assignment in _assignments(n) if assignments is None else assignments:
        expected = evaluate_clue_semantic(clue, assignment, n)
        assert evaluator.evaluate(clue, assignment) == expected
        assert _circuit_holds(clauses, assignment, encoder.varmap) == expected, (clue, assignment)


def test_b01_varmap_bijection():
    for n in (3, 4, 5):
        vm = VarMap(n)
        for var, cell in enumerate(all_cells(n), 1):
            assert vm.var(cell) == var
            assert vm.cell(var) == cell
        assert vm.new_aux() == n*n + 1
        assert vm.new_aux() == n*n + 2
        assert vm.num_aux == 2
        for bad in (0, -1, True, 1.0, n*n + 1):
            with pytest.raises(ClueError):
                vm.cell(bad)
        vm.reset_aux()
        assert vm.num_aux == 0
        assert vm.new_aux() == n*n + 1
    for bad in (True, 2, 6, 3.0):
        with pytest.raises(ClueError):
            VarMap(bad)
    with pytest.raises(ClueError):
        VarMap(3).var("D1")


def test_b02_binary_projection():
    for status in Status:
        _check_clue(Clue("fact", ClueType.FACT, cells=("A1",), status=status))
    for kind in (ClueType.SAME, ClueType.DIFFERENT):
        _check_clue(Clue("binary", kind, cells=("A1", "C3")))


def test_b03_counting_all_bounds():
    for size in (1, 3, 9):
        region = Region(RegionKind.EXPLICIT, all_cells(3)[:size])
        for kind in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
            for k in range(size + 1):
                _check_clue(Clue("count", kind, region=region, k=k))


def test_b04_parity_and_region_kinds():
    regions = (Region(RegionKind.ROW, 1), Region(RegionKind.COL, "C"),
               Region(RegionKind.NEIGHBORS, "B2"), Region(RegionKind.EXPLICIT, ("C3",)))
    for region in regions:
        for parity in Parity:
            _check_clue(Clue("parity", ClueType.PARITY, region=region, parity=parity))


def test_b05_compare_overlap_and_identical_regions():
    row = Region(RegionKind.ROW, 1)
    pairs = ((row, Region(RegionKind.COL, "B")), (row, row),
             (row, Region(RegionKind.ROW, 2)),
             (Region(RegionKind.EXPLICIT, ("A1",)), row),
             (row, Region(RegionKind.EXPLICIT, ("A1",))))
    for left, right in pairs:
        for op in CompareOp:
            _check_clue(Clue("compare", ClueType.COMPARE, left=left, right=right, op=op))


def test_b06_independent_bruteforce_auxiliary_projection():
    region = Region(RegionKind.EXPLICIT, ("A1", "B1"))
    clues = [Clue("count", ClueType.EXACTLY, region=region, k=1),
             Clue("parity", ClueType.PARITY, region=region, parity=Parity.EVEN),
             Clue("compare", ClueType.COMPARE, left=region,
                  right=Region(RegionKind.EXPLICIT, ("C1",)), op=CompareOp.LT)]
    for clue in clues:
        encoder = CNFEncoder(3)
        clauses = encoder.encode_clue(clue)
        models = brute_force_cnf_models(clauses, encoder.varmap.num_vars)
        projected = {tuple(model[i] for i in range(1, 10)) for model in models}
        expected = {tuple(a.values()) for a in _assignments() if evaluate_clue_semantic(clue, a, 3)}
        assert projected == expected


def test_b07_kb_rebuild_isolation_and_public_inputs():
    encoder = CNFEncoder(3)
    clues = [Clue("count", ClueType.EXACTLY, region=Region(RegionKind.ROW, 1), k=1),
             Clue("parity", ClueType.PARITY, region=Region(RegionKind.COL, "A"), parity=Parity.ODD)]
    known = {"C3": Status.INNOCENT, "B2": Status.CRIMINAL}
    kb = encoder.build_kb(clues, known)
    assert kb.num_primary == 9 and kb.num_aux > 0
    assert kb.num_vars == kb.num_primary + kb.num_aux
    assert kb.num_clauses == len(kb.clauses)
    for assignment in _assignments():
        expected = all(evaluate_clue_semantic(c, assignment, 3) for c in clues)
        expected = expected and not assignment["C3"] and assignment["B2"]
        assert _circuit_holds(kb.clauses, assignment, encoder.varmap) == expected
    assert encoder.build_kb(clues, dict(reversed(list(known.items())))) == kb
    saved = kb.clauses
    clues.clear()
    known.clear()
    empty = encoder.build_kb([], {})
    assert empty.clauses == () and empty.num_aux == 0
    assert kb.clauses == saved
    assert encoder.unit_clause("A1", Status.CRIMINAL) == [1]
    assert encoder.unit_clause("A1", Status.INNOCENT) == [-1]


def test_b08_standalone_clues_do_not_reuse_auxiliaries():
    encoder = CNFEncoder(3)
    region = Region(RegionKind.ROW, 1)
    first = encoder.encode_clue(Clue("odd", ClueType.PARITY, region=region, parity=Parity.ODD))
    last_var = encoder.varmap.num_vars
    second = encoder.encode_clue(Clue("even", ClueType.PARITY, region=region, parity=Parity.EVEN))
    assert all(abs(lit) <= 9 or abs(lit) > last_var for clause in second for lit in clause)
    for assignment in _assignments():
        assert not _circuit_holds(first + second, assignment, encoder.varmap)


def test_b09_reject_invalid_clues_and_assignments():
    encoder, evaluator = CNFEncoder(3), SemanticEvaluator(3)
    invalid = [Clue("bad", ClueType.EXACTLY, region=Region(RegionKind.ROW, 1), k=True),
               Clue("bad", ClueType.FACT, cells=("D1",), status=Status.CRIMINAL),
               Clue("bad", ClueType.PARITY, region=Region(RegionKind.EXPLICIT, ("A1", "A1")), parity=Parity.ODD)]
    for clue in invalid:
        with pytest.raises(ClueError):
            encoder.encode_clue(clue)
        with pytest.raises(ClueError):
            evaluator.evaluate(clue, dict.fromkeys(all_cells(3), False))
    valid = Clue("fact", ClueType.FACT, cells=("A1",), status=Status.CRIMINAL)
    for assignment in ({}, dict.fromkeys(all_cells(3), 0), dict.fromkeys(all_cells(3), Status.INNOCENT)):
        with pytest.raises(ClueError):
            evaluator.evaluate(valid, assignment)
    with pytest.raises(ClueError):
        encoder.build_kb([valid, valid], {})
    with pytest.raises(TypeError):
        encoder.unit_clause("A1", True)


def test_b10_larger_boards_have_bounded_encoding():
    rng = random.Random(2026)
    for n in (4, 5):
        cells = all_cells(n)
        region = Region(RegionKind.EXPLICIT, cells)
        assignments = [dict.fromkeys(cells, False), dict.fromkeys(cells, True)]
        assignments += [dict(zip(cells, (rng.choice((False, True)) for _ in cells))) for _ in range(20)]
        clues = [Clue("large", ClueType.EXACTLY, region=region, k=n*n//2),
                 Clue("parity", ClueType.PARITY, region=region, parity=Parity.EVEN),
                 Clue("compare", ClueType.COMPARE, left=region,
                      right=Region(RegionKind.ROW, 1), op=CompareOp.GT)]
        for clue in clues:
            _check_clue(clue, assignments, n)
            kb = CNFEncoder(n).build_kb([clue], {})
            assert kb.num_aux < 4 * (n*n)**2
            assert kb.num_clauses < 12 * (n*n)**2


def test_b11_only_public_snapshot_enters_kb():
    from engine.game_engine import GameEngine
    engine = GameEngine()
    state = engine.load(Path(__file__).resolve().parents[1] / "puzzles/examples/3x3_chain.json")
    kb = CNFEncoder(state.n).build_kb(tuple(state.revealed_clues.values()), state.known_statuses)
    # Only A1's public FACT(B1=CRIMINAL) and A1=INNOCENT are active.
    assert kb.clauses == ((2,), (-1,))
    assert kb.num_aux == 0

