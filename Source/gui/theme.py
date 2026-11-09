"""Hệ thống bảng màu và hàm tính toán bố cục bàn cờ cân đối (Module E)."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk


@dataclass(frozen=True)
class ThemePalette:
    """Bảng màu ngữ nghĩa cho chế độ Đêm Trinh Thám (Dark) và Hồ Sơ Cổ Điển (Light)."""

    id: str
    name: str
    is_dark: bool

    bg_canvas: str
    bg_surface: str
    bg_elevated: str
    border_hairline: str

    ink_primary: str
    ink_secondary: str
    ink_muted: str

    card_unsolved_bg: str
    card_unsolved_hover: str
    card_unsolved_border: str
    card_revealed_bg: str
    card_revealed_ink: str
    card_revealed_subink: str

    status_innocent: str
    status_innocent_bg: str
    status_criminal: str
    status_criminal_bg: str
    status_warning: str
    status_warning_bg: str

    accent_primary: str
    accent_hover: str
    highlight_ref: str
    highlight_left: str
    highlight_right: str
    highlight_overlap: str


WARM_NOIR_GOLD = ThemePalette(
    id="warm-noir-gold",
    name="Đêm Trinh Thám (Dark Mystery)",
    is_dark=True,
    bg_canvas="#0B0D13",
    bg_surface="#131722",
    bg_elevated="#1B2030",
    border_hairline="#283046",
    ink_primary="#F8FAFC",
    ink_secondary="#CBD5E1",
    ink_muted="#94A3B8",
    card_unsolved_bg="#181D2B",
    card_unsolved_hover="#20273A",
    card_unsolved_border="#2E374F",
    card_revealed_bg="#FCF9F2",
    card_revealed_ink="#1E293B",
    card_revealed_subink="#475569",
    status_innocent="#059669",
    status_innocent_bg="#D1FAE5",
    status_criminal="#E11D48",
    status_criminal_bg="#FFE4E6",
    status_warning="#D97706",
    status_warning_bg="#FEF3C7",
    accent_primary="#F59E0B",
    accent_hover="#FBBF24",
    highlight_ref="#FBBF24",
    highlight_left="#F59E0B",
    highlight_right="#38BDF8",
    highlight_overlap="#C084FC",
)

NEWSPRINT_BRASS = ThemePalette(
    id="newsprint-brass",
    name="Hồ Sơ Cổ Điển (Warm Light)",
    is_dark=False,
    bg_canvas="#F4EFE6",
    bg_surface="#FFFDF9",
    bg_elevated="#EFE7DA",
    border_hairline="#D6C9B5",
    ink_primary="#1E293B",
    ink_secondary="#334155",
    ink_muted="#64748B",
    card_unsolved_bg="#E8DFD1",
    card_unsolved_hover="#DFD3C0",
    card_unsolved_border="#C8B9A2",
    card_revealed_bg="#FFFFFF",
    card_revealed_ink="#0F172A",
    card_revealed_subink="#475569",
    status_innocent="#059669",
    status_innocent_bg="#D1FAE5",
    status_criminal="#E11D48",
    status_criminal_bg="#FFE4E6",
    status_warning="#B45309",
    status_warning_bg="#FEF3C7",
    accent_primary="#B45309",
    accent_hover="#D97706",
    highlight_ref="#D97706",
    highlight_left="#B45309",
    highlight_right="#0284C7",
    highlight_overlap="#7C3AED",
)

THEMES: dict[str, ThemePalette] = {
    WARM_NOIR_GOLD.id: WARM_NOIR_GOLD,
    NEWSPRINT_BRASS.id: NEWSPRINT_BRASS,
}


@dataclass(frozen=True)
class BoardLayoutMetrics:
    """Thông số hình học lưới N x N đảm bảo lề trái/phải cân bằng tuyệt đối."""

    n: int
    canvas_width: int
    canvas_height: int
    header_col_height: int
    header_row_width: int
    origin_x: int
    origin_y: int
    card_width: int
    card_height: int
    gap: int
    corner_radius: int

    def card_bbox(self, row_idx: int, col_idx: int) -> tuple[int, int, int, int]:
        x1 = self.origin_x + col_idx * (self.card_width + self.gap)
        y1 = self.origin_y + row_idx * (self.card_height + self.gap)
        return x1, y1, x1 + self.card_width, y1 + self.card_height


def compute_board_metrics(n: int, canvas_w: int, canvas_h: int) -> BoardLayoutMetrics:
    """Tính toán kích thước thẻ N x N cân đối cho 3x3, 4x4, 5x5."""
    w = max(canvas_w, 420)
    h = max(canvas_h, 420)

    gap = 14 if n == 3 else (11 if n == 4 else 8)
    radius = 12 if n <= 4 else 9
    header_col_h = 28
    header_row_w = 28
    pad_outer = 16

    avail_w = max(240, w - header_row_w - 2 * pad_outer)
    avail_h = max(240, h - header_col_h - 2 * pad_outer)

    raw_cw = (avail_w - (n - 1) * gap) // n
    raw_ch = (avail_h - (n - 1) * gap) // n

    card_w = min(raw_cw, int(raw_ch * 1.18))
    card_h = min(raw_ch, int(card_w * 1.12))
    card_w = max(card_w, 72)
    card_h = max(card_h, 76)

    total_grid_w = n * card_w + (n - 1) * gap
    total_grid_h = n * card_h + (n - 1) * gap

    origin_x = header_row_w + max(pad_outer, (w - header_row_w - total_grid_w) // 2)
    origin_y = header_col_h + max(pad_outer, (h - header_col_h - total_grid_h) // 2)

    return BoardLayoutMetrics(
        n=n,
        canvas_width=w,
        canvas_height=h,
        header_col_height=header_col_h,
        header_row_width=header_row_w,
        origin_x=origin_x,
        origin_y=origin_y,
        card_width=card_w,
        card_height=card_h,
        gap=gap,
        corner_radius=radius,
    )


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float = 10,
    **kwargs: object,
) -> int:
    r = max(0.0, min(radius, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)
