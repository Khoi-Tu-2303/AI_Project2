"""Deterministic primary variables and a separate auxiliary namespace."""

from common.errors import ClueError
from common.regions import cell_to_index, index_to_cell
from common.types import Cell


class VarMap:
    def __init__(self, n: int) -> None:
        if type(n) is not int or n not in (3, 4, 5):
            raise ClueError("Grid size must be 3, 4, or 5")
        self._n = n
        self.reset_aux()

    @property
    def n(self) -> int:
        return self._n

    @property
    def num_primary(self) -> int:
        return self.n * self.n

    @property
    def num_vars(self) -> int:
        return self._next - 1

    @property
    def num_aux(self) -> int:
        return self.num_vars - self.num_primary

    def var(self, cell: Cell) -> int:
        row, col = cell_to_index(cell, self.n)
        return row * self.n + col + 1

    def cell(self, var: int) -> Cell:
        if type(var) is not int or not 1 <= var <= self.num_primary:
            raise ClueError("Expected a positive primary variable, not an auxiliary")
        row, col = divmod(var - 1, self.n)
        return index_to_cell(row, col, self.n)

    def new_aux(self) -> int:
        var = self._next
        self._next += 1
        return var

    def reset_aux(self) -> None:
        self._next = self.num_primary + 1
