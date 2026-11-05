# Griductive Solver — Phụ lục Sử dụng Trí tuệ Nhân tạo (report/ai-usage.md)

Theo yêu cầu mục 4.6 của đề bài: Ghi nhận trung thực việc sử dụng các công cụ Generative AI (LLMs) trong quá trình thực hiện đồ án, các prompt đã sử dụng và cách thức kiểm chứng tính đúng đắn của mã nguồn.

---

## 1. Mục đích sử dụng AI

Nhóm sử dụng công cụ AI (Antigravity / Gemini) làm trợ lý lập trình (Pair Programmer) phục vụ các mục tiêu sau:
1. **Thiết kế kiến trúc hệ thống**: Tham khảo các mẫu thiết kế hướng đối tượng (OOP Design Patterns), đặc biệt là mô hình tách biệt quyền hạn `GameEngine` và `GamePort` facade.
2. **Khung mã nguồn chuẩn (Boilerplate)**: Sinh các dataclass chuẩn (`types.py`), cây phân cấp ngoại lệ (`errors.py`) và các bộ kiểm thử tự động.
3. **Xây dựng Oracle độc lập**: Hỗ trợ hiện thực thuật toán vét cạn chân trị ($2^{n^2}$ trạng thái) trong `tests/oracles.py` để làm cơ sở kiểm chứng đối chiếu độc lập với các thuật toán của các thành viên khác.

---

## 2. Nhật ký Prompt chính đã sử dụng

### Prompt 1: Khởi tạo và thiết kế hợp đồng Phần A
- **Vai trò gán cho AI**: Chuyên gia thiết kế kiến trúc phần mềm AI, phụ trách Phần A của dự án Griductive Solver.
- **Nội dung tóm tắt**: Đọc đề bài `AI - Project 2.pdf` và bộ đặc tả kỹ thuật v2 (`06-INTERFACES.md`, `07-VERIFICATION.md`, `08-MASTER-PROMPT-A.md`), triển khai toàn bộ các module của Phần A theo đúng quy ước v2.
- **Kết quả đầu ra**: Các module `common/types.py`, `errors.py`, `protocols.py`, `regions.py`, `validation.py`, `puzzle_io.py`, `manifest_io.py`, `game_engine.py`, `public_port.py`.

### Prompt 2: Xây dựng bộ kiểm thử và Oracle độc lập
- **Nội dung tóm tắt**: Viết bộ test `tests/` gồm ít nhất 20 test cases bao quát toàn bộ yêu cầu G-A (A-01 đến A-22), cài đặt Oracle đánh giá chân trị của 8 loại clue mà không phụ thuộc vào solver hay encoder.
- **Kết quả đầu ra**: File `tests/oracles.py` và 8 file test đơn vị tương ứng.

---

## 3. Quy trình Kiểm chứng của Con người (Human Verification)

Toàn bộ mã nguồn sinh ra bởi AI đều được nhóm kiểm tra lại nghiêm ngặt theo quy trình:
1. **Kiểm tra tính tuân thủ quy định đề bài**:
   - Đảm bảo không sử dụng thư viện SAT solver bên ngoài (như Z3, PySAT) để giải bài.
   - Đảm bảo thuật toán chính tự cài đặt.
   - Đảm bảo Agent không được cung cấp solution ẩn hay clue chưa lộ.
2. **Chạy kiểm thử tự động**:
   - Chạy 100% test cases với `pytest` (28/28 passed).
   - Chạy `tools.verify_project` để xác nhận tính toàn vẹn của StateToken, snapshot isolation và atomicity của các giao dịch verdict.
   - Thử nghiệm chèn lỗi nhân tạo (Fault Injection) để kiểm chứng rằng harness phát hiện được lỗi khi có sai phạm logic.

