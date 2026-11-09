"""Điểm khởi chạy chính cho ứng dụng Hồ Sơ Logic: Griductive (Mặc định mở Giao diện Web Tiếng Việt)."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SOURCE_DIR = Path(__file__).resolve().parent
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

from gui.app import GriductiveApp
from gui.controller import GUIController
from gui.web_server import WebGUIApp


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hồ Sơ Logic: Griductive — Trò chơi Phá án Suy luận Mệnh đề & DPLL SAT",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        default=True,
        help="Khởi chạy giao diện Web Tiếng Việt trên trình duyệt (mặc định bật).",
    )
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Khởi chạy giao diện cửa sổ Tkinter Desktop thay vì Web.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Địa chỉ host cho Web Server (mặc định: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Cổng cho Web Server (mặc định: 8080).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Không tự động bật tab trình duyệt khi khởi động máy chủ Web.",
    )
    parser.add_argument(
        "--puzzle",
        type=str,
        default=None,
        help="Đường dẫn tới file JSON màn chơi muốn nạp ngay khi mở.",
    )
    parser.add_argument(
        "--theme",
        choices=["noir", "paper"],
        default="noir",
        help="Giao diện ban đầu: 'noir' (Đêm Trinh Thám) hoặc 'paper' (Hồ Sơ Cổ Điển).",
    )
    parser.add_argument(
        "--reduced-motion",
        action="store_true",
        help="Giảm chuyển động hiệu ứng.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    controller = GUIController()

    if not args.desktop:
        web_app = WebGUIApp(
            controller=controller,
            initial_puzzle=args.puzzle,
            host=args.host,
            port=args.port,
        )
        web_app.serve(open_browser=not args.no_browser)
        return 0

    app = GriductiveApp(controller=controller, initial_puzzle=args.puzzle)
    if args.theme == "paper":
        app.on_toggle_theme()
    if args.reduced_motion:
        app.on_toggle_motion()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
