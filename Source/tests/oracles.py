"""Test-only independent semantics and brute-force oracles.

This module MUST NOT be imported or used by production code, agents, or GUI.
"""

from __future__ import annotations

import itertools
import time
from typing import Mapping, Sequence

from common.errors import ClueError, ReasoningFailure
from common.regions import all_cells, resolve_region
from common.types import (
    Cell,
    Classification,
    ClassificationReport,
    Clue,
    ClueType,
    CompareOp,
    Parity,
    PublicState,
    ReasoningStatus,
    Status,
    status_to_bool,
)


def evaluate_clue_semantic(
    clue: Clue,
    assignment: Mapping[Cell, bool],
    n: int,
) -> bool:
    """Evaluate whether a clue is logically satisfied by a complete assignment."""
    if clue.type is ClueType.FACT:
        cell = clue.cells[0]
        if cell not in assignment:
            raise ClueError(f"Cell {cell} missing from assignment")
        expected_bool = status_to_bool(clue.status)  # type: ignore[arg-type]
        return assignment[cell] is expected_bool

    if clue.type is ClueType.SAME:
        c1, c2 = clue.cells
        return assignment[c1] is assignment[c2]

    if clue.type is ClueType.DIFFERENT:
        c1, c2 = clue.cells
        return assignment[c1] is not assignment[c2]

    if clue.type in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        cells = resolve_region(clue.region, n)  # type: ignore[arg-type]
        count = sum(1 for c in cells if assignment[c] is True)
        k = clue.k
        assert k is not None
        if clue.type is ClueType.EXACTLY:
            return count == k
        if clue.type is ClueType.AT_LEAST:
            return count >= k
        if clue.type is ClueType.AT_MOST:
            return count <= k

    if clue.type is ClueType.PARITY:
        cells = resolve_region(clue.region, n)  # type: ignore[arg-type]
        count = sum(1 for c in cells if assignment[c] is True)
        if clue.parity is Parity.EVEN:
            return count % 2 == 0
        if clue.parity is Parity.ODD:
            return count % 2 == 1
        raise ClueError(f"Invalid Parity: {clue.parity}")

    if clue.type is ClueType.COMPARE:
        left_cells = resolve_region(clue.left, n)  # type: ignore[arg-type]
        right_cells = resolve_region(clue.right, n)  # type: ignore[arg-type]
        left_cnt = sum(1 for c in left_cells if assignment[c] is True)
        right_cnt = sum(1 for c in right_cells if assignment[c] is True)
        if clue.op is CompareOp.EQ:
            return left_cnt == right_cnt
        if clue.op is CompareOp.LT:
            return left_cnt < right_cnt
        if clue.op is CompareOp.LE:
            return left_cnt <= right_cnt
        if clue.op is CompareOp.GT:
            return left_cnt > right_cnt
        if clue.op is CompareOp.GE:
            return left_cnt >= right_cnt
        raise ClueError(f"Invalid CompareOp: {clue.op}")

    raise ClueError(f"Unknown ClueType: {clue.type}")


def find_satisfying_models(
    state: PublicState,
    *,
    deadline: float | None = None,
) -> list[dict[Cell, bool]]:
    """Enumerate all satisfying models for the current public state (up to 3x3)."""
    n = state.n
    if n > 3:
        raise ValueError("Brute-force oracle only supports n <= 3 (up to 512 assignments)")

    cells = all_cells(n)
    satisfying_models: list[dict[Cell, bool]] = []

    # Iterate all 2^(n*n) binary assignments
    for values in itertools.product([False, True], repeat=len(cells)):
        if deadline is not None and time.monotonic() > deadline:
            raise ReasoningFailure(ReasoningStatus.TIMEOUT, "Oracle deadline exceeded")

        assignment = dict(zip(cells, values))

        # Check known statuses
        mismatch = False
        for c, st in state.known_statuses.items():
            if assignment[c] is not status_to_bool(st):
                mismatch = True
                break
        if mismatch:
            continue

        # Check revealed clues
        for clue in state.revealed_clues.values():
            if not evaluate_clue_semantic(clue, assignment, n):
                mismatch = True
                break
        if mismatch:
            continue

        satisfying_models.append(assignment)

    return satisfying_models


def classify_public_state_oracle(
    state: PublicState,
    *,
    deadline: float | None = None,
) -> ClassificationReport:
    """Classify all unrevealed cells using independent brute-force truth enumeration."""
    models = find_satisfying_models(state, deadline=deadline)

    if not models:
        return ClassificationReport(
            token=state.token,
            status=ReasoningStatus.INCONSISTENT,
            by_cell={},
            message="Public KB is unsatisfiable (no satisfying models)",
        )

    by_cell: dict[Cell, Classification] = {}
    for cell in state.unsolved:
        crim_possible = any(m[cell] is True for m in models)
        inno_possible = any(m[cell] is False for m in models)

        if crim_possible and not inno_possible:
            by_cell[cell] = Classification.CRIMINAL
        elif inno_possible and not crim_possible:
            by_cell[cell] = Classification.INNOCENT
        else:
            by_cell[cell] = Classification.UNKNOWN

    return ClassificationReport(
        token=state.token,
        status=ReasoningStatus.READY,
        by_cell=by_cell,
    )


class OracleClassifier:
    """Test-only callable classifier conforming to common.protocols.Classifier."""

    def __call__(
        self, state: PublicState, *, deadline: float | None = None
    ) -> ClassificationReport:
        return classify_public_state_oracle(state, deadline=deadline)


def brute_force_cnf_models(
    clauses: Sequence[Sequence[int]],
    num_vars: int,
    assumptions: Sequence[int] = (),
) -> list[dict[int, bool]]:
    """Tiny brute-force SAT solver for testing CNF logic on small variable counts."""
    if num_vars > 16:
        raise ValueError("Brute force CNF only supports num_vars <= 16")

    models: list[dict[int, bool]] = []
    # Variables are 1..num_vars
    for values in itertools.product([False, True], repeat=num_vars):
        # 1-indexed mapping
        assignment = {i + 1: values[i] for i in range(num_vars)}

        # Check assumptions
        assumptions_ok = True
        for lit in assumptions:
            var = abs(lit)
            expected = lit > 0
            if assignment[var] is not expected:
                assumptions_ok = False
                break
        if not assumptions_ok:
            continue

        # Check clauses
        clauses_ok = True
        for cl in clauses:
            if not cl:  # Empty clause is false
                clauses_ok = False
                break
            clause_sat = False
            for lit in cl:
                var = abs(lit)
                expected = lit > 0
                if assignment[var] is expected:
                    clause_sat = True
                    break
            if not clause_sat:
                clauses_ok = False
                break

        if clauses_ok:
            models.append(assignment)

    return models

