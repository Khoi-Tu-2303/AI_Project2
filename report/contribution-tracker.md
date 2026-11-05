# Griductive Solver — Bảng theo dõi phân công và đóng góp (report/contribution-tracker.md)

Theo yêu cầu mục 4.6 của đề bài: Ghi nhận phân công công việc và đánh giá mức độ đóng góp trung thực của từng thành viên.

---

## 1. Phân công vai trò trong nhóm 5 người

| Thành viên | Vai trò | Nhiệm vụ chính được giao | Trạng thái hiện tại |
|---|---|---|---|
| **A** | Trưởng nhóm / Lõi game | - Quản lý tiến độ, quy ước chung và shared contracts.<br>- Xây dựng lõi GameEngine, StateToken, snapshot isolation.<br>- Parser JSON strict, validator 8 clue và regions.<br>- Viết test runner, test harness, oracle độc lập. | **100% Hoàn thành Phần A** (Đạt Gate G-A) |
| **B** | Biểu diễn tri thức | - Xây dựng VarMap và ánh xạ biến.<br>- Triển khai CNFEncoder cho 6 core + 2 extensions.<br>- Triển khai SemanticEvaluator độc lập. | Đang chờ bàn giao mã nguồn (Chờ Gate G-B) |
| **C** | Thuật toán SAT & Dữ liệu | - Cài đặt DPLL Solver (unit prop, backtrack, ledger).<br>- Cài đặt EntailmentChecker.<br>- Xây dựng bộ màn puzzle (normal, negative, stress). | Đang chờ bàn giao mã nguồn (Chờ Gate G-C, G-P) |
| **D** | Tác tử suy luận | - Cài đặt LogicAgent không đoán (no-guess).<br>- Deduction loop, Hint, Uniqueness check offline.<br>- Thiết lập pipeline thực nghiệm và ghi số liệu. | Đang chờ bàn giao mã nguồn (Chờ Gate G-D) |
| **E** | Giao diện & Đa phương tiện | - Thiết kế giao diện đồ họa GUI (Board, Clues, Highlight).<br>- Tích hợp GamePort và LogicAgent vào GUI.<br>- Biên tập video thuyết minh demo sản phẩm. | Đang chờ bàn giao mã nguồn (Chờ Gate G-E) |

---

## 2. Ghi nhận đóng góp thực tế giai đoạn 1 (Phần A)

- **Thành viên A**:
  - Triển khai toàn bộ mã nguồn của gói `common/` (`types.py`, `errors.py`, `protocols.py`, `regions.py`, `validation.py`, `puzzle_io.py`, `manifest_io.py`).
  - Triển khai lõi `engine/` (`game_engine.py`, `public_port.py`).
  - Xây dựng bộ kiểm thử độc lập `tests/` gồm 28 test cases và Oracle chân trị độc lập (`oracles.py`).
  - Xây dựng bộ công cụ nghiệm thu `tools/` (`verify_project.py`, `integration_runner.py`).
  - Xây dựng tài liệu hướng dẫn bàn giao `docs/handoff-A.md` và khung báo cáo kỹ thuật.
  - Tỷ lệ hoàn thành công việc được giao của phần A: **100%**.

- **Các thành viên B, C, D, E**:
  - Đã thống nhất tài liệu hợp đồng và giao diện v2 (`06-INTERFACES.md`).
  - Sẽ tiếp tục cập nhật tỷ lệ đóng góp chi tiết khi nộp mã nguồn và vượt qua các cổng kiểm thử G-B, G-C, G-D, G-E, G-I tương ứng.

