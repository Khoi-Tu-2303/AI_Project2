"""Shared validation rules for cells, regions, clues, and puzzles."""

from __future__ import annotations

from typing import Mapping
from common.errors import ClueError, PuzzleError
from common.regions import all_cells, cell_to_index, resolve_region
from common.types import (
    Cell,
    Character,
    Clue,
    ClueType,
    CompareOp,
    Parity,
    Puzzle,
    Region,
    RegionKind,
    Status,
)


def validate_cell(cell: Cell, n: int) -> None:
    """Validate that cell is canonical and within 1..n bounds."""
    cell_to_index(cell, n)


def validate_region(region: Region, n: int) -> None:
    """Validate that region definition is syntactically and semantically valid."""
    if not isinstance(region, Region):
        raise ClueError(f"Expected Region instance, got {type(region).__name__}")
    if not isinstance(region.kind, RegionKind):
        raise ClueError(f"Invalid RegionKind: {region.kind!r}")
    # resolve_region validates arguments and bounds
    resolve_region(region, n)


def validate_clue(clue: Clue, n: int) -> None:
    """Validate that a Clue conforms strictly to its ClueType specification."""
    if not isinstance(clue, Clue):
        raise ClueError(f"Expected Clue instance, got {type(clue).__name__}")
    if not isinstance(clue.id, str) or not clue.id.strip():
        raise ClueError(f"Clue id must be a non-empty string, got {clue.id!r}")
    if not isinstance(clue.type, ClueType):
        raise ClueError(f"Invalid ClueType: {clue.type!r}")

    if clue.type is ClueType.FACT:
        if len(clue.cells) != 1:
            raise ClueError(f"FACT clue {clue.id} must specify exactly 1 cell, got {len(clue.cells)}")
        validate_cell(clue.cells[0], n)
        if not isinstance(clue.status, Status):
            raise ClueError(f"FACT clue {clue.id} must specify valid Status, got {clue.status!r}")
        if clue.region is not None or clue.k is not None or clue.parity is not None or clue.left is not None or clue.right is not None or clue.op is not None:
            raise ClueError(f"FACT clue {clue.id} contains irrelevant fields")

    elif clue.type in (ClueType.SAME, ClueType.DIFFERENT):
        if len(clue.cells) != 2:
            raise ClueError(f"{clue.type.value} clue {clue.id} must specify exactly 2 cells, got {len(clue.cells)}")
        validate_cell(clue.cells[0], n)
        validate_cell(clue.cells[1], n)
        if clue.cells[0] == clue.cells[1]:
            raise ClueError(f"{clue.type.value} clue {clue.id} cells must be distinct: {clue.cells[0]}")
        if clue.status is not None or clue.region is not None or clue.k is not None or clue.parity is not None or clue.left is not None or clue.right is not None or clue.op is not None:
            raise ClueError(f"{clue.type.value} clue {clue.id} contains irrelevant fields")

    elif clue.type in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        if clue.region is None:
            raise ClueError(f"{clue.type.value} clue {clue.id} requires a region")
        validate_region(clue.region, n)
        if isinstance(clue.k, bool) or not isinstance(clue.k, int):
            raise ClueError(f"{clue.type.value} clue {clue.id} k must be an int, got {clue.k!r}")
        region_size = len(resolve_region(clue.region, n))
        if not (0 <= clue.k <= region_size):
            raise ClueError(f"{clue.type.value} clue {clue.id} k={clue.k} out of range [0, {region_size}]")
        if clue.cells != () or clue.status is not None or clue.parity is not None or clue.left is not None or clue.right is not None or clue.op is not None:
            raise ClueError(f"{clue.type.value} clue {clue.id} contains irrelevant fields")

    elif clue.type is ClueType.PARITY:
        if clue.region is None:
            raise ClueError(f"PARITY clue {clue.id} requires a region")
        validate_region(clue.region, n)
        if not isinstance(clue.parity, Parity):
            raise ClueError(f"PARITY clue {clue.id} requires valid Parity (EVEN/ODD), got {clue.parity!r}")
        if clue.cells != () or clue.status is not None or clue.k is not None or clue.left is not None or clue.right is not None or clue.op is not None:
            raise ClueError(f"PARITY clue {clue.id} contains irrelevant fields")

    elif clue.type is ClueType.COMPARE:
        if clue.left is None or clue.right is None:
            raise ClueError(f"COMPARE clue {clue.id} requires both left and right regions")
        validate_region(clue.left, n)
        validate_region(clue.right, n)
        if not isinstance(clue.op, CompareOp):
            raise ClueError(f"COMPARE clue {clue.id} requires valid CompareOp, got {clue.op!r}")
        if clue.cells != () or clue.status is not None or clue.region is not None or clue.k is not None or clue.parity is not None:
            raise ClueError(f"COMPARE clue {clue.id} contains irrelevant fields")

    else:
        raise ClueError(f"Unknown ClueType: {clue.type}")


def validate_puzzle_structure(puzzle: Puzzle) -> None:
    """Validate the complete Puzzle structure and consistency."""
    if not isinstance(puzzle, Puzzle):
        raise PuzzleError(f"Expected Puzzle instance, got {type(puzzle).__name__}")

    # schema_version must be strict int == 2
    if isinstance(puzzle.schema_version, bool) or not isinstance(puzzle.schema_version, int) or puzzle.schema_version != 2:
        raise PuzzleError(f"schema_version must be int 2, got {puzzle.schema_version!r}")

    # id must be non-empty string
    if not isinstance(puzzle.id, str) or not puzzle.id.strip():
        raise PuzzleError(f"Puzzle id must be a non-empty string, got {puzzle.id!r}")

    # n must be int in {3, 4, 5}
    if isinstance(puzzle.n, bool) or not isinstance(puzzle.n, int) or puzzle.n not in (3, 4, 5):
        raise PuzzleError(f"Puzzle n must be 3, 4, or 5; got {puzzle.n!r}")

    n = puzzle.n
    expected_cells = all_cells(n)
    num_cells = n * n

    # Characters validation
    if not isinstance(puzzle.characters, (tuple, list)) or len(puzzle.characters) != num_cells:
        raise PuzzleError(f"Puzzle must have exactly {num_cells} characters, got {len(puzzle.characters) if hasattr(puzzle, 'characters') else 'none'}")

    seen_char_cells: set[str] = set()
    prev_name_casefold: str | None = None

    for idx, char in enumerate(puzzle.characters):
        if not isinstance(char, Character):
            raise PuzzleError(f"Character {idx} is not Character instance")
        expected_cell = expected_cells[idx]
        if char.cell != expected_cell:
            raise PuzzleError(f"Character {idx} must be for cell {expected_cell}, got {char.cell}")
        if char.cell in seen_char_cells:
            raise PuzzleError(f"Duplicate character cell {char.cell}")
        seen_char_cells.add(char.cell)

        if not isinstance(char.name, str) or not char.name.strip():
            raise PuzzleError(f"Character at {char.cell} has empty name")
        if not isinstance(char.profession, str) or not char.profession.strip():
            raise PuzzleError(f"Character at {char.cell} has empty profession")

        name_cf = char.name.casefold()
        if prev_name_casefold is not None:
            if name_cf <= prev_name_casefold:
                raise PuzzleError(
                    f"Characters must be ordered alphabetically by name: '{char.name}' <= previous"
                )
        prev_name_casefold = name_cf

    # Clues validation
    if not isinstance(puzzle.clues, Mapping) or len(puzzle.clues) != num_cells:
        raise PuzzleError(f"Puzzle must contain exactly {num_cells} clues, got {len(puzzle.clues) if hasattr(puzzle, 'clues') else 'none'}")

    seen_clue_ids: set[str] = set()
    for cell in expected_cells:
        if cell not in puzzle.clues:
            raise PuzzleError(f"Missing clue for cell {cell}")
        clue = puzzle.clues[cell]
        validate_clue(clue, n)
        if clue.id in seen_clue_ids:
            raise PuzzleError(f"Duplicate clue id {clue.id!r}")
        seen_clue_ids.add(clue.id)

    # Initial revealed validation
    if not isinstance(puzzle.initial_revealed, Mapping):
        raise PuzzleError("initial_revealed must be a mapping of Cell to Status")
    if len(puzzle.initial_revealed) == 0:
        raise PuzzleError("initial_revealed cannot be empty")
    for cell, status in puzzle.initial_revealed.items():
        if cell not in expected_cells:
            raise PuzzleError(f"initial_revealed cell {cell!r} not in grid")
        if not isinstance(status, Status):
            raise PuzzleError(f"initial_revealed status for {cell} must be Status enum, got {status!r}")

    # Solution validation (optional, but if present must be complete and consistent)
    if puzzle.solution is not None:
        if not isinstance(puzzle.solution, Mapping) or len(puzzle.solution) != num_cells:
            raise PuzzleError(f"solution must have exactly {num_cells} cells if present")
        for cell in expected_cells:
            if cell not in puzzle.solution:
                raise PuzzleError(f"solution missing cell {cell}")
            sol_status = puzzle.solution[cell]
            if not isinstance(sol_status, Status):
                raise PuzzleError(f"solution status for {cell} must be Status enum, got {sol_status!r}")

        # Check initial_revealed matches solution
        for cell, status in puzzle.initial_revealed.items():
            if puzzle.solution[cell] != status:
                raise PuzzleError(
                    f"initial_revealed {cell}={status.value} contradicts solution {puzzle.solution[cell].value}"
                )

