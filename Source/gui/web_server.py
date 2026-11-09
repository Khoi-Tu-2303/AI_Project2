"""Máy chủ Web Giao diện Tiếng Việt cho Hồ Sơ Logic: Griductive (Module E).

Phục vụ các file giao diện tĩnh tách rời trong ``Source/gui/web/``:
- ``index.html`` (Cấu trúc 3 màn hình & 2 hộp thoại Tiếng Việt)
- ``styles.css`` (Bảng định kiểu Dark Mystery Glass & Gold / Hồ Sơ Cổ Điển)
- ``app.js`` (Logic tương tác bàn cờ 3D, chọn màn, khoanh vùng lời khai, ngăn kéo AI)
"""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
from typing import Any
from urllib.parse import urlparse
import webbrowser

from common.errors import GriductiveError, ReasoningFailure
from common.puzzle_io import puzzle_from_dict
from common.regions import all_cells
from common.types import Status
from gui.clue_formatter import format_clue, format_clue_formula
from gui.controller import CASE_METADATA_VN, GUIController

WEB_ASSETS_DIR = Path(__file__).resolve().parent / "web"
INDEX_HTML = (WEB_ASSETS_DIR / "index.html").read_text(encoding="utf-8")


def serialize_state_payload(
    controller: GUIController,
    *,
    banner_kind: str = "READY",
    banner_message: str = "",
    last_outcome: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Đóng gói toàn bộ trạng thái PublicState, lời khai Tiếng Việt, Telemetry và Trace cho Web UI."""
    state = controller.get_public_state()
    char_by_cell = {c.cell: c for c in state.characters}
    breakdown = controller.get_clue_region_breakdown()
    hint = controller.active_hint

    reveal_map = controller.reveal_step_by_cell
    cells_payload: list[dict[str, Any]] = []
    for cell in all_cells(state.n):
        ch = char_by_cell[cell]
        is_revealed = cell in state.known_statuses
        status_str = state.known_statuses[cell].value if is_revealed else None
        clue = state.revealed_clues.get(cell)
        clue_dict = None
        if clue is not None:
            f_info = format_clue_formula(clue, state.n)
            clue_dict = {
                "id": clue.id,
                "type": clue.type.value,
                "text": format_clue(clue, state, compact=False),
                "short_text": format_clue(clue, state, compact=(state.n == 5)),
                "math_formula": f_info["math_formula"],
                "cnf_preview": f_info["cnf_preview"],
                "clause_count": f_info["clause_count"],
            }

        hl_role = None
        if cell in breakdown.get("overlap", ()):
            hl_role = "L∩R"
        elif cell in breakdown.get("left", ()):
            hl_role = "LEFT"
        elif cell in breakdown.get("right", ()):
            hl_role = "RIGHT"
        elif cell in breakdown.get("primary", ()):
            hl_role = "REF"

        cells_payload.append({
            "cell": cell,
            "name": ch.name,
            "profession": ch.profession,
            "revealed": is_revealed,
            "status": status_str,
            "reveal_step": reveal_map.get(cell, 0) if is_revealed else None,
            "clue": clue_dict,
            "is_selected_clue": controller.selected_clue_cell == cell,
            "highlight_role": hl_role,
            "is_hinted": bool(hint is not None and hint.cell == cell),
        })

    revealed_list: list[dict[str, Any]] = []
    initial_clues: list[dict[str, Any]] = []
    for cell in all_cells(state.n):
        if cell in state.revealed_clues:
            clue = state.revealed_clues[cell]
            f_info = format_clue_formula(clue, state.n)
            r_step = reveal_map.get(cell, 0)
            entry = {
                "cell": cell,
                "owner": char_by_cell[cell].name,
                "profession": char_by_cell[cell].profession,
                "status": state.known_statuses[cell].value if cell in state.known_statuses else "INNOCENT",
                "reveal_step": r_step,
                "id": clue.id,
                "type": clue.type.value,
                "text": format_clue(clue, state, compact=False),
                "math_formula": f_info["math_formula"],
                "cnf_preview": f_info["cnf_preview"],
                "clause_count": f_info["clause_count"],
                "selected": controller.selected_clue_cell == cell,
            }
            revealed_list.append(entry)
            if r_step == 0:
                initial_clues.append(entry)

    sel_cell = controller.selected_clue_cell
    selected_inspector = None
    if sel_cell is not None and sel_cell in state.revealed_clues:
        cl = state.revealed_clues[sel_cell]
        selected_inspector = {
            "cell": sel_cell,
            "owner": char_by_cell[sel_cell].name,
            "profession": char_by_cell[sel_cell].profession,
            "id": cl.id,
            "type": cl.type.value,
            "text": format_clue(cl, state, compact=False),
            "referenced": list(controller.highlighted_cells),
            "left": list(breakdown.get("left", ())),
            "right": list(breakdown.get("right", ())),
            "overlap": list(breakdown.get("overlap", ())),
        }

    tel = controller.telemetry
    puzzles_list = [
        {
            "case_id": it.case_id,
            "label": it.label,
            "kind": it.kind,
            "code": it.code,
            "title": it.title,
            "subtitle": it.subtitle,
            "story": it.story,
            "difficulty": it.difficulty,
            "badge": it.badge,
            "n": it.n,
        }
        for it in controller.discover_puzzles()
    ]

    cur_meta = CASE_METADATA_VN.get(state.puzzle_id, {})

    return {
        "ok": True,
        "puzzle_id": state.puzzle_id,
        "case_code": cur_meta.get("code", "HỒ SƠ VỤ ÁN"),
        "case_title": cur_meta.get("title", state.puzzle_id),
        "case_subtitle": cur_meta.get("subtitle", f"Bàn cờ {state.n}×{state.n}"),
        "case_story": cur_meta.get("story", ""),
        "n": state.n,
        "session_id": state.token.session_id,
        "revision": state.token.revision,
        "revealed_count": len(state.known_statuses),
        "total_cells": state.n * state.n,
        "is_complete": controller.is_complete(),
        "banner_kind": banner_kind,
        "banner_message": banner_message,
        "last_outcome": last_outcome,
        "cells": cells_payload,
        "revealed_clues": revealed_list,
        "selected_inspector": selected_inspector,
        "hint": (
            {
                "cell": hint.cell,
                "verdict": hint.verdict.value,
                "clue_ids": list(hint.clue_ids),
            }
            if hint is not None
            else None
        ),
        "telemetry": {
            "num_primary": tel.num_primary,
            "num_aux": tel.num_aux,
            "num_clauses": tel.num_clauses,
            "sat_calls": tel.sat_calls,
            "decisions": tel.decisions,
            "propagations": tel.propagations,
            "backtracks": tel.backtracks,
            "deduction_steps": len(controller.deduction_steps),
            "runtime_ms": round(tel.runtime_ms, 2),
        },
        "initial_clues": initial_clues,
        "deduction_steps": list(controller.deduction_steps),
        "trace": [
            {
                "step_no": tr.step_no,
                "revision": tr.revision,
                "outcome": tr.outcome,
                "detail": tr.detail,
            }
            for tr in controller.trace[-40:]
        ],
        "puzzles": puzzles_list,
    }


class WebGUIApp:
    """Máy chủ HTTP cung cấp Giao diện Web Tiếng Việt từ thư mục Source/gui/web/."""

    def __init__(
        self,
        controller: GUIController | None = None,
        initial_puzzle: str | Path | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
    ) -> None:
        self.controller = controller if controller is not None else GUIController()
        self.host = host
        self.port = port
        self._lock = threading.Lock()
        self._banner_kind = "READY"
        self._banner_message = "Bấm vào thẻ hồ sơ sáng màu để khoanh vùng lời khai, hoặc kết luận Vô tội / Thủ phạm."

        puzzles = self.controller.discover_puzzles()
        self._case_map = {it.case_id: it.path for it in puzzles}

        target = initial_puzzle
        if target is None and puzzles:
            preferred = next(
                (it for it in puzzles if "classic" in it.case_id or "detective" in it.case_id),
                puzzles[0],
            )
            target = preferred.path
        if target is not None:
            st = self.controller.load_puzzle(target)
            meta = CASE_METADATA_VN.get(st.puzzle_id, {})
            title_vn = meta.get("title", st.puzzle_id)
            self._banner_message = (
                f"Đang điều tra vụ án \"{title_vn}\" ({st.n}×{st.n}). Bấm vào thẻ đã mở để xem vùng lời khai."
            )

    def handle_api(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            last_outcome: dict[str, Any] | None = None
            try:
                if path == "/api/state":
                    pass

                elif path == "/api/load":
                    case_id = body.get("case_id", "")
                    p_path = self._case_map.get(case_id)
                    if p_path is None:
                        raise GriductiveError(f"Không tìm thấy hồ sơ vụ án: {case_id!r}")
                    st = self.controller.load_puzzle(p_path)
                    meta = CASE_METADATA_VN.get(st.puzzle_id, {})
                    title_vn = meta.get("title", st.puzzle_id)
                    self._banner_kind = "READY"
                    self._banner_message = f"Đã mở hồ sơ \"{title_vn}\" ({st.n}×{st.n}). Hãy bắt đầu suy luận!"

                elif path == "/api/load_raw":
                    raw_dict = json.loads(body.get("content", "{}"))
                    puzzle = puzzle_from_dict(raw_dict)
                    st = self.controller.load_puzzle(puzzle)
                    self._banner_kind = "READY"
                    self._banner_message = f"Đã tải hồ sơ tùy chỉnh '{st.puzzle_id}' ({st.n}×{st.n})."

                elif path == "/api/restart":
                    st = self.controller.restart()
                    meta = CASE_METADATA_VN.get(st.puzzle_id, {})
                    title_vn = meta.get("title", st.puzzle_id)
                    self._banner_kind = "READY"
                    self._banner_message = f"Đã khởi động lại vụ án \"{title_vn}\"."

                elif path == "/api/select_clue":
                    cell = body.get("cell")
                    self.controller.select_clue(cell)

                elif path == "/api/verdict":
                    cell = str(body["cell"])
                    verdict = Status(str(body["verdict"]))
                    verdict_vn = "VÔ TỘI" if verdict is Status.INNOCENT else "THỦ PHẠM"
                    st_before = self.controller.get_public_state()
                    char_map = {c.cell: c.name for c in st_before.characters}
                    name = char_map.get(cell, cell)

                    out = self.controller.submit_verdict(cell, verdict)
                    last_outcome = {"cell": cell, "verdict": verdict.value, "result": out.result.value}
                    if out.result.value == "ACCEPTED":
                        if self.controller.is_complete():
                            self._banner_kind = "SOLVED"
                            self._banner_message = f"Phá án hoàn tất! {name} ({cell}) đã được xác nhận là {verdict_vn}."
                        else:
                            clue_txt = format_clue(out.new_clue, st_before) if out.new_clue else ""
                            self._banner_kind = "ACCEPTED"
                            self._banner_message = f"Chính xác! {name} ({cell}) là {verdict_vn}. Lời khai mới: “{clue_txt}”"
                    elif out.result.value == "NOT_PROVABLE":
                        self._banner_kind = "NOT_PROVABLE"
                        self._banner_message = (
                            f"Chưa đủ bằng chứng kết luận {name} ({cell}) là {verdict_vn}! Tuyệt đối không đoán mò."
                        )
                    else:
                        self._banner_kind = "CONTRADICTED"
                        self._banner_message = (
                            f"Sai lầm! Kết luận {name} ({cell}) là {verdict_vn} mâu thuẫn trực tiếp với lời khai hiện có!"
                        )

                elif path == "/api/hint":
                    st = self.controller.get_public_state()
                    if not st.unsolved:
                        self._banner_kind = "SOLVED"
                        self._banner_message = "Toàn bộ nghi phạm trong hồ sơ này đã được làm rõ."
                    else:
                        hint = self.controller.get_hint()
                        if hint is None:
                            self._banner_kind = "STUCK"
                            self._banner_message = (
                                "Không có nghi phạm nào bị ép buộc logic từ các lời khai hiện tại (Chưa đủ dữ kiện)."
                            )
                        else:
                            char_map = {c.cell: c.name for c in st.characters}
                            name = char_map.get(hint.cell, hint.cell)
                            self._banner_kind = "HINT"
                            self._banner_message = (
                                f"Gợi ý AI: Nghi phạm {name} ở ô {hint.cell} đã có thể suy luận chắc chắn từ các lời khai đang mở!"
                            )

                elif path == "/api/step":
                    st_before = self.controller.get_public_state()
                    if not st_before.unsolved:
                        self._banner_kind = "SOLVED"
                        self._banner_message = "Vụ án đã được giải quyết hoàn toàn."
                    else:
                        out = self.controller.step_auto_solve()
                        if out is None:
                            self._banner_kind = "STUCK"
                            self._banner_message = (
                                "Bộ giải AI tạm dừng: Không còn nghi phạm nào có thể suy diễn tất yếu (STUCK)."
                            )
                        else:
                            char_map = {c.cell: c.name for c in st_before.characters}
                            name = char_map.get(out.cell, out.cell)
                            verdict_vn = "VÔ TỘI" if out.verdict is Status.INNOCENT else "THỦ PHẠM"
                            last_outcome = {"cell": out.cell, "verdict": out.verdict.value, "result": out.result.value}
                            if self.controller.is_complete():
                                self._banner_kind = "SOLVED"
                                self._banner_message = (
                                    f"Phá án hoàn tất! AI xác nhận {name} ({out.cell}) là {verdict_vn}."
                                )
                            else:
                                clue_txt = format_clue(out.new_clue, st_before) if out.new_clue else ""
                                self._banner_kind = "ACCEPTED"
                                self._banner_message = (
                                    f"AI suy diễn: {name} ({out.cell}) chắc chắn là {verdict_vn}! Lời khai: “{clue_txt}”"
                                )

            except ReasoningFailure as rf:
                self._banner_kind = rf.status.value
                self._banner_message = f"Phát hiện mâu thuẫn logic ({rf.status.value}): {rf.message}"
            except Exception as exc:
                self._banner_kind = "ERROR"
                self._banner_message = f"Lỗi hệ thống: {exc}"

            return serialize_state_payload(
                self.controller,
                banner_kind=self._banner_kind,
                banner_message=self._banner_message,
                last_outcome=last_outcome,
            )

    def serve(self, *, open_browser: bool = True) -> None:
        app_ref = self
        static_routes = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/index.html": ("index.html", "text/html; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
            "/app.js": ("app.js", "application/javascript; charset=utf-8"),
        }

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                pass

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                route = static_routes.get(parsed.path)
                if route is not None:
                    filename, content_type = route
                    file_path = WEB_ASSETS_DIR / filename
                    if file_path.is_file():
                        data = file_path.read_bytes()
                        self.send_response(HTTPStatus.OK)
                        self.send_header("Content-Type", content_type)
                        self.send_header("Cache-Control", "no-cache")
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                        return
                self.send_error(HTTPStatus.NOT_FOUND)

            def do_POST(self) -> None:
                parsed = urlparse(self.path)
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                body = json.loads(raw) if raw.strip() else {}
                payload = app_ref.handle_api(parsed.path, body)
                out = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

        server = ThreadingHTTPServer((self.host, self.port), Handler)
        url = f"http://{self.host}:{self.port}"
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(f"Griductive Web UI (Tieng Viet) running at: {url}")
        if open_browser:
            threading.Timer(0.3, lambda: webbrowser.open(url)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
