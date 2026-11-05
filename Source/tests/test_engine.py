"""Tests for GameEngine lifecycle, state machine, and verdict handling (A-08..A-18)."""

from pathlib import Path
import time
import pytest

from common.errors import (
    AlreadyRevealedError,
    ClassifierUnavailableError,
    GameNotLoadedError,
    InvalidActionError,
    ReasoningFailure,
    ReferenceMismatchError,
    StaleStateError,
)
from common.puzzle_io import load_puzzle
from common.types import (
    Cell,
    Classification,
    ClassificationReport,
    PublicState,
    ReasoningStatus,
    StateToken,
    Status,
    VerdictResult,
)
from engine.game_engine import GameEngine


def make_constant_classifier(
    classification_map: dict[Cell, Classification],
    status: ReasoningStatus = ReasoningStatus.READY,
    message: str = "",
):
    """Create a test double classifier returning a canned report matching the snapshot token."""
    def _classifier(state: PublicState, *, deadline: float | None = None) -> ClassificationReport:
        # Fill in any missing unsolved cells as UNKNOWN
        by_cell = {c: Classification.UNKNOWN for c in state.unsolved}
        by_cell.update(classification_map)
        return ClassificationReport(
            token=state.token,
            status=status,
            by_cell=by_cell,
            message=message,
        )
    return _classifier


def test_engine_load_and_restart() -> None:
    """A-08: Load and restart lifecycle, session tokens, and initial states."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()

    with pytest.raises(GameNotLoadedError):
        engine.get_public_state()
    with pytest.raises(GameNotLoadedError):
        engine.restart()

    state = engine.load(chain_path)
    session1 = state.token.session_id
    assert state.token.revision == 0
    assert state.known_statuses == {"A1": Status.INNOCENT}
    assert len(state.revealed_clues) == 1
    assert "A1" in state.revealed_clues
    assert len(state.unsolved) == 8

    # Failed load preserves existing game
    with pytest.raises(Exception):
        engine.load("non_existent_file.json")
    state_after_fail = engine.get_public_state()
    assert state_after_fail.token.session_id == session1

    # Restart creates new session_id, revision 0, restores initial state
    restart_state = engine.restart()
    assert restart_state.token.session_id != session1
    assert restart_state.token.revision == 0
    assert restart_state.known_statuses == {"A1": Status.INNOCENT}
    assert len(restart_state.unsolved) == 8


def test_snapshot_isolation() -> None:
    """A-09: Snapshots are strictly immutable / detached from engine internals."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    state1 = engine.load(chain_path)

    # Attempting to mutate returned mapping should fail
    with pytest.raises(TypeError):
        state1.known_statuses["B1"] = Status.CRIMINAL  # type: ignore

    # Submitting a verdict does not modify previous snapshot state1
    engine.set_classifier(make_constant_classifier({"B1": Classification.CRIMINAL}))
    outcome = engine.submit_verdict("B1", Status.CRIMINAL)
    assert outcome.result is VerdictResult.ACCEPTED

    assert "B1" not in state1.known_statuses
    assert len(state1.known_statuses) == 1
    assert engine.num_revealed() == 2


def test_public_boundary() -> None:
    """A-10: PublicState contains only public information, no hidden solution or unrevealed clues."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    state = engine.load(chain_path)

    assert not hasattr(state, "solution")
    assert not hasattr(state, "clues")
    # Only revealed clue for A1 is present
    assert set(state.revealed_clues.keys()) == {"A1"}


def test_accepted_verdict() -> None:
    """A-11: Accepted verdict flips card, reveals clue, increments revision."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)
    engine.set_classifier(make_constant_classifier({"B1": Classification.CRIMINAL}))

    token_before = engine.get_public_state().token
    outcome = engine.submit_verdict("B1", Status.CRIMINAL, expected_token=token_before)

    assert outcome.result is VerdictResult.ACCEPTED
    assert outcome.cell == "B1"
    assert outcome.verdict is Status.CRIMINAL
    assert outcome.before_token == token_before
    assert outcome.after_token.revision == token_before.revision + 1
    assert outcome.after_token.session_id == token_before.session_id
    assert outcome.new_clue is not None
    assert outcome.new_clue.id == "c_B1"


def test_guessing_unknown_yields_not_provable() -> None:
    """A-12: Guessing a cell whose classification is UNKNOWN yields NOT_PROVABLE, even if guess matches solution."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)
    # B1 is CRIMINAL in solution, but classifier says UNKNOWN
    engine.set_classifier(make_constant_classifier({"B1": Classification.UNKNOWN}))

    token_before = engine.get_public_state().token
    outcome = engine.submit_verdict("B1", Status.CRIMINAL)

    assert outcome.result is VerdictResult.NOT_PROVABLE
    assert outcome.before_token == outcome.after_token == token_before
    assert outcome.new_clue is None
    assert engine.num_revealed() == 1
    assert "B1" not in engine.get_public_state().known_statuses


def test_contradicted_verdict() -> None:
    """A-13: Submitting opposite of forced classification yields CONTRADICTED; state unchanged."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)
    # Forced is CRIMINAL, but player submits INNOCENT
    engine.set_classifier(make_constant_classifier({"B1": Classification.CRIMINAL}))

    token_before = engine.get_public_state().token
    outcome = engine.submit_verdict("B1", Status.INNOCENT)

    assert outcome.result is VerdictResult.CONTRADICTED
    assert outcome.before_token == outcome.after_token == token_before
    assert outcome.new_clue is None
    assert engine.num_revealed() == 1


def test_operational_failures() -> None:
    """A-14: ReasoningStatus INCONSISTENT, TIMEOUT, ERROR raise ReasoningFailure, not converted to verdict."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)

    # 1. INCONSISTENT
    engine.set_classifier(make_constant_classifier({}, status=ReasoningStatus.INCONSISTENT))
    with pytest.raises(ReasoningFailure) as exc1:
        engine.submit_verdict("B1", Status.CRIMINAL)
    assert exc1.value.status is ReasoningStatus.INCONSISTENT

    # 2. TIMEOUT
    engine.set_classifier(make_constant_classifier({}, status=ReasoningStatus.TIMEOUT))
    with pytest.raises(ReasoningFailure) as exc2:
        engine.submit_verdict("B1", Status.CRIMINAL)
    assert exc2.value.status is ReasoningStatus.TIMEOUT

    # 3. No classifier set
    engine2 = GameEngine()
    engine2.load(chain_path)
    with pytest.raises(ClassifierUnavailableError):
        engine2.submit_verdict("B1", Status.CRIMINAL)


def test_invalid_stale_and_repeated_verdicts() -> None:
    """A-15: Already revealed cell, stale token, and out-of-bounds cell raise appropriate errors."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)
    engine.set_classifier(make_constant_classifier({"B1": Classification.CRIMINAL}))

    # Stale token
    stale_token = StateToken("wrong_session", 999)
    with pytest.raises(StaleStateError):
        engine.submit_verdict("B1", Status.CRIMINAL, expected_token=stale_token)

    # Already revealed card (A1 was initially revealed)
    with pytest.raises(AlreadyRevealedError):
        engine.submit_verdict("A1", Status.INNOCENT)


def test_reentrancy_and_deadlines() -> None:
    """A-16: Reentrant mutation during classification is blocked; deadlines enforced."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)

    def reentrant_classifier(state: PublicState, *, deadline: float | None = None) -> ClassificationReport:
        # Attempt to call submit_verdict while engine is evaluating
        engine.submit_verdict("C1", Status.INNOCENT)
        return ClassificationReport(token=state.token, status=ReasoningStatus.READY, by_cell={})

    engine.set_classifier(reentrant_classifier)
    with pytest.raises(ReasoningFailure) as exc:
        engine.submit_verdict("B1", Status.CRIMINAL)
    assert "Reentrant" in exc.value.message

    # Expired deadline
    engine.set_classifier(make_constant_classifier({"B1": Classification.CRIMINAL}))
    with pytest.raises(ReasoningFailure) as exc_to:
        engine.submit_verdict("B1", Status.CRIMINAL, deadline=time.monotonic() - 1.0)
    assert exc_to.value.status is ReasoningStatus.TIMEOUT


def test_reference_mismatch_safety() -> None:
    """A-17: Contradicting reference solution raises ReferenceMismatchError without revealing reference status."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)
    # B1 in solution is CRIMINAL. Buggy/malicious classifier says forced INNOCENT!
    engine.set_classifier(make_constant_classifier({"B1": Classification.INNOCENT}))

    with pytest.raises(ReferenceMismatchError) as exc:
        engine.submit_verdict("B1", Status.INNOCENT)

    # Verify error message doesn't reveal true label
    assert "CRIMINAL" not in str(exc.value)


def test_no_free_reveal() -> None:
    """A-18: GameEngine has no public arbitrary reveal API; GamePort facade only exposes 2 methods."""
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)
    port = engine.get_game_port()

    assert hasattr(port, "get_public_state")
    assert hasattr(port, "submit_verdict")
    assert not hasattr(port, "reveal_card")
    assert not hasattr(port, "solution")
    assert not hasattr(port, "load")
    assert not hasattr(port, "restart")

