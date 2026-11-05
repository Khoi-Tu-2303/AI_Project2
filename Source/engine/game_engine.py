"""GameEngine managing lifecycle, public state progression, and verdict transactions."""

from __future__ import annotations

import copy
from pathlib import Path
import time
from typing import Mapping
import uuid

from common.errors import (
    AlreadyRevealedError,
    ClassifierUnavailableError,
    GameNotLoadedError,
    InvalidActionError,
    ReasoningFailure,
    ReferenceMismatchError,
    StaleStateError,
)
from common.protocols import Classifier, GamePort
from common.puzzle_io import load_puzzle
from common.regions import all_cells, cell_to_index
from common.types import (
    Cell,
    Character,
    Classification,
    ClassificationReport,
    Clue,
    PublicState,
    Puzzle,
    ReasoningStatus,
    StateToken,
    Status,
    VerdictOutcome,
    VerdictResult,
)
from common.validation import validate_cell, validate_puzzle_structure
from engine.public_port import PublicGamePort


class GameEngine:
    """Core game engine managing puzzle progression, state tokens, and verdicts."""

    def __init__(self, classifier: Classifier | None = None) -> None:
        self._classifier: Classifier | None = classifier
        self._pristine_puzzle: Puzzle | None = None
        self._session_id: str | None = None
        self._revision: int = 0
        self._known_statuses: dict[Cell, Status] = {}
        self._revealed_clues: dict[Cell, Clue] = {}
        self._is_evaluating: bool = False

    def set_classifier(self, classifier: Classifier) -> None:
        """Inject or update the classifier used for deductive verification."""
        self._classifier = classifier

    def load(self, path_or_puzzle: str | Path | Puzzle) -> PublicState:
        """Load and initialize a puzzle from path or Puzzle instance.
        
        If loading or validation fails, previous game state is untouched.
        """
        if isinstance(path_or_puzzle, (str, Path)):
            new_puzzle = load_puzzle(path_or_puzzle)
        elif isinstance(path_or_puzzle, Puzzle):
            validate_puzzle_structure(path_or_puzzle)
            new_puzzle = copy.deepcopy(path_or_puzzle)
        else:
            raise InvalidActionError(f"Unsupported puzzle input type: {type(path_or_puzzle).__name__}")

        # Deep copy to ensure pristine puzzle cannot be mutated from outside
        self._pristine_puzzle = copy.deepcopy(new_puzzle)
        self._session_id = uuid.uuid4().hex
        self._revision = 0
        self._known_statuses = dict(self._pristine_puzzle.initial_revealed)
        self._revealed_clues = {
            cell: copy.deepcopy(self._pristine_puzzle.clues[cell])
            for cell in self._pristine_puzzle.initial_revealed
        }
        self._is_evaluating = False
        return self.get_public_state()

    def restart(self) -> PublicState:
        """Restart the currently loaded game, generating a new session and clearing verdicts."""
        if self._pristine_puzzle is None:
            raise GameNotLoadedError("Cannot restart: no game loaded")

        self._session_id = uuid.uuid4().hex
        self._revision = 0
        self._known_statuses = dict(self._pristine_puzzle.initial_revealed)
        self._revealed_clues = {
            cell: copy.deepcopy(self._pristine_puzzle.clues[cell])
            for cell in self._pristine_puzzle.initial_revealed
        }
        self._is_evaluating = False
        return self.get_public_state()

    def get_public_state(self) -> PublicState:
        """Return an independent, deep-copied snapshot of the current public state."""
        if self._pristine_puzzle is None or self._session_id is None:
            raise GameNotLoadedError("Cannot get public state: no game loaded")

        n = self._pristine_puzzle.n
        cells_ordered = all_cells(n)
        unsolved = tuple(c for c in cells_ordered if c not in self._known_statuses)
        token = StateToken(session_id=self._session_id, revision=self._revision)

        # Build characters tuple
        chars = tuple(copy.deepcopy(self._pristine_puzzle.characters))

        return PublicState(
            puzzle_id=self._pristine_puzzle.id,
            token=token,
            n=n,
            characters=chars,
            known_statuses=dict(self._known_statuses),
            revealed_clues={k: copy.deepcopy(v) for k, v in self._revealed_clues.items()},
            unsolved=unsolved,
        )

    def is_complete(self) -> bool:
        """Return True if all cards in the grid have been revealed."""
        if self._pristine_puzzle is None:
            raise GameNotLoadedError("Game not loaded")
        return len(self._known_statuses) == self._pristine_puzzle.n ** 2

    def num_revealed(self) -> int:
        """Return the count of currently revealed cards."""
        if self._pristine_puzzle is None:
            raise GameNotLoadedError("Game not loaded")
        return len(self._known_statuses)

    def get_game_port(self) -> GamePort:
        """Return the restricted GamePort facade."""
        return PublicGamePort(self)

    def submit_verdict(
        self,
        cell: Cell,
        verdict: Status,
        *,
        expected_token: StateToken | None = None,
        deadline: float | None = None,
    ) -> VerdictOutcome:
        """Submit a single verdict for an unrevealed cell.
        
        Evaluates deduction via classifier, verifies reference solution if present,
        and atomically reveals the card and its clue if proved.
        """
        if self._pristine_puzzle is None or self._session_id is None:
            raise GameNotLoadedError("Cannot submit verdict: no game loaded")

        if self._is_evaluating:
            raise InvalidActionError("Reentrant verdict submission during evaluation is prohibited")

        n = self._pristine_puzzle.n
        validate_cell(cell, n)

        if not isinstance(verdict, Status):
            raise InvalidActionError(f"Verdict must be Status enum, got {type(verdict).__name__}: {verdict!r}")

        if cell in self._known_statuses:
            raise AlreadyRevealedError(f"Cell {cell} has already been revealed")

        cur_token = StateToken(session_id=self._session_id, revision=self._revision)
        if expected_token is not None and expected_token != cur_token:
            raise StaleStateError(
                f"StateToken mismatch: expected {expected_token}, current is {cur_token}"
            )

        if deadline is not None and time.monotonic() > deadline:
            raise ReasoningFailure(ReasoningStatus.TIMEOUT, "Deadline exceeded before classification")

        if self._classifier is None:
            raise ClassifierUnavailableError("No classifier registered with GameEngine")

        # Snapshot generation
        snapshot = self.get_public_state()

        # Execute classifier under reentrancy guard
        self._is_evaluating = True
        try:
            report = self._classifier(snapshot, deadline=deadline)
        except ReasoningFailure:
            raise
        except Exception as e:
            raise ReasoningFailure(ReasoningStatus.ERROR, f"Classifier raised unhandled error: {e}") from e
        finally:
            self._is_evaluating = False

        # Validate report
        if not isinstance(report, ClassificationReport):
            raise ReasoningFailure(ReasoningStatus.ERROR, f"Invalid classifier report type: {type(report).__name__}")

        if report.token != cur_token:
            raise ReasoningFailure(
                ReasoningStatus.ERROR,
                f"Report token {report.token} does not match snapshot token {cur_token}",
            )

        if report.status is not ReasoningStatus.READY:
            raise ReasoningFailure(report.status, report.message)

        # Check coverage of unsolved cells
        for unres in snapshot.unsolved:
            if unres not in report.by_cell:
                raise ReasoningFailure(
                    ReasoningStatus.ERROR,
                    f"ClassificationReport missing status for unresolved cell {unres}",
                )

        target_class = report.by_cell[cell]

        # Post-callback checks
        if self._session_id != cur_token.session_id or self._revision != cur_token.revision:
            raise StaleStateError("Engine state mutated during classifier execution")

        if deadline is not None and time.monotonic() > deadline:
            raise ReasoningFailure(ReasoningStatus.TIMEOUT, "Deadline exceeded before verdict commit")

        # Deductive outcomes
        if target_class is Classification.UNKNOWN:
            return VerdictOutcome(
                result=VerdictResult.NOT_PROVABLE,
                cell=cell,
                verdict=verdict,
                before_token=cur_token,
                after_token=cur_token,
                new_clue=None,
            )

        forced_verdict = Status.CRIMINAL if target_class is Classification.CRIMINAL else Status.INNOCENT

        if forced_verdict != verdict:
            return VerdictOutcome(
                result=VerdictResult.CONTRADICTED,
                cell=cell,
                verdict=verdict,
                before_token=cur_token,
                after_token=cur_token,
                new_clue=None,
            )

        # Forced verdict agrees with submitted verdict!
        # Check reference consistency if solution is known
        if self._pristine_puzzle.solution is not None:
            ref_status = self._pristine_puzzle.solution.get(cell)
            if ref_status is not None and ref_status != verdict:
                raise ReferenceMismatchError(
                    f"Proved verdict for cell {cell} contradicts hidden reference solution"
                )

        # Atomic commit
        self._known_statuses[cell] = verdict
        new_clue = copy.deepcopy(self._pristine_puzzle.clues[cell])
        self._revealed_clues[cell] = new_clue
        self._revision += 1
        after_token = StateToken(session_id=self._session_id, revision=self._revision)

        return VerdictOutcome(
            result=VerdictResult.ACCEPTED,
            cell=cell,
            verdict=verdict,
            before_token=cur_token,
            after_token=after_token,
            new_clue=new_clue,
        )

