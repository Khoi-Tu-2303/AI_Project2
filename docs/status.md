# Griductive Solver — Bảng trạng thái tiến độ (docs/status.md)

Cập nhật lần cuối: 2026-11-05
Trạng thái tổng thể: Đã hoàn tất toàn bộ Phần A (A0–A10). G-A đạt PASS. Các cổng B–E sẵn sàng tiếp nhận khi có code.

## 1. Bảng tiến độ các chặng Phần A

| Chặng | Mô tả | Chủ sở hữu | Trạng thái | Gate liên quan | Ghi chú / Bằng chứng |
|---|---|---|---|---|---|
| A0 | Khảo sát repo, inventory, status & decisions | A | DONE | - | Hoàn tất khảo sát cấu trúc thực tế, lập status.md & decisions.md |
| A1 | Shared types, errors, protocols, validation | A | DONE | A-01, A-03, A-06 | Đầy đủ tại `Source/common/` (types, errors, protocols, validation) |
| A2 | Regions và clue references (8 clue types) | A | DONE | A-02, A-04 | Đầy đủ tại `Source/common/regions.py` (hỗ trợ cả 8 loại clue và overlap) |
| A3 | Strict Puzzle & Manifest IO (JSON v2) | A | DONE | A-05, A-07, A-21 | Đầy đủ tại `puzzle_io.py`, `manifest_io.py`, fixture `3x3_chain.json` |
| A4 | GameEngine, GamePort facade, isolation | A | DONE | A-08, A-09, A-10, A-18 | `game_engine.py`, `public_port.py` (cách ly hoàn toàn, StateToken) |
| A5 | Verdict handling, token, deadline, classifier | A | DONE | A-11..A-17 | Xử lý ACCEPTED, NOT_PROVABLE, CONTRADICTED, ReferenceMismatchError |
| A6 | Independent Oracles, Fixtures & Unit Tests | A | DONE | A-19, A-20 | `tests/oracles.py`, toàn bộ 28 tests pytest PASS |
| A7 | Verification Runner, Acceptance Adapters | A | DONE | A-22, G-A | `verify_project.py`, `integration_runner.py` (exit codes 0, 1, 2) |
| A8 | Nghiệm thu B–E (hiện trạng) | A | DONE | G-B, G-C, G-D, G-E, G-I | Khảo sát thực tế: B–E chưa có mã nguồn -> BLOCKED có chủ đích |
| A9 | README, requirements, handoff docs | A | DONE | A-23 | `Source/README.md`, `Source/requirements*.txt`, `docs/handoff-A.md` |
| A10 | Khung báo cáo: formulation, contributions, AI | A | DONE | 4.6 (Đề PDF) | `report/A-formulation.md`, `report/contribution-tracker.md`, v.v. |

## 2. Kiểm kê mã nguồn các module

| Module | Thư mục | Người phụ trách | Trạng thái mã | Chi tiết |
|---|---|---|---|---|
| A (Common & Engine) | `Source/common/`, `Source/engine/` | A | DONE | Đã hoàn thiện toàn bộ theo chuẩn v2 |
| B (CNF & Logic) | `Source/logic/` | B | MISSING | Chưa có mã từ thành viên B (đã có adapter nghiệm thu) |
| C (DPLL & Entailment) | `Source/logic/` | C | MISSING | Chưa có mã từ thành viên C (đã có adapter nghiệm thu) |
| D (Agent & Experiments) | `Source/agent/`, `Source/experiments/` | D | MISSING | Chưa có mã từ thành viên D (đã có adapter nghiệm thu) |
| E (GUI & Entrypoint) | `Source/gui/`, `Source/main.py` | E | MISSING | Chưa có mã từ thành viên E (đã có adapter nghiệm thu) |

## 3. Trạng thái các cổng nghiệm thu (Verification Gates)

| Gate | Mô tả | Trạng thái hiện tại | Bằng chứng / Lý do |
|---|---|---|---|
| G-A | Lõi game, hợp đồng và Engine phần A | **PASS** | 7/7 subchecks PASS qua `verify_project --scope a` (Exit code 0) |
| G-B | CNF encoder và Semantic Evaluator | **BLOCKED** | Thiếu mã nguồn module B (`logic.encoder`) |
| G-C | DPLL Solver và Entailment Checker | **BLOCKED** | Thiếu mã nguồn module C (`logic.dpll`) |
| G-P | Bộ màn chơi và Manifest mở rộng | **BLOCKED** | Thiếu bộ màn từ C (`puzzles`) |
| G-D | LogicAgent, Uniqueness, Experiments | **BLOCKED** | Thiếu mã nguồn module D (`agent.logic_agent`) |
| G-E | GUI và giao diện tương tác | **BLOCKED** | Thiếu mã nguồn module E (`gui.app`) |
| G-I | Tích hợp hệ thống toàn diện | **BLOCKED** | Chờ các module B–E hoàn thiện |
