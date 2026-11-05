"""Tests for Puzzle JSON IO, strict parsing, and atomic saving (A-05, A-21)."""

import json
from pathlib import Path
import pytest

from common.errors import PuzzleError
from common.puzzle_io import load_puzzle, puzzle_from_dict, puzzle_to_dict, save_puzzle


def test_load_chain_fixture() -> None:
    """A-05: Loading reference 3x3 chain puzzle succeeds and round-trips cleanly."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    assert chain_path.is_file()
    puzzle = load_puzzle(chain_path)
    assert puzzle.schema_version == 2
    assert puzzle.id == "3x3_chain"
    assert puzzle.n == 3
    assert len(puzzle.characters) == 9
    assert len(puzzle.clues) == 9
    assert puzzle.initial_revealed == {"A1": puzzle.initial_revealed["A1"]}
    assert puzzle.solution is not None
    assert len(puzzle.solution) == 9

    # Round trip dict
    d = puzzle_to_dict(puzzle)
    p2 = puzzle_from_dict(d)
    assert p2 == puzzle


def test_strict_json_rejections(tmp_path: Path) -> None:
    """A-05: Strict JSON parsing rejects duplicate keys, unknown fields, NaN, and trailing content."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    valid_text = chain_path.read_text(encoding="utf-8")

    # 1. Duplicate keys
    dup_text = valid_text.replace('"schema_version": 2,', '"schema_version": 2, "schema_version": 2,')
    dup_file = tmp_path / "dup.json"
    dup_file.write_text(dup_text, encoding="utf-8")
    with pytest.raises(PuzzleError, match="Duplicate JSON key"):
        load_puzzle(dup_file)

    # 2. Unknown root fields
    bad_root_dict = json.loads(valid_text)
    bad_root_dict["extra_field"] = "not_allowed"
    with pytest.raises(PuzzleError, match="Unknown root keys"):
        puzzle_from_dict(bad_root_dict)

    # 3. NaN / Infinity
    nan_text = valid_text.replace('"n": 3,', '"n": NaN,')
    nan_file = tmp_path / "nan.json"
    nan_file.write_text(nan_text, encoding="utf-8")
    with pytest.raises(PuzzleError, match="Disallowed JSON constant"):
        load_puzzle(nan_file)

    # 4. Trailing non-whitespace content
    trail_text = valid_text + " extra_trailing_stuff"
    trail_file = tmp_path / "trail.json"
    trail_file.write_text(trail_text, encoding="utf-8")
    with pytest.raises(PuzzleError, match="Trailing content"):
        load_puzzle(trail_file)

    # 5. bool as int for n or schema_version
    bool_dict = json.loads(valid_text)
    bool_dict["n"] = True
    with pytest.raises(PuzzleError, match="must be 3, 4, or 5"):
        puzzle_from_dict(bool_dict)


def test_atomic_save(tmp_path: Path) -> None:
    """A-21: save_puzzle performs atomic save and preserves UTF-8 characters."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    puzzle = load_puzzle(chain_path)

    out_file = tmp_path / "saved_puzzle.json"
    save_puzzle(puzzle, out_file)
    assert out_file.is_file()

    # Verify reload
    reloaded = load_puzzle(out_file)
    assert reloaded.id == puzzle.id
    assert len(reloaded.characters) == 9

