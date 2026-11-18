"""Bộ điều khiển GUIController kết nối GameEngine, PublicState và Bộ suy diễn SAT (Module E)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common.errors import GriductiveError, ReasoningFailure
from common.manifest_io import load_manifest
from common.protocols import Classifier
from common.puzzle_io import load_puzzle
from common.regions import referenced_cells, resolve_region
from common.types import (
    Cell,
    Classification,
    ClueType,
    Hint,
    PublicState,
    Puzzle,
    ReasoningStatus,
    Status,
    VerdictOutcome,
    VerdictResult,
)
from engine.game_engine import GameEngine
from gui.clue_formatter import format_clue, format_clue_formula
from logic.encoder import CNFEncoder
from logic.entailment import EntailmentClassifier

try:
    from agent.logic_agent import LogicAgent
except ImportError:  # pragma: no cover
    LogicAgent = None  # type: ignore[assignment,misc]


CASE_METADATA_VN: dict[str, dict[str, Any]] = {
    "3x3_classic": {
        "code": "HỒ SƠ #01",
        "title": "Đêm Gala Thượng Lưu",
        "subtitle": "Suy diễn phản chứng tam giác từ 1 manh mối (3×3)",
        "story": "Viên kim cương biến mất giữa dạ tiệc bảo tàng nghệ thuật. Chỉ từ lời khai ban đầu của Thanh tra ngầm Hải (B2), hãy kết hợp phản chứng đa manh mối để lật mặt toàn bộ đồng phạm.",
        "difficulty": 1,
        "badge": "Cơ bản 3×3",
    },
    "3x3_extensions": {
        "code": "HỒ SƠ #02",
        "title": "Chuyến Tàu Đêm Phương Đông",
        "subtitle": "Mệnh đề Chẵn/Lẻ PARITY & Đối chiếu vùng COMPARE (3×3)",
        "story": "Mật thư ngoại giao bị đánh cắp trên chuyến tàu tốc hành xuyên biên giới. Từ Tùy viên Duy (C1), hãy giải mã các ràng buộc chẵn/lẻ và đối chiếu hàng – cột hóc búa.",
        "difficulty": 2,
        "badge": "Mở rộng 3×3",
    },
    "4x4_detective": {
        "code": "HỒ SƠ #03",
        "title": "Chuyên Án Dinh Thự Cổ",
        "subtitle": "16 nghi phạm trên đảo sương mù — Quay lui DPLL (4×4)",
        "story": "16 người bị cô lập trong dinh thự cổ sau cơn bão lớn. Xuất phát duy nhất từ Quản gia Kiên (C2), truy vết đan chéo 15 bước suy luận không một lời khai thừa.",
        "difficulty": 2,
        "badge": "Thám tử 4×4",
    },
    "4x4_crossfire": {
        "code": "HỒ SƠ #04",
        "title": "Mạng Lưới Giao Thoa",
        "subtitle": "Thương cảng sương mù — Giao thoa PARITY & COMPARE (4×4)",
        "story": "Đường dây buôn lậu cổ vật ẩn mình tại bến cảng đêm. Chỉ từ Đặc vụ cảng vụ Mạnh (B3), hãy bóc tách mạng lưới giao thoa giữa các vùng láng giềng và hàng cột.",
        "difficulty": 3,
        "badge": "Chuyên sâu 4×4",
    },
    "5x5_mastermind": {
        "code": "HỒ SƠ #05",
        "title": "Trùm Cuối Tuyệt Mật",
        "subtitle": "Hội nghị thượng đỉnh — Đại án 25 nghi phạm (5×5)",
        "story": "Âm mưu rò rỉ tài liệu mật tại Hội nghị Thượng đỉnh Quốc tế. Bắt đầu từ tâm bàn cờ Thanh tra liên bang Nga (C3), vượt qua 24 bước suy diễn phản chứng đan chéo.",
        "difficulty": 3,
        "badge": "Siêu cấp 5×5",
    },
    "5x5_syndicate": {
        "code": "HỒ SƠ #06",
        "title": "Mạng Lưới Ngầm 5×5",
        "subtitle": "Sòng bạc Hoàng gia — Đỉnh cao suy diễn đa tầng (5×5)",
        "story": "Tổ chức tội phạm ngầm ẩn náu trong Câu lạc bộ Jazz & Sòng bạc Hoàng gia. Từ Thám tử chìm Hồng (D2), kết hợp đủ hệ mệnh đề mở rộng để phá giải đại án 25 người.",
        "difficulty": 3,
        "badge": "Siêu cấp 5×5",
    },
    "chain_demo": {
        "code": "MẪU THỬ #00",
        "title": "Mắt Xích Đầu Tiên (Fixture)",
        "subtitle": "Hồ sơ mẫu kiểm thử chuỗi suy luận cơ bản (3×3)",
        "story": "Hồ sơ mẫu chuẩn dùng cho kiểm thử tự động: từ lời khai của Alice (A1), lần theo chuỗi suy luận tất yếu qua 8 nghi phạm.",
        "difficulty": 1,
        "badge": "Mẫu chuẩn 3×3",
    },
    "3x3_chain": {
        "code": "MẪU THỬ #00",
        "title": "Mắt Xích Đầu Tiên (Fixture)",
        "subtitle": "Hồ sơ mẫu kiểm thử chuỗi suy luận cơ bản (3×3)",
        "story": "Hồ sơ mẫu chuẩn dùng cho kiểm thử tự động: từ lời khai của Alice (A1), lần theo chuỗi suy luận tất yếu qua 8 nghi phạm.",
        "difficulty": 1,
        "badge": "Mẫu chuẩn 3×3",
    },
    "3x3_stuck": {
        "code": "KIỂM THỬ #07",
        "title": "Manh Mối Bỏ Ngỏ (Stuck)",
        "subtitle": "Kiểm thử AI dừng an toàn khi thiếu dữ kiện",
        "story": "Sau khi vạch mặt Bình (B1), lời khai thu được không đủ để buộc tội chắc chắn bất kỳ ai tiếp theo. Bộ giải phải nhận diện trạng thái CHƯA ĐỦ CHỨNG CỨ thay vì đoán mò.",
        "difficulty": 2,
        "badge": "Kiểm thử biên AI",
    },
    "3x3_multi": {
        "code": "KIỂM THỬ #08",
        "title": "Hai Kịch Bản Song Song",
        "subtitle": "Kiểm thử phát hiện đa nghiệm (Multiple Solutions)",
        "story": "Hai nghi phạm cuối cùng ở B3 và C3 có vai trò đối xứng tạo ra 2 nghiệm hợp lệ khác nhau. Kiểm chứng khả năng từ chối phán quyết khi nghiệm chưa duy nhất.",
        "difficulty": 2,
        "badge": "Kiểm thử biên AI",
    },
    "3x3_inconsistent": {
        "code": "KIỂM THỬ #09",
        "title": "Lời Khai Nguỵ Tạo (UNSAT)",
        "subtitle": "Kiểm thử phát hiện mâu thuẫn cơ sở tri thức",
        "story": "Hai thủ phạm đã lộ diện ở Hàng 1 nhưng lời khai lại tuyên bố Hàng 1 có tối đa 1 thủ phạm. Bộ giải DPLL sẽ lập tức báo cáo MÂU THUẪN LOGIC (INCONSISTENT).",
        "difficulty": 2,
        "badge": "Kiểm thử biên AI",
    },
}


def _create_default_classifier() -> Classifier:
    return EntailmentClassifier()


def _create_logic_agent(classifier: Classifier) -> Any:
    if LogicAgent is not None:
        return LogicAgent(classifier=classifier)
    return None


@dataclass(frozen=True)
class TraceEntry:
    step_no: int
    revision: int
    action: str
    cell: Cell | None
    verdict: Status | None
    outcome: str
    detail: str
    clue_id: str | None = None


@dataclass(frozen=True)
class TelemetrySnapshot:
    num_primary: int = 0
    num_aux: int = 0
    num_clauses: int = 0
    sat_calls: int = 0
    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0
    runtime_ms: float = 0.0


@dataclass(frozen=True)
class ManifestPuzzleItem:
    case_id: str
    path: Path
    kind: str
    label: str
    code: str = ""
    title: str = ""
    subtitle: str = ""
    story: str = ""
    difficulty: int = 1
    badge: str = ""
    n: int = 3


class GUIController:
    """Bộ điều khiển trung tâm cho cả Web UI và Desktop UI."""

    def __init__(
        self,
        classifier: Classifier | None = None,
        puzzles_dir: Path | None = None,
    ) -> None:
        self._classifier: Classifier = classifier if classifier is not None else _create_default_classifier()
        self._agent: Any = _create_logic_agent(self._classifier)
        self._engine: GameEngine | None = None
        self._current_puzzle_path: Path | None = None
        self._selected_clue_cell: Cell | None = None
        self._active_hint: Hint | None = None
        self._trace: list[TraceEntry] = []
        self._telemetry: TelemetrySnapshot = TelemetrySnapshot()
        self._reveal_step_by_cell: dict[Cell, int] = {}
        self._deduction_steps: list[dict[str, Any]] = []

        if puzzles_dir is None:
            puzzles_dir = Path(__file__).resolve().parent.parent / "puzzles"
        self._puzzles_dir = puzzles_dir

    @property
    def agent(self) -> Any:
        return self._agent

    @property
    def reveal_step_by_cell(self) -> dict[Cell, int]:
        return dict(self._reveal_step_by_cell)

    @property
    def deduction_steps(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._deduction_steps)

    @property
    def is_loaded(self) -> bool:
        return self._engine is not None

    @property
    def current_puzzle_path(self) -> Path | None:
        return self._current_puzzle_path

    @property
    def selected_clue_cell(self) -> Cell | None:
        return self._selected_clue_cell

    @property
    def active_hint(self) -> Hint | None:
        return self._active_hint

    @property
    def trace(self) -> tuple[TraceEntry, ...]:
        return tuple(self._trace)

    @property
    def telemetry(self) -> TelemetrySnapshot:
        return self._telemetry

    def discover_puzzles(self) -> list[ManifestPuzzleItem]:
        items: list[ManifestPuzzleItem] = []
        manifest_path = self._puzzles_dir / "index.json"
        seen_paths: set[Path] = set()

        if manifest_path.exists():
            try:
                manifest = load_manifest(manifest_path)
                for idx, entry in enumerate(manifest.get("cases", []), start=1):
                    rel = entry.get("path", "")
                    full = (self._puzzles_dir / rel).resolve()
                    if full.exists():
                        cid = str(entry.get("case_id", full.stem))
                        kind = str(entry.get("kind", "normal"))
                        meta = CASE_METADATA_VN.get(cid, {})
                        n_val = 5 if "5x5" in cid else (4 if "4x4" in cid else 3)
                        code = meta.get("code", f"HỒ SƠ #{idx:02d}")
                        title = meta.get("title", cid)
                        subtitle = meta.get("subtitle", f"Bàn cờ {n_val}×{n_val}")
                        story = meta.get("story", "Hồ sơ vụ án logic mệnh đề.")
                        diff = int(meta.get("difficulty", 2))
                        badge = meta.get("badge", f"{n_val}×{n_val}")
                        items.append(
                            ManifestPuzzleItem(
                                case_id=cid,
                                path=full,
                                kind=kind,
                                label=f"{code}: {title} ({n_val}×{n_val})",
                                code=code,
                                title=title,
                                subtitle=subtitle,
                                story=story,
                                difficulty=diff,
                                badge=badge,
                                n=n_val,
                            )
                        )
                        seen_paths.add(full)
            except Exception:
                pass

        examples_dir = self._puzzles_dir / "examples"
        if examples_dir.exists():
            for p in sorted(examples_dir.glob("*.json")):
                resolved = p.resolve()
                if resolved not in seen_paths:
                    cid = p.stem
                    meta = CASE_METADATA_VN.get(cid, {})
                    n_val = 5 if "5x5" in cid else (4 if "4x4" in cid else 3)
                    items.append(
                        ManifestPuzzleItem(
                            case_id=cid,
                            path=resolved,
                            kind="normal",
                            label=meta.get("title", cid),
                            code=meta.get("code", "HỒ SƠ"),
                            title=meta.get("title", cid),
                            subtitle=meta.get("subtitle", f"Bàn cờ {n_val}×{n_val}"),
                            story=meta.get("story", "Hồ sơ điều tra bổ sung."),
                            difficulty=int(meta.get("difficulty", 2)),
                            badge=meta.get("badge", f"{n_val}×{n_val}"),
                            n=n_val,
                        )
                    )
        return items

    def load_puzzle(self, source: str | Path | Puzzle) -> PublicState:
        if isinstance(source, Puzzle):
            puzzle_in: str | Path | Puzzle = source
            self._current_puzzle_path = None
        else:
            path = Path(source).resolve()
            puzzle_in = load_puzzle(path)
            self._current_puzzle_path = path

        self._engine = GameEngine(classifier=self._classifier)
        self._agent = _create_logic_agent(self._classifier)
        state = self._engine.load(puzzle_in)
        self._selected_clue_cell = None
        self._active_hint = None
        self._trace.clear()
        self._deduction_steps.clear()
        self._reveal_step_by_cell = {c: 0 for c in state.known_statuses}

        self._refresh_kb_telemetry(state)
        self._append_trace(
            action="LOAD",
            cell=None,
            verdict=None,
            outcome="INFO",
            detail=(
                f"Đã mở hồ sơ '{state.puzzle_id}' ({state.n}×{state.n}) — "
                f"{len(state.known_statuses)}/{state.n * state.n} nghi phạm đã rõ thân phận ban đầu."
            ),
        )
        return state

    def restart(self) -> PublicState:
        self._require_engine()
        assert self._engine is not None
        self._agent = _create_logic_agent(self._classifier)
        state = self._engine.restart()
        self._selected_clue_cell = None
        self._active_hint = None
        self._trace.clear()
        self._deduction_steps.clear()
        self._reveal_step_by_cell = {c: 0 for c in state.known_statuses}
        self._refresh_kb_telemetry(state)
        self._append_trace(
            action="RESTART",
            cell=None,
            verdict=None,
            outcome="INFO",
            detail=f"Đã làm mới hồ sơ '{state.puzzle_id}' về trạng thái khởi điểm.",
        )
        return state

    def get_public_state(self) -> PublicState:
        self._require_engine()
        assert self._engine is not None
        return self._engine.get_public_state()

    def is_complete(self) -> bool:
        self._require_engine()
        assert self._engine is not None
        return self._engine.is_complete()

    def select_clue(self, cell: Cell | None) -> tuple[Cell, ...]:
        state = self.get_public_state()
        if cell is None or cell not in state.revealed_clues:
            self._selected_clue_cell = None
            return ()
        self._selected_clue_cell = cell
        clue = state.revealed_clues[cell]
        return referenced_cells(clue, state.n)

    @property
    def highlighted_cells(self) -> tuple[Cell, ...]:
        if self._engine is None or self._selected_clue_cell is None:
            return ()
        state = self._engine.get_public_state()
        clue = state.revealed_clues.get(self._selected_clue_cell)
        if clue is None:
            return ()
        return referenced_cells(clue, state.n)

    def get_clue_region_breakdown(self) -> dict[str, tuple[Cell, ...]]:
        if self._engine is None or self._selected_clue_cell is None:
            return {"primary": (), "left": (), "right": (), "overlap": ()}
        state = self._engine.get_public_state()
        clue = state.revealed_clues.get(self._selected_clue_cell)
        if clue is None:
            return {"primary": (), "left": (), "right": (), "overlap": ()}

        refs = referenced_cells(clue, state.n)
        if clue.type is ClueType.COMPARE and clue.left is not None and clue.right is not None:
            left_cells = resolve_region(clue.left, state.n)
            right_cells = resolve_region(clue.right, state.n)
            left_set = set(left_cells)
            right_set = set(right_cells)
            overlap = tuple(c for c in left_cells if c in right_set)
            left_only = tuple(c for c in left_cells if c not in right_set)
            right_only = tuple(c for c in right_cells if c not in left_set)
            return {
                "primary": refs,
                "left": left_only,
                "right": right_only,
                "overlap": overlap,
            }
        return {
            "primary": refs,
            "left": (),
            "right": (),
            "overlap": (),
        }

    def submit_verdict(self, cell: Cell, verdict: Status) -> VerdictOutcome:
        self._require_engine()
        assert self._engine is not None

        state_before = self._engine.get_public_state()
        outcome = self._engine.submit_verdict(cell, verdict)
        state = self._engine.get_public_state()
        self._refresh_solver_telemetry(state)
        self._record_verdict_outcome(state_before, state, cell, verdict, outcome, actor="Người chơi")
        return outcome

    def _record_verdict_outcome(
        self,
        state_before: PublicState,
        state: PublicState,
        cell: Cell,
        verdict: Status,
        outcome: VerdictOutcome,
        *,
        actor: str = "LogicAgent",
    ) -> None:
        verdict_vn = "VÔ TỘI" if verdict is Status.INNOCENT else "THỦ PHẠM"

        if outcome.result is VerdictResult.ACCEPTED:
            if self._active_hint is not None and self._active_hint.cell == cell:
                self._active_hint = None
            step_idx = len(self._deduction_steps) + 1
            self._reveal_step_by_cell[cell] = step_idx

            char_map = {ch.cell: ch for ch in state_before.characters}
            target_ch = char_map.get(cell)
            target_name = target_ch.name if target_ch else cell
            target_prof = target_ch.profession if target_ch else ""

            supporting: list[dict[str, Any]] = []
            for c_cell, cl in state_before.revealed_clues.items():
                refs = referenced_cells(cl, state_before.n)
                if cell in refs:
                    f_info = format_clue_formula(cl, state_before.n)
                    supporting.append({
                        "cell": c_cell,
                        "owner": char_map[c_cell].name if c_cell in char_map else c_cell,
                        "id": cl.id,
                        "type": cl.type.value,
                        "text": format_clue(cl, state_before, compact=True),
                        "math_formula": f_info["math_formula"],
                        "cnf_preview": f_info["cnf_preview"],
                    })
            if not supporting:
                for c_cell, cl in list(state_before.revealed_clues.items())[-2:]:
                    f_info = format_clue_formula(cl, state_before.n)
                    supporting.append({
                        "cell": c_cell,
                        "owner": char_map[c_cell].name if c_cell in char_map else c_cell,
                        "id": cl.id,
                        "type": cl.type.value,
                        "text": format_clue(cl, state_before, compact=True),
                        "math_formula": f_info["math_formula"],
                        "cnf_preview": f_info["cnf_preview"],
                    })

            if verdict is Status.CRIMINAL:
                ref_q = f"KB_{step_idx - 1} ∧ ¬C_{cell}  ⟹  UNSAT"
                ref_desc = f"Giả sử {target_name} ({cell}) Vô tội (¬C_{cell}) → Xung đột mệnh đề (UNSAT)"
                con_q = f"KB_{step_idx - 1} ∧ C_{cell}  ⟹  SAT"
                ent_f = f"KB_{step_idx - 1} ⊨ C_{cell}"
                unit_c = f"(C_{cell})"
            else:
                ref_q = f"KB_{step_idx - 1} ∧ C_{cell}  ⟹  UNSAT"
                ref_desc = f"Giả sử {target_name} ({cell}) Thủ phạm (C_{cell}) → Xung đột mệnh đề (UNSAT)"
                con_q = f"KB_{step_idx - 1} ∧ ¬C_{cell}  ⟹  SAT"
                ent_f = f"KB_{step_idx - 1} ⊨ ¬C_{cell}"
                unit_c = f"(¬C_{cell})"

            new_clue_data = None
            if outcome.new_clue is not None:
                nf = format_clue_formula(outcome.new_clue, state.n)
                new_clue_data = {
                    "id": outcome.new_clue.id,
                    "type": outcome.new_clue.type.value,
                    "text": format_clue(outcome.new_clue, state, compact=False),
                    "math_formula": nf["math_formula"],
                    "cnf_preview": nf["cnf_preview"],
                    "clause_count": nf["clause_count"],
                }

            tel = self._telemetry
            self._deduction_steps.append({
                "step_no": step_idx,
                "cell": cell,
                "name": target_name,
                "profession": target_prof,
                "verdict": verdict.value,
                "verdict_vn": verdict_vn,
                "refutation_query": ref_q,
                "refutation_desc": ref_desc,
                "consistency_query": con_q,
                "entailment_formula": ent_f,
                "unit_clause": unit_c,
                "supporting_clues": supporting[:3],
                "new_clue": new_clue_data,
                "telemetry": {
                    "num_clauses": tel.num_clauses,
                    "num_primary": tel.num_primary,
                    "num_aux": tel.num_aux,
                    "sat_calls": tel.sat_calls,
                    "decisions": tel.decisions,
                    "propagations": tel.propagations,
                    "backtracks": tel.backtracks,
                    "runtime_ms": round(tel.runtime_ms, 2),
                },
            })

            clue_id = outcome.new_clue.id if outcome.new_clue is not None else None
            self._append_trace(
                action="VERDICT",
                cell=cell,
                verdict=verdict,
                outcome="ACCEPTED",
                detail=f"[{actor}] Chấp nhận {cell} là {verdict_vn} (đã chứng minh tất yếu). Mở lời khai {clue_id}.",
                clue_id=clue_id,
            )
        elif outcome.result is VerdictResult.NOT_PROVABLE:
            self._append_trace(
                action="VERDICT",
                cell=cell,
                verdict=verdict,
                outcome="NOT_PROVABLE",
                detail=f"[{actor}] Từ chối {cell} = {verdict_vn}: Chưa đủ bằng chứng suy diễn (cấm đoán mò).",
            )
        else:
            self._append_trace(
                action="VERDICT",
                cell=cell,
                verdict=verdict,
                outcome="CONTRADICTED",
                detail=f"[{actor}] Từ chối {cell} = {verdict_vn}: Mâu thuẫn trực tiếp với các lời khai hiện tại!",
            )

    def get_hint(self) -> Hint | None:
        self._require_engine()
        assert self._engine is not None
        port = self._engine.get_game_port()
        state = port.get_public_state()
        if not state.unsolved:
            self._active_hint = None
            return None

        if self._agent is not None:
            hint = self._agent.hint(state)
            self._refresh_solver_telemetry(state)
        else:
            report = self._classifier(state)
            self._refresh_solver_telemetry(state)
            if report.status is not ReasoningStatus.READY:
                raise ReasoningFailure(report.status, report.message)
            clue_ids = tuple(c.id for c in state.revealed_clues.values())
            hint = None
            for cell in state.unsolved:
                cls_val = report.by_cell.get(cell, Classification.UNKNOWN)
                if cls_val is Classification.CRIMINAL:
                    hint = Hint(token=state.token, cell=cell, verdict=Status.CRIMINAL, clue_ids=clue_ids)
                    break
                if cls_val is Classification.INNOCENT:
                    hint = Hint(token=state.token, cell=cell, verdict=Status.INNOCENT, clue_ids=clue_ids)
                    break

        if hint is not None:
            self._active_hint = hint
            self._append_trace(
                action="HINT",
                cell=hint.cell,
                verdict=hint.verdict,
                outcome="FORCED",
                detail=f"[LogicAgent] Gợi ý: Nghi phạm ở ô {hint.cell} đã đủ bằng chứng chứng minh suy diễn.",
            )
            return hint

        self._active_hint = None
        self._append_trace(
            action="HINT",
            cell=None,
            verdict=None,
            outcome="STUCK",
            detail="[LogicAgent] Không có ô nào bị ép buộc logic từ các lời khai hiện tại (STUCK / UNKNOWN).",
        )
        return None

    def step_auto_solve(self) -> VerdictOutcome | None:
        self._require_engine()
        assert self._engine is not None

        if self._agent is None:
            hint = self.get_hint()
            if hint is None:
                return None
            return self.submit_verdict(hint.cell, hint.verdict)

        port = self._engine.get_game_port()
        state_before = port.get_public_state()
        if not state_before.unsolved:
            self._active_hint = None
            return None

        step_res = self._agent.step(port)
        if step_res is None:
            self._active_hint = None
            self._refresh_solver_telemetry(state_before)
            self._append_trace(
                action="AGENT_STEP",
                cell=None,
                verdict=None,
                outcome="STUCK",
                detail="[LogicAgent] Dừng an toàn: Không có ô nào bị ép buộc logic tiếp theo (cấm đoán mò).",
            )
            return None

        state_after = port.get_public_state()
        self._refresh_solver_telemetry(
            state_after,
            extra_sat_calls=len(step_res.sat_queries),
            extra_stats=step_res.stats,
        )
        self._record_verdict_outcome(
            state_before,
            state_after,
            step_res.cell,
            step_res.verdict,
            step_res.outcome,
            actor="LogicAgent",
        )
        return step_res.outcome

    def auto_solve_all(self, max_steps: int = 100) -> list[VerdictOutcome]:
        outcomes: list[VerdictOutcome] = []
        for _ in range(max_steps):
            if self.is_complete():
                break
            out = self.step_auto_solve()
            if out is None or out.result is not VerdictResult.ACCEPTED:
                break
            outcomes.append(out)
        return outcomes

    def _require_engine(self) -> None:
        if self._engine is None:
            raise GriductiveError("Chưa tải hồ sơ vụ án nào vào GUIController.")

    def _refresh_kb_telemetry(self, state: PublicState) -> None:
        encoder = CNFEncoder(state.n)
        kb = encoder.build_kb(tuple(state.revealed_clues.values()), state.known_statuses)
        self._telemetry = TelemetrySnapshot(
            num_primary=kb.num_primary,
            num_aux=kb.num_aux,
            num_clauses=len(kb.clauses),
            sat_calls=0,
            decisions=0,
            propagations=0,
            backtracks=0,
            runtime_ms=0.0,
        )

    def _refresh_solver_telemetry(
        self,
        state: PublicState,
        *,
        extra_sat_calls: int | None = None,
        extra_stats: Any = None,
    ) -> None:
        encoder = CNFEncoder(state.n)
        kb = encoder.build_kb(tuple(state.revealed_clues.values()), state.known_statuses)
        prev = self._telemetry
        if extra_stats is not None and extra_sat_calls is not None:
            self._telemetry = TelemetrySnapshot(
                num_primary=kb.num_primary,
                num_aux=kb.num_aux,
                num_clauses=len(kb.clauses),
                sat_calls=prev.sat_calls + extra_sat_calls,
                decisions=prev.decisions + extra_stats.decisions,
                propagations=prev.propagations + extra_stats.propagations,
                backtracks=prev.backtracks + extra_stats.backtracks,
                runtime_ms=prev.runtime_ms + extra_stats.runtime_seconds * 1000.0,
            )
            return

        ent_stats = getattr(self._classifier, "last_stats", None)
        if ent_stats is not None and hasattr(ent_stats, "solver"):
            s = ent_stats.solver
            self._telemetry = TelemetrySnapshot(
                num_primary=kb.num_primary,
                num_aux=kb.num_aux,
                num_clauses=len(kb.clauses),
                sat_calls=prev.sat_calls + ent_stats.sat_calls,
                decisions=prev.decisions + s.decisions,
                propagations=prev.propagations + s.propagations,
                backtracks=prev.backtracks + s.backtracks,
                runtime_ms=prev.runtime_ms + s.runtime_seconds * 1000.0,
            )
        else:
            self._telemetry = TelemetrySnapshot(
                num_primary=kb.num_primary,
                num_aux=kb.num_aux,
                num_clauses=len(kb.clauses),
                sat_calls=prev.sat_calls + 1,
                decisions=prev.decisions,
                propagations=prev.propagations,
                backtracks=prev.backtracks,
                runtime_ms=prev.runtime_ms,
            )

    def _append_trace(
        self,
        *,
        action: str,
        cell: Cell | None,
        verdict: Status | None,
        outcome: str,
        detail: str,
        clue_id: str | None = None,
    ) -> None:
        rev = self._engine.get_public_state().token.revision if self._engine is not None else 0
        entry = TraceEntry(
            step_no=len(self._trace) + 1,
            revision=rev,
            action=action,
            cell=cell,
            verdict=verdict,
            outcome=outcome,
            detail=detail,
            clue_id=clue_id,
        )
        self._trace.append(entry)
