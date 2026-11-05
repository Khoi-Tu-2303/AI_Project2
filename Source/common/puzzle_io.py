"""Strict JSON serialization and deserialization for Puzzles and Clues."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from common.errors import ClueError, PuzzleError
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
from common.validation import validate_clue, validate_puzzle_structure


def _json_no_duplicates_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Strict dict constructor that rejects duplicate keys."""
    res: dict[str, Any] = {}
    for k, v in pairs:
        if k in res:
            raise PuzzleError(f"Duplicate JSON key: {k!r}")
        res[k] = v
    return res


def _strict_parse_constant(c: str) -> None:
    """Reject NaN, Infinity, and -Infinity."""
    raise PuzzleError(f"Disallowed JSON constant: {c!r}")


def region_from_dict(data: Mapping[str, Any], n: int) -> Region:
    """Parse a Region from dictionary, rejecting unknown fields."""
    if not isinstance(data, Mapping):
        raise ClueError(f"Region must be an object, got {type(data).__name__}")
    allowed_keys = {"kind", "arg"}
    extra_keys = set(data.keys()) - allowed_keys
    if extra_keys:
        raise ClueError(f"Unknown keys in Region: {sorted(extra_keys)}")

    if "kind" not in data or "arg" not in data:
        raise ClueError("Region requires 'kind' and 'arg'")

    kind_str = data["kind"]
    if not isinstance(kind_str, str):
        raise ClueError(f"Region kind must be str, got {type(kind_str).__name__}")
    try:
        kind = RegionKind(kind_str)
    except ValueError:
        raise ClueError(f"Invalid RegionKind: {kind_str!r}")

    arg = data["arg"]
    if kind is RegionKind.ROW:
        if isinstance(arg, bool) or not isinstance(arg, int):
            raise ClueError(f"ROW region arg must be an int, got {arg!r}")
    elif kind is RegionKind.COL:
        if not isinstance(arg, str):
            raise ClueError(f"COL region arg must be a string, got {arg!r}")
    elif kind is RegionKind.NEIGHBORS:
        if not isinstance(arg, str):
            raise ClueError(f"NEIGHBORS region arg must be a cell string, got {arg!r}")
    elif kind is RegionKind.EXPLICIT:
        if not isinstance(arg, list):
            raise ClueError(f"EXPLICIT region arg must be a list of cells, got {type(arg).__name__}")
        arg = tuple(arg)
    return Region(kind=kind, arg=arg)


def region_to_dict(region: Region) -> dict[str, Any]:
    """Serialize a Region to a dictionary."""
    arg = list(region.arg) if isinstance(region.arg, tuple) else region.arg
    return {"kind": region.kind.value, "arg": arg}


def clue_from_dict(data: Mapping[str, Any], n: int) -> Clue:
    """Parse a Clue from a dictionary strictly, rejecting unknown fields."""
    if not isinstance(data, Mapping):
        raise ClueError(f"Clue must be an object, got {type(data).__name__}")

    if "id" not in data or "type" not in data:
        raise ClueError("Clue requires 'id' and 'type'")

    clue_id = data["id"]
    if not isinstance(clue_id, str):
        raise ClueError(f"Clue id must be string, got {type(clue_id).__name__}")

    type_str = data["type"]
    if not isinstance(type_str, str):
        raise ClueError(f"Clue type must be string, got {type(type_str).__name__}")
    try:
        clue_type = ClueType(type_str)
    except ValueError:
        raise ClueError(f"Invalid ClueType: {type_str!r}")

    # Determine allowed keys for this specific clue type
    base_allowed = {"id", "type"}
    if clue_type is ClueType.FACT:
        allowed = base_allowed | {"cells", "status"}
    elif clue_type in (ClueType.SAME, ClueType.DIFFERENT):
        allowed = base_allowed | {"cells"}
    elif clue_type in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        allowed = base_allowed | {"region", "k"}
    elif clue_type is ClueType.PARITY:
        allowed = base_allowed | {"region", "parity"}
    elif clue_type is ClueType.COMPARE:
        allowed = base_allowed | {"left", "right", "op"}
    else:
        allowed = base_allowed

    extra = set(data.keys()) - allowed
    if extra:
        raise ClueError(f"Unknown fields for clue type {clue_type.value}: {sorted(extra)}")

    cells: tuple[Cell, ...] = ()
    if "cells" in data:
        raw_cells = data["cells"]
        if not isinstance(raw_cells, list):
            raise ClueError(f"cells must be a list, got {type(raw_cells).__name__}")
        cells = tuple(raw_cells)

    status: Status | None = None
    if "status" in data:
        raw_status = data["status"]
        if not isinstance(raw_status, str):
            raise ClueError(f"status must be a string, got {type(raw_status).__name__}")
        try:
            status = Status(raw_status)
        except ValueError:
            raise ClueError(f"Invalid Status: {raw_status!r}")

    region: Region | None = None
    if "region" in data:
        region = region_from_dict(data["region"], n)

    k: int | None = None
    if "k" in data:
        raw_k = data["k"]
        if isinstance(raw_k, bool) or not isinstance(raw_k, int):
            raise ClueError(f"k must be an integer, got {raw_k!r}")
        k = raw_k

    parity: Parity | None = None
    if "parity" in data:
        raw_parity = data["parity"]
        if not isinstance(raw_parity, str):
            raise ClueError(f"parity must be string, got {type(raw_parity).__name__}")
        try:
            parity = Parity(raw_parity)
        except ValueError:
            raise ClueError(f"Invalid Parity: {raw_parity!r}")

    left: Region | None = None
    if "left" in data:
        left = region_from_dict(data["left"], n)

    right: Region | None = None
    if "right" in data:
        right = region_from_dict(data["right"], n)

    op: CompareOp | None = None
    if "op" in data:
        raw_op = data["op"]
        if not isinstance(raw_op, str):
            raise ClueError(f"op must be string, got {type(raw_op).__name__}")
        try:
            op = CompareOp(raw_op)
        except ValueError:
            raise ClueError(f"Invalid CompareOp: {raw_op!r}")

    clue = Clue(
        id=clue_id,
        type=clue_type,
        cells=cells,
        region=region,
        k=k,
        status=status,
        parity=parity,
        left=left,
        right=right,
        op=op,
    )
    validate_clue(clue, n)
    return clue


def clue_to_dict(clue: Clue) -> dict[str, Any]:
    """Serialize a Clue to a dictionary with only relevant fields."""
    d: dict[str, Any] = {"id": clue.id, "type": clue.type.value}
    if clue.type is ClueType.FACT:
        d["cells"] = list(clue.cells)
        if clue.status is not None:
            d["status"] = clue.status.value
    elif clue.type in (ClueType.SAME, ClueType.DIFFERENT):
        d["cells"] = list(clue.cells)
    elif clue.type in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        if clue.region is not None:
            d["region"] = region_to_dict(clue.region)
        d["k"] = clue.k
    elif clue.type is ClueType.PARITY:
        if clue.region is not None:
            d["region"] = region_to_dict(clue.region)
        if clue.parity is not None:
            d["parity"] = clue.parity.value
    elif clue.type is ClueType.COMPARE:
        if clue.left is not None:
            d["left"] = region_to_dict(clue.left)
        if clue.right is not None:
            d["right"] = region_to_dict(clue.right)
        if clue.op is not None:
            d["op"] = clue.op.value
    return d


def puzzle_from_dict(data: Mapping[str, Any]) -> Puzzle:
    """Parse and validate a Puzzle from a dictionary strictly."""
    if not isinstance(data, Mapping):
        raise PuzzleError(f"Puzzle data must be an object, got {type(data).__name__}")

    allowed_root = {
        "schema_version",
        "id",
        "n",
        "characters",
        "clues",
        "initial_revealed",
        "solution",
    }
    extra_keys = set(data.keys()) - allowed_root
    if extra_keys:
        raise PuzzleError(f"Unknown root keys in puzzle: {sorted(extra_keys)}")

    missing_keys = {"schema_version", "id", "n", "characters", "clues", "initial_revealed"} - set(data.keys())
    if missing_keys:
        raise PuzzleError(f"Missing required puzzle keys: {sorted(missing_keys)}")

    schema_version = data["schema_version"]
    if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version != 2:
        raise PuzzleError(f"schema_version must be int 2, got {schema_version!r}")

    puzzle_id = data["id"]
    if not isinstance(puzzle_id, str) or not puzzle_id.strip():
        raise PuzzleError("Puzzle 'id' must be a non-empty string")

    n = data["n"]
    if isinstance(n, bool) or not isinstance(n, int) or n not in (3, 4, 5):
        raise PuzzleError(f"Puzzle 'n' must be 3, 4, or 5, got {n!r}")

    # Characters
    raw_chars = data["characters"]
    if not isinstance(raw_chars, list):
        raise PuzzleError(f"'characters' must be a list, got {type(raw_chars).__name__}")

    characters: list[Character] = []
    for idx, c in enumerate(raw_chars):
        if not isinstance(c, Mapping):
            raise PuzzleError(f"Character {idx} must be an object")
        c_allowed = {"cell", "name", "profession"}
        if set(c.keys()) != c_allowed:
            raise PuzzleError(f"Character {idx} keys must be exactly {c_allowed}, got {set(c.keys())}")
        if not isinstance(c["cell"], str) or not isinstance(c["name"], str) or not isinstance(c["profession"], str):
            raise PuzzleError(f"Character {idx} fields must be strings")
        characters.append(Character(cell=c["cell"], name=c["name"], profession=c["profession"]))

    # Clues
    raw_clues = data["clues"]
    if not isinstance(raw_clues, Mapping):
        raise PuzzleError(f"'clues' must be an object mapping cell to clue, got {type(raw_clues).__name__}")

    clues: dict[Cell, Clue] = {}
    for cell_key, raw_clue in raw_clues.items():
        if not isinstance(cell_key, str):
            raise PuzzleError(f"Clue key must be cell string, got {cell_key!r}")
        clue_obj = clue_from_dict(raw_clue, n)
        clues[cell_key] = clue_obj

    # Initial revealed
    raw_init = data["initial_revealed"]
    if not isinstance(raw_init, Mapping):
        raise PuzzleError(f"'initial_revealed' must be an object, got {type(raw_init).__name__}")
    initial_revealed: dict[Cell, Status] = {}
    for cell_key, raw_stat in raw_init.items():
        if not isinstance(cell_key, str):
            raise PuzzleError(f"initial_revealed key must be cell string, got {cell_key!r}")
        if not isinstance(raw_stat, str):
            raise PuzzleError(f"initial_revealed value must be string, got {raw_stat!r}")
        try:
            initial_revealed[cell_key] = Status(raw_stat)
        except ValueError:
            raise PuzzleError(f"Invalid Status in initial_revealed for {cell_key}: {raw_stat!r}")

    # Solution
    solution: dict[Cell, Status] | None = None
    if "solution" in data and data["solution"] is not None:
        raw_sol = data["solution"]
        if not isinstance(raw_sol, Mapping):
            raise PuzzleError(f"'solution' must be an object or null, got {type(raw_sol).__name__}")
        solution = {}
        for cell_key, raw_stat in raw_sol.items():
            if not isinstance(cell_key, str):
                raise PuzzleError(f"solution key must be cell string, got {cell_key!r}")
            if not isinstance(raw_stat, str):
                raise PuzzleError(f"solution value must be string, got {raw_stat!r}")
            try:
                solution[cell_key] = Status(raw_stat)
            except ValueError:
                raise PuzzleError(f"Invalid Status in solution for {cell_key}: {raw_stat!r}")

    puzzle = Puzzle(
        schema_version=schema_version,
        id=puzzle_id,
        n=n,
        characters=tuple(characters),
        clues=clues,
        initial_revealed=initial_revealed,
        solution=solution,
    )
    validate_puzzle_structure(puzzle)
    return puzzle


def puzzle_to_dict(puzzle: Puzzle) -> dict[str, Any]:
    """Serialize a Puzzle to a JSON-compatible dictionary."""
    validate_puzzle_structure(puzzle)
    d: dict[str, Any] = {
        "schema_version": puzzle.schema_version,
        "id": puzzle.id,
        "n": puzzle.n,
        "characters": [
            {"cell": c.cell, "name": c.name, "profession": c.profession}
            for c in puzzle.characters
        ],
        "clues": {cell: clue_to_dict(clue) for cell, clue in puzzle.clues.items()},
        "initial_revealed": {
            cell: status.value for cell, status in puzzle.initial_revealed.items()
        },
        "solution": (
            {cell: status.value for cell, status in puzzle.solution.items()}
            if puzzle.solution is not None
            else None
        ),
    }
    return d


def load_puzzle(path: str | Path) -> Puzzle:
    """Load and strictly parse a Puzzle from a JSON file."""
    p = Path(path)
    if not p.is_file():
        raise PuzzleError(f"Puzzle file does not exist: {p}")
    try:
        content = p.read_text(encoding="utf-8")
    except Exception as e:
        raise PuzzleError(f"Failed to read puzzle file {p}: {e}") from e

    try:
        decoder = json.JSONDecoder(
            object_pairs_hook=_json_no_duplicates_hook,
            parse_constant=_strict_parse_constant,
        )
        data, end_idx = decoder.raw_decode(content)
        # Check for trailing non-whitespace content
        if content[end_idx:].strip():
            raise PuzzleError(f"Trailing content in JSON file: {p}")
    except json.JSONDecodeError as e:
        raise PuzzleError(f"Invalid JSON in puzzle file {p}: {e}") from e

    return puzzle_from_dict(data)


def save_puzzle(puzzle: Puzzle, path: str | Path) -> None:
    """Save a Puzzle atomically to a JSON file via a temporary file."""
    target_path = Path(path).resolve()
    target_dir = target_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    data = puzzle_to_dict(puzzle)
    serialized = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    # Write atomically
    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=target_dir,
        delete=False,
    )
    temp_path = Path(temp_file.name)
    try:
        with temp_file:
            temp_file.write(serialized)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        temp_path.replace(target_path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise PuzzleError(f"Failed to save puzzle atomically to {target_path}: {e}") from e

