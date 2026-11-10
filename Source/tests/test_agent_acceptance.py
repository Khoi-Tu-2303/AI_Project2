"""Acceptance tests for Module D (LogicAgent, Uniqueness, Experiments) (G-D)."""

from pathlib import Path
import pytest

from common.puzzle_io import load_puzzle
from common.types import Classification, Status, VerdictResult
from engine.game_engine import GameEngine
from logic.entailment import EntailmentClassifier

try:
    import agent.logic_agent
    import agent.uniqueness
    from agent.logic_agent import AgentStatus, LogicAgent
    from agent.uniqueness import Uniqueness, check_uniqueness
    HAS_MODULE_D = True
except ImportError:
    HAS_MODULE_D = False

PUZZLES_DIR = Path(__file__).resolve().parent.parent / "puzzles" / "examples"


@pytest.mark.skipif(not HAS_MODULE_D, reason="Module D not yet implemented (BLOCKED)")
def test_d01_no_guess_entailment_only() -> None:
    """D-01: Agent makes only entailed verdicts with no guessing in row-major order."""
    chain_path = PUZZLES_DIR / "3x3_chain.json"
    engine = GameEngine(classifier=EntailmentClassifier())
    engine.load(chain_path)
    port = engine.get_game_port()

    agent = LogicAgent()
    run_res = agent.run(port)

    assert run_res.is_solved
    assert run_res.status is AgentStatus.SOLVED
    assert len(run_res.steps) == 8

    expected_order = [
        ("B1", Status.CRIMINAL),
        ("C1", Status.INNOCENT),
        ("A2", Status.CRIMINAL),
        ("B2", Status.INNOCENT),
        ("C2", Status.CRIMINAL),
        ("A3", Status.INNOCENT),
        ("B3", Status.CRIMINAL),
        ("C3", Status.INNOCENT),
    ]

    for step_res, (exp_cell, exp_verdict) in zip(run_res.steps, expected_order):
        assert step_res.cell == exp_cell
        assert step_res.verdict == exp_verdict
        assert step_res.outcome.result is VerdictResult.ACCEPTED

    assert engine.is_complete()


@pytest.mark.skipif(not HAS_MODULE_D, reason="Module D not yet implemented (BLOCKED)")
def test_d02_hint_identifies_forced_cell() -> None:
    """D-02: Hint function identifies forced character without modifying game state."""
    chain_path = PUZZLES_DIR / "3x3_chain.json"
    engine = GameEngine(classifier=EntailmentClassifier())
    engine.load(chain_path)
    port = engine.get_game_port()

    agent = LogicAgent()
    state_before = port.get_public_state()

    hint = agent.hint(state_before)
    assert hint is not None
    assert hint.cell == "B1"
    assert hint.verdict is Status.CRIMINAL
    assert hint.token == state_before.token
    assert len(hint.clue_ids) >= 1

    # Ensure hint call did not change engine state
    state_after = port.get_public_state()
    assert state_before.token == state_after.token
    assert len(state_after.known_statuses) == 1


@pytest.mark.skipif(not HAS_MODULE_D, reason="Module D not yet implemented (BLOCKED)")
def test_d03_stuck_puzzle_stops_cleanly() -> None:
    """D-03: Agent stops cleanly with STUCK and never guesses when no cell is entailed."""
    stuck_path = PUZZLES_DIR / "3x3_stuck.json"
    engine = GameEngine(classifier=EntailmentClassifier())
    engine.load(stuck_path)
    port = engine.get_game_port()

    agent = LogicAgent()
    run_res = agent.run(port)

    assert run_res.status is AgentStatus.STUCK
    assert not run_res.is_solved
    assert not engine.is_complete()


@pytest.mark.skipif(not HAS_MODULE_D, reason="Module D not yet implemented (BLOCKED)")
def test_d04_inconsistent_puzzle_reports_failure() -> None:
    """D-04: Agent detects unsatisfiable KB and halts with INCONSISTENT status."""
    inconsistent_path = PUZZLES_DIR / "3x3_inconsistent.json"
    engine = GameEngine(classifier=EntailmentClassifier())
    engine.load(inconsistent_path)
    port = engine.get_game_port()

    agent = LogicAgent()
    run_res = agent.run(port)

    assert run_res.status is AgentStatus.INCONSISTENT
    assert not run_res.is_solved


@pytest.mark.skipif(not HAS_MODULE_D, reason="Module D not yet implemented (BLOCKED)")
def test_d05_deduction_trace_contains_sat_queries() -> None:
    """D-05: Deduction trace records active clues, step numbers, and SAT queries."""
    chain_path = PUZZLES_DIR / "3x3_chain.json"
    engine = GameEngine(classifier=EntailmentClassifier())
    engine.load(chain_path)
    port = engine.get_game_port()

    agent = LogicAgent()
    run_res = agent.run(port)

    assert len(run_res.steps) > 0
    for s in run_res.steps:
        assert s.step_no >= 1
        assert len(s.active_clue_ids) >= 1
        assert len(s.sat_queries) >= 1
        assert s.stats.propagations >= 0


@pytest.mark.skipif(not HAS_MODULE_D, reason="Module D not yet implemented (BLOCKED)")
def test_d08_offline_uniqueness() -> None:
    """D-08: Offline uniqueness check on complete clue set without hidden solution."""
    # 1. Unique puzzle
    p_chain = load_puzzle(PUZZLES_DIR / "3x3_chain.json")
    u_chain = check_uniqueness(tuple(p_chain.clues.values()), p_chain.n)
    assert u_chain.status is Uniqueness.UNIQUE
    assert len(u_chain.solutions) == 1

    # 2. Multi-solution puzzle
    p_multi = load_puzzle(PUZZLES_DIR / "3x3_multi.json")
    u_multi = check_uniqueness(tuple(p_multi.clues.values()), p_multi.n)
    assert u_multi.status is Uniqueness.MULTIPLE
    assert len(u_multi.solutions) == 2

    # 3. Inconsistent puzzle
    p_incons = load_puzzle(PUZZLES_DIR / "3x3_inconsistent.json")
    u_incons = check_uniqueness(tuple(p_incons.clues.values()), p_incons.n)
    assert u_incons.status is Uniqueness.NONE
