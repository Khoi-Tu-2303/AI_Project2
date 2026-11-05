"""Tests for Manifest JSON parsing and validation (A-07)."""

from pathlib import Path
import pytest

from common.errors import PuzzleError
from common.manifest_io import load_manifest, validate_manifest


def test_load_sample_manifest() -> None:
    """A-07: Load sample index.json manifest successfully."""
    manifest_path = Path(__file__).resolve().parent.parent / "puzzles" / "index.json"
    data = load_manifest(manifest_path)
    assert data["schema_version"] == 2
    assert len(data["cases"]) >= 1
    assert data["cases"][0]["case_id"] == "chain_demo"


def test_manifest_validation_security_and_traversal(tmp_path: Path) -> None:
    """A-07: Manifest rejects path traversal, absolute paths, and duplicate IDs."""
    base_dir = tmp_path

    # Path traversal with '..'
    bad_traversal = {
        "schema_version": 2,
        "cases": [
            {
                "case_id": "bad1",
                "path": "../secret.json",
                "kind": "normal",
                "expected": {"load": "VALID"},
            }
        ],
    }
    with pytest.raises(PuzzleError, match="path traversal"):
        validate_manifest(bad_traversal, base_dir=base_dir)

    # Absolute path
    bad_abs = {
        "schema_version": 2,
        "cases": [
            {
                "case_id": "bad2",
                "path": "/etc/passwd",
                "kind": "normal",
                "expected": {"load": "VALID"},
            }
        ],
    }
    with pytest.raises(PuzzleError, match="must not be absolute"):
        validate_manifest(bad_abs, base_dir=base_dir)

    # Duplicate case IDs
    dup_ids = {
        "schema_version": 2,
        "cases": [
            {
                "case_id": "same_id",
                "path": "c1.json",
                "kind": "normal",
                "expected": {"load": "VALID"},
            },
            {
                "case_id": "same_id",
                "path": "c2.json",
                "kind": "normal",
                "expected": {"load": "VALID"},
            },
        ],
    }
    with pytest.raises(PuzzleError, match="Duplicate case_id"):
        validate_manifest(dup_ids, base_dir=base_dir)

    # INVALID load cannot have run expectations
    invalid_with_run = {
        "schema_version": 2,
        "cases": [
            {
                "case_id": "inv",
                "path": "c.json",
                "kind": "invalid",
                "expected": {"load": "INVALID", "run": "SOLVED"},
            }
        ],
    }
    with pytest.raises(PuzzleError, match="cannot have logical run expectations"):
        validate_manifest(invalid_with_run, base_dir=base_dir)

