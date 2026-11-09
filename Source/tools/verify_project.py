"""CLI verification runner for Griductive Solver project.

Usage:
    python -m tools.verify_project --scope a --output ../verification
    python -m tools.verify_project --scope all --require-real --output ../verification
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from tools.integration_runner import IntegrationRunner, VerificationReport


def generate_markdown_summary(report: VerificationReport) -> str:
    """Generate human-readable Markdown summary of gate results."""
    lines: list[str] = [
        f"# Griductive Solver — Báo cáo nghiệm thu ({report.scope.upper()})",
        "",
        f"- **Thời gian thực hiện**: `{report.timestamp}`",
        f"- **Phạm vi kiểm tra (Scope)**: `{report.scope}`",
        f"- **Yêu cầu mã thật (require_real)**: `{report.require_real}`",
        f"- **Kết quả tổng thể**: **{report.overall_status}** (Exit code: `{report.exit_code}`)",
        "",
        "## Bảng tổng hợp các cổng nghiệm thu (Gates)",
        "",
        "| Cổng (Gate) | Phụ trách | Trạng thái | Passed | Failed | Blocked | Tổng số |",
        "|---|---|---|---:|---:|---:|---:|",
    ]

    for gate_id, gate in report.gates.items():
        lines.append(
            f"| `{gate_id}` | {gate.module_owner} | **{gate.status}** | {gate.passed_count} | {gate.failed_count} | {gate.blocked_count} | {gate.total_count} |"
        )

    lines.append("")
    lines.append("## Chi tiết các bước kiểm tra (Subchecks)")
    lines.append("")

    for gate_id, gate in report.gates.items():
        lines.append(f"### Cổng `{gate_id}`: {gate.module_owner} — [{gate.status}]")
        lines.append("")
        for sub in gate.subchecks:
            badge = "[PASS]" if sub.status == "PASS" else f"[{sub.status}]"
            lines.append(f"- **{badge} {sub.check_id}**: {sub.description} ({sub.duration_ms} ms)")
            lines.append(f"  - *Bằng chứng / Ghi chú*: {sub.evidence}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Griductive Solver Verification Runner")
    parser.add_argument(
        "--scope",
        choices=["a", "b", "c", "d", "e", "p", "integration", "all"],
        default="a",
        help="Scope of verification to run (default: a)",
    )
    parser.add_argument(
        "--require-real",
        action="store_true",
        help="Require real implementations without mocks or test doubles",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../verification",
        help="Output directory for results.json and summary.md (default: ../verification)",
    )

    args = parser.parse_args()

    # Determine source root
    source_dir = Path(__file__).resolve().parent.parent

    runner = IntegrationRunner(source_dir=source_dir, require_real=args.require_real)
    report = runner.run_scope(args.scope)

    # Output directory
    out_dir = Path(args.output)
    if not out_dir.is_absolute():
        out_dir = (source_dir / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write results.json
    results_path = out_dir / "results.json"
    results_path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Write summary.md
    summary_md = generate_markdown_summary(report)
    summary_path = out_dir / "summary.md"
    summary_path.write_text(summary_md, encoding="utf-8")

    # Print to console
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(summary_md)
    print(f"\n[INFO] Machine-readable report saved to: {results_path}")
    print(f"[INFO] Markdown summary saved to: {summary_path}")

    sys.exit(report.exit_code)


if __name__ == "__main__":
    main()
