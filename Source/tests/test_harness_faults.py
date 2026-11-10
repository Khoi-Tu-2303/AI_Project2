"""Fault injection tests verifying the verification runner and harness detect faults (A-22)."""

from pathlib import Path
import pytest

from common.errors import ReferenceMismatchError
from common.puzzle_io import load_puzzle
from common.types import (
    Classification,
    ClassificationReport,
    PublicState,
    ReasoningStatus,
    Status,
    VerdictResult,
)
from engine.game_engine import GameEngine
from tools.integration_runner import IntegrationRunner


def test_fault_injection_always_unknown_cannot_solve() -> None:
    """A-22: A faulty classifier that always returns UNKNOWN cannot solve the chain puzzle."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)

    def always_unknown(state: PublicState, *, deadline: float | None = None) -> ClassificationReport:
        return ClassificationReport(
            token=state.token,
            status=ReasoningStatus.READY,
            by_cell={c: Classification.UNKNOWN for c in state.unsolved},
        )

    engine.set_classifier(always_unknown)
    outcome = engine.submit_verdict("B1", Status.CRIMINAL)
    assert outcome.result is VerdictResult.NOT_PROVABLE
    assert not engine.is_complete()


def test_fault_injection_wrong_forced_caught_by_reference() -> None:
    """A-22: A faulty classifier that forces an incorrect verdict is caught by ReferenceMismatchError."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)

    def wrong_forced(state: PublicState, *, deadline: float | None = None) -> ClassificationReport:
        by_cell = {c: Classification.UNKNOWN for c in state.unsolved}
        by_cell["B1"] = Classification.INNOCENT
        return ClassificationReport(token=state.token, status=ReasoningStatus.READY, by_cell=by_cell)

    engine.set_classifier(wrong_forced)
    with pytest.raises(ReferenceMismatchError):
        engine.submit_verdict("B1", Status.INNOCENT)


def test_runner_missing_module_yields_blocked(monkeypatch) -> None:
    """A-22: Runner marks missing modules as BLOCKED and produces exit code 2."""
    source_dir = Path(__file__).resolve().parent.parent
    runner = IntegrationRunner(source_dir=source_dir, require_real=True)

    from tools import integration_runner
    original = integration_runner.is_module_available
    monkeypatch.setattr(
        integration_runner,
        "is_module_available",
        lambda name: False if name in ("logic.encoder", "logic.dpll", "gui.app", "gui.controller") else original(name),
    )

    report_b = runner.run_scope("b")
    assert report_b.overall_status == "BLOCKED"
    assert report_b.exit_code == 2
    assert "G-B" in report_b.gates
    assert report_b.gates["G-B"].status == "BLOCKED"

    report_all = runner.run_scope("all")
    assert report_all.overall_status == "BLOCKED"
    assert report_all.exit_code == 2
    assert report_all.gates["G-A"].status == "PASS"
    assert report_all.gates["G-B"].status == "BLOCKED"
    assert report_all.gates["G-C"].status == "BLOCKED"
    assert report_all.gates["G-D"].status == "BLOCKED"
    assert report_all.gates["G-E"].status == "BLOCKED"


def test_runner_rejects_broken_real_encoder(monkeypatch) -> None:
    """G-B must fail if the delivered encoder silently drops constraints."""
    from logic.encoder import CNFEncoder
    monkeypatch.setattr(CNFEncoder, "encode_clue", lambda self, clue: [])
    runner = IntegrationRunner(Path(__file__).resolve().parent.parent, require_real=True)
    report = runner.run_scope("b")
    assert report.overall_status == "FAIL"
    assert report.exit_code == 1
    assert report.gates["G-B"].failed_count > 0
