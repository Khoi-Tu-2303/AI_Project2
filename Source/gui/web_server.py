"""Máy chủ Web Giao diện Tiếng Việt cho Hồ Sơ Logic: Griductive (Module E).

Cung cấp ứng dụng Web 3 màn hình (Màn hình Bắt đầu, Kho Hồ sơ Vụ án, Bàn cờ Điều tra 3D
kèm Ngăn kéo Phân tích AI CNF/DPLL và Hộp thoại Phá án) hoàn toàn bằng Tiếng Việt.
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
from gui.clue_formatter import format_clue
from gui.controller import CASE_METADATA_VN, GUIController


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

    cells_payload: list[dict[str, Any]] = []
    for cell in all_cells(state.n):
        ch = char_by_cell[cell]
        is_revealed = cell in state.known_statuses
        status_str = state.known_statuses[cell].value if is_revealed else None
        clue = state.revealed_clues.get(cell)
        clue_dict = None
        if clue is not None:
            clue_dict = {
                "id": clue.id,
                "type": clue.type.value,
                "text": format_clue(clue, state, compact=False),
                "short_text": format_clue(clue, state, compact=(state.n == 5)),
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
            "clue": clue_dict,
            "is_selected_clue": controller.selected_clue_cell == cell,
            "highlight_role": hl_role,
            "is_hinted": bool(hint is not None and hint.cell == cell),
        })

    revealed_list: list[dict[str, Any]] = []
    for cell in all_cells(state.n):
        if cell in state.revealed_clues:
            clue = state.revealed_clues[cell]
            revealed_list.append({
                "cell": cell,
                "owner": char_by_cell[cell].name,
                "profession": char_by_cell[cell].profession,
                "id": clue.id,
                "type": clue.type.value,
                "text": format_clue(clue, state, compact=False),
                "selected": controller.selected_clue_cell == cell,
            })

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
            "runtime_ms": round(tel.runtime_ms, 2),
        },
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


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="vi" data-theme="noir" data-motion="on">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Hồ Sơ Logic: Griductive — Phá Án Không Đoán Mò</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@500;600;700&family=Playfair+Display:ital,wght@0,700;0,800;1,600&display=swap" rel="stylesheet">
  <style>
    :root, [data-theme="noir"] {
      --bg-deep: #07090E;
      --bg-canvas: #0B0E17;
      --bg-surface: rgba(19, 24, 36, 0.86);
      --bg-elevated: #171D2B;
      --bg-glass: rgba(18, 23, 35, 0.78);
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-strong: rgba(245, 158, 11, 0.35);

      --ink-primary: #F8FAFC;
      --ink-secondary: #CBD5E1;
      --ink-muted: #94A3B8;

      --gold: #F59E0B;
      --gold-bright: #FBBF24;
      --gold-soft: rgba(245, 158, 11, 0.15);

      --innocent: #10B981;
      --innocent-dark: #047857;
      --innocent-soft: rgba(16, 185, 129, 0.16);
      --paper-innocent: #FAF7F0;
      --paper-innocent-border: #10B981;

      --criminal: #F43F5E;
      --criminal-dark: #BE123C;
      --criminal-soft: rgba(244, 63, 94, 0.16);
      --paper-criminal: #FFF5F5;
      --paper-criminal-border: #F43F5E;

      --card-front-bg: linear-gradient(160deg, #1A2133 0%, #111623 100%);
      --card-front-border: rgba(255, 255, 255, 0.11);
      --card-back-ink: #1E293B;
      --card-back-sub: #475569;

      --hl-ref: #FBBF24;
      --hl-right: #38BDF8;
      --hl-overlap: #C084FC;

      --shadow-card: 0 12px 28px -6px rgba(0, 0, 0, 0.55), 0 4px 10px -2px rgba(0, 0, 0, 0.35);
      --shadow-glow-gold: 0 0 28px rgba(245, 158, 11, 0.32);
    }

    [data-theme="paper"] {
      --bg-deep: #EAE2D3;
      --bg-canvas: #F3EDE2;
      --bg-surface: rgba(255, 252, 246, 0.92);
      --bg-elevated: #E8DFD1;
      --bg-glass: rgba(255, 251, 244, 0.88);
      --border-subtle: rgba(30, 41, 59, 0.12);
      --border-strong: rgba(180, 83, 9, 0.38);

      --ink-primary: #0F172A;
      --ink-secondary: #334155;
      --ink-muted: #64748B;

      --gold: #B45309;
      --gold-bright: #D97706;
      --gold-soft: rgba(180, 83, 9, 0.12);

      --innocent: #059669;
      --innocent-dark: #065F46;
      --innocent-soft: rgba(5, 150, 105, 0.12);
      --paper-innocent: #FFFFFF;
      --paper-innocent-border: #059669;

      --criminal: #E11D48;
      --criminal-dark: #9F1239;
      --criminal-soft: rgba(225, 29, 72, 0.12);
      --paper-criminal: #FFF8F8;
      --paper-criminal-border: #E11D48;

      --card-front-bg: linear-gradient(160deg, #EFE7DA 0%, #E2D7C5 100%);
      --card-front-border: rgba(30, 41, 59, 0.16);
      --card-back-ink: #0F172A;
      --card-back-sub: #475569;

      --hl-ref: #D97706;
      --hl-right: #0284C7;
      --hl-overlap: #7C3AED;

      --shadow-card: 0 10px 24px -6px rgba(45, 35, 20, 0.14), 0 4px 8px -2px rgba(45, 35, 20, 0.08);
      --shadow-glow-gold: 0 0 24px rgba(180, 83, 9, 0.25);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    html, body {
      width: 100%;
      height: 100%;
      font-family: 'Be Vietnam Pro', system-ui, -apple-system, sans-serif;
      background: var(--bg-canvas);
      color: var(--ink-primary);
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* Ambient Detective Background */
    .ambient-bg {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      background:
        radial-gradient(circle at 15% 18%, rgba(245, 158, 11, 0.11), transparent 40%),
        radial-gradient(circle at 85% 82%, rgba(16, 185, 129, 0.09), transparent 42%),
        radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.05), transparent 60%);
    }
    .ambient-grid {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      background-image:
        linear-gradient(to right, rgba(255,255,255,0.025) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255,255,255,0.025) 1px, transparent 1px);
      background-size: 44px 44px;
    }
    [data-theme="paper"] .ambient-grid {
      background-image:
        linear-gradient(to right, rgba(15,23,42,0.035) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(15,23,42,0.035) 1px, transparent 1px);
    }

    /* Screen Management */
    .screen {
      position: relative;
      z-index: 1;
      display: none;
      width: 100%;
      min-height: 100vh;
    }
    .screen.active {
      display: flex;
      flex-direction: column;
      animation: screenFadeIn 0.32s cubic-bezier(0.22, 1, 0.36, 1);
    }
    @keyframes screenFadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* =====================================================================
       SCREEN 1: MÀN HÌNH BẮT ĐẦU (START / HERO SCREEN)
       ===================================================================== */
    .start-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 36px 24px;
      max-width: 1120px;
      margin: 0 auto;
      text-align: center;
    }

    .start-top-controls {
      position: absolute;
      top: 22px;
      right: 28px;
      display: flex;
      gap: 10px;
    }

    .agency-badge {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 18px;
      border-radius: 999px;
      background: var(--gold-soft);
      border: 1px solid var(--border-strong);
      color: var(--gold-bright);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 22px;
      box-shadow: var(--shadow-glow-gold);
    }

    .hero-crest {
      width: 88px;
      height: 88px;
      margin-bottom: 18px;
      filter: drop-shadow(0 8px 24px rgba(245, 158, 11, 0.35));
    }

    .hero-title {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(2.6rem, 5.2vw, 4.4rem);
      font-weight: 800;
      line-height: 1.08;
      letter-spacing: -0.02em;
      margin-bottom: 10px;
      background: linear-gradient(135deg, var(--ink-primary) 20%, var(--gold-bright) 90%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
      font-family: 'Playfair Display', Georgia, serif;
      font-style: italic;
      font-size: clamp(1.25rem, 2.2vw, 1.75rem);
      color: var(--gold-bright);
      margin-bottom: 20px;
    }

    .hero-desc {
      max-width: 690px;
      font-size: 15.5px;
      line-height: 1.68;
      color: var(--ink-secondary);
      margin-bottom: 34px;
    }

    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      gap: 16px;
      margin-bottom: 48px;
    }

    .btn-hero-primary {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      padding: 16px 34px;
      border-radius: 14px;
      border: none;
      background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
      color: #090B10;
      font-family: inherit;
      font-size: 16px;
      font-weight: 800;
      letter-spacing: 0.02em;
      cursor: pointer;
      box-shadow: 0 12px 30px -4px rgba(245, 158, 11, 0.5);
      transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
    }
    .btn-hero-primary:hover {
      transform: translateY(-2px);
      filter: brightness(1.06);
      box-shadow: 0 16px 36px -4px rgba(245, 158, 11, 0.65);
    }

    .btn-hero-secondary {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 15px 26px;
      border-radius: 14px;
      border: 1px solid var(--border-strong);
      background: var(--bg-glass);
      backdrop-filter: blur(12px);
      color: var(--ink-primary);
      font-family: inherit;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.18s ease;
    }
    .btn-hero-secondary:hover {
      transform: translateY(-2px);
      border-color: var(--gold-bright);
      background: var(--bg-elevated);
    }

    .hero-features {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 18px;
      width: 100%;
      max-width: 980px;
    }
    @media (max-width: 820px) {
      .hero-features { grid-template-columns: 1fr; }
    }
    .feature-card {
      text-align: left;
      padding: 20px 22px;
      border-radius: 16px;
      background: var(--bg-glass);
      border: 1px solid var(--border-subtle);
      backdrop-filter: blur(14px);
      box-shadow: var(--shadow-card);
    }
    .feature-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: var(--gold-soft);
      color: var(--gold-bright);
      margin-bottom: 12px;
    }
    .feature-title {
      font-size: 15px;
      font-weight: 700;
      margin-bottom: 6px;
      color: var(--ink-primary);
    }
    .feature-text {
      font-size: 13px;
      line-height: 1.55;
      color: var(--ink-muted);
    }

    /* =====================================================================
       SCREEN 2: KHO HỒ SƠ VỤ ÁN (LEVEL / CASE SELECTION SCREEN)
       ===================================================================== */
    .cases-wrapper {
      width: 100%;
      max-width: 1280px;
      margin: 0 auto;
      padding: 28px 28px 60px;
    }

    .cases-header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding-bottom: 22px;
      border-bottom: 1px solid var(--border-subtle);
      margin-bottom: 24px;
    }

    .cases-title-block h1 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 28px;
      font-weight: 800;
      color: var(--ink-primary);
    }
    .cases-title-block p {
      font-size: 13.5px;
      color: var(--ink-muted);
      margin-top: 4px;
    }

    .filter-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 24px;
    }
    .filter-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .filter-tab {
      padding: 8px 16px;
      border-radius: 999px;
      border: 1px solid var(--border-subtle);
      background: var(--bg-elevated);
      color: var(--ink-secondary);
      font-family: inherit;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .filter-tab:hover {
      border-color: var(--gold);
      color: var(--ink-primary);
    }
    .filter-tab.active {
      background: var(--gold);
      border-color: var(--gold);
      color: #090B10;
      font-weight: 700;
    }

    .cases-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 20px;
    }

    .dossier-card {
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 22px 24px;
      border-radius: 18px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      box-shadow: var(--shadow-card);
      transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
      cursor: pointer;
      overflow: hidden;
    }
    .dossier-card::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, var(--gold), transparent);
      opacity: 0.75;
    }
    .dossier-card:hover {
      transform: translateY(-4px);
      border-color: var(--gold);
      box-shadow: var(--shadow-card), var(--shadow-glow-gold);
    }

    .dossier-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 12px;
    }
    .dossier-code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 6px;
      background: var(--gold-soft);
      color: var(--gold-bright);
      border: 1px solid var(--border-strong);
    }
    .dossier-badges {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .solved-pill {
      font-size: 11px;
      font-weight: 700;
      padding: 3px 9px;
      border-radius: 999px;
      background: var(--innocent-soft);
      color: var(--innocent);
      border: 1px solid var(--innocent);
    }
    .stars {
      color: var(--gold-bright);
      font-size: 13px;
      letter-spacing: 1px;
    }

    .dossier-title {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 21px;
      font-weight: 800;
      color: var(--ink-primary);
      margin-bottom: 4px;
    }
    .dossier-sub {
      font-size: 12.5px;
      font-weight: 600;
      color: var(--gold-bright);
      margin-bottom: 10px;
    }
    .dossier-story {
      font-size: 13.2px;
      line-height: 1.58;
      color: var(--ink-secondary);
      margin-bottom: 18px;
    }
    .dossier-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 14px;
      border-top: 1px solid var(--border-subtle);
    }
    .dossier-tag {
      font-size: 12px;
      font-weight: 600;
      color: var(--ink-muted);
    }
    .dossier-cta {
      font-size: 13px;
      font-weight: 700;
      color: var(--gold-bright);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    /* =====================================================================
       SCREEN 3: MÀN HÌNH ĐIỀU TRA BÀN CỜ 3D (INVESTIGATION SCREEN)
       ===================================================================== */
    #screenGame.active {
      height: 100vh;
      overflow: hidden;
    }

    .game-topbar {
      height: 62px;
      padding: 0 20px;
      background: var(--bg-surface);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-shrink: 0;
      z-index: 20;
    }

    .topbar-left, .topbar-center, .topbar-right {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .case-header-pill {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 6px 12px;
      border-radius: 10px;
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
    }
    .case-header-code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      color: var(--gold-bright);
    }
    .case-header-title {
      font-size: 14px;
      font-weight: 700;
      color: var(--ink-primary);
    }

    .progress-widget {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 6px 12px;
      border-radius: 10px;
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
      font-size: 12.5px;
      font-weight: 600;
    }
    .progress-bar-track {
      width: 76px;
      height: 7px;
      border-radius: 999px;
      background: rgba(255,255,255,0.1);
      overflow: hidden;
    }
    [data-theme="paper"] .progress-bar-track {
      background: rgba(15,23,42,0.12);
    }
    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--gold), var(--innocent));
      border-radius: 999px;
      transition: width 0.35s ease;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 8px 13px;
      border-radius: 10px;
      border: 1px solid var(--border-subtle);
      background: var(--bg-elevated);
      color: var(--ink-primary);
      font-family: inherit;
      font-size: 12.8px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .btn:hover {
      border-color: var(--gold);
      transform: translateY(-1px);
    }
    .btn-gold {
      background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
      border-color: #F59E0B;
      color: #090B10;
      font-weight: 700;
    }
    .btn-gold:hover {
      filter: brightness(1.07);
      border-color: #FBBF24;
    }
    .btn-ai-drawer {
      position: relative;
      border-color: var(--border-strong);
      background: var(--gold-soft);
      color: var(--gold-bright);
    }
    .badge-count {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 999px;
      background: rgba(0,0,0,0.35);
      color: var(--ink-primary);
    }
    .ctrl-select {
      padding: 7px 10px;
      border-radius: 10px;
      border: 1px solid var(--border-subtle);
      background: var(--bg-elevated);
      color: var(--ink-primary);
      font-family: inherit;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
    }

    /* Clue Spotlight & Feedback Ribbon */
    .spotlight-bar {
      width: 100%;
      max-width: 1160px;
      margin: 10px auto 4px;
      padding: 0 20px;
      flex-shrink: 0;
    }
    .spotlight-inner {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 16px;
      border-radius: 14px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      box-shadow: var(--shadow-card);
      transition: border-color 0.2s ease;
    }
    .spotlight-inner[data-kind="ACCEPTED"],
    .spotlight-inner[data-kind="SOLVED"] {
      border-color: var(--innocent);
    }
    .spotlight-inner[data-kind="NOT_PROVABLE"],
    .spotlight-inner[data-kind="STUCK"],
    .spotlight-inner[data-kind="HINT"] {
      border-color: var(--gold-bright);
    }
    .spotlight-inner[data-kind="CONTRADICTED"],
    .spotlight-inner[data-kind="INCONSISTENT"],
    .spotlight-inner[data-kind="ERROR"] {
      border-color: var(--criminal);
    }

    .status-msg-group {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 260px;
      flex: 1;
    }
    .status-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 7px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      flex-shrink: 0;
      background: var(--gold-soft);
      color: var(--gold-bright);
    }
    .status-badge[data-kind="ACCEPTED"],
    .status-badge[data-kind="SOLVED"] {
      background: var(--innocent-soft);
      color: var(--innocent);
    }
    .status-badge[data-kind="CONTRADICTED"],
    .status-badge[data-kind="INCONSISTENT"],
    .status-badge[data-kind="ERROR"] {
      background: var(--criminal-soft);
      color: var(--criminal);
    }

    .status-text {
      font-size: 13.5px;
      font-weight: 600;
      color: var(--ink-primary);
    }

    .active-clue-pill {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 6px 12px;
      border-radius: 10px;
      background: var(--bg-elevated);
      border: 1px solid var(--border-strong);
      font-size: 12.5px;
    }
    .active-clue-owner {
      font-weight: 700;
      color: var(--gold-bright);
    }
    .active-clue-refs {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px;
      color: var(--ink-secondary);
    }
    .btn-clear-hl {
      border: none;
      background: rgba(255,255,255,0.08);
      color: var(--ink-secondary);
      border-radius: 6px;
      padding: 2px 7px;
      font-size: 11px;
      cursor: pointer;
    }
    .btn-clear-hl:hover { color: var(--ink-primary); background: rgba(255,255,255,0.16); }

    /* Main Board Stage */
    .board-stage {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 6px 24px 18px;
      min-height: 0;
      overflow: hidden;
    }

    .board-shell {
      display: flex;
      flex-direction: column;
      gap: 8px;
      width: 100%;
      height: 100%;
      max-height: calc(100vh - 150px);
    }
    .board-shell[data-n="3"] { max-width: 820px; }
    .board-shell[data-n="4"] { max-width: 980px; }
    .board-shell[data-n="5"] { max-width: 1120px; }

    .col-headers {
      display: grid;
      padding-left: 38px;
      gap: 12px;
      height: 24px;
      flex-shrink: 0;
    }
    .col-hdr {
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: var(--gold-bright);
      background: var(--gold-soft);
      border-radius: 6px;
      border: 1px solid var(--border-subtle);
    }

    .board-rows-wrap {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-height: 0;
    }
    .board-shell[data-n="4"] .board-rows-wrap,
    .board-shell[data-n="4"] .col-headers { gap: 10px; }
    .board-shell[data-n="5"] .board-rows-wrap,
    .board-shell[data-n="5"] .col-headers { gap: 8px; }

    .board-row {
      flex: 1;
      display: flex;
      gap: 10px;
      min-height: 0;
    }
    .row-hdr {
      width: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 700;
      color: var(--gold-bright);
      background: var(--gold-soft);
      border-radius: 6px;
      border: 1px solid var(--border-subtle);
      flex-shrink: 0;
    }
    .row-cards {
      flex: 1;
      display: grid;
      gap: 12px;
      min-height: 0;
    }
    .board-shell[data-n="4"] .row-cards { gap: 10px; }
    .board-shell[data-n="5"] .row-cards { gap: 8px; }

    /* =====================================================================
       3D SUSPECT CARDS (FRONT: UNSOLVED / BACK: REVEALED DOSSIER)
       ===================================================================== */
    .suspect-scene {
      position: relative;
      perspective: 1200px;
      min-height: 0;
      height: 100%;
    }

    .suspect-card {
      position: relative;
      width: 100%;
      height: 100%;
      border-radius: 14px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: var(--shadow-card);
      transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.22s ease, border-color 0.22s ease;
      overflow: hidden;
      user-select: none;
    }
    .board-shell[data-n="5"] .suspect-card {
      padding: 6px 8px;
      border-radius: 11px;
    }

    .suspect-card.unsolved {
      background: var(--card-front-bg);
      border: 1.5px solid var(--card-front-border);
      color: var(--ink-primary);
    }
    .suspect-card.unsolved:hover {
      transform: translateY(-2px);
      border-color: rgba(245, 158, 11, 0.45);
    }

    .suspect-card.revealed-innocent {
      background: var(--paper-innocent);
      border: 2px solid var(--paper-innocent-border);
      color: var(--card-back-ink);
      cursor: pointer;
    }
    .suspect-card.revealed-criminal {
      background: var(--paper-criminal);
      border: 2px solid var(--paper-criminal-border);
      color: var(--card-back-ink);
      cursor: pointer;
    }
    .suspect-card.revealed-innocent:hover,
    .suspect-card.revealed-criminal:hover {
      transform: translateY(-2px);
    }

    .suspect-card.selected-clue {
      box-shadow: 0 0 0 3px var(--gold-bright), var(--shadow-card);
    }
    .suspect-card.hinted {
      border-color: var(--gold-bright) !important;
      box-shadow: 0 0 0 2.5px var(--gold-bright), 0 0 24px rgba(251, 191, 36, 0.45);
      animation: pulseHint 1.6s infinite ease-in-out;
    }
    @keyframes pulseHint {
      0%, 100% { box-shadow: 0 0 0 2px var(--gold-bright), 0 0 16px rgba(251, 191, 36, 0.35); }
      50% { box-shadow: 0 0 0 4px var(--gold-bright), 0 0 28px rgba(251, 191, 36, 0.65); }
    }

    [data-motion="on"] .anim-flip {
      animation: flipReveal3D 0.48s cubic-bezier(0.22, 1, 0.36, 1);
    }
    @keyframes flipReveal3D {
      0% { transform: rotateY(90deg) scale(0.94); opacity: 0.4; }
      60% { transform: rotateY(-8deg) scale(1.02); opacity: 1; }
      100% { transform: rotateY(0deg) scale(1); }
    }

    [data-motion="on"] .anim-shake {
      animation: rejectShake 0.42s cubic-bezier(0.36, 0.07, 0.19, 0.97);
    }
    @keyframes rejectShake {
      10%, 90% { transform: translateX(-4px); }
      20%, 80% { transform: translateX(6px); }
      30%, 50%, 70% { transform: translateX(-7px); }
      40%, 60% { transform: translateX(7px); }
    }

    /* Card Header */
    .card-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      z-index: 2;
    }
    .coord-pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 6px;
      background: rgba(255,255,255,0.09);
      color: var(--ink-secondary);
    }
    .revealed-innocent .coord-pill,
    .revealed-criminal .coord-pill {
      background: rgba(15, 23, 42, 0.08);
      color: #334155;
    }
    .board-shell[data-n="5"] .coord-pill {
      font-size: 10px;
      padding: 1px 5px;
    }

    .stamp-badge {
      font-size: 10.5px;
      font-weight: 800;
      padding: 2.5px 8px;
      border-radius: 6px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .stamp-badge.innocent {
      background: #D1FAE5;
      color: #065F46;
      border: 1px solid #10B981;
    }
    .stamp-badge.criminal {
      background: #FFE4E6;
      color: #9F1239;
      border: 1px solid #F43F5E;
    }
    .stamp-badge.hint-pill {
      background: #FEF3C7;
      color: #92400E;
      border: 1px solid #F59E0B;
    }
    .stamp-badge.unsolved-pill {
      font-size: 10px;
      font-weight: 600;
      color: var(--ink-muted);
      opacity: 0.8;
    }
    .board-shell[data-n="5"] .stamp-badge {
      font-size: 9px;
      padding: 1.5px 5px;
    }

    /* Suspect Avatar & Identity */
    .identity-unsolved {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 3px;
      margin: auto 0;
      z-index: 2;
    }
    .avatar-wrap {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at 30% 30%, rgba(245, 158, 11, 0.18), rgba(255, 255, 255, 0.04));
      border: 1.5px solid rgba(255, 255, 255, 0.14);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    .board-shell[data-n="4"] .avatar-wrap { width: 40px; height: 40px; }
    .board-shell[data-n="5"] .avatar-wrap { width: 28px; height: 28px; }

    .identity-revealed {
      display: flex;
      align-items: center;
      gap: 9px;
      z-index: 2;
      margin: 2px 0;
    }
    .identity-revealed .avatar-wrap {
      width: 36px;
      height: 36px;
      flex-shrink: 0;
      background: rgba(15, 23, 42, 0.06);
      border-color: rgba(15, 23, 42, 0.15);
      box-shadow: none;
    }
    .board-shell[data-n="5"] .identity-revealed .avatar-wrap {
      width: 24px;
      height: 24px;
    }

    .char-name {
      font-size: 14.5px;
      font-weight: 800;
      line-height: 1.15;
    }
    .char-prof {
      font-size: 11.5px;
      font-weight: 500;
      opacity: 0.78;
    }
    .board-shell[data-n="4"] .char-name { font-size: 13px; }
    .board-shell[data-n="5"] .char-name { font-size: 11px; }
    .board-shell[data-n="5"] .char-prof { font-size: 9.5px; }

    /* Testimony Bubble on Revealed Card */
    .clue-bubble {
      position: relative;
      background: rgba(15, 23, 42, 0.055);
      border-left: 3px solid var(--gold);
      border-radius: 6px;
      padding: 6px 8px;
      font-size: 12px;
      font-weight: 600;
      line-height: 1.36;
      color: #0F172A;
      z-index: 2;
    }
    .revealed-innocent .clue-bubble { border-left-color: #059669; }
    .revealed-criminal .clue-bubble { border-left-color: #E11D48; }
    .board-shell[data-n="4"] .clue-bubble {
      font-size: 11px;
      padding: 5px 7px;
      line-height: 1.3;
    }
    .board-shell[data-n="5"] .clue-bubble {
      font-size: 9.6px;
      padding: 3px 5px;
      line-height: 1.22;
    }

    /* Verdict Buttons on Unsolved Card */
    .verdict-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      z-index: 2;
    }
    .btn-verdict {
      padding: 6px 4px;
      border-radius: 8px;
      font-family: inherit;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.14s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 3px;
    }
    .board-shell[data-n="5"] .btn-verdict {
      padding: 3.5px 2px;
      font-size: 9.2px;
      border-radius: 6px;
    }
    .btn-verdict.innocent {
      background: rgba(16, 185, 129, 0.13);
      border: 1px solid rgba(16, 185, 129, 0.45);
      color: #34D399;
    }
    [data-theme="paper"] .btn-verdict.innocent { color: #047857; }
    .btn-verdict.innocent:hover {
      background: #10B981;
      border-color: #10B981;
      color: #FFFFFF;
    }
    .btn-verdict.criminal {
      background: rgba(244, 63, 94, 0.13);
      border: 1px solid rgba(244, 63, 94, 0.45);
      color: #FB7185;
    }
    [data-theme="paper"] .btn-verdict.criminal { color: #BE123C; }
    .btn-verdict.criminal:hover {
      background: #F43F5E;
      border-color: #F43F5E;
      color: #FFFFFF;
    }

    /* Region Highlight Brackets Overlay */
    .region-overlay-svg {
      position: absolute;
      inset: 3px;
      width: calc(100% - 6px);
      height: calc(100% - 6px);
      pointer-events: none;
      z-index: 4;
    }
    .region-role-pill {
      position: absolute;
      bottom: 6px;
      right: 6px;
      z-index: 5;
      pointer-events: none;
      font-family: 'JetBrains Mono', monospace;
      font-size: 9.5px;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 5px;
      background: var(--hl-ref);
      color: #090B10;
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }
    .region-role-pill[data-role="RIGHT"] { background: var(--hl-right); }
    .region-role-pill[data-role="L∩R"] { background: var(--hl-overlap); color: #FFF; }

    /* =====================================================================
       SLIDE-OVER AI & CNF DRAWER (NGĂN KÉO PHÂN TÍCH AI)
       ===================================================================== */
    .drawer-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(5, 7, 12, 0.55);
      backdrop-filter: blur(4px);
      z-index: 50;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.25s ease;
    }
    .drawer-backdrop.open {
      opacity: 1;
      pointer-events: auto;
    }

    .ai-drawer {
      position: fixed;
      top: 0;
      right: 0;
      bottom: 0;
      width: 440px;
      max-width: 92vw;
      background: var(--bg-surface);
      backdrop-filter: blur(22px);
      border-left: 1px solid var(--border-strong);
      box-shadow: -16px 0 40px rgba(0, 0, 0, 0.6);
      z-index: 60;
      display: flex;
      flex-direction: column;
      transform: translateX(102%);
      transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
    }
    .ai-drawer.open {
      transform: translateX(0);
    }

    .drawer-header {
      padding: 18px 20px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .drawer-title {
      font-size: 16px;
      font-weight: 800;
      color: var(--gold-bright);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .drawer-body {
      flex: 1;
      overflow-y: auto;
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .drawer-section-title {
      font-size: 11.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--ink-muted);
      margin-bottom: 10px;
    }

    .telemetry-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .metric-box {
      padding: 10px 12px;
      border-radius: 10px;
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
      display: flex;
      align-items: baseline;
      justify-content: space-between;
    }
    .metric-lbl {
      font-size: 12px;
      color: var(--ink-secondary);
    }
    .metric-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 15px;
      font-weight: 700;
      color: var(--gold-bright);
    }

    .clue-drawer-list {
      display: flex;
      flex-direction: column;
      gap: 7px;
      max-height: 200px;
      overflow-y: auto;
    }
    .clue-drawer-item {
      padding: 8px 11px;
      border-radius: 9px;
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
      font-size: 12.2px;
      line-height: 1.45;
      cursor: pointer;
      transition: border-color 0.15s ease;
    }
    .clue-drawer-item:hover,
    .clue-drawer-item.active {
      border-color: var(--gold-bright);
    }
    .clue-drawer-tag {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      color: var(--gold-bright);
      margin-right: 6px;
    }

    .trace-box {
      flex: 1;
      min-height: 180px;
      padding: 12px;
      border-radius: 10px;
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px;
      line-height: 1.55;
      overflow-y: auto;
    }
    .trace-entry { margin-bottom: 7px; }
    .trace-tag { font-weight: 700; }
    .trace-tag.ACCEPTED { color: var(--innocent); }
    .trace-tag.NOT_PROVABLE, .trace-tag.STUCK, .trace-tag.FORCED { color: var(--gold-bright); }
    .trace-tag.CONTRADICTED { color: var(--criminal); }
    .trace-tag.INFO { color: var(--ink-muted); }

    /* =====================================================================
       MODALS (LUẬT CHƠI & PHÁ ÁN THÀNH CÔNG)
       ===================================================================== */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(5, 8, 15, 0.72);
      backdrop-filter: blur(8px);
      z-index: 80;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .modal-overlay.open {
      display: flex;
      animation: screenFadeIn 0.25s ease;
    }
    .modal-card {
      width: 100%;
      max-width: 620px;
      border-radius: 22px;
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.65), var(--shadow-glow-gold);
      padding: 28px 32px;
      max-height: 90vh;
      overflow-y: auto;
    }
    .modal-card h2 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 26px;
      font-weight: 800;
      color: var(--gold-bright);
      margin-bottom: 10px;
    }
    .modal-card p {
      font-size: 14px;
      line-height: 1.65;
      color: var(--ink-secondary);
      margin-bottom: 14px;
    }
    .rule-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin: 16px 0 24px;
    }
    .rule-list li {
      padding: 12px 14px;
      border-radius: 12px;
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
      font-size: 13.5px;
      line-height: 1.55;
    }
    .victory-stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin: 20px 0 24px;
    }
    .victory-stat-tile {
      text-align: center;
      padding: 14px 10px;
      border-radius: 14px;
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
    }
    .victory-stat-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 22px;
      font-weight: 800;
      color: var(--gold-bright);
    }
    .victory-stat-lbl {
      font-size: 12px;
      color: var(--ink-muted);
      margin-top: 4px;
    }
  </style>
</head>
<body>
  <div class="ambient-bg"></div>
  <div class="ambient-grid"></div>

  <!-- ===================================================================
       MÀN HÌNH 1: MÀN HÌNH BẮT ĐẦU (START SCREEN)
       =================================================================== -->
  <section id="screenStart" class="screen active">
    <div class="start-top-controls">
      <button type="button" class="btn" onclick="toggleTheme()">
        <span id="lblThemeStart">🌗 Giao diện: Đêm Trinh Thám</span>
      </button>
      <button type="button" class="btn" onclick="openModal('modalRules')">
        📖 Luật chơi &amp; AI
      </button>
    </div>

    <div class="start-container">
      <div class="agency-badge">
        <span>✦ CỤC ĐIỀU TRA LOGIC MỆNH ĐỀ · DPLL SAT SOLVER ✦</span>
      </div>

      <svg class="hero-crest" viewBox="0 0 96 96" fill="none">
        <polygon points="48,6 86,24 76,72 48,90 20,72 10,24" fill="rgba(245,158,11,0.12)" stroke="#F59E0B" stroke-width="2.5"/>
        <circle cx="48" cy="46" r="22" fill="rgba(16,185,129,0.12)" stroke="#FBBF24" stroke-width="2"/>
        <path d="M38 46 L45 53 L59 39" stroke="#10B981" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>

      <h1 class="hero-title">HỒ SƠ LOGIC: GRIDUCTIVE</h1>
      <div class="hero-subtitle">Phá Án Bằng Suy Luận Thuần Túy — Tuyệt Đối Không Đoán Mò</div>
      <p class="hero-desc">
        Chào mừng Thám tử đến với bàn cờ thẩm vấn nghi phạm. Mỗi nghi phạm đã lộ diện sẽ cung cấp một lời khai
        được mã hóa thành <strong>mệnh đề logic dạng chuẩn hội (CNF)</strong>. Nhiệm vụ của bạn là chỉ ra ai
        <strong>Vô tội</strong>, ai là <strong>Thủ phạm</strong> khi và chỉ khi phán quyết đó được chứng minh tất yếu!
      </p>

      <div class="hero-actions">
        <button type="button" class="btn-hero-primary" onclick="startImmediateInvestigation()">
          <span>▶ BẮT ĐẦU ĐIỀU TRA NGAY</span>
        </button>
        <button type="button" class="btn-hero-secondary" onclick="showScreen('screenCases')">
          <span>📂 KHO HỒ SƠ VỤ ÁN (9 MÀN)</span>
        </button>
        <button type="button" class="btn-hero-secondary" onclick="openModal('modalRules')">
          <span>📖 HƯỚNG DẪN &amp; CƠ CHẾ SAT</span>
        </button>
      </div>

      <div class="hero-features">
        <div class="feature-card">
          <div class="feature-icon">🔍</div>
          <div class="feature-title">Suy Diễn Logic Không Đoán Mò</div>
          <div class="feature-text">
            Hệ thống kiểm tra suy diễn bằng chứng minh phản chứng <code>KB ∧ ¬L = UNSAT</code>. Mọi phán quyết vội vàng đều bị cảnh báo ngay lập tức.
          </div>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🧩</div>
          <div class="feature-title">8 Mẫu Lời Khai &amp; Khoanh Vùng Trực Quan</div>
          <div class="feature-text">
            Bấm vào bất kỳ hồ sơ đã mở nào để chiếu sáng Hàng, Cột, Láng giềng xung quanh hoặc vùng đối chiếu Chẵn/Lẻ (PARITY, COMPARE).
          </div>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🧠</div>
          <div class="feature-title">Trợ Lý AI &amp; Phân Tích DPLL Trực Tiếp</div>
          <div class="feature-text">
            Tích hợp Gợi ý nước đi, Giải từng bước, Tự động phá án và Ngăn kéo theo dõi thông số Unit Propagation thời gian thực.
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ===================================================================
       MÀN HÌNH 2: KHO HỒ SƠ VỤ ÁN / CHỌN MÀN CHƠI (CASE SELECTION)
       =================================================================== -->
  <section id="screenCases" class="screen">
    <div class="cases-wrapper">
      <div class="cases-header">
        <div class="cases-title-block">
          <h1>📂 KHO LƯU TRỮ HỒ SƠ VỤ ÁN</h1>
          <p>Chọn một hồ sơ vụ án dưới đây để bắt đầu thẩm vấn hoặc tải lên file JSON tùy chỉnh</p>
        </div>
        <div style="display:flex; gap:10px; align-items:center;">
          <label class="btn" for="uploadJsonCases" style="cursor:pointer;">
            📤 Tải File JSON Từ Máy
          </label>
          <input id="uploadJsonCases" type="file" accept=".json" style="display:none" />
          <button type="button" class="btn" onclick="toggleTheme()">🌗 Đổi giao diện</button>
          <button type="button" class="btn btn-gold" onclick="showScreen('screenStart')">← Màn hình chính</button>
        </div>
      </div>

      <div class="filter-bar">
        <div class="filter-tabs" id="caseFilterTabs">
          <button type="button" class="filter-tab active" data-filter="all" onclick="setCaseFilter('all')">Tất cả hồ sơ (9)</button>
          <button type="button" class="filter-tab" data-filter="3" onclick="setCaseFilter('3')">Cấp độ 3×3</button>
          <button type="button" class="filter-tab" data-filter="4" onclick="setCaseFilter('4')">Cấp độ 4×4</button>
          <button type="button" class="filter-tab" data-filter="5" onclick="setCaseFilter('5')">Siêu cấp 5×5</button>
          <button type="button" class="filter-tab" data-filter="edge" onclick="setCaseFilter('edge')">Kiểm thử biên AI</button>
        </div>
      </div>

      <div class="cases-grid" id="casesGrid"></div>
    </div>
  </section>

  <!-- ===================================================================
       MÀN HÌNH 3: MÀN HÌNH ĐIỀU TRA BÀN CỜ 3D (GAMEPLAY SCREEN)
       =================================================================== -->
  <section id="screenGame" class="screen">
    <!-- Thanh công cụ phía trên -->
    <header class="game-topbar">
      <div class="topbar-left">
        <button type="button" class="btn" onclick="showScreen('screenCases')" title="Quay về Kho Hồ Sơ Vụ Án">
          ← Kho Hồ Sơ
        </button>
        <div class="case-header-pill">
          <span class="case-header-code" id="hdrCaseCode">HỒ SƠ #02</span>
          <span class="case-header-title" id="hdrCaseTitle">Đêm Gala Thượng Lưu</span>
        </div>
        <select id="quickPuzzleSelect" class="ctrl-select" aria-label="Đổi nhanh vụ án"></select>
        <div class="progress-widget">
          <span id="progressLabel">Đã xác minh: 2/9</span>
          <div class="progress-bar-track">
            <div class="progress-bar-fill" id="progressBarFill" style="width: 22%;"></div>
          </div>
        </div>
      </div>

      <div class="topbar-center">
        <button type="button" class="btn" id="btnHint" title="AI tìm 1 ô đã đủ chứng cứ suy diễn (không tự lật thẻ)">
          💡 Gợi ý
        </button>
        <button type="button" class="btn" id="btnStep" title="AI tự động lật 1 ô chắc chắn đúng">
          ⏭ Giải 1 bước
        </button>
        <button type="button" class="btn btn-gold" id="btnAuto" title="AI tự động phá án tuần tự">
          <span id="lblAuto">⚡ Tự động phá án</span>
        </button>
        <select id="speedSelect" class="ctrl-select" aria-label="Tốc độ giải tự động">
          <option value="220">Tốc độ: Nhanh</option>
          <option value="480" selected>Tốc độ: Vừa</option>
          <option value="850">Tốc độ: Chậm</option>
        </select>
        <button type="button" class="btn" id="btnRestart" title="Làm mới lại màn chơi này">
          ↺ Chơi lại
        </button>
      </div>

      <div class="topbar-right">
        <button type="button" class="btn btn-ai-drawer" onclick="toggleDrawer(true)">
          🧠 Phân tích AI <span class="badge-count" id="badgeClauseCount">0 CNF</span>
        </button>
        <button type="button" class="btn" onclick="openModal('modalRules')" title="Xem luật chơi">
          📖 Luật
        </button>
        <button type="button" class="btn" onclick="toggleTheme()" title="Đổi chế độ Sáng / Tối">
          🌗
        </button>
      </div>
    </header>

    <!-- Thanh Tiêu Điểm Lời Khai & Phản Hồi -->
    <div class="spotlight-bar">
      <div class="spotlight-inner" id="spotlightInner" data-kind="READY">
        <div class="status-msg-group">
          <span class="status-badge" id="statusBadge" data-kind="READY">ĐANG ĐIỀU TRA</span>
          <span class="status-text" id="statusText">Bấm vào thẻ đã mở để khoanh vùng lời khai, hoặc chọn Vô tội / Thủ phạm cho nghi phạm.</span>
        </div>
        <div class="active-clue-pill" id="activeCluePill" style="display:none;">
          <span class="active-clue-owner" id="activeClueOwner">An (A1):</span>
          <span class="active-clue-refs" id="activeClueRefs">Ô liên quan: A1, B1</span>
          <button type="button" class="btn-clear-hl" onclick="selectClue(null)">✕ Bỏ chọn</button>
        </div>
      </div>
    </div>

    <!-- Bàn Cờ Nghi Phạm 3D -->
    <main class="board-stage">
      <div class="board-shell" id="boardShell" data-n="3">
        <div class="col-headers" id="colHeaders"></div>
        <div class="board-rows-wrap" id="boardRowsWrap"></div>
      </div>
    </main>
  </section>

  <!-- ===================================================================
       NGĂN KÉO TRƯỢT PHÂN TÍCH AI (CNF & DPLL TELEMETRY DRAWER)
       =================================================================== -->
  <div class="drawer-backdrop" id="drawerBackdrop" onclick="toggleDrawer(false)"></div>
  <aside class="ai-drawer" id="aiDrawer">
    <div class="drawer-header">
      <div class="drawer-title">🧠 Bảng Phân Tích Logic CNF &amp; DPLL SAT</div>
      <button type="button" class="btn" onclick="toggleDrawer(false)">✕ Đóng</button>
    </div>
    <div class="drawer-body">
      <div>
        <div class="drawer-section-title">Thông số Cơ sở Tri thức CNF &amp; Bộ giải DPLL</div>
        <div class="telemetry-grid">
          <div class="metric-box"><span class="metric-lbl">Biến chính (N²)</span><span class="metric-val" id="mPrimary">0</span></div>
          <div class="metric-box"><span class="metric-lbl">Biến phụ trợ</span><span class="metric-val" id="mAux">0</span></div>
          <div class="metric-box"><span class="metric-lbl">Mệnh đề CNF</span><span class="metric-val" id="mClauses">0</span></div>
          <div class="metric-box"><span class="metric-lbl">Truy vấn SAT</span><span class="metric-val" id="mQueries">0</span></div>
          <div class="metric-box"><span class="metric-lbl">Phân nhánh</span><span class="metric-val" id="mDecisions">0</span></div>
          <div class="metric-box"><span class="metric-lbl">Lan truyền đơn vị</span><span class="metric-val" id="mProps">0</span></div>
          <div class="metric-box"><span class="metric-lbl">Quay lui (Backtrack)</span><span class="metric-val" id="mBacktracks">0</span></div>
          <div class="metric-box"><span class="metric-lbl">Thời gian giải</span><span class="metric-val" id="mRuntime">0.0ms</span></div>
        </div>
      </div>

      <div>
        <div class="drawer-section-title">Danh sách Lời khai Đã mở (Bấm để khoanh vùng)</div>
        <div class="clue-drawer-list" id="clueDrawerList"></div>
      </div>

      <div style="flex:1; display:flex; flex-direction:column;">
        <div class="drawer-section-title">Nhật ký Suy diễn AI (Deduction Trace)</div>
        <div class="trace-box" id="traceBox"></div>
      </div>
    </div>
  </aside>

  <!-- ===================================================================
       MODAL 1: LUẬT CHƠI & CƠ CHẾ AI
       =================================================================== -->
  <div class="modal-overlay" id="modalRules" onclick="if(event.target===this) closeModal('modalRules')">
    <div class="modal-card">
      <h2>📖 Luật Chơi &amp; Cơ Chế Suy Diễn SAT</h2>
      <p>
        <strong>Hồ Sơ Logic: Griductive</strong> là trò chơi trinh thám dựa trên <strong>Logic Mệnh Đề (Propositional Logic)</strong>
        và bộ giải <strong>DPLL SAT Solver</strong>, lấy cảm hứng từ <em>Clues by Sam</em>.
      </p>
      <ul class="rule-list">
        <li>
          <strong>1. Hai thân phận duy nhất:</strong> Mỗi nghi phạm trên bàn cờ <code>N×N</code> chỉ có thể là
          <strong style="color:var(--innocent)">✓ VÔ TỘI (INNOCENT)</strong> hoặc
          <strong style="color:var(--criminal)">✕ THỦ PHẠM (CRIMINAL)</strong>.
        </li>
        <li>
          <strong>2. Mọi lời khai đều là sự thật:</strong> Ngay cả Thủ phạm hay người Vô tội, một khi hồ sơ đã được lật mở,
          nội dung lời khai trên thẻ của họ luôn luôn đúng 100%.
        </li>
        <li>
          <strong>3. Nguyên tắc vàng — Cấm đoán mò:</strong> Bạn chỉ được phép kết luận một nghi phạm khi trạng thái của họ
          <strong>bắt buộc phải đúng trong mọi nghiệm hợp lệ</strong> của các lời khai hiện có:
          <br/>• Phán quyết đúng tất yếu → <strong>CHẤP NHẬN</strong> &amp; lật thẻ mở lời khai mới.
          <br/>• Phán quyết khi chưa đủ chứng cứ → Cảnh báo <strong>CHƯA ĐỦ BẰNG CHỨNG</strong>.
          <br/>• Phán quyết trái ngược lời khai → Cảnh báo <strong>MÂU THUẪN LOGIC</strong>.
        </li>
        <li>
          <strong>4. Khoanh vùng trực quan:</strong> Bấm vào bất kỳ thẻ sáng màu nào đã mở để chiếu sáng các ô mà lời khai đó đang nhắc tới trên bàn cờ.
        </li>
      </ul>
      <div style="display:flex; justify-content:flex-end;">
        <button type="button" class="btn btn-gold" onclick="closeModal('modalRules')">Đã hiểu, bắt đầu phá án!</button>
      </div>
    </div>
  </div>

  <!-- ===================================================================
       MODAL 2: PHÁ ÁN THÀNH CÔNG (VICTORY MODAL)
       =================================================================== -->
  <div class="modal-overlay" id="modalVictory" onclick="if(event.target===this) closeModal('modalVictory')">
    <div class="modal-card" style="text-align:center;">
      <div style="font-size:46px; margin-bottom:6px;">🏆</div>
      <h2>VỤ ÁN ĐÃ KHÉP LẠI!</h2>
      <p id="victoryDesc">Chúc mừng Thám tử! Bạn đã xác minh chính xác toàn bộ nghi phạm bằng suy luận logic thuần túy.</p>
      <div class="victory-stats">
        <div class="victory-stat-tile">
          <div class="victory-stat-val" id="vStatCells">9/9</div>
          <div class="victory-stat-lbl">Nghi phạm đã mở</div>
        </div>
        <div class="victory-stat-tile">
          <div class="victory-stat-val" id="vStatClauses">0</div>
          <div class="victory-stat-lbl">Mệnh đề CNF</div>
        </div>
        <div class="victory-stat-tile">
          <div class="victory-stat-val" id="vStatProps">0</div>
          <div class="victory-stat-lbl">Lan truyền đơn vị</div>
        </div>
      </div>
      <div style="display:flex; justify-content:center; gap:12px; flex-wrap:wrap;">
        <button type="button" class="btn" onclick="closeModal('modalVictory')">Xem lại bàn cờ</button>
        <button type="button" class="btn" onclick="closeModal('modalVictory'); showScreen('screenCases')">Về Kho Hồ Sơ</button>
        <button type="button" class="btn btn-gold" onclick="playNextCase()">Hồ Sơ Tiếp Theo →</button>
      </div>
    </div>
  </div>

  <script>
    let currentState = null;
    let autoTimer = null;
    let lastAnimatedCell = null;
    let lastAnimationKind = null;
    let currentCaseFilter = "all";
    let victoryShownForSession = null;

    function getSolvedCases() {
      try {
        return JSON.parse(localStorage.getItem("griductive_solved_cases") || "[]");
      } catch (e) {
        return [];
      }
    }
    function markCaseSolved(puzzleId) {
      try {
        const list = getSolvedCases();
        if (!list.includes(puzzleId)) {
          list.push(puzzleId);
          localStorage.setItem("griductive_solved_cases", JSON.stringify(list));
        }
      } catch (e) {}
    }

    function showScreen(screenId) {
      stopAutoSolve();
      document.querySelectorAll(".screen").forEach(el => el.classList.remove("active"));
      const target = document.getElementById(screenId);
      if (target) target.classList.add("active");
      if (screenId === "screenCases" && currentState) {
        renderCaseSelection(currentState.puzzles || []);
      }
    }

    function openModal(id) {
      document.getElementById(id).classList.add("open");
    }
    function closeModal(id) {
      document.getElementById(id).classList.remove("open");
    }

    function toggleDrawer(open) {
      const dr = document.getElementById("aiDrawer");
      const bd = document.getElementById("drawerBackdrop");
      if (open) {
        dr.classList.add("open");
        bd.classList.add("open");
      } else {
        dr.classList.remove("open");
        bd.classList.remove("open");
      }
    }

    function toggleTheme() {
      const html = document.documentElement;
      const next = html.dataset.theme === "noir" ? "paper" : "noir";
      html.dataset.theme = next;
      const lbl = document.getElementById("lblThemeStart");
      if (lbl) {
        lbl.textContent = next === "noir"
          ? "🌗 Giao diện: Đêm Trinh Thám"
          : "🌕 Giao diện: Hồ Sơ Cổ Điển";
      }
    }

    async function startImmediateInvestigation() {
      if (!currentState) {
        await apiCall("/api/state", {});
      }
      showScreen("screenGame");
    }

    function setCaseFilter(f) {
      currentCaseFilter = f;
      document.querySelectorAll("#caseFilterTabs .filter-tab").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.filter === f);
      });
      if (currentState && currentState.puzzles) {
        renderCaseSelection(currentState.puzzles);
      }
    }

    function renderCaseSelection(puzzles) {
      const grid = document.getElementById("casesGrid");
      grid.innerHTML = "";
      const solved = getSolvedCases();

      const filtered = puzzles.filter(p => {
        if (currentCaseFilter === "all") return true;
        if (currentCaseFilter === "edge") return p.kind !== "normal" && p.kind !== "stress";
        return String(p.n) === currentCaseFilter && (p.kind === "normal" || p.kind === "stress");
      });

      filtered.forEach(p => {
        const isSolved = solved.includes(p.case_id);
        const stars = "★".repeat(p.difficulty || 1) + "☆".repeat(Math.max(0, 3 - (p.difficulty || 1)));
        const card = document.createElement("div");
        card.className = "dossier-card";
        card.innerHTML = `
          <div>
            <div class="dossier-top">
              <span class="dossier-code">${p.code || "HỒ SƠ"} · ${p.n}×${p.n}</span>
              <div class="dossier-badges">
                ${isSolved ? '<span class="solved-pill">✓ ĐÃ PHÁ ÁN</span>' : ''}
                <span class="stars" title="Độ khó">${stars}</span>
              </div>
            </div>
            <div class="dossier-title">${p.title || p.case_id}</div>
            <div class="dossier-sub">${p.subtitle || ""}</div>
            <div class="dossier-story">${p.story || ""}</div>
          </div>
          <div class="dossier-footer">
            <span class="dossier-tag">📌 ${p.badge || (p.n + "×" + p.n)}</span>
            <span class="dossier-cta">Mở Hồ Sơ Điều Tra →</span>
          </div>
        `;
        card.addEventListener("click", async () => {
          const data = await apiCall("/api/load", { case_id: p.case_id });
          render(data);
          showScreen("screenGame");
        });
        grid.appendChild(card);
      });
    }

    /* Multi-color SVG Suspect Portrait Generator */
    function suspectPortraitSvg(profession, isRevealed, status) {
      const p = (profession || "").toLowerCase();
      let accent = "#F59E0B";
      let coat = "#334155";
      let badge = "";

      if (p.includes("thám tử") || p.includes("detective") || p.includes("cảnh sát")) {
        accent = "#F59E0B"; coat = "#1E293B";
        badge = `<path d="M9 13 Q18 8 27 13" stroke="#FBBF24" stroke-width="2.2" fill="none"/><ellipse cx="18" cy="10" rx="6" ry="3.2" fill="#F59E0B"/>`;
      } else if (p.includes("bác sĩ") || p.includes("dược") || p.includes("pháp y") || p.includes("nurse") || p.includes("doctor")) {
        accent = "#38BDF8"; coat = "#0F766E";
        badge = `<rect x="16.5" y="24" width="3" height="7" rx="1" fill="#38BDF8"/><rect x="14" y="26.5" width="8" height="2.6" rx="1" fill="#38BDF8"/>`;
      } else if (p.includes("đầu bếp") || p.includes("baker") || p.includes("chef")) {
        accent = "#FB923C"; coat = "#475569";
        badge = `<path d="M12 11 C12 6, 24 6, 24 11" fill="#F8FAFC" stroke="#FB923C" stroke-width="1.5"/>`;
      } else if (p.includes("phi công") || p.includes("thuyền trưởng") || p.includes("pilot")) {
        accent = "#60A5FA"; coat = "#1E3A8A";
        badge = `<polygon points="18,8 25,11 18,13 11,11" fill="#FBBF24"/>`;
      } else if (p.includes("thẩm phán") || p.includes("luật sư") || p.includes("ngoại giao")) {
        accent = "#C084FC"; coat = "#312E81";
        badge = `<path d="M15 24 L18 29 L21 24" stroke="#FBBF24" stroke-width="1.8" fill="none"/>`;
      } else if (p.includes("kỹ sư") || p.includes("kiến trúc") || p.includes("mật mã")) {
        accent = "#34D399"; coat = "#065F46";
        badge = `<rect x="12" y="13" width="12" height="3.2" rx="1.5" fill="#38BDF8"/>`;
      } else if (p.includes("nghệ sĩ") || p.includes("nhạc") || p.includes("đạo diễn")) {
        accent = "#F472B6"; coat = "#701A75";
        badge = `<ellipse cx="19" cy="9.5" rx="7" ry="3" fill="#F472B6"/>`;
      } else {
        accent = "#A78BFA"; coat = "#374151";
      }

      if (isRevealed) {
        coat = status === "INNOCENT" ? "#059669" : "#E11D48";
      }

      return `<svg width="34" height="34" viewBox="0 0 36 36" fill="none" aria-hidden="true">
        <path d="M7 33 C7 24.5, 29 24.5, 29 33" fill="${coat}"/>
        <circle cx="18" cy="15.5" r="6" fill="#FDE68A" stroke="${accent}" stroke-width="1.4"/>
        <circle cx="16" cy="15" r="0.9" fill="#1E293B"/>
        <circle cx="20" cy="15" r="0.9" fill="#1E293B"/>
        <path d="M16 18 Q18 19.4 20 18" stroke="#1E293B" stroke-width="1.1" fill="none" stroke-linecap="round"/>
        ${badge}
      </svg>`;
    }

    function regionOverlayHtml(role) {
      let col = "var(--hl-ref)";
      let label = "📍 VÙNG LỜI KHAI";
      if (role === "LEFT") { col = "var(--hl-ref)"; label = "◀ VẾ TRÁI"; }
      if (role === "RIGHT") { col = "var(--hl-right)"; label = "▶ VẾ PHẢI"; }
      if (role === "L∩R") { col = "var(--hl-overlap)"; label = "✦ GIAO NHAU"; }
      return `
        <div class="region-role-pill" data-role="${role}">${label}</div>
        <svg class="region-overlay-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
          <path d="M 2 18 L 2 2 L 18 2 M 82 2 L 98 2 L 98 18 M 2 82 L 2 98 L 18 98 M 82 98 L 98 98 L 98 82"
                stroke="${col}" stroke-width="3.2" fill="none" vector-effect="non-scaling-stroke"/>
        </svg>
      `;
    }

    const BANNER_LABEL_VN = {
      READY: "ĐANG ĐIỀU TRA",
      ACCEPTED: "SUY LUẬN CHÍNH XÁC",
      NOT_PROVABLE: "CHƯA ĐỦ BẰNG CHỨNG",
      CONTRADICTED: "MÂU THUẪN LOGIC",
      HINT: "GỢI Ý TỪ AI",
      STUCK: "TẠM DỪNG SUY DIỄN",
      SOLVED: "PHÁ ÁN THÀNH CÔNG",
      INCONSISTENT: "LỜI KHAI MÂU THUẪN",
      ERROR: "THÔNG BÁO LỖI",
    };

    async function apiCall(path, body = {}) {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      return await res.json();
    }

    function render(data) {
      currentState = data;

      // Mark solved in localStorage if complete
      if (data.is_complete) {
        markCaseSolved(data.puzzle_id);
      }

      // Populate Quick Select & Case Grid
      const qSel = document.getElementById("quickPuzzleSelect");
      if (data.puzzles) {
        qSel.innerHTML = "";
        data.puzzles.forEach(p => {
          const opt = document.createElement("option");
          opt.value = p.case_id;
          opt.textContent = `${p.code}: ${p.title} (${p.n}×${p.n})`;
          if (p.case_id === data.puzzle_id || data.puzzle_id.includes(p.case_id)) {
            opt.selected = true;
          }
          qSel.appendChild(opt);
        });
        renderCaseSelection(data.puzzles);
      }

      // Header Info
      document.getElementById("hdrCaseCode").textContent = data.case_code || "HỒ SƠ";
      document.getElementById("hdrCaseTitle").textContent = data.case_title || data.puzzle_id;
      document.getElementById("progressLabel").textContent = `Đã xác minh: ${data.revealed_count}/${data.total_cells}`;
      const pct = data.total_cells > 0 ? Math.round((data.revealed_count / data.total_cells) * 100) : 0;
      document.getElementById("progressBarFill").style.width = `${pct}%`;
      document.getElementById("badgeClauseCount").textContent = `${data.telemetry.num_clauses} CNF`;

      // Spotlight & Status Ribbon
      const kind = data.banner_kind || "READY";
      const spInner = document.getElementById("spotlightInner");
      const stBadge = document.getElementById("statusBadge");
      spInner.dataset.kind = kind;
      stBadge.dataset.kind = kind;
      stBadge.textContent = BANNER_LABEL_VN[kind] || kind;
      document.getElementById("statusText").textContent = data.banner_message || "";

      const insp = data.selected_inspector;
      const cluePill = document.getElementById("activeCluePill");
      if (insp) {
        cluePill.style.display = "flex";
        document.getElementById("activeClueOwner").textContent = `Lời khai ${insp.owner} (${insp.cell}):`;
        if ((insp.left && insp.left.length) || (insp.right && insp.right.length)) {
          const parts = [];
          if (insp.left.length) parts.push(`Vế trái: ${insp.left.join(", ")}`);
          if (insp.right.length) parts.push(`Vế phải: ${insp.right.join(", ")}`);
          if (insp.overlap.length) parts.push(`Giao nhau: ${insp.overlap.join(", ")}`);
          document.getElementById("activeClueRefs").textContent = parts.join(" | ");
        } else {
          document.getElementById("activeClueRefs").textContent = `Khoanh vùng (${insp.referenced.length} ô): ${insp.referenced.join(", ")}`;
        }
      } else {
        cluePill.style.display = "none";
      }

      // Render Board Grid
      const n = data.n;
      const shell = document.getElementById("boardShell");
      shell.dataset.n = String(n);

      const colHeaders = document.getElementById("colHeaders");
      colHeaders.innerHTML = "";
      colHeaders.style.gridTemplateColumns = `repeat(${n}, 1fr)`;
      for (let c = 0; c < n; c++) {
        const ch = document.createElement("div");
        ch.className = "col-hdr";
        ch.textContent = `CỘT ${String.fromCharCode(65 + c)}`;
        colHeaders.appendChild(ch);
      }

      const rowsWrap = document.getElementById("boardRowsWrap");
      rowsWrap.innerHTML = "";
      for (let r = 0; r < n; r++) {
        const rowEl = document.createElement("div");
        rowEl.className = "board-row";

        const rHdr = document.createElement("div");
        rHdr.className = "row-hdr";
        rHdr.textContent = `${r + 1}`;
        rowEl.appendChild(rHdr);

        const cardsGrid = document.createElement("div");
        cardsGrid.className = "row-cards";
        cardsGrid.style.gridTemplateColumns = `repeat(${n}, 1fr)`;

        for (let c = 0; c < n; c++) {
          const item = data.cells[r * n + c];
          const scene = document.createElement("div");
          scene.className = "suspect-scene";

          const card = document.createElement("div");
          const classes = ["suspect-card"];
          if (item.revealed) {
            classes.push(item.status === "INNOCENT" ? "revealed-innocent" : "revealed-criminal");
          } else {
            classes.push("unsolved");
          }
          if (item.is_selected_clue) classes.push("selected-clue");
          if (item.is_hinted) classes.push("hinted");
          if (lastAnimatedCell === item.cell && lastAnimationKind) {
            classes.push(lastAnimationKind);
          }
          card.className = classes.join(" ");

          const overlay = item.highlight_role ? regionOverlayHtml(item.highlight_role) : "";

          if (item.revealed) {
            const isInn = item.status === "INNOCENT";
            const badgeClass = isInn ? "innocent" : "criminal";
            const badgeText = isInn ? "✓ VÔ TỘI" : "✕ THỦ PHẠM";
            const clueText = n === 5 ? item.clue.short_text : item.clue.text;

            card.innerHTML = `
              ${overlay}
              <div class="card-top">
                <span class="coord-pill">${item.cell}</span>
                <span class="stamp-badge ${badgeClass}">${badgeText}</span>
              </div>
              <div class="identity-revealed">
                <div class="avatar-wrap">${suspectPortraitSvg(item.profession, true, item.status)}</div>
                <div>
                  <div class="char-name">${item.name}</div>
                  <div class="char-prof">${item.profession}</div>
                </div>
              </div>
              <div class="clue-bubble" title="Bấm vào thẻ để khoanh vùng các ô liên quan">
                “${clueText}”
              </div>
            `;
            card.addEventListener("click", () => selectClue(item.is_selected_clue ? null : item.cell));
          } else {
            const topRight = item.is_hinted
              ? `<span class="stamp-badge hint-pill">💡 AI GỢI Ý</span>`
              : `<span class="stamp-badge unsolved-pill">ĐANG THẨM VẤN</span>`;
            card.innerHTML = `
              ${overlay}
              <div class="card-top">
                <span class="coord-pill">${item.cell}</span>
                ${topRight}
              </div>
              <div class="identity-unsolved">
                <div class="avatar-wrap">${suspectPortraitSvg(item.profession, false, null)}</div>
                <div class="char-name">${item.name}</div>
                <div class="char-prof">${item.profession}</div>
              </div>
              <div class="verdict-row">
                <button type="button" class="btn-verdict innocent" data-cell="${item.cell}" data-v="INNOCENT">✓ Vô tội</button>
                <button type="button" class="btn-verdict criminal" data-cell="${item.cell}" data-v="CRIMINAL">✕ Thủ phạm</button>
              </div>
            `;
            card.querySelectorAll(".btn-verdict").forEach(btn => {
              btn.addEventListener("click", (ev) => {
                ev.stopPropagation();
                submitVerdict(btn.dataset.cell, btn.dataset.v);
              });
            });
          }

          scene.appendChild(card);
          cardsGrid.appendChild(scene);
        }
        rowEl.appendChild(cardsGrid);
        rowsWrap.appendChild(rowEl);
      }

      lastAnimatedCell = null;
      lastAnimationKind = null;

      // Render AI Drawer Telemetry & Clues & Trace
      const t = data.telemetry;
      document.getElementById("mPrimary").textContent = t.num_primary;
      document.getElementById("mAux").textContent = t.num_aux;
      document.getElementById("mClauses").textContent = t.num_clauses;
      document.getElementById("mQueries").textContent = t.sat_calls;
      document.getElementById("mDecisions").textContent = t.decisions;
      document.getElementById("mProps").textContent = t.propagations;
      document.getElementById("mBacktracks").textContent = t.backtracks;
      document.getElementById("mRuntime").textContent = `${t.runtime_ms.toFixed(1)}ms`;

      const cList = document.getElementById("clueDrawerList");
      cList.innerHTML = "";
      data.revealed_clues.forEach(rc => {
        const item = document.createElement("div");
        item.className = "clue-drawer-item" + (rc.selected ? " active" : "");
        item.innerHTML = `<span class="clue-drawer-tag">[${rc.cell} · ${rc.owner}]</span>${rc.text}`;
        item.addEventListener("click", () => selectClue(rc.cell));
        cList.appendChild(item);
      });

      const traceBox = document.getElementById("traceBox");
      traceBox.innerHTML = "";
      data.trace.forEach(tr => {
        const row = document.createElement("div");
        row.className = "trace-entry";
        row.innerHTML = `<span class="trace-tag ${tr.outcome}">#${String(tr.step_no).padStart(2, '0')} [${tr.outcome}]</span> ${tr.detail}`;
        traceBox.appendChild(row);
      });
      traceBox.scrollTop = traceBox.scrollHeight;

      // Trigger Victory Modal once when puzzle completes
      if (data.is_complete && victoryShownForSession !== data.session_id) {
        victoryShownForSession = data.session_id;
        document.getElementById("vStatCells").textContent = `${data.revealed_count}/${data.total_cells}`;
        document.getElementById("vStatClauses").textContent = t.num_clauses;
        document.getElementById("vStatProps").textContent = t.propagations;
        setTimeout(() => openModal("modalVictory"), 420);
      }
    }

    async function selectClue(cell) {
      const data = await apiCall("/api/select_clue", { cell });
      render(data);
    }

    async function submitVerdict(cell, verdict) {
      stopAutoSolve();
      const data = await apiCall("/api/verdict", { cell, verdict });
      if (data.last_outcome) {
        lastAnimatedCell = cell;
        lastAnimationKind = data.last_outcome.result === "ACCEPTED" ? "anim-flip" : "anim-shake";
      }
      render(data);
    }

    async function requestHint() {
      stopAutoSolve();
      const data = await apiCall("/api/hint", {});
      render(data);
    }

    async function stepSolve() {
      const data = await apiCall("/api/step", {});
      if (data.last_outcome && data.last_outcome.cell) {
        lastAnimatedCell = data.last_outcome.cell;
        lastAnimationKind = data.last_outcome.result === "ACCEPTED" ? "anim-flip" : "anim-shake";
      }
      render(data);
      return data;
    }

    function stopAutoSolve() {
      if (autoTimer) {
        clearTimeout(autoTimer);
        autoTimer = null;
      }
      document.getElementById("lblAuto").textContent = "⚡ Tự động phá án";
    }

    async function loopAutoSolve() {
      if (!autoTimer) return;
      const data = await stepSolve();
      if (!autoTimer || data.is_complete || !data.last_outcome || data.last_outcome.result !== "ACCEPTED") {
        stopAutoSolve();
        return;
      }
      const speed = parseInt(document.getElementById("speedSelect").value, 10) || 480;
      autoTimer = setTimeout(loopAutoSolve, speed);
    }

    async function playNextCase() {
      closeModal("modalVictory");
      if (!currentState || !currentState.puzzles || !currentState.puzzles.length) return;
      const list = currentState.puzzles;
      const idx = list.findIndex(p => p.case_id === currentState.puzzle_id);
      const nextItem = list[(idx + 1) % list.length];
      const data = await apiCall("/api/load", { case_id: nextItem.case_id });
      render(data);
    }

    document.getElementById("btnAuto").addEventListener("click", () => {
      if (autoTimer) {
        stopAutoSolve();
        return;
      }
      document.getElementById("lblAuto").textContent = "⏸ Tạm dừng";
      autoTimer = setTimeout(loopAutoSolve, 60);
    });

    document.getElementById("btnHint").addEventListener("click", requestHint);
    document.getElementById("btnStep").addEventListener("click", () => { stopAutoSolve(); stepSolve(); });
    document.getElementById("btnRestart").addEventListener("click", async () => {
      stopAutoSolve();
      victoryShownForSession = null;
      render(await apiCall("/api/restart", {}));
    });

    document.getElementById("quickPuzzleSelect").addEventListener("change", async (e) => {
      stopAutoSolve();
      victoryShownForSession = null;
      render(await apiCall("/api/load", { case_id: e.target.value }));
    });

    document.getElementById("uploadJsonCases").addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      stopAutoSolve();
      victoryShownForSession = null;
      const text = await file.text();
      const data = await apiCall("/api/load_raw", { content: text });
      render(data);
      showScreen("screenGame");
      e.target.value = "";
    });

    // Khởi tạo dữ liệu ban đầu
    apiCall("/api/state", {}).then(render);
  </script>
</body>
</html>
"""


class WebGUIApp:
    """Máy chủ HTTP cung cấp Giao diện Web Tiếng Việt cho Hồ Sơ Logic: Griductive."""

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

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                pass

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                if parsed.path in ("/", "/index.html"):
                    data = INDEX_HTML.encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                else:
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
