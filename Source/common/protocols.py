"""Protocols and structural interfaces for Griductive Solver."""

from __future__ import annotations

from typing import Protocol
from common.types import Cell, Status, StateToken, PublicState, ClassificationReport, VerdictOutcome


class Classifier(Protocol):
    """Protocol for deduction engine classifiers."""

    def __call__(
        self, state: PublicState, *, deadline: float | None = None
    ) -> ClassificationReport:
        """Classify unrevealed cells from a public state snapshot."""
        ...


class GamePort(Protocol):
    """Restricted public facade provided to LogicAgent and GUI."""

    def get_public_state(self) -> PublicState:
        """Get the current public snapshot of the game."""
        ...

    def submit_verdict(
        self,
        cell: Cell,
        verdict: Status,
        *,
        expected_token: StateToken | None = None,
        deadline: float | None = None,
    ) -> VerdictOutcome:
        """Submit a single verdict for an unrevealed cell."""
        ...

