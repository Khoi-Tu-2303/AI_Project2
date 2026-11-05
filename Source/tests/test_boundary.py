"""Tests for independent chain solving with Oracle and public boundary isolation (A-19, A-20)."""

import copy
from pathlib import Path

from common.puzzle_io import load_puzzle
from common.types import Classification, Clue, Status, VerdictResult
from engine.game_engine import GameEngine
from tests.oracles import OracleClassifier, classify_public_state_oracle


def test_independent_chain_reveal_with_oracle() -> None:
    """A-19: Sequential deduction of 3x3 chain puzzle using independent OracleClassifier.
    
    Verifies 8 accepted verdicts in exact specified order, reaching all 9 cards revealed.
    """
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    engine = GameEngine()
    engine.load(chain_path)
    oracle = OracleClassifier()
    engine.set_classifier(oracle)

    expected_order = ["B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3"]
    expected_verdicts = [
        Status.CRIMINAL,
        Status.INNOCENT,
        Status.CRIMINAL,
        Status.INNOCENT,
        Status.CRIMINAL,
        Status.INNOCENT,
        Status.CRIMINAL,
        Status.INNOCENT,
    ]

    for step_idx, (target_cell, expected_verdict) in enumerate(zip(expected_order, expected_verdicts)):
        state = engine.get_public_state()
        assert target_cell in state.unsolved

        # Check oracle says this cell is indeed forced
        report = oracle(state)
        expected_class = (
            Classification.CRIMINAL if expected_verdict is Status.CRIMINAL else Classification.INNOCENT
        )
        assert report.by_cell[target_cell] is expected_class

        # Submit verdict
        outcome = engine.submit_verdict(target_cell, expected_verdict)
        assert outcome.result is VerdictResult.ACCEPTED
        assert outcome.cell == target_cell
        assert outcome.verdict is expected_verdict
        assert engine.num_revealed() == step_idx + 2

    assert engine.is_complete()
    assert engine.num_revealed() == 9


def test_public_equivalent_fixtures() -> None:
    """A-20: Two puzzles with identical public state but different hidden content.
    
    Ensures engine snapshot and classifier behave identically based solely on public knowledge.
    """
    chain_path = Path(__file__).resolve().parent.parent / "puzzles" / "examples" / "3x3_chain.json"
    puzzle1 = load_puzzle(chain_path)

    # Create puzzle2 with different hidden solution and clues on unrevealed cells
    puzzle2 = copy.deepcopy(puzzle1)
    # Mutate unrevealed clues on C3 with a unique clue ID
    new_clues = dict(puzzle2.clues)
    clue_b1 = puzzle1.clues["B1"]
    new_clues["C3"] = Clue(
        id="c_C3_alt",
        type=clue_b1.type,
        cells=clue_b1.cells,
        status=clue_b1.status,
    )
    object.__setattr__(puzzle2, "clues", new_clues)

    engine1 = GameEngine()
    engine2 = GameEngine()
    state1 = engine1.load(puzzle1)
    state2 = engine2.load(puzzle2)

    # Public states must have identical visible information
    assert state1.known_statuses == state2.known_statuses
    assert state1.revealed_clues == state2.revealed_clues
    assert state1.unsolved == state2.unsolved

    # Oracle classification must be identical
    rep1 = classify_public_state_oracle(state1)
    rep2 = classify_public_state_oracle(state2)
    assert rep1.status == rep2.status
    assert rep1.by_cell == rep2.by_cell
