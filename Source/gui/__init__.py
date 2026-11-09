"""Module E: Giao diện Web Tiếng Việt & Bộ điều khiển cho Hồ Sơ Logic: Griductive."""

from gui.app import GriductiveApp
from gui.clue_formatter import format_clue, format_region
from gui.controller import GUIController, ManifestPuzzleItem, TelemetrySnapshot, TraceEntry
from gui.theme import NEWSPRINT_BRASS, THEMES, WARM_NOIR_GOLD, ThemePalette
from gui.web_server import WebGUIApp

__all__ = [
    "GriductiveApp",
    "WebGUIApp",
    "GUIController",
    "ManifestPuzzleItem",
    "TelemetrySnapshot",
    "TraceEntry",
    "ThemePalette",
    "WARM_NOIR_GOLD",
    "NEWSPRINT_BRASS",
    "THEMES",
    "format_clue",
    "format_region",
]
