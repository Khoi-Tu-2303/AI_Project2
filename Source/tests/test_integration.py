"""Acceptance tests for full end-to-end integration (G-I)."""

from pathlib import Path
import pytest

from agent.logic_agent import AgentStatus, LogicAgent
from engine.game_engine import GameEngine
from logic.entailment import EntailmentClassifier

try:
    import agent.logic_agent
    import logic.dpll
    import logic.encoder
    HAS_FULL_STACK = True
except ImportError:
    HAS_FULL_STACK = False

PUZZLES_DIR = Path(__file__).resolve().parent.parent / "puzzles" / "examples"


@pytest.mark.skipif(not HAS_FULL_STACK, reason="Full stack (B, C, D) not yet complete (BLOCKED)")
def test_full_chain_solve_real() -> None:
    """G-I: End-to-end solving of 3x3 chain using real B, C, D without test doubles."""
    engine = GameEngine(classifier=EntailmentClassifier())
    engine.load(PUZZLES_DIR / "3x3_chain.json")
    port = engine.get_game_port()

    agent = LogicAgent()
    res = agent.run(port)

    assert res.is_solved
    assert res.status is AgentStatus.SOLVED
    assert engine.is_complete()
    assert len(res.steps) == 8


@pytest.mark.skipif(not HAS_FULL_STACK, reason="Full stack (B, C, D) not yet complete (BLOCKED)")
def test_full_stack_crossfire_4x4() -> None:
    """G-I: End-to-end solving of 4x4 crossfire puzzle with PARITY and COMPARE extensions."""
    engine = GameEngine(classifier=EntailmentClassifier())
    engine.load(PUZZLES_DIR / "4x4_crossfire.json")
    port = engine.get_game_port()

    agent = LogicAgent()
    res = agent.run(port)

    assert res.is_solved
    assert res.status is AgentStatus.SOLVED
    assert engine.is_complete()


@pytest.mark.skipif(not HAS_FULL_STACK, reason="Full stack (B, C, D) not yet complete (BLOCKED)")
def test_full_stack_5x5_stress() -> None:
    """G-I: End-to-end stress test solving 5x5 mastermind puzzle (25 characters)."""
    engine = GameEngine(classifier=EntailmentClassifier())
    engine.load(PUZZLES_DIR / "5x5_mastermind.json")
    port = engine.get_game_port()

    agent = LogicAgent()
    res = agent.run(port)

    assert res.is_solved
    assert res.status is AgentStatus.SOLVED
    assert engine.is_complete()
