# Griductive Solver — Sổ tay quyết định thiết kế (docs/decisions.md)

Tài liệu này ghi lại các quyết định thiết kế quan trọng, ranh giới kiến trúc và các lựa chọn kỹ thuật áp dụng cho dự án theo bộ đặc tả v2.

## Quyết định 1: Cấu trúc thư mục và môi trường thực tế
- **Bối cảnh**: Workspace của dự án nằm tại `D:\Academic_document\Term_5_year_3\BaseAI\AI-Project-2\AI_Project2` (đã khởi tạo git tại `AI_Project2`).
- **Quyết định**: 
  - Toàn bộ mã nguồn sản phẩm và kiểm thử nằm trong `Source/` của thư mục `AI_Project2`.
  - Không tạo thêm git repo hoặc project lồng nhau.
  - Các tài liệu đặc tả, tiến độ, bàn giao nằm trong `AI_Project2/docs/`.
  - Các báo cáo nghiệm thu tự động xuất ra `AI_Project2/verification/`.
  - Khung báo cáo môn học nằm tại `AI_Project2/report/`.
  - Môi trường phát triển và kiểm thử chạy từ thư mục `Source/` với Python >= 3.11.

## Quyết định 2: Migration từ chuẩn cũ sang chuẩn v2
- **Dữ liệu `initial_revealed`**: 
  - *Cũ*: Danh sách các ô (ví dụ `["A1"]`).
  - *Mới (v2)*: Mapping cụ thể giữa ô và trạng thái (ví dụ `{"A1": "INNOCENT"}`). Điều này tránh việc Engine phải tra cứu lén solution để biết ô ban đầu là gì.
- **Cấu trúc `Clue`**:
  - *Cũ*: Dùng `params: dict` tự do, thiếu type safety.
  - *Mới (v2)*: Định dạng cấu trúc chặt chẽ với các trường có kiểu tường minh (`region`, `k`, `status`, `parity`, `left`, `right`, `op`). Parser từ chối mọi trường lạ hoặc sai kiểu.
- **Quản lý phiên và snapshot (`StateToken`)**:
  - Tạo `StateToken(session_id, revision)`. Mỗi lần Load hoặc Restart tạo session mới với revision 0. Mỗi lượt verdict được chấp thuận (`ACCEPTED`) tăng revision đúng 1.
  - Rejection (`NOT_PROVABLE`, `CONTRADICTED`) hoặc lỗi (`ReasoningFailure`) không làm tăng revision.
  - Dùng facade `GamePort` để cung cấp cho `LogicAgent` và `GUI`, ngăn chặn việc Agent truy cập các trường private hoặc tham chiếu tới `Puzzle` gốc.

## Quyết định 3: Xử lý 8 mẫu Clue và các Extensions
- **6 Clue cốt lõi**: `FACT`, `SAME`, `DIFFERENT`, `EXACTLY`, `AT_LEAST`, `AT_MOST`.
- **2 Clue mở rộng**:
  1. `PARITY`: Kiểm tra tính chẵn (`EVEN`) hoặc lẻ (`ODD`) của tổng số Criminal trong một vùng.
  2. `COMPARE`: So sánh số lượng Criminal giữa hai vùng (`left`, `right`) qua phép toán so sánh `op` (`EQ`, `LT`, `LE`, `GT`, `GE`).
- **Xử lý vùng chồng lấn trong COMPARE**:
  - Khi hai vùng giao nhau, các ô chung thuộc tập hợp logic được đếm độc lập ở cả hai vế theo đúng ngữ nghĩa toán học.
  - Khi tính `referenced_cells` để highlight giao diện, trả về hợp (union) không trùng lặp các ô được tham chiếu theo thứ tự row-major.

## Quyết định 4: Cơ chế Oracle độc lập cho kiểm thử Phần A
- Phần A cài đặt một Oracle độc lập trong `tests/oracles.py` (sử dụng duyệt không gian trạng thái $2^{N^2}$ cho bàn $3 \times 3$, tức 512 trường hợp).
- Oracle tự kiểm chứng ngữ nghĩa của 8 loại clue mà không phụ thuộc vào `CNFEncoder` của B hay `DPLLSolver` của C.
- Oracle tuyệt đối chỉ phục vụ kiểm thử (test-only), không được đưa vào runtime sản phẩm hoặc fallback.

## Quyết định 5: Runner nghiệm thu đa cấp độ (verify_project)
- Runner hỗ trợ các scope: `a`, `b`, `c`, `d`, `e`, `integration`, `all`.
- Với scope `a`: chỉ yêu cầu các module của A và chạy độc lập hoàn toàn mà không cần B–E.
- Các module chưa có mã nguồn được runner đánh dấu là `BLOCKED` (không được ngụy tạo `PASS`).
- Báo cáo sinh ra dưới dạng `results.json` và `summary.md` tại thư mục nghiệm thu.

