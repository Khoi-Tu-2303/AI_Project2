# Griductive Solver — Báo cáo nghiệm thu (P)

- **Thời gian thực hiện**: `2026-11-09T10:38:55.754490+00:00`
- **Phạm vi kiểm tra (Scope)**: `p`
- **Yêu cầu mã thật (require_real)**: `True`
- **Kết quả tổng thể**: **PASS** (Exit code: `0`)

## Bảng tổng hợp các cổng nghiệm thu (Gates)

| Cổng (Gate) | Phụ trách | Trạng thái | Passed | Failed | Blocked | Tổng số |
|---|---|---|---:|---:|---:|---:|
| `G-P` | C/E (Puzzle Suite) | **PASS** | 10 | 0 | 0 | 10 |

## Chi tiết các bước kiểm tra (Subchecks)

### Cổng `G-P`: C/E (Puzzle Suite) — [PASS]

- **[PASS] P-chain_demo**: Verify puzzle case 'chain_demo' (examples/3x3_chain.json) (18.08 ms)
  - *Bằng chứng / Ghi chú*: Case 'chain_demo' (3x3, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-3x3_classic**: Verify puzzle case '3x3_classic' (examples/3x3_classic.json) (32.63 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_classic' (3x3, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-3x3_extensions**: Verify puzzle case '3x3_extensions' (examples/3x3_extensions.json) (51.23 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_extensions' (3x3, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-4x4_detective**: Verify puzzle case '4x4_detective' (examples/4x4_detective.json) (164.04 ms)
  - *Bằng chứng / Ghi chú*: Case '4x4_detective' (4x4, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-4x4_crossfire**: Verify puzzle case '4x4_crossfire' (examples/4x4_crossfire.json) (216.09 ms)
  - *Bằng chứng / Ghi chú*: Case '4x4_crossfire' (4x4, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-5x5_mastermind**: Verify puzzle case '5x5_mastermind' (examples/5x5_mastermind.json) (494.05 ms)
  - *Bằng chứng / Ghi chú*: Case '5x5_mastermind' (5x5, stress) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-5x5_syndicate**: Verify puzzle case '5x5_syndicate' (examples/5x5_syndicate.json) (534.18 ms)
  - *Bằng chứng / Ghi chú*: Case '5x5_syndicate' (5x5, stress) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-3x3_stuck**: Verify puzzle case '3x3_stuck' (examples/3x3_stuck.json) (12.05 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_stuck' (3x3, stuck) verified: uniqueness=UNIQUE, run=STUCK
- **[PASS] P-3x3_multi**: Verify puzzle case '3x3_multi' (examples/3x3_multi.json) (24.86 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_multi' (3x3, multi_solution) verified: uniqueness=MULTIPLE, run=STUCK
- **[PASS] P-3x3_inconsistent**: Verify puzzle case '3x3_inconsistent' (examples/3x3_inconsistent.json) (4.86 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_inconsistent' (3x3, inconsistent) verified: uniqueness=UNSAT, run=INCONSISTENT
