"""Strict JSON parser and validator for puzzle test suites manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from common.errors import PuzzleError
from common.puzzle_io import _json_no_duplicates_hook, _strict_parse_constant


ALLOWED_KINDS = {
    "normal",
    "stuck",
    "inconsistent",
    "multi_solution",
    "invalid",
    "stress",
}
ALLOWED_LOAD = {"VALID", "INVALID"}
ALLOWED_UNIQUENESS = {"UNIQUE", "MULTIPLE", "UNSAT", None}
ALLOWED_RUN = {"SOLVED", "STUCK", "INCONSISTENT", None}


def validate_manifest(data: Mapping[str, Any], base_dir: Path | None = None) -> None:
    """Validate a parsed manifest against schema v2 and security constraints."""
    if not isinstance(data, Mapping):
        raise PuzzleError(f"Manifest root must be an object, got {type(data).__name__}")

    allowed_root = {"schema_version", "cases"}
    extra_root = set(data.keys()) - allowed_root
    if extra_root:
        raise PuzzleError(f"Unknown root keys in manifest: {sorted(extra_root)}")

    schema_version = data.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version != 2:
        raise PuzzleError(f"Manifest schema_version must be int 2, got {schema_version!r}")

    cases = data.get("cases")
    if not isinstance(cases, list):
        raise PuzzleError(f"Manifest 'cases' must be a list, got {type(cases).__name__}")

    seen_case_ids: set[str] = set()

    for idx, case in enumerate(cases):
        if not isinstance(case, Mapping):
            raise PuzzleError(f"Case {idx} must be an object")

        allowed_case_keys = {"case_id", "path", "kind", "expected"}
        extra_case = set(case.keys()) - allowed_case_keys
        if extra_case:
            raise PuzzleError(f"Unknown keys in case {idx}: {sorted(extra_case)}")

        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise PuzzleError(f"Case {idx} case_id must be non-empty str")
        if case_id in seen_case_ids:
            raise PuzzleError(f"Duplicate case_id {case_id!r}")
        seen_case_ids.add(case_id)

        rel_path = case.get("path")
        if not isinstance(rel_path, str) or not rel_path.strip():
            raise PuzzleError(f"Case {case_id} path must be non-empty str")

        # Security check: forbid absolute path and path traversal
        p = Path(rel_path)
        if p.is_absolute() or rel_path.startswith("/") or rel_path.startswith("\\"):
            raise PuzzleError(f"Case {case_id} path must not be absolute: {rel_path!r}")
        if ".." in p.parts:
            raise PuzzleError(f"Case {case_id} path contains path traversal '..': {rel_path!r}")

        if base_dir is not None:
            resolved_base = base_dir.resolve()
            target = (base_dir / p).resolve()
            if not target.is_relative_to(resolved_base):
                raise PuzzleError(f"Case {case_id} path escapes base directory: {rel_path!r}")

        kind = case.get("kind")
        if kind not in ALLOWED_KINDS:
            raise PuzzleError(f"Case {case_id} has invalid kind {kind!r}")

        expected = case.get("expected")
        if not isinstance(expected, Mapping):
            raise PuzzleError(f"Case {case_id} expected must be an object")

        allowed_exp = {"load", "full_clue_uniqueness", "run", "reference_matches", "accepted_order"}
        extra_exp = set(expected.keys()) - allowed_exp
        if extra_exp:
            raise PuzzleError(f"Case {case_id} expected has unknown keys: {sorted(extra_exp)}")

        load_exp = expected.get("load")
        if load_exp not in ALLOWED_LOAD:
            raise PuzzleError(f"Case {case_id} expected.load must be 'VALID' or 'INVALID', got {load_exp!r}")

        uniq_exp = expected.get("full_clue_uniqueness")
        if uniq_exp not in ALLOWED_UNIQUENESS:
            raise PuzzleError(f"Case {case_id} invalid full_clue_uniqueness: {uniq_exp!r}")

        run_exp = expected.get("run")
        if run_exp not in ALLOWED_RUN:
            raise PuzzleError(f"Case {case_id} invalid run: {run_exp!r}")

        ref_exp = expected.get("reference_matches")
        if ref_exp is not None and not isinstance(ref_exp, bool):
            raise PuzzleError(f"Case {case_id} reference_matches must be bool or null, got {ref_exp!r}")

        order_exp = expected.get("accepted_order")
        if order_exp is not None:
            if not isinstance(order_exp, list):
                raise PuzzleError(f"Case {case_id} accepted_order must be list or null")
            seen_cells: set[str] = set()
            for c in order_exp:
                if not isinstance(c, str):
                    raise PuzzleError(f"Case {case_id} accepted_order cell must be str, got {c!r}")
                if c in seen_cells:
                    raise PuzzleError(f"Case {case_id} duplicate cell in accepted_order: {c!r}")
                seen_cells.add(c)

        # Consistency: if load is INVALID, logic outcomes must be null
        if load_exp == "INVALID":
            if uniq_exp is not None or run_exp is not None or ref_exp is not None or order_exp is not None:
                raise PuzzleError(f"Case {case_id} marked INVALID load cannot have logical run expectations")


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load and validate manifest from a JSON file."""
    p = Path(path).resolve()
    if not p.is_file():
        raise PuzzleError(f"Manifest file does not exist: {p}")
    try:
        content = p.read_text(encoding="utf-8")
    except Exception as e:
        raise PuzzleError(f"Failed to read manifest {p}: {e}") from e

    try:
        decoder = json.JSONDecoder(
            object_pairs_hook=_json_no_duplicates_hook,
            parse_constant=_strict_parse_constant,
        )
        data, end_idx = decoder.raw_decode(content)
        if content[end_idx:].strip():
            raise PuzzleError(f"Trailing content in manifest JSON: {p}")
    except json.JSONDecodeError as e:
        raise PuzzleError(f"Invalid JSON in manifest {p}: {e}") from e

    validate_manifest(data, base_dir=p.parent)
    return data
