# Griductive Solver — Bảng theo dõi phân công và đóng góp (report/contribution-tracker.md)

Theo yêu cầu mục 4.6 của đề bài: Ghi nhận phân công công việc và đánh giá mức độ đóng góp trung thực của từng thành viên.

---

## 1. Phân công vai trò trong nhóm 5 người

| Thành viên | Vai trò | Nhiệm vụ chính được giao | Trạng thái hiện tại | Mức độ đóng góp |
|---|---|---|---|:---:|
| **A** | Trưởng nhóm / Lõi game | - Quản lý tiến độ, quy ước chung và shared contracts.<br>- Xây dựng lõi GameEngine, StateToken, snapshot isolation.<br>- Parser JSON strict, validator 8 clue và regions.<br>- Viết test runner, test harness, oracle độc lập. | **100% Hoàn thành** (Đạt Gate G-A) | 100% |
| **B** | Biểu diễn tri thức | - Xây dựng VarMap và ánh xạ biến.<br>- Triển khai CNFEncoder cho 6 core + 2 extensions.<br>- Triển khai SemanticEvaluator độc lập. | **100% Hoàn thành** (Đạt Gate G-B) | 100% |
| **C** | Thuật toán SAT & Dữ liệu | - Cài đặt DPLL Solver (unit prop, backtrack, stats).<br>- Cài đặt EntailmentChecker.<br>- Xây dựng bộ màn puzzle (normal, negative, stress). | **100% Hoàn thành** (Đạt Gate G-C, G-P) | 100% |
| **D** | Tác tử suy luận & Thực nghiệm | - Cài đặt LogicAgent không đoán (no-guess).<br>- Deduction loop, Hint, Uniqueness check offline.<br>- Thiết lập pipeline thực nghiệm và ghi số liệu Mục 4.5. | **100% Hoàn thành** (Đạt Gate G-D) | 100% |
| **E** | Giao diện & Tích hợp | - Thiết kế giao diện đồ họa Web Noir Tiếng Việt 3D.<br>- Tích hợp GUIController, Hint, AutoSolve, Highlight Clue.<br>- File khởi chạy main.py, kịch bản video demo. | **100% Hoàn thành** (Đạt Gate G-E, G-I) | 100% |

---

## 2. Ghi nhận đóng góp thực tế toàn diện dự án

- **Thành viên A (Phần A)**:
  - Triển khai toàn bộ mã nguồn của gói `common/` (`types.py`, `errors.py`, `protocols.py`, `regions.py`, `validation.py`, `puzzle_io.py`, `manifest_io.py`).
  - Triển khai lõi `engine/` (`game_engine.py`, `public_port.py`).
  - Xây dựng bộ kiểm thử độc lập `tests/` gồm 28 test cases và Oracle chân trị độc lập (`oracles.py`).
  - Xây dựng bộ công cụ nghiệm thu `tools/` (`verify_project.py`, `integration_runner.py`).

- **Thành viên B (Phần B)**:
  - Triển khai `logic/varmap.py`, `logic/encoder.py`, `logic/evaluator.py`.
  - Mã hóa chuẩn xác 8 loại clue (Sequential Counter cho counting, XOR chain cho PARITY, overlap cho COMPARE).
  - Vượt qua 11 kiểm tra nghiệm thu Gate `G-B` và tài liệu lý thuyết `report/B-encoding.md`.

- **Thành viên C (Phần C)**:
  - Triển khai `logic/dpll.py`, `logic/entailment.py`, `tests/test_solver.py`.
  - Bộ giải DPLL SAT đầy đủ Unit Propagation, Conflict Detection, Backtracking và thống kê `SolveStats`.
  - Thuật toán `check_uniqueness` và phân loại ô tối ưu với nhân chứng model.

- **Thành viên D (Phần D & Thực nghiệm)**:
  - Triển khai `agent/logic_agent.py`, `agent/uniqueness.py`, `tests/test_agent_acceptance.py`.
  - Xây dựng kịch bản thực nghiệm `experiments/run_experiments.py` đo lường đầy đủ 6 chỉ số trên 10 hồ sơ vụ án.
  - Vượt qua kiểm định Gate `G-D`.

- **Thành viên E (Phần E & Tích hợp)**:
  - Xây dựng giao diện Web Noir Detective Tiếng Việt tại `gui/web/` với bảng cờ 3D, hiệu ứng hồ sơ manila, ghim polaroid.
  - Triển khai `gui/controller.py`, `gui/clue_formatter.py`, `gui/web_server.py`, `main.py`.
  - Vượt qua kiểm định Gate `G-E` và `G-I`.
