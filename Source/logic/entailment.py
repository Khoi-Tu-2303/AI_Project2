"""Entailment checking and cell classification on top of the DPLL solver.

For a knowledge base KB and a primary literal l:

    KB |= l   <=>   KB ∧ ¬l is UNSAT

Per unsolved cell x (variable v, True = Criminal):

    CRIMINAL  if KB ∧ ¬v is UNSAT
    INNOCENT  if KB ∧  v is UNSAT
    UNKNOWN   if both are SAT
    (the whole KB is INCONSISTENT when KB itself is UNSAT)

``EntailmentChecker.classify_cells`` returns exactly these answers but needs about
one SAT call per cell instead of two: every satisfying model found is a witness
for *both* its value of every cell, and a cell with witnesses for True and False
is UNKNOWN without further queries. Only the opposite of the witnessed value has
to be refuted for the remaining cells. A timeout is never reported as a proof:
it raises ``ReasoningFailure(TIMEOUT)`` (or yields a TIMEOUT report in
``EntailmentClassifier``).

For the deduction trace and the experiment tables the checker also records every
SAT query (``query_log``) and their summed cost (``stats``), and
``check_uniqueness`` decides whether a clue set has exactly one solution.

Only public data enters the classifier: a ``KnowledgeBase`` or a ``PublicState``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from common.errors import ReasoningFailure
from common.types import (
    Cell,
    Classification,
    ClassificationReport,
    KnowledgeBase,
    PublicState,
    ReasoningStatus,
    Status,
    bool_to_status,
    freeze_mapping,
)
from logic.dpll import DPLLSolver, SatStatus, SolveResult, SolveStats
from logic.encoder import CNFEncoder
from logic.varmap import VarMap


@dataclass(frozen=True)
class EntailmentStats:
    """Totals over every SAT call a checker made (for the trace and the experiments)."""
    sat_calls: int = 0                  # number of SAT queries issued
    solver: SolveStats = SolveStats()   # decisions, propagations, backtracks, runtime, summed


@dataclass(frozen=True)
class QueryRecord:
    """One SAT call: the literals assumed on top of the KB, and what came out."""
    assumptions: tuple[int, ...]   # () means "is the KB itself satisfiable?"
    status: SatStatus
    stats: SolveStats


class Uniqueness(Enum):
    """How many complete assignments satisfy a clue set."""
    NONE = "NONE"          # zero: the clues contradict each other
    UNIQUE = "UNIQUE"      # exactly one: a valid puzzle
    MULTIPLE = "MULTIPLE"  # two or more: the puzzle is ambiguous


@dataclass(frozen=True)
class UniquenessReport:
    status: Uniqueness
    # UNIQUE: the one solution. MULTIPLE: two different solutions as evidence. NONE: empty.
    solutions: tuple[Mapping[Cell, Status], ...] = ()


class EntailmentChecker:
    """Entailment queries over one immutable ``KnowledgeBase``.

    ``stats`` and ``query_log`` accumulate over every query made through this checker,
    so create one checker per classification if you want per-classification numbers.
    """

    def __init__(self, kb: KnowledgeBase) -> None:
        """Create one solver for the KB; all queries below reuse it."""
        self._kb = kb
        self._varmap = VarMap(kb.n)
        # Branch on primary variables first; auxiliaries are functionally determined.
        self._solver = DPLLSolver(
            kb.clauses, kb.num_vars, decision_vars=range(1, kb.num_primary + 1)
        )
        self._sat_calls = 0                 # running totals, exposed through ``stats``
        self._solver_stats = SolveStats()
        self._log: list[QueryRecord] = []

    @property
    def kb(self) -> KnowledgeBase:
        """The knowledge base being queried."""
        return self._kb

    @property
    def queries(self) -> int:
        """Number of SAT calls issued so far."""
        return self._sat_calls

    @property
    def stats(self) -> EntailmentStats:
        """Cost of all queries so far (a snapshot; later queries do not change it)."""
        return EntailmentStats(self._sat_calls, self._solver_stats)

    @property
    def query_log(self) -> tuple[QueryRecord, ...]:
        """Every SAT query so far, in order (a snapshot)."""
        return tuple(self._log)

    # ---- helpers

    def _solve(self, assumptions: Sequence[int], deadline: float | None) -> SolveResult:
        """Run one SAT call, record it, and add its cost to the totals.

        A timeout becomes an exception, never a "proof"; its cost is still counted.
        """
        result = self._solver.solve(assumptions, deadline=deadline)
        self._sat_calls += 1
        self._solver_stats = self._solver_stats + result.stats
        self._log.append(QueryRecord(tuple(assumptions), result.status, result.stats))
        if result.status is SatStatus.TIMEOUT:
            raise ReasoningFailure(ReasoningStatus.TIMEOUT, "SAT search exceeded the deadline")
        return result

    def _primary(self, var: int) -> int:
        """Return var if it is a cell literal (not an auxiliary variable)."""
        if type(var) is not int or not 1 <= abs(var) <= self._kb.num_primary:
            raise ValueError(f"Expected a primary literal, got {var!r}")
        return var

    def _solution(self, model: Mapping[int, bool]) -> Mapping[Cell, Status]:
        """Project a full model onto the cells: {cell: CRIMINAL or INNOCENT}."""
        return freeze_mapping({
            self._varmap.cell(v): bool_to_status(model[v])
            for v in range(1, self._kb.num_primary + 1)
        })

    # ---- basic queries

    def is_consistent(self, *, deadline: float | None = None) -> bool:
        """True iff the KB is satisfiable."""
        return self._solve((), deadline).is_sat

    def satisfiable_with(self, literal: int, *, deadline: float | None = None) -> bool:
        """True iff KB ∧ literal is satisfiable (``literal`` is a primary literal)."""
        return self._solve((self._primary(literal),), deadline).is_sat

    def entails(self, literal: int, *, deadline: float | None = None) -> bool:
        """KB |= literal, i.e. KB ∧ ¬literal is UNSAT.

        An inconsistent KB entails everything (ex falso); callers that care should
        check ``is_consistent`` first (``classify_cells`` does).
        """
        return self._solve((-self._primary(literal),), deadline).is_unsat

    # ---- cell classification

    def classify_cell(self, cell: Cell, *, deadline: float | None = None) -> Classification:
        """Classify one cell with the two textbook queries. Raises if the KB is UNSAT."""
        # Can the cell be Criminal? Can it be Innocent? Both -> UNKNOWN.
        var = self._varmap.var(cell)
        if not self.is_consistent(deadline=deadline):
            raise ReasoningFailure(ReasoningStatus.INCONSISTENT, "Knowledge base is unsatisfiable")
        can_be_true = self.satisfiable_with(var, deadline=deadline)
        can_be_false = self.satisfiable_with(-var, deadline=deadline)
        return self._label(can_be_true, can_be_false)

    @staticmethod
    def _label(can_be_true: bool, can_be_false: bool) -> Classification:
        """Turn "which values are possible" into a Classification."""
        if can_be_true and can_be_false:
            return Classification.UNKNOWN
        if can_be_true:
            return Classification.CRIMINAL
        if can_be_false:
            return Classification.INNOCENT
        raise AssertionError("unreachable: consistent KB admits a value for every cell")

    def classify_cells(
        self, cells: Sequence[Cell], *, deadline: float | None = None
    ) -> Mapping[Cell, Classification]:
        """Classify ``cells`` (any cells, in the given order).

        Raises ``ReasoningFailure(INCONSISTENT)`` if the KB is UNSAT and
        ``ReasoningFailure(TIMEOUT)`` on deadline expiry.
        """
        variables = {cell: self._varmap.var(cell) for cell in cells}

        # Step 1: the KB must be satisfiable; its model is our first witness.
        base = self._solve((), deadline)
        if not base.is_sat:
            raise ReasoningFailure(ReasoningStatus.INCONSISTENT, "Knowledge base is unsatisfiable")

        # seen[v] = values that variable v took in some model found so far.
        seen: dict[int, set[bool]] = {v: set() for v in variables.values()}

        def record(model: Mapping[int, bool]) -> None:
            """Remember every cell's value in this model."""
            for v, values in seen.items():
                values.add(model[v])

        record(base.model)  # type: ignore[arg-type]
        out: dict[Cell, Classification] = {}

        # Step 2: per cell, either both values were already seen, or test the other one.
        for cell, var in variables.items():
            values = seen[var]
            if len(values) == 2:
                out[cell] = Classification.UNKNOWN
                continue
            witnessed = next(iter(values))
            # Try to find a model with the opposite value; if none exists it is forced.
            result = self._solve((-var if witnessed else var,), deadline)
            if result.is_sat:
                record(result.model)  # type: ignore[arg-type]
                out[cell] = Classification.UNKNOWN
            else:
                out[cell] = Classification.CRIMINAL if witnessed else Classification.INNOCENT
        return out

    # ---- uniqueness

    def check_uniqueness(self, *, deadline: float | None = None) -> UniquenessReport:
        """Does the KB have no, exactly one, or several complete assignments?

        Build the KB from the *complete* clue set (no known statuses) to check a puzzle.
        Idea: take any solution; it is the only one iff every cell is forced to its
        value, i.e. no query "KB ∧ (this cell takes the other value)" is satisfiable.
        That is at most 1 + n² SAT calls. If some query is SAT, its model is a second,
        different solution and both are returned as evidence.
        """
        first = self._solve((), deadline)
        if not first.is_sat:
            return UniquenessReport(Uniqueness.NONE)
        for var in range(1, self._kb.num_primary + 1):
            other = self._solve((-var if first.model[var] else var,), deadline)  # type: ignore[index]
            if other.is_sat:
                return UniquenessReport(
                    Uniqueness.MULTIPLE,
                    (self._solution(first.model), self._solution(other.model)),  # type: ignore[arg-type]
                )
        return UniquenessReport(Uniqueness.UNIQUE, (self._solution(first.model),))  # type: ignore[arg-type]


class EntailmentClassifier:
    """``common.protocols.Classifier`` backed by CNF encoding + DPLL entailment.

    Builds the KB from the public snapshot only and returns a report that always
    carries the snapshot token. Reasoning failures become non-READY reports (the
    engine turns those into ``ReasoningFailure``); programming errors propagate.

    After each call (None before the first), also when it ended in INCONSISTENT
    or TIMEOUT, these describe that call, for the trace and experiment tables:
      last_kb      the CNF that was built (variable and clause counts)
      last_stats   summed SAT cost
      last_queries every SAT query, in order
    """

    def __init__(self) -> None:
        self.last_kb: KnowledgeBase | None = None
        self.last_stats: EntailmentStats | None = None
        self.last_queries: tuple[QueryRecord, ...] | None = None

    def __call__(
        self, state: PublicState, *, deadline: float | None = None
    ) -> ClassificationReport:
        """Public state -> CNF -> classify every unsolved cell -> report."""
        encoder = CNFEncoder(state.n)
        kb = encoder.build_kb(tuple(state.revealed_clues.values()), state.known_statuses)
        checker = EntailmentChecker(kb)
        try:
            by_cell = checker.classify_cells(state.unsolved, deadline=deadline)
        except ReasoningFailure as failure:
            self._remember(kb, checker)
            # INCONSISTENT / TIMEOUT: report it, with no cell classifications.
            return ClassificationReport(
                token=state.token,
                status=failure.status,
                by_cell={},
                message=failure.message,
            )
        self._remember(kb, checker)
        return ClassificationReport(token=state.token, status=ReasoningStatus.READY, by_cell=by_cell)

    def _remember(self, kb: KnowledgeBase, checker: EntailmentChecker) -> None:
        self.last_kb = kb
        self.last_stats = checker.stats
        self.last_queries = checker.query_log


def classify_state(
    state: PublicState, *, deadline: float | None = None
) -> ClassificationReport:
    """Functional form of :class:`EntailmentClassifier`."""
    return EntailmentClassifier()(state, deadline=deadline)  # one-off call, no object to keep
