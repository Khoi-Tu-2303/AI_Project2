"""Deductive LogicAgent for autonomous no-guess reasoning (Module D)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from common.errors import ReasoningFailure
from common.protocols import Classifier, GamePort
from common.types import (
    Cell,
    Classification,
    ClassificationReport,
    Clue,
    Hint,
    PublicState,
    ReasoningStatus,
    Status,
    VerdictOutcome,
    VerdictResult,
)
from logic.dpll import SolveStats
from logic.entailment import EntailmentClassifier, QueryRecord


class AgentStatus(Enum):
    """Terminal or operational state of the logic agent."""
    SOLVED = "SOLVED"
    STUCK = "STUCK"
    INCONSISTENT = "INCONSISTENT"
    TIMEOUT = "TIMEOUT"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class StepResult:
    """Detailed record of a single deduction step in the agent loop."""
    step_no: int
    cell: Cell
    verdict: Status
    outcome: VerdictOutcome
    new_clue: Clue | None = None
    active_clue_ids: tuple[str, ...] = ()
    sat_queries: tuple[QueryRecord, ...] = ()
    stats: SolveStats = field(default_factory=SolveStats)


@dataclass(frozen=True)
class RunResult:
    """Comprehensive summary of a multi-step agent deduction run."""
    status: AgentStatus
    steps: tuple[StepResult, ...] = ()
    total_sat_calls: int = 0
    total_stats: SolveStats = field(default_factory=SolveStats)
    final_state: PublicState | None = None
    message: str = ""

    @property
    def is_solved(self) -> bool:
        return self.status is AgentStatus.SOLVED


class LogicAgent:
    """Autonomous no-guess reasoning agent powered by DPLL SAT entailment.

    Strictly complies with the information security boundary:
    - Never accesses private GameEngine, hidden characters, or unrevealed clues.
    - Only queries PublicState and interacts with GamePort.
    - Selects forced verdicts in deterministic row-major order.
    """

    def __init__(self, classifier: Classifier | None = None) -> None:
        self._classifier: Classifier = classifier if classifier is not None else EntailmentClassifier()
        self._step_counter: int = 0

    def classify_state(
        self, state: PublicState, *, deadline: float | None = None
    ) -> ClassificationReport:
        """Classify each unrevealed cell using the current public knowledge base."""
        return self._classifier(state, deadline=deadline)

    def hint(
        self, state: PublicState, *, deadline: float | None = None
    ) -> Hint | None:
        """Find the next logically forced cell in row-major order without guessing."""
        if not state.unsolved:
            return None

        report = self.classify_state(state, deadline=deadline)
        if report.status is not ReasoningStatus.READY:
            raise ReasoningFailure(report.status, report.message)

        clue_ids = tuple(c.id for c in state.revealed_clues.values())
        for cell in state.unsolved:
            classification = report.by_cell.get(cell, Classification.UNKNOWN)
            if classification is Classification.CRIMINAL:
                return Hint(token=state.token, cell=cell, verdict=Status.CRIMINAL, clue_ids=clue_ids)
            if classification is Classification.INNOCENT:
                return Hint(token=state.token, cell=cell, verdict=Status.INNOCENT, clue_ids=clue_ids)

        return None

    def step(
        self,
        port: GamePort,
        *,
        deadline: float | None = None,
    ) -> StepResult | None:
        """Perform one deduction step: classify, pick first forced cell, and submit verdict."""
        state = port.get_public_state()
        if not state.unsolved:
            return None

        hint_val = self.hint(state, deadline=deadline)
        if hint_val is None:
            return None

        outcome = port.submit_verdict(
            hint_val.cell,
            hint_val.verdict,
            expected_token=state.token,
            deadline=deadline,
        )
        self._step_counter += 1

        active_ids = tuple(c.id for c in state.revealed_clues.values())
        last_queries = getattr(self._classifier, "last_queries", ()) or ()
        last_stats_obj = getattr(self._classifier, "last_stats", None)
        solve_stats = (
            last_stats_obj.solver
            if (last_stats_obj and hasattr(last_stats_obj, "solver"))
            else SolveStats()
        )

        return StepResult(
            step_no=self._step_counter,
            cell=hint_val.cell,
            verdict=hint_val.verdict,
            outcome=outcome,
            new_clue=outcome.new_clue,
            active_clue_ids=active_ids,
            sat_queries=last_queries,
            stats=solve_stats,
        )

    def run(
        self,
        port: GamePort,
        *,
        deadline: float | None = None,
        max_steps: int = 100,
    ) -> RunResult:
        """Run the full deduction loop until solved, stuck, or in an error state."""
        steps: list[StepResult] = []
        total_calls = 0
        acc_stats = SolveStats()

        for _ in range(max_steps):
            state = port.get_public_state()
            if not state.unsolved:
                return RunResult(
                    status=AgentStatus.SOLVED,
                    steps=tuple(steps),
                    total_sat_calls=total_calls,
                    total_stats=acc_stats,
                    final_state=state,
                    message="Bàn cờ đã được giải mã trọn vẹn thành công.",
                )

            try:
                step_res = self.step(port, deadline=deadline)
            except ReasoningFailure as rf:
                status = (
                    AgentStatus.INCONSISTENT
                    if rf.status is ReasoningStatus.INCONSISTENT
                    else AgentStatus.TIMEOUT
                )
                return RunResult(
                    status=status,
                    steps=tuple(steps),
                    total_sat_calls=total_calls,
                    total_stats=acc_stats,
                    final_state=port.get_public_state(),
                    message=rf.message,
                )

            if step_res is None:
                return RunResult(
                    status=AgentStatus.STUCK,
                    steps=tuple(steps),
                    total_sat_calls=total_calls,
                    total_stats=acc_stats,
                    final_state=port.get_public_state(),
                    message="Không có ô nào bị ép buộc logic tiếp theo (STUCK).",
                )

            steps.append(step_res)
            last_stats_obj = getattr(self._classifier, "last_stats", None)
            if last_stats_obj:
                total_calls += getattr(last_stats_obj, "sat_calls", 0)
                acc_stats = acc_stats + getattr(last_stats_obj, "solver", SolveStats())

            if step_res.outcome.result is not VerdictResult.ACCEPTED:
                return RunResult(
                    status=AgentStatus.REJECTED,
                    steps=tuple(steps),
                    total_sat_calls=total_calls,
                    total_stats=acc_stats,
                    final_state=port.get_public_state(),
                    message=f"Phán quyết bị từ chối: {step_res.outcome.result.value}",
                )

        final_state = port.get_public_state()
        final_status = AgentStatus.SOLVED if not final_state.unsolved else AgentStatus.STUCK
        return RunResult(
            status=final_status,
            steps=tuple(steps),
            total_sat_calls=total_calls,
            total_stats=acc_stats,
            final_state=final_state,
        )


__all__ = [
    "AgentStatus",
    "LogicAgent",
    "RunResult",
    "StepResult",
]
