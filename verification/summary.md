# Griductive Solver — Báo cáo nghiệm thu (ALL)

- **Thời gian thực hiện**: `2026-11-10T10:51:44.263287+00:00`
- **Phạm vi kiểm tra (Scope)**: `all`
- **Yêu cầu mã thật (require_real)**: `True`
- **Kết quả tổng thể**: **BLOCKED** (Exit code: `2`)

## Bảng tổng hợp các cổng nghiệm thu (Gates)

| Cổng (Gate) | Phụ trách | Trạng thái | Passed | Failed | Blocked | Tổng số |
|---|---|---|---:|---:|---:|---:|
| `G-A` | A (Core & Engine) | **PASS** | 7 | 0 | 0 | 7 |
| `G-B` | B (CNF Encoder) | **PASS** | 11 | 0 | 0 | 11 |
| `G-C` | C (DPLL Solver) | **PASS** | 2 | 0 | 0 | 2 |
| `G-P` | C/E (Puzzle Suite) | **PASS** | 10 | 0 | 0 | 10 |
| `G-D` | D (Logic Agent) | **BLOCKED** | 0 | 0 | 1 | 1 |
| `G-E` | E (GUI & Main) | **PASS** | 7 | 0 | 0 | 7 |
| `G-I` | Integration (All Members) | **BLOCKED** | 0 | 0 | 1 | 1 |

## Chi tiết các bước kiểm tra (Subchecks)

### Cổng `G-A`: A (Core & Engine) — [PASS]

- **[PASS] A-01**: Imports and layout boundaries (31.26 ms)
  - *Bằng chứng / Ghi chú*: All common and engine modules import cleanly without external dependencies
- **[PASS] A-02**: Coordinates, bounds, and neighbors (0.3 ms)
  - *Bằng chứng / Ghi chú*: Cell coordinates, bounds, row-major order, and neighbor counts verified for 3x3, 4x4, 5x5
- **[PASS] A-03/04**: Regions and referenced_cells for 8 clues (0.07 ms)
  - *Bằng chứng / Ghi chú*: Region resolution and referenced_cells verified with COMPARE overlap
- **[PASS] A-05/06**: Strict JSON IO and Puzzle structure (1.41 ms)
  - *Bằng chứng / Ghi chú*: Strict JSON parsed and round-tripped fixture 3x3_chain.json
- **[PASS] A-07**: Manifest loader and security (12.89 ms)
  - *Bằng chứng / Ghi chú*: Manifest loader loaded index.json and enforced path security
- **[PASS] A-08..18**: GameEngine lifecycle and verdict transactions (1.98 ms)
  - *Bằng chứng / Ghi chú*: Engine load, verdict submission, token increment, and isolation verified
- **[PASS] A-19**: Sequential chain solving via OracleClassifier (40.74 ms)
  - *Bằng chứng / Ghi chú*: 8-step sequential chain reveal fully verified with independent Oracle

### Cổng `G-B`: B (CNF Encoder) — [PASS]

- **[PASS] test_b01_varmap_bijection**: test_b01_varmap_bijection (0.64 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b02_binary_projection**: test_b02_binary_projection (224.52 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b03_counting_all_bounds**: test_b03_counting_all_bounds (27273.33 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b04_parity_and_region_kinds**: test_b04_parity_and_region_kinds (758.86 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b05_compare_overlap_and_identical_regions**: test_b05_compare_overlap_and_identical_regions (4008.44 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b06_independent_bruteforce_auxiliary_projection**: test_b06_independent_bruteforce_auxiliary_projection (93.65 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b07_kb_rebuild_isolation_and_public_inputs**: test_b07_kb_rebuild_isolation_and_public_inputs (91.56 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b08_standalone_clues_do_not_reuse_auxiliaries**: test_b08_standalone_clues_do_not_reuse_auxiliaries (55.67 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b09_reject_invalid_clues_and_assignments**: test_b09_reject_invalid_clues_and_assignments (0.43 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b10_larger_boards_have_bounded_encoding**: test_b10_larger_boards_have_bounded_encoding (1768.52 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b11_only_public_snapshot_enters_kb**: test_b11_only_public_snapshot_enters_kb (3.45 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles

### Cổng `G-C`: C (DPLL Solver) — [PASS]

- **[PASS] test_c01_empty_contradictory_cases**: C-01: [] SAT, [[]] UNSAT, [x] & [-x] UNSAT, complete model assignment. (0.31 ms)
  - *Bằng chứng / Ghi chú*: Real Module C implementation verified
- **[PASS] test_c03_pdf_example**: C-03: (A or B) and (-A or B): B is criminal, A is unknown. (1.06 ms)
  - *Bằng chứng / Ghi chú*: Real Module C implementation verified

### Cổng `G-P`: C/E (Puzzle Suite) — [PASS]

- **[PASS] P-chain_demo**: Verify puzzle case 'chain_demo' (examples/3x3_chain.json) (40.09 ms)
  - *Bằng chứng / Ghi chú*: Case 'chain_demo' (3x3, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-3x3_classic**: Verify puzzle case '3x3_classic' (examples/3x3_classic.json) (70.13 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_classic' (3x3, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-3x3_extensions**: Verify puzzle case '3x3_extensions' (examples/3x3_extensions.json) (99.21 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_extensions' (3x3, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-4x4_detective**: Verify puzzle case '4x4_detective' (examples/4x4_detective.json) (377.44 ms)
  - *Bằng chứng / Ghi chú*: Case '4x4_detective' (4x4, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-4x4_crossfire**: Verify puzzle case '4x4_crossfire' (examples/4x4_crossfire.json) (580.81 ms)
  - *Bằng chứng / Ghi chú*: Case '4x4_crossfire' (4x4, normal) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-5x5_mastermind**: Verify puzzle case '5x5_mastermind' (examples/5x5_mastermind.json) (1215.33 ms)
  - *Bằng chứng / Ghi chú*: Case '5x5_mastermind' (5x5, stress) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-5x5_syndicate**: Verify puzzle case '5x5_syndicate' (examples/5x5_syndicate.json) (1190.5 ms)
  - *Bằng chứng / Ghi chú*: Case '5x5_syndicate' (5x5, stress) verified: uniqueness=UNIQUE, run=SOLVED
- **[PASS] P-3x3_stuck**: Verify puzzle case '3x3_stuck' (examples/3x3_stuck.json) (10.01 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_stuck' (3x3, stuck) verified: uniqueness=UNIQUE, run=STUCK
- **[PASS] P-3x3_multi**: Verify puzzle case '3x3_multi' (examples/3x3_multi.json) (57.42 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_multi' (3x3, multi_solution) verified: uniqueness=MULTIPLE, run=STUCK
- **[PASS] P-3x3_inconsistent**: Verify puzzle case '3x3_inconsistent' (examples/3x3_inconsistent.json) (10.84 ms)
  - *Bằng chứng / Ghi chú*: Case '3x3_inconsistent' (3x3, inconsistent) verified: uniqueness=UNSAT, run=INCONSISTENT

### Cổng `G-D`: D (Logic Agent) — [BLOCKED]

- **[BLOCKED] G-D-MOD**: Inspect availability of agent.logic_agent (0.0 ms)
  - *Bằng chứng / Ghi chú*: Module 'agent.logic_agent' is not yet implemented or delivered by D (Logic Agent)

### Cổng `G-E`: E (GUI & Main) — [PASS]

- **[PASS] test_e01_controller_load_restart**: E-01: GUIController tải và làm mới màn chơi qua PublicState mà không làm lộ solution. (7.49 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e02_clue_highlighting_and_overlap**: E-02: Chọn lời khai trả về đúng vùng ô tham chiếu và phân tách Trái/Phải/Giao nhau của COMPARE. (20.81 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e03_manual_verdict_outcomes**: E-03: Phân biệt rõ NOT_PROVABLE, CONTRADICTED và ACCEPTED mà không đổi trạng thái khi bị từ chối. (11.47 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e04_hint_and_autosolve_isolation**: E-04: Gợi ý tìm đúng ô bị ép buộc mà không tự lật thẻ; Tự động phá án giải trọn vẹn. (91.17 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e05_clue_formatter_and_layout_metrics**: E-05: Trình dịch lời khai Tiếng Việt hỗ trợ đủ 8 mẫu ClueType và bố cục bàn cờ cân đối. (5.22 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e06_puzzle_suite_and_manifest_verification**: E-06: Toàn bộ 9 màn chơi trong puzzles/index.json khớp tính duy nhất nghiệm và thứ tự suy diễn. (3709.32 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e07_web_gui_vietnamese_screens_and_api**: E-07: Giao diện Web Tiếng Việt có đủ 3 màn hình (Bắt đầu, Kho Hồ Sơ, Bàn cờ 3D) và các endpoint API. (164.97 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified

### Cổng `G-I`: Integration (All Members) — [BLOCKED]

- **[BLOCKED] G-I-MOD**: Inspect availability of Full stack (logic & agent) (0.0 ms)
  - *Bằng chứng / Ghi chú*: Module 'Full stack (logic & agent)' is not yet implemented or delivered by Integration (All Members)
