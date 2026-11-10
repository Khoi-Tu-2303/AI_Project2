# Báo Cáo Thực Nghiệm & Đo Lường Hệ Thống Griductive Solver (Mục 4.5)

Được sinh tự động từ kịch bản đo đạc thực nghiệm trên bộ dữ liệu kiểm thử chuẩn của dự án.

## 1. Bảng số liệu tổng hợp (Benchmark Table)

| Hồ sơ (Case ID) | Kích thước | Phân loại | Nghiệm | Kết quả | Bước lật | Biến (Pri/Aux) | Mệnh đề CNF | Số cuộc gọi SAT | Decisions | Propagations | Backtracks | Thời gian (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `chain_demo` | 3x3 | normal | UNIQUE | **SOLVED** | 8 | 9/0 | 9 | 44 | 140 | 168 | 0 | 4.51 |
| `3x3_classic` | 3x3 | normal | UNIQUE | **SOLVED** | 7 | 9/43 | 146 | 35 | 91 | 112 | 0 | 10.27 |
| `3x3_extensions` | 3x3 | normal | UNIQUE | **SOLVED** | 7 | 9/56 | 186 | 34 | 62 | 100 | 0 | 11.96 |
| `4x4_detective` | 4x4 | normal | UNIQUE | **SOLVED** | 14 | 16/157 | 499 | 119 | 595 | 691 | 0 | 61.64 |
| `4x4_crossfire` | 4x4 | normal | UNIQUE | **SOLVED** | 14 | 16/172 | 545 | 117 | 544 | 638 | 0 | 85.98 |
| `5x5_mastermind` | 5x5 | stress | UNIQUE | **SOLVED** | 23 | 25/244 | 777 | 299 | 2890 | 3094 | 0 | 206.06 |
| `5x5_syndicate` | 5x5 | stress | UNIQUE | **SOLVED** | 23 | 25/292 | 924 | 299 | 3751 | 4002 | 0 | 254.65 |
| `3x3_stuck` | 3x3 | stuck | UNIQUE | **STUCK** | 1 | 9/9 | 37 | 9 | 49 | 56 | 0 | 1.06 |
| `3x3_multi` | 3x3 | multi_solution | MULTIPLE | **STUCK** | 6 | 9/7 | 32 | 39 | 139 | 166 | 0 | 7.82 |
| `3x3_inconsistent` | 3x3 | inconsistent | NONE | **INCONSISTENT** | 0 | 9/5 | 24 | 0 | 0 | 0 | 0 | 0.5 |

## 2. Phân tích nhận xét thực nghiệm

### 2.1. Đánh giá tính co giãn và hiệu năng thuật toán
- **Bảng kích thước 3×3**: Thời gian giải mã cực kỳ nhanh (< 15 ms). Thuật toán giải quyết mượt mà với 0 lần quay lui (0 backtracks) nhờ sức mạnh của lan truyền đơn vị (Unit Propagation).
- **Bảng kích thước 4×4 (16 ô)**: Đầy đủ các mệnh đề mở rộng `PARITY` và `COMPARE`. Số lượng mệnh đề tăng tương ứng theo kích thước miền tham chiếu ($O(m \cdot k)$), tuy nhiên bộ giải DPLL vẫn hoàn thành trong ~100 ms.
- **Đại án 5×5 (Stress test 25 ô)**: Hệ thống chịu tải xuất sắc trên cả hai hồ sơ `5x5_mastermind` và `5x5_syndicate`. Thuật toán tìm ra chuỗi 24 bước lật bài tất yếu trọn vẹn chỉ trong ~250–300 ms.

### 2.2. Kiểm thử an toàn trên các trường hợp đặc biệt (Negative Cases)
- **Bế tắc (`3x3_stuck`)**: Agent chỉ lật các ô chứng minh được và dừng lại an toàn (`STUCK`), kiên quyết **không đoán mò** khi tri thức rơi vào trạng thái `UNKNOWN`.
- **Đa nghiệm (`3x3_multi`)**: Thuật toán `check_uniqueness` phát hiện chính xác trạng thái `MULTIPLE` và trích xuất đủ 2 nghiệm làm bằng chứng.
- **Mâu thuẫn (`3x3_inconsistent`)**: Phát hiện ngay lập tức KB gốc `INCONSISTENT` (UNSAT), không đưa ra phán quyết sai lệch.
