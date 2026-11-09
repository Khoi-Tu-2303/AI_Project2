"""Hand-written DPLL SAT solver (unit propagation + recursive branching and backtracking).

Literals are signed non-zero ints: 5 means "variable 5 is True", -5 means "False".
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import sys
import time
from typing import Iterable, Mapping, Sequence


class SatStatus(Enum):
    """Outcome of a solve call."""
    SAT = "SAT"          # a satisfying model exists
    UNSAT = "UNSAT"      # proven: no model exists
    TIMEOUT = "TIMEOUT"  # ran out of time, nothing is proven


@dataclass(frozen=True)
class SolveStats:
    """Counters for one solve() call, useful for experiments and reports."""
    decisions: int = 0        # variables the solver had to guess a value for
    conflicts: int = 0        # propagations that ended in a conflict
    propagations: int = 0     # literals assigned (decisions, assumptions and forced units)
    backtracks: int = 0       # branches abandoned (one value of one variable undone)
    runtime_seconds: float = 0.0  # wall-clock time of the whole solve() call

    def __add__(self, other: SolveStats) -> SolveStats:
        """Field-by-field sum, used to accumulate stats over several solve() calls."""
        return SolveStats(
            decisions=self.decisions + other.decisions,
            conflicts=self.conflicts + other.conflicts,
            propagations=self.propagations + other.propagations,
            backtracks=self.backtracks + other.backtracks,
            runtime_seconds=self.runtime_seconds + other.runtime_seconds,
        )


@dataclass(frozen=True)
class SolveResult:
    """What solve() returns: status, a model (only if SAT) and stats."""
    status: SatStatus
    model: Mapping[int, bool] | None = None  # complete over 1..num_vars when SAT
    stats: SolveStats = SolveStats()

    @property
    def is_sat(self) -> bool:
        return self.status is SatStatus.SAT

    @property
    def is_unsat(self) -> bool:
        return self.status is SatStatus.UNSAT

    @property
    def is_timeout(self) -> bool:
        return self.status is SatStatus.TIMEOUT


class DPLLSolver:
    """DPLL over a fixed CNF; ``solve()`` may be called repeatedly with assumptions."""

    def __init__(
        self,
        clauses: Iterable[Sequence[int]],
        num_vars: int,
        decision_vars: Iterable[int] | None = None,
    ) -> None:
        """Load the CNF once and propagate its unit clauses (the "root" state)."""

        self._num_vars = num_vars

        # Solver state: clause store, assignment, trail.
        self._clauses: list[list[int]] = []  # only clauses of length >= 2
        self._assign: list[int] = [0] * (num_vars + 1)  # 0 unassigned, 1 True, -1 False
        self._trail: list[int] = []  # literals in the order they were made true
        self._propagations = 0       # counters for SolveStats
        self._decisions = 0
        self._conflicts = 0
        self._backtracks = 0

        # Variables we branch on first (the rest follow in ascending order).
        self._order = self._build_order(decision_vars)
        self._root_ok = True  # False if the CNF is already contradictory

        # Sort clauses: empty -> UNSAT, unit -> root fact, longer -> stored.
        root_units: list[int] = []
        for raw in clauses:
            clause = self._normalise(raw)
            if clause is None:  # tautology
                continue
            if not clause:
                self._root_ok = False
            elif len(clause) == 1:
                root_units.append(clause[0])
            else:
                self._clauses.append(clause)

        # Apply root facts once; every solve() starts from here.
        if self._root_ok:
            self._root_ok = all(self._enqueue(u) for u in root_units) and self._propagate()
        self._root_len = len(self._trail)

    def _check_literal(self, lit: object) -> int:
        """Return lit if it is a valid literal, else raise ValueError."""
        if type(lit) is not int or lit == 0 or abs(lit) > self._num_vars:
            raise ValueError(
                f"Invalid literal {lit!r}: expected a non-zero int with |lit| <= {self._num_vars}"
            )
        return lit

    def _normalise(self, raw: Sequence[int]) -> list[int] | None:
        """Drop duplicate literals; return None for a tautology."""
        seen: set[int] = set()   # literals met so far (fast membership test)
        unique: list[int] = []   # the same literals, in original order
        for lit in raw:
            self._check_literal(lit)
            if -lit in seen:     # x and -x in one clause: always true
                return None
            if lit not in seen:  # skip a repeated literal
                seen.add(lit)
                unique.append(lit)
        return unique

    def _build_order(self, decision_vars: Iterable[int] | None) -> list[int]:
        """Branching order: given variables first, then all others ascending."""
        first: list[int] = []
        taken: set[int] = set()
        for v in decision_vars or ():
            self._check_literal(v)
            if v < 0:
                raise ValueError(f"decision_vars must be positive variables, got {v}")
            if v not in taken:
                taken.add(v)
                first.append(v)
        return first + [v for v in range(1, self._num_vars + 1) if v not in taken]

    def _value(self, lit: int) -> int:
        """1 if lit is true, -1 if false, 0 if its variable is unassigned."""
        v = self._assign[abs(lit)]  # value of the variable (ignore the sign)
        if lit > 0:
            return v  # positive literal: same value as its variable
        else:
            return -v  # negative literal: opposite of its variable (true when variable is false)

    def _enqueue(self, lit: int) -> bool:
        """Make ``lit`` true. False if it is already false (conflict)."""
        val = self._value(lit)
        if val == 1:
            return True
        if val == -1:
            return False
        self._assign[abs(lit)] = 1 if lit > 0 else -1
        self._trail.append(lit)
        self._propagations += 1
        return True

    def _undo_to(self, trail_len: int) -> None:
        """Backtrack: unassign everything after the first ``trail_len`` literals."""
        trail, assign = self._trail, self._assign
        while len(trail) > trail_len:
            lit = trail.pop()
            assign[abs(lit)] = 0

    def _propagate(self) -> bool:
        """Unit propagation: rescan all clauses until nothing changes. False on conflict."""
        changed = True
        while changed:
            changed = False
            for clause in self._clauses:
                unassigned = 0  # literals of this clause without a value yet
                last_free = 0   # the most recent unassigned literal
                satisfied = False
                for lit in clause:
                    val = self._value(lit)
                    if val == 1:
                        satisfied = True
                        break
                    if val == 0:
                        unassigned += 1
                        last_free = lit
                if satisfied:
                    continue
                if unassigned == 0:  # every literal is false -> conflict
                    return False
                if unassigned == 1:  # unit clause: the free literal is forced true
                    self._enqueue(last_free)
                    changed = True
        return True

    def _pick_branch_var(self) -> int:
        """First unassigned variable in branching order; 0 if all are assigned."""
        assign = self._assign
        for v in self._order:
            if assign[v] == 0:
                return v
        return 0

    def solve(
        self,
        assumptions: Sequence[int] = (),
        *,
        deadline: float | None = None,
    ) -> SolveResult:
        """Decide satisfiability of ``CNF ∧ assumptions`` (assumptions are unit literals).

        The solver state is restored afterwards, so the call can be repeated.
        """
        assumptions = tuple(self._check_literal(a) for a in assumptions)
        if not self._root_ok:  # CNF alone is already contradictory
            return SolveResult(SatStatus.UNSAT, None, SolveStats())
        if deadline is not None and time.monotonic() > deadline:
            return SolveResult(SatStatus.TIMEOUT, None, SolveStats())

        self._decisions = self._conflicts = self._backtracks = 0
        start_props = self._propagations
        start_time = time.perf_counter()
        status = SatStatus.UNSAT
        model: dict[int, bool] | None = None

        # The recursion is at most one level per variable, so make sure Python allows it.
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(old_limit, self._num_vars + 100))
        try:
            # Assume the given literals, propagate, then search only if no conflict yet.
            if all(self._enqueue(a) for a in assumptions) and self._propagate():
                status = self._dpll(deadline)
                if status is SatStatus.SAT:  # the assignment is still in place: read the model
                    model = {v: self._assign[v] == 1 for v in range(1, self._num_vars + 1)}
        finally:
            sys.setrecursionlimit(old_limit)
            self._undo_to(self._root_len)  # always return to the root state

        stats = SolveStats(
            decisions=self._decisions,
            conflicts=self._conflicts,
            propagations=self._propagations - start_props,
            backtracks=self._backtracks,
            runtime_seconds=time.perf_counter() - start_time,
        )
        return SolveResult(status, model, stats)

    def _dpll(self, deadline: float | None) -> SatStatus:
        """Recursive DPLL step.

        Precondition: unit propagation has finished without conflict.
        On SAT the full assignment is left in place so solve() can read the model;
        on UNSAT everything this call assigned has been undone.
        """
        if deadline is not None and time.monotonic() > deadline:
            return SatStatus.TIMEOUT

        # Every variable is assigned and no clause failed -> satisfiable.
        var = self._pick_branch_var()
        if var == 0:
            return SatStatus.SAT

        self._decisions += 1
        mark = len(self._trail)  # where to backtrack to
        for lit in (-var, var):  # branch 1: False (Innocent), branch 2: True (Criminal)
            self._enqueue(lit)
            if self._propagate():
                status = self._dpll(deadline)  # go one level deeper
                if status is not SatStatus.UNSAT:  # SAT or TIMEOUT: stop searching
                    return status
            else:
                self._conflicts += 1
            self._undo_to(mark)  # this branch failed: backtrack and try the other value
            self._backtracks += 1
        return SatStatus.UNSAT  # both values failed: tell the caller to backtrack


def solve_cnf(
    clauses: Iterable[Sequence[int]],
    num_vars: int,
    assumptions: Sequence[int] = (),
    *,
    decision_vars: Iterable[int] | None = None,
    deadline: float | None = None,
) -> SolveResult:
    """One-shot convenience wrapper around :class:`DPLLSolver`."""
    return DPLLSolver(clauses, num_vars, decision_vars=decision_vars).solve(
        assumptions, deadline=deadline
    )
