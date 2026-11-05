"""Error and exception hierarchy for Griductive Solver."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from common.types import ReasoningStatus


class GriductiveError(Exception):
    """Base exception for all Griductive errors."""


class PuzzleError(GriductiveError):
    """Raised when puzzle data or format is malformed or invalid."""


class ClueError(PuzzleError):
    """Raised when a specific clue definition or parameter is invalid."""


class GameNotLoadedError(GriductiveError):
    """Raised when an operation requires an active loaded game but none is loaded."""


class InvalidActionError(GriductiveError):
    """Raised when a submitted action/verdict violates game rules."""


class AlreadyRevealedError(InvalidActionError):
    """Raised when attempting to submit a verdict for an already revealed cell."""


class ClassifierUnavailableError(GriductiveError):
    """Raised when an engine operation requires a classifier but none is set."""


class StaleStateError(GriductiveError):
    """Raised when a state token does not match the engine's current session or revision."""


class ReferenceMismatchError(GriductiveError):
    """Internal safety error raised when a proved verdict contradicts hidden reference solution.
    
    This is an internal error and MUST NOT expose the true label in user-facing contexts.
    """


class ReasoningFailure(GriductiveError):
    """Raised when classification fails due to INCONSISTENT, TIMEOUT, or ERROR."""

    def __init__(self, status: ReasoningStatus, message: str = "") -> None:
        self.status = status
        self.message = message
        super().__init__(f"Reasoning failure [{status.value}]: {message}" if message else f"Reasoning failure [{status.value}]")

