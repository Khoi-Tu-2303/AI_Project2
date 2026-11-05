"""Tests for cell coordinates, regions, and referenced_cells (A-02, A-03, A-04)."""

import pytest

from common.errors import ClueError
from common.regions import (
    all_cells,
    cell_to_index,
    col_cells,
    index_to_cell,
    neighbor_cells,
    referenced_cells,
    resolve_region,
    row_cells,
)
from common.types import (
    Clue,
    ClueType,
    CompareOp,
    Parity,
    Region,
    RegionKind,
    Status,
)


def test_cell_roundtrip_and_bounds() -> None:
    """A-02: Round-trip cell conversions, bounds, and row-major ordering."""
    for n in (3, 4, 5):
        cells = all_cells(n)
        assert len(cells) == n * n
        # First row then second row
        assert cells[0] == "A1"
        assert cells[1] == "B1"
        assert cells[n] == "A2"

        for idx, c in enumerate(cells):
            r, col = cell_to_index(c, n)
            assert index_to_cell(r, col, n) == c
            # Primary variable mapping: r * n + col + 1 == idx + 1
            assert r * n + col + 1 == idx + 1

    # Bounds errors
    with pytest.raises(ClueError):
        cell_to_index("D1", 3)
    with pytest.raises(ClueError):
        cell_to_index("A4", 3)
    with pytest.raises(ClueError):
        cell_to_index("a1", 3)  # lowercase forbidden
    with pytest.raises(ClueError):
        cell_to_index("A01", 3)  # leading zero forbidden
    with pytest.raises(ClueError):
        cell_to_index(" A1", 3)  # whitespace forbidden


def test_neighbor_counts_and_exclusion() -> None:
    """A-02: Corner (3), edge (5), interior (8) neighbors; cell itself excluded."""
    # 3x3 board
    # Corner: A1 -> B1, A2, B2 (3 neighbors)
    a1_nb = neighbor_cells("A1", 3)
    assert len(a1_nb) == 3
    assert a1_nb == ("B1", "A2", "B2")
    assert "A1" not in a1_nb

    # Edge: B1 -> A1, C1, A2, B2, C2 (5 neighbors)
    b1_nb = neighbor_cells("B1", 3)
    assert len(b1_nb) == 5
    assert b1_nb == ("A1", "C1", "A2", "B2", "C2")
    assert "B1" not in b1_nb

    # Interior: B2 -> 8 neighbors
    b2_nb = neighbor_cells("B2", 3)
    assert len(b2_nb) == 8
    assert b2_nb == ("A1", "B1", "C1", "A2", "C2", "A3", "B3", "C3")
    assert "B2" not in b2_nb


def test_region_validation() -> None:
    """A-03: Region resolution and invalid parameter rejection."""
    # ROW
    assert row_cells(1, 3) == ("A1", "B1", "C1")
    assert row_cells(2, 3) == ("A2", "B2", "C2")
    with pytest.raises(ClueError):
        row_cells(0, 3)
    with pytest.raises(ClueError):
        row_cells(4, 3)
    with pytest.raises(ClueError):
        row_cells(True, 3)  # bool not accepted as int

    # COL
    assert col_cells("A", 3) == ("A1", "A2", "A3")
    assert col_cells("B", 3) == ("B1", "B2", "B3")
    with pytest.raises(ClueError):
        col_cells("D", 3)
    with pytest.raises(ClueError):
        col_cells("a", 3)

    # EXPLICIT
    reg_exp = Region(kind=RegionKind.EXPLICIT, arg=("C1", "A1", "B2"))
    assert resolve_region(reg_exp, 3) == ("A1", "C1", "B2")

    # Empty explicit
    with pytest.raises(ClueError):
        resolve_region(Region(kind=RegionKind.EXPLICIT, arg=()), 3)

    # Duplicate explicit
    with pytest.raises(ClueError):
        resolve_region(Region(kind=RegionKind.EXPLICIT, arg=("A1", "A1")), 3)


def test_referenced_cells_for_all_8_clues() -> None:
    """A-04: referenced_cells returns exact union in row-major order for all 8 clue types."""
    n = 3

    # 1. FACT
    c_fact = Clue(id="f", type=ClueType.FACT, cells=("B2",), status=Status.CRIMINAL)
    assert referenced_cells(c_fact, n) == ("B2",)

    # 2. SAME
    c_same = Clue(id="s", type=ClueType.SAME, cells=("B2", "A1"))
    assert referenced_cells(c_same, n) == ("A1", "B2")

    # 3. DIFFERENT
    c_diff = Clue(id="d", type=ClueType.DIFFERENT, cells=("C3", "B1"))
    assert referenced_cells(c_diff, n) == ("B1", "C3")

    # 4. EXACTLY
    c_ex = Clue(id="e", type=ClueType.EXACTLY, region=Region(RegionKind.ROW, 1), k=1)
    assert referenced_cells(c_ex, n) == ("A1", "B1", "C1")

    # 5. AT_LEAST
    c_al = Clue(id="al", type=ClueType.AT_LEAST, region=Region(RegionKind.COL, "B"), k=1)
    assert referenced_cells(c_al, n) == ("B1", "B2", "B3")

    # 6. AT_MOST
    c_am = Clue(id="am", type=ClueType.AT_MOST, region=Region(RegionKind.NEIGHBORS, "A1"), k=2)
    assert referenced_cells(c_am, n) == ("B1", "A2", "B2")

    # 7. PARITY
    c_par = Clue(
        id="p",
        type=ClueType.PARITY,
        region=Region(RegionKind.EXPLICIT, ("B2", "A1")),
        parity=Parity.EVEN,
    )
    assert referenced_cells(c_par, n) == ("A1", "B2")

    # 8. COMPARE with overlap
    # Left = Row 1 (A1, B1, C1); Right = Col B (B1, B2, B3)
    # Overlap is B1. Union must be {A1, B1, C1, B2, B3} in row-major order: A1, B1, C1, B2, B3
    c_cmp = Clue(
        id="c",
        type=ClueType.COMPARE,
        left=Region(RegionKind.ROW, 1),
        right=Region(RegionKind.COL, "B"),
        op=CompareOp.GE,
    )
    ref = referenced_cells(c_cmp, n)
    assert ref == ("A1", "B1", "C1", "B2", "B3")
    assert len(ref) == len(set(ref))

