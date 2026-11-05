"""GamePort public facade exposing only public operations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from common.protocols import GamePort
from common.types import Cell, PublicState, StateToken, Status, VerdictOutcome

if TYPE_CHECKING:
    from engine.game_engine import GameEngine


class PublicGamePort:
    """Facade wrapping GameEngine to expose only GamePort protocol methods."""

    def __init__(self, engine: GameEngine) -> None:
        self._engine = engine

    def get_public_state(self) -> PublicState:
        """Get current public state snapshot."""
        return self._engine.get_public_state()

    def submit_verdict(
        self,
        cell: Cell,
        verdict: Status,
        *,
        expected_token: StateToken | None = None,
        deadline: float | None = None,
    ) -> VerdictOutcome:
        """Submit a verdict through the public port."""
        return self._engine.submit_verdict(
            cell=cell,
            verdict=verdict,
            expected_token=expected_token,
            deadline=deadline,
        )

