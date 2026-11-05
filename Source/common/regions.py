"""Coordinates, regions, and clue reference resolution."""

from __future__ import annotations

import re
from typing import Iterable, Sequence
from common.errors import ClueError
from common.types import Cell, Clue, ClueType, Region, RegionKind

CELL_PATTERN = re.compile(r"^([A-Z])([1-9][0-9]*)$")


def validate_cell_format(cell: str) -> tuple[str, int]:
    """Validate canonical cell format (single uppercase letter + 1-based number).
    
    Rejects lowercase, whitespace, leading zeros like A01, etc.
    """
    if not isinstance(cell, str):
        raise ClueError(f"Cell must be a string, got {type(cell).__name__}")
    match = CELL_PATTERN.match(cell)
    if not match:
        raise ClueError(f"Invalid canonical cell format: {cell!r}")
    col_str, row_str = match.groups()
    if row_str.startswith("0"):
        raise ClueError(f"Leading zeros not allowed in cell: {cell!r}")
    return col_str, int(row_str)


def cell_to_index(cell: Cell, n: int) -> tuple[int, int]:
    """Convert canonical cell string to 0-based (row, col)."""
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ClueError(f"Grid size n must be positive int, got {n!r}")
    col_str, row_num = validate_cell_format(cell)
    col = ord(col_str) - ord("A")
    row = row_num - 1
    if not (0 <= row < n and 0 <= col < n):
        raise ClueError(f"Cell {cell!r} is out of bounds for {n}x{n} grid")
    return row, col


def index_to_cell(row: int, col: int, n: int) -> Cell:
    """Convert 0-based (row, col) to canonical cell string."""
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ClueError(f"Grid size n must be positive int, got {n!r}")
    if isinstance(row, bool) or not isinstance(row, int) or not (0 <= row < n):
        raise ClueError(f"Row {row!r} out of bounds for {n}x{n} grid")
    if isinstance(col, bool) or not isinstance(col, int) or not (0 <= col < n):
        raise ClueError(f"Col {col!r} out of bounds for {n}x{n} grid")
    return f"{chr(ord('A') + col)}{row + 1}"


def all_cells(n: int) -> tuple[Cell, ...]:
    """Return all cells in an n x n grid in row-major order: A1, B1, ..., A2, B2, ..."""
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ClueError(f"Grid size n must be positive int, got {n!r}")
    return tuple(index_to_cell(r, c, n) for r in range(n) for c in range(n))


def sort_cells_row_major(cells: Iterable[Cell], n: int) -> tuple[Cell, ...]:
    """Sort an iterable of cells according to row-major order."""
    indices = {cell: cell_to_index(cell, n) for cell in cells}
    return tuple(sorted(cells, key=lambda c: (indices[c][0], indices[c][1])))


def row_cells(row: int, n: int) -> tuple[Cell, ...]:
    """Return all cells in the specified 1-based row, in row-major order."""
    if isinstance(row, bool) or not isinstance(row, int):
        raise ClueError(f"Row must be an integer, got {row!r}")
    if not (1 <= row <= n):
        raise ClueError(f"Row {row} is out of bounds for {n}x{n} grid (1..{n})")
    r = row - 1
    return tuple(index_to_cell(r, c, n) for c in range(n))


def col_cells(col: str, n: int) -> tuple[Cell, ...]:
    """Return all cells in the specified column letter, in row-major order."""
    if not isinstance(col, str) or len(col) != 1 or not ("A" <= col <= "Z"):
        raise ClueError(f"Column must be a single uppercase letter, got {col!r}")
    c = ord(col) - ord("A")
    if not (0 <= c < n):
        max_col = chr(ord("A") + n - 1)
        raise ClueError(f"Column {col!r} out of bounds for {n}x{n} grid (A..{max_col})")
    return tuple(index_to_cell(r, c, n) for r in range(n))


def neighbor_cells(cell: Cell, n: int) -> tuple[Cell, ...]:
    """Return the neighboring cells (horizontal, vertical, diagonal) of cell, excluding cell itself.
    
    Ordered in row-major.
    """
    row, col = cell_to_index(cell, n)
    neighbors: list[tuple[int, int]] = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, col + dc
            if 0 <= nr < n and 0 <= nc < n:
                neighbors.append((nr, nc))
    # Sort row-major (r ascending, c ascending)
    neighbors.sort()
    return tuple(index_to_cell(r, c, n) for r, c in neighbors)


def resolve_region(region: Region, n: int) -> tuple[Cell, ...]:
    """Resolve a Region to a concrete tuple of cells in row-major order."""
    if not isinstance(region, Region):
        raise ClueError(f"Expected Region instance, got {type(region).__name__}")
    
    if region.kind is RegionKind.ROW:
        if isinstance(region.arg, bool) or not isinstance(region.arg, int):
            raise ClueError(f"ROW region arg must be an int, got {region.arg!r}")
        return row_cells(region.arg, n)

    if region.kind is RegionKind.COL:
        if not isinstance(region.arg, str):
            raise ClueError(f"COL region arg must be a string, got {region.arg!r}")
        return col_cells(region.arg, n)

    if region.kind is RegionKind.NEIGHBORS:
        if not isinstance(region.arg, str):
            raise ClueError(f"NEIGHBORS region arg must be a cell string, got {region.arg!r}")
        return neighbor_cells(region.arg, n)

    if region.kind is RegionKind.EXPLICIT:
        if not isinstance(region.arg, (tuple, list)):
            raise ClueError(f"EXPLICIT region arg must be a sequence of cells, got {type(region.arg).__name__}")
        if len(region.arg) == 0:
            raise ClueError("EXPLICIT region cannot be empty")
        
        # Verify no duplicates
        seen: set[str] = set()
        for c in region.arg:
            if not isinstance(c, str):
                raise ClueError(f"EXPLICIT cell must be string, got {c!r}")
            cell_to_index(c, n)  # Validates format and bounds
            if c in seen:
                raise ClueError(f"Duplicate cell {c!r} in EXPLICIT region")
            seen.add(c)
        return sort_cells_row_major(region.arg, n)

    raise ClueError(f"Unknown RegionKind: {region.kind}")


def referenced_cells(clue: Clue, n: int) -> tuple[Cell, ...]:
    """Return all cells referenced or counted by the clue, deduplicated, in row-major order."""
    if not isinstance(clue, Clue):
        raise ClueError(f"Expected Clue instance, got {type(clue).__name__}")

    if clue.type in (ClueType.FACT, ClueType.SAME, ClueType.DIFFERENT):
        for c in clue.cells:
            cell_to_index(c, n)
        return sort_cells_row_major(set(clue.cells), n)

    if clue.type in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST, ClueType.PARITY):
        if clue.region is None:
            raise ClueError(f"Clue {clue.id} of type {clue.type.value} requires a region")
        return resolve_region(clue.region, n)

    if clue.type is ClueType.COMPARE:
        if clue.left is None or clue.right is None:
            raise ClueError(f"COMPARE clue {clue.id} requires both left and right regions")
        left_cells = resolve_region(clue.left, n)
        right_cells = resolve_region(clue.right, n)
        # Union of left and right, deduplicated and sorted row-major
        union_set = set(left_cells) | set(right_cells)
        return sort_cells_row_major(union_set, n)

    raise ClueError(f"Unknown ClueType: {clue.type}")

