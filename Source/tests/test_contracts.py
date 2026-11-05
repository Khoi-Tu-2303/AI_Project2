"""Tests for shared contracts, layout boundaries, and puzzle structure rules (A-01, A-06)."""

import copy
from pathlib import Path
import pytest

from common.errors import PuzzleError
from common.puzzle_io import load_puzzle
from common.types import Character, Status
from common.validation import validate_puzzle_structure


def test_import_boundaries() -> None:
    """A-01: Importing common and engine requires no external heavy libraries or B-E packages."""
    import common.types
    import common.errors
    import common.protocols
    import common.regions
    import common.validation
    import common.puzzle_io
    import common.manifest_io
    import engine.game_engine
    import engine.public_port

    assert hasattr(common.types, "PublicState")
    assert hasattr(engine.game_engine, "GameEngine")


def test_character_name_ordering_and_uniqueness() -> None:
    """A-06: Characters must be in row-major order and strictly alphabetical by name.casefold()."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    puzzle = load_puzzle(chain_path)

    # 1. Reverse two character names to break alphabetical ordering
    bad_chars = list(puzzle.characters)
    bad_chars[0] = Character(cell=bad_chars[0].cell, name="Zoe", profession="Baker")
    p_bad = copy.deepcopy(puzzle)
    object.__setattr__(p_bad, "characters", tuple(bad_chars))

    with pytest.raises(PuzzleError, match="ordered alphabetically"):
        validate_puzzle_structure(p_bad)

    # 2. Duplicate character name (case-insensitive)
    bad_chars2 = list(puzzle.characters)
    bad_chars2[1] = Character(cell=bad_chars2[1].cell, name="alice", profession="Doctor")
    p_bad2 = copy.deepcopy(puzzle)
    object.__setattr__(p_bad2, "characters", tuple(bad_chars2))
    with pytest.raises(PuzzleError, match="ordered alphabetically"):
        validate_puzzle_structure(p_bad2)


def test_initial_revealed_contradicting_solution() -> None:
    """A-06: initial_revealed must not contradict the reference solution."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    puzzle = load_puzzle(chain_path)

    # A1 in chain is INNOCENT in solution. Set initial_revealed A1 to CRIMINAL
    bad_init = {"A1": Status.CRIMINAL}
    p_bad = copy.deepcopy(puzzle)
    object.__setattr__(p_bad, "initial_revealed", bad_init)

    with pytest.raises(PuzzleError, match="contradicts solution"):
        validate_puzzle_structure(p_bad)

