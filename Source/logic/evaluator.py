"""Direct clue semantics, independent of the CNF encoder and SAT solver."""

from typing import Mapping

from common.errors import ClueError
from common.regions import all_cells, resolve_region
from common.types import Cell, Clue, ClueType, CompareOp, Parity, status_to_bool
from common.validation import validate_clue
from logic.varmap import VarMap


class SemanticEvaluator:
    def __init__(self, n: int) -> None:
        self.n = VarMap(n).n

    def evaluate(self, clue: Clue, assignment: Mapping[Cell, bool]) -> bool:
        """Require a complete, strictly Boolean assignment of this board."""
        validate_clue(clue, self.n)
        if set(assignment) != set(all_cells(self.n)):
            raise ClueError("Assignment must contain exactly all board cells")
        if any(type(value) is not bool for value in assignment.values()):
            raise ClueError("Assignment values must be bool, not Status or integers")

        kind = clue.type
        if kind is ClueType.FACT:
            return assignment[clue.cells[0]] == status_to_bool(clue.status)
        if kind is ClueType.SAME:
            return assignment[clue.cells[0]] == assignment[clue.cells[1]]
        if kind is ClueType.DIFFERENT:
            return assignment[clue.cells[0]] != assignment[clue.cells[1]]

        def count(region):
            return sum(assignment[c] for c in resolve_region(region, self.n))

        if kind is ClueType.COMPARE:
            left, right = count(clue.left), count(clue.right)
            return {
                CompareOp.EQ: left == right,
                CompareOp.LT: left < right,
                CompareOp.LE: left <= right,
                CompareOp.GT: left > right,
                CompareOp.GE: left >= right,
            }[clue.op]
        total = count(clue.region)
        if kind is ClueType.EXACTLY:
            return total == clue.k
        if kind is ClueType.AT_LEAST:
            return total >= clue.k
        if kind is ClueType.AT_MOST:
            return total <= clue.k
        return total % 2 == (1 if clue.parity is Parity.ODD else 0)
