"""Acceptance tests for Module C (DPLLSolver and EntailmentChecker) (G-C)."""

import pytest

try:
    import logic.dpll  # type: ignore
    import logic.entailment  # type: ignore
    HAS_MODULE_C = True
except ImportError:
    HAS_MODULE_C = False


@pytest.mark.skipif(not HAS_MODULE_C, reason="Module C (logic.dpll/entailment) not yet implemented (BLOCKED)")
def test_c01_empty_contradictory_cases() -> None:
    """C-01: [] SAT, [[]] UNSAT, [x] & [-x] UNSAT, complete model assignment."""
    from logic.dpll import solve_cnf

    assert solve_cnf([], 4).is_sat
    assert solve_cnf([[]], 4).is_unsat
    assert solve_cnf([[1], [-1]], 4).is_unsat
    result = solve_cnf([[1], [-2, 3]], 4)
    assert result.is_sat and set(result.model) == {1, 2, 3, 4}
    assert all(any(result.model[abs(l)] == (l > 0) for l in c) for c in [[1], [-2, 3]])


@pytest.mark.skipif(not HAS_MODULE_C, reason="Module C (logic.dpll/entailment) not yet implemented (BLOCKED)")
def test_c03_pdf_example() -> None:
    """C-03: (A or B) and (-A or B): B is criminal, A is unknown."""
    from common.types import Classification, KnowledgeBase
    from logic.entailment import EntailmentChecker

    # A = A1 (var 1), B = B1 (var 2) on a 3x3 board
    checker = EntailmentChecker(KnowledgeBase(3, ((1, 2), (-1, 2)), 9, 0))
    assert checker.classify_cell("B1") is Classification.CRIMINAL
    assert checker.classify_cell("A1") is Classification.UNKNOWN
    assert checker.entails(2) and not checker.entails(1) and not checker.entails(-1)

