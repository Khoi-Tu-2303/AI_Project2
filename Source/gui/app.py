"""Lớp GriductiveApp tương thích kiểm thử và kết nối với GUIController (Module E)."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from common.errors import ReasoningFailure
from common.regions import all_cells
from common.types import Status, VerdictResult
from gui.clue_formatter import format_clue
from gui.controller import GUIController
from gui.theme import (
    NEWSPRINT_BRASS,
    WARM_NOIR_GOLD,
    ThemePalette,
    compute_board_metrics,
    draw_rounded_rect,
)


class GriductiveApp:
    """Ứng dụng giao diện Desktop đồng bộ với GUIController cho các bài test tự động."""

    def __init__(
        self,
        root: tk.Tk | None = None,
        controller: GUIController | None = None,
        initial_puzzle: str | Path | None = None,
    ) -> None:
        self._owns_root = root is None
        self.root: tk.Tk = root if root is not None else tk.Tk()
        self.root.title("Hồ Sơ Logic: Griductive — Phá Án Không Đoán Mò")
        self.root.geometry("1280x820")

        self.controller: GUIController = controller if controller is not None else GUIController()
        self.theme: ThemePalette = WARM_NOIR_GOLD
        self.reduced_motion: bool = False

        self._main = ttk.Frame(self.root)
        self._main.pack(fill=tk.BOTH, expand=True)
        self._board_canvas = tk.Canvas(self._main, width=900, height=760, highlightthickness=0)
        self._board_canvas.pack(fill=tk.BOTH, expand=True)

        puzzles = self.controller.discover_puzzles()
        target = initial_puzzle
        if target is None and puzzles:
            target = puzzles[0].path
        if target is not None:
            self.load_puzzle_path(target)

    def load_puzzle_path(self, path: str | Path) -> None:
        self.controller.load_puzzle(path)
        self.redraw_board()

    def on_restart(self) -> None:
        self.controller.restart()
        self.redraw_board()

    def on_toggle_theme(self) -> None:
        self.theme = NEWSPRINT_BRASS if self.theme.is_dark else WARM_NOIR_GOLD
        self.redraw_board()

    def on_toggle_motion(self) -> None:
        self.reduced_motion = not self.reduced_motion

    def on_hint(self) -> None:
        self.controller.get_hint()
        self.redraw_board()

    def on_step(self) -> bool:
        try:
            out = self.controller.step_auto_solve()
        except ReasoningFailure:
            return False
        self.redraw_board()
        return out is not None and out.result is VerdictResult.ACCEPTED

    def redraw_board(self) -> None:
        self._board_canvas.delete("all")
        if not self.controller.is_loaded:
            return
        state = self.controller.get_public_state()
        w = max(self._board_canvas.winfo_width(), 900)
        h = max(self._board_canvas.winfo_height(), 760)
        m = compute_board_metrics(state.n, w, h)
        t = self.theme
        char_by_cell = {c.cell: c for c in state.characters}
        cells = all_cells(state.n)

        for idx, cell in enumerate(cells):
            r = idx // state.n
            c = idx % state.n
            x1, y1, x2, y2 = m.card_bbox(r, c)
            ch = char_by_cell[cell]
            is_rev = cell in state.known_statuses
            bg = t.card_revealed_bg if is_rev else t.card_unsolved_bg
            outline = t.status_innocent if (is_rev and state.known_statuses[cell] is Status.INNOCENT) else (
                t.status_criminal if is_rev else t.card_unsolved_border
            )
            draw_rounded_rect(self._board_canvas, x1, y1, x2, y2, radius=m.corner_radius, fill=bg, outline=outline, width=2)
            self._board_canvas.create_text(x1 + 12, y1 + 14, text=f"{cell} · {ch.name}", anchor="w", fill=t.ink_primary)
            if is_rev and cell in state.revealed_clues:
                txt = format_clue(state.revealed_clues[cell], state, compact=True)
                self._board_canvas.create_text(x1 + 12, y2 - 18, text=txt, anchor="w", width=(x2 - x1 - 24), fill=t.card_revealed_ink)

    def run(self) -> None:
        self.root.mainloop()

    def destroy(self) -> None:
        if self._owns_root:
            self.root.destroy()
