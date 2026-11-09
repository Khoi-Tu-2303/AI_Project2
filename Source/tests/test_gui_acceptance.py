"""Kiểm thử nghiệm thu cho Module E (GUI Tiếng Việt, Controller & Bộ Màn chơi)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import pytest

from common.errors import ReasoningFailure
from common.manifest_io import load_manifest
from common.puzzle_io import load_puzzle
from common.regions import referenced_cells
from common.types import (
    Clue,
    ClueType,
    CompareOp,
    Parity,
    PublicState,
    Region,
    RegionKind,
    Status,
    VerdictResult,
    status_to_bool,
)
from gui.clue_formatter import format_clue
from gui.controller import GUIController
from gui.theme import NEWSPRINT_BRASS, WARM_NOIR_GOLD, compute_board_metrics
from gui.web_server import WebGUIApp
from logic.encoder import CNFEncoder
from logic.entailment import EntailmentChecker, Uniqueness
from logic.evaluator import SemanticEvaluator


PUZZLES_DIR = Path(__file__).resolve().parent.parent / "puzzles"
EXAMPLES_DIR = PUZZLES_DIR / "examples"


def test_e01_controller_load_restart() -> None:
    """E-01: GUIController tải và làm mới màn chơi qua PublicState mà không làm lộ solution."""
    ctrl = GUIController()
    state0 = ctrl.load_puzzle(EXAMPLES_DIR / "3x3_classic.json")
    assert isinstance(state0, PublicState)
    assert not hasattr(state0, "solution")
    assert state0.n == 3
    assert set(state0.known_statuses.keys()) == {"A1", "C3"}
    assert set(state0.revealed_clues.keys()) == {"A1", "C3"}
    assert state0.token.revision == 0

    outcome = ctrl.submit_verdict("B1", Status.CRIMINAL)
    assert outcome.result is VerdictResult.ACCEPTED
    state1 = ctrl.get_public_state()
    assert state1.token.revision == 1
    assert "B1" in state1.known_statuses

    state2 = ctrl.restart()
    assert state2.token.revision == 0
    assert state2.token.session_id != state0.token.session_id
    assert set(state2.known_statuses.keys()) == {"A1", "C3"}


def test_e02_clue_highlighting_and_overlap() -> None:
    """E-02: Chọn lời khai trả về đúng vùng ô tham chiếu và phân tách Trái/Phải/Giao nhau của COMPARE."""
    ctrl = GUIController()
    ctrl.load_puzzle(EXAMPLES_DIR / "3x3_classic.json")

    refs_a1 = ctrl.select_clue("A1")
    assert refs_a1 == ("A1", "B1")
    assert ctrl.highlighted_cells == ("A1", "B1")

    assert ctrl.select_clue("B1") == ()
    assert ctrl.highlighted_cells == ()

    ctrl.load_puzzle(EXAMPLES_DIR / "3x3_extensions.json")
    ctrl.submit_verdict("C1", Status.INNOCENT)
    refs_c1 = ctrl.select_clue("C1")
    assert refs_c1 == ("A1", "B1", "C1", "A2", "A3")
    breakdown = ctrl.get_clue_region_breakdown()
    assert breakdown["overlap"] == ("A1",)
    assert breakdown["left"] == ("B1", "C1")
    assert breakdown["right"] == ("A2", "A3")


def test_e03_manual_verdict_outcomes() -> None:
    """E-03: Phân biệt rõ NOT_PROVABLE, CONTRADICTED và ACCEPTED mà không đổi trạng thái khi bị từ chối."""
    ctrl = GUIController()
    state0 = ctrl.load_puzzle(EXAMPLES_DIR / "3x3_classic.json")

    out_np = ctrl.submit_verdict("B2", Status.CRIMINAL)
    assert out_np.result is VerdictResult.NOT_PROVABLE
    assert ctrl.get_public_state().token == state0.token

    out_contra = ctrl.submit_verdict("B1", Status.INNOCENT)
    assert out_contra.result is VerdictResult.CONTRADICTED
    assert ctrl.get_public_state().token == state0.token

    out_ok = ctrl.submit_verdict("B1", Status.CRIMINAL)
    assert out_ok.result is VerdictResult.ACCEPTED
    assert out_ok.new_clue is not None and out_ok.new_clue.id == "c_B1"
    assert ctrl.get_public_state().token.revision == 1


def test_e04_hint_and_autosolve_isolation() -> None:
    """E-04: Gợi ý tìm đúng ô bị ép buộc mà không tự lật thẻ; Tự động phá án giải trọn vẹn."""
    raw_puzzle = load_puzzle(EXAMPLES_DIR / "3x3_classic.json")
    stripped_puzzle = replace(raw_puzzle, solution=None)

    ctrl = GUIController()
    state_before = ctrl.load_puzzle(stripped_puzzle)
    hint = ctrl.get_hint()
    assert hint is not None
    assert hint.cell == "B1"
    assert hint.verdict is Status.CRIMINAL
    assert ctrl.get_public_state().token == state_before.token
    assert "B1" not in ctrl.get_public_state().known_statuses

    outcomes = ctrl.auto_solve_all()
    assert len(outcomes) == 7
    assert ctrl.is_complete()

    ctrl.load_puzzle(EXAMPLES_DIR / "3x3_stuck.json")
    stuck_outcomes = ctrl.auto_solve_all()
    assert [o.cell for o in stuck_outcomes] == ["B1"]
    assert not ctrl.is_complete()
    assert ctrl.get_hint() is None


def test_e05_clue_formatter_and_layout_metrics() -> None:
    """E-05: Trình dịch lời khai Tiếng Việt hỗ trợ đủ 8 mẫu ClueType và bố cục bàn cờ cân đối."""
    ctrl = GUIController()
    state = ctrl.load_puzzle(EXAMPLES_DIR / "3x3_classic.json")

    sample_clues = [
        Clue("f1", ClueType.FACT, cells=("A1",), status=Status.INNOCENT),
        Clue("s1", ClueType.SAME, cells=("A1", "B1")),
        Clue("d1", ClueType.DIFFERENT, cells=("A1", "B1")),
        Clue("e0", ClueType.EXACTLY, region=Region(RegionKind.ROW, 1), k=0),
        Clue("e2", ClueType.EXACTLY, region=Region(RegionKind.COL, "B"), k=2),
        Clue("al", ClueType.AT_LEAST, region=Region(RegionKind.NEIGHBORS, "B2"), k=1),
        Clue("am", ClueType.AT_MOST, region=Region(RegionKind.EXPLICIT, ("A1", "C3")), k=1),
        Clue("p1", ClueType.PARITY, region=Region(RegionKind.ROW, 2), parity=Parity.EVEN),
        Clue(
            "c1",
            ClueType.COMPARE,
            left=Region(RegionKind.ROW, 1),
            right=Region(RegionKind.COL, "A"),
            op=CompareOp.GT,
        ),
    ]
    for clue in sample_clues:
        text = format_clue(clue, state)
        assert isinstance(text, str) and len(text) > 10
        assert text.endswith(".")
        assert len(referenced_cells(clue, 3)) >= 1

    assert WARM_NOIR_GOLD.is_dark and not NEWSPRINT_BRASS.is_dark
    for n in (3, 4, 5):
        m = compute_board_metrics(n, 900, 760)
        x1_first, _, _, _ = m.card_bbox(0, 0)
        _, _, x2_last, _ = m.card_bbox(0, n - 1)
        left_margin = x1_first - m.header_row_width
        right_margin = 900 - x2_last
        assert abs(left_margin - right_margin) <= 1


def test_e06_puzzle_suite_and_manifest_verification() -> None:
    """E-06: Toàn bộ 9 màn chơi trong puzzles/index.json khớp tính duy nhất nghiệm và thứ tự suy diễn."""
    manifest = load_manifest(PUZZLES_DIR / "index.json")
    cases = manifest["cases"]
    assert len(cases) >= 8

    for case in cases:
        rel_path = case["path"]
        expected = case["expected"]
        puzzle_path = PUZZLES_DIR / rel_path
        puzzle = load_puzzle(puzzle_path)

        if puzzle.solution is not None:
            ev = SemanticEvaluator(puzzle.n)
            bool_map = {c: status_to_bool(s) for c, s in puzzle.solution.items()}
            for cell, clue in puzzle.clues.items():
                assert ev.evaluate(clue, bool_map), f"{case['case_id']}: clue {clue.id} false under solution"

        enc = CNFEncoder(puzzle.n)
        full_kb = enc.build_kb(tuple(puzzle.clues.values()), {})
        u_rep = EntailmentChecker(full_kb).check_uniqueness()
        actual_uniq = "UNSAT" if u_rep.status is Uniqueness.NONE else u_rep.status.value
        assert actual_uniq == expected["full_clue_uniqueness"], case["case_id"]

        ctrl = GUIController()
        ctrl.load_puzzle(puzzle_path)
        if expected["run"] == "INCONSISTENT":
            with pytest.raises(ReasoningFailure):
                ctrl.auto_solve_all()
        else:
            outcomes = ctrl.auto_solve_all()
            actual_order = [o.cell for o in outcomes]
            actual_run = "SOLVED" if ctrl.is_complete() else "STUCK"
            assert actual_run == expected["run"], case["case_id"]
            if expected["accepted_order"] is not None:
                assert actual_order == expected["accepted_order"], case["case_id"]


def test_e07_web_gui_vietnamese_screens_and_api() -> None:
    """E-07: Giao diện Web Tiếng Việt có đủ 3 màn hình (Bắt đầu, Kho Hồ Sơ, Bàn cờ 3D) và các endpoint API."""
    from gui.web_server import INDEX_HTML

    assert 'id="screenStart"' in INDEX_HTML
    assert 'id="screenCases"' in INDEX_HTML
    assert 'id="screenGame"' in INDEX_HTML
    assert 'id="aiDrawer"' in INDEX_HTML
    assert "BẮT ĐẦU ĐIỀU TRA NGAY" in INDEX_HTML
    assert "KHO LƯU TRỮ HỒ SƠ VỤ ÁN" in INDEX_HTML

    web = WebGUIApp(initial_puzzle=EXAMPLES_DIR / "3x3_classic.json")
    s0 = web.handle_api("/api/state", {})
    assert s0["puzzle_id"] == "3x3_classic"
    assert s0["case_title"] == "Đêm Gala Thượng Lưu"
    assert len(s0["puzzles"]) >= 9

    s1 = web.handle_api("/api/select_clue", {"cell": "A1"})
    assert s1["selected_inspector"]["cell"] == "A1"
    b1_item = next(c for c in s1["cells"] if c["cell"] == "B1")
    assert b1_item["highlight_role"] == "REF"

    s2 = web.handle_api("/api/hint", {})
    assert s2["banner_kind"] == "HINT"
    b1_hinted = next(c for c in s2["cells"] if c["cell"] == "B1")
    assert b1_hinted["is_hinted"] is True
    assert b1_hinted["revealed"] is False

    s3 = web.handle_api("/api/step", {})
    assert s3["last_outcome"]["cell"] == "B1"
    assert s3["last_outcome"]["result"] == "ACCEPTED"
