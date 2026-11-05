# Griductive Solver — Báo cáo nghiệm thu (ALL)

- **Thời gian thực hiện**: `2026-11-05T14:23:09.444077+00:00`
- **Phạm vi kiểm tra (Scope)**: `all`
- **Yêu cầu mã thật (require_real)**: `True`
- **Kết quả tổng thể**: **BLOCKED** (Exit code: `2`)

## Bảng tổng hợp các cổng nghiệm thu (Gates)

| Cổng (Gate) | Phụ trách | Trạng thái | Passed | Failed | Blocked | Tổng số |
|---|---|---|---:|---:|---:|---:|
| `G-A` | A (Core & Engine) | **PASS** | 7 | 0 | 0 | 7 |
| `G-B` | B (CNF Encoder) | **PASS** | 11 | 0 | 0 | 11 |
| `G-C` | C (DPLL Solver) | **BLOCKED** | 0 | 0 | 1 | 1 |
| `G-P` | C (Puzzle Suite) | **BLOCKED** | 0 | 0 | 1 | 1 |
| `G-D` | D (Logic Agent) | **BLOCKED** | 0 | 0 | 1 | 1 |
| `G-E` | E (GUI & Main) | **BLOCKED** | 0 | 0 | 1 | 1 |
| `G-I` | Integration (All Members) | **BLOCKED** | 0 | 0 | 1 | 1 |

## Chi tiết các bước kiểm tra (Subchecks)

### Cổng `G-A`: A (Core & Engine) — [PASS]

- **[PASS] A-01**: Imports and layout boundaries (67.68 ms)
  - *Bằng chứng / Ghi chú*: All common and engine modules import cleanly without external dependencies
- **[PASS] A-02**: Coordinates, bounds, and neighbors (0.32 ms)
  - *Bằng chứng / Ghi chú*: Cell coordinates, bounds, row-major order, and neighbor counts verified for 3x3, 4x4, 5x5
- **[PASS] A-03/04**: Regions and referenced_cells for 8 clues (0.43 ms)
  - *Bằng chứng / Ghi chú*: Region resolution and referenced_cells verified with COMPARE overlap
- **[PASS] A-05/06**: Strict JSON IO and Puzzle structure (2.93 ms)
  - *Bằng chứng / Ghi chú*: Strict JSON parsed and round-tripped fixture 3x3_chain.json
- **[PASS] A-07**: Manifest loader and security (5.32 ms)
  - *Bằng chứng / Ghi chú*: Manifest loader loaded index.json and enforced path security
- **[PASS] A-08..18**: GameEngine lifecycle and verdict transactions (2.09 ms)
  - *Bằng chứng / Ghi chú*: Engine load, verdict submission, token increment, and isolation verified
- **[PASS] A-19**: Sequential chain solving via OracleClassifier (29.66 ms)
  - *Bằng chứng / Ghi chú*: 8-step sequential chain reveal fully verified with independent Oracle

### Cổng `G-B`: B (CNF Encoder) — [PASS]

- **[PASS] test_b01_varmap_bijection**: test_b01_varmap_bijection (0.58 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b02_binary_projection**: test_b02_binary_projection (100.01 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b03_counting_all_bounds**: test_b03_counting_all_bounds (9495.75 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b04_parity_and_region_kinds**: test_b04_parity_and_region_kinds (393.57 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b05_compare_overlap_and_identical_regions**: test_b05_compare_overlap_and_identical_regions (1842.37 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b06_independent_bruteforce_auxiliary_projection**: test_b06_independent_bruteforce_auxiliary_projection (31.52 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b07_kb_rebuild_isolation_and_public_inputs**: test_b07_kb_rebuild_isolation_and_public_inputs (25.44 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b08_standalone_clues_do_not_reuse_auxiliaries**: test_b08_standalone_clues_do_not_reuse_auxiliaries (16.17 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b09_reject_invalid_clues_and_assignments**: test_b09_reject_invalid_clues_and_assignments (0.21 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b10_larger_boards_have_bounded_encoding**: test_b10_larger_boards_have_bounded_encoding (490.9 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles
- **[PASS] test_b11_only_public_snapshot_enters_kb**: test_b11_only_public_snapshot_enters_kb (1.62 ms)
  - *Bằng chứng / Ghi chú*: Real Module B implementation checked against independent oracles

### Cổng `G-C`: C (DPLL Solver) — [BLOCKED]

- **[BLOCKED] G-C-MOD**: Inspect availability of logic.dpll (0.0 ms)
  - *Bằng chứng / Ghi chú*: Module 'logic.dpll' is not yet implemented or delivered by C (DPLL Solver)

### Cổng `G-P`: C (Puzzle Suite) — [BLOCKED]

- **[BLOCKED] G-P-MOD**: Inspect availability of puzzles (requires B & C) (0.0 ms)
  - *Bằng chứng / Ghi chú*: Module 'puzzles (requires B & C)' is not yet implemented or delivered by C (Puzzle Suite)

### Cổng `G-D`: D (Logic Agent) — [BLOCKED]

- **[BLOCKED] G-D-MOD**: Inspect availability of agent.logic_agent (0.0 ms)
  - *Bằng chứng / Ghi chú*: Module 'agent.logic_agent' is not yet implemented or delivered by D (Logic Agent)

### Cổng `G-E`: E (GUI & Main) — [BLOCKED]

- **[BLOCKED] G-E-MOD**: Inspect availability of gui.app / gui.controller (0.0 ms)
  - *Bằng chứng / Ghi chú*: Module 'gui.app / gui.controller' is not yet implemented or delivered by E (GUI & Main)

### Cổng `G-I`: Integration (All Members) — [BLOCKED]

- **[BLOCKED] G-I-MOD**: Inspect availability of Full stack (logic & agent) (0.0 ms)
  - *Bằng chứng / Ghi chú*: Module 'Full stack (logic & agent)' is not yet implemented or delivered by Integration (All Members)
