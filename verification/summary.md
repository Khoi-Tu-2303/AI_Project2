# Griductive Solver — Báo cáo nghiệm thu (E)

- **Thời gian thực hiện**: `2026-11-09T09:14:13.365449+00:00`
- **Phạm vi kiểm tra (Scope)**: `e`
- **Yêu cầu mã thật (require_real)**: `True`
- **Kết quả tổng thể**: **PASS** (Exit code: `0`)

## Bảng tổng hợp các cổng nghiệm thu (Gates)

| Cổng (Gate) | Phụ trách | Trạng thái | Passed | Failed | Blocked | Tổng số |
|---|---|---|---:|---:|---:|---:|
| `G-E` | E (GUI & Main) | **PASS** | 7 | 0 | 0 | 7 |

## Chi tiết các bước kiểm tra (Subchecks)

### Cổng `G-E`: E (GUI & Main) — [PASS]

- **[PASS] test_e01_controller_load_restart**: E-01: GUIController tải và làm mới màn chơi qua PublicState mà không làm lộ solution. (5.04 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e02_clue_highlighting_and_overlap**: E-02: Chọn lời khai trả về đúng vùng ô tham chiếu và phân tách Trái/Phải/Giao nhau của COMPARE. (6.71 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e03_manual_verdict_outcomes**: E-03: Phân biệt rõ NOT_PROVABLE, CONTRADICTED và ACCEPTED mà không đổi trạng thái khi bị từ chối. (5.95 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e04_hint_and_autosolve_isolation**: E-04: Gợi ý tìm đúng ô bị ép buộc mà không tự lật thẻ; Tự động phá án giải trọn vẹn. (21.59 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e05_clue_formatter_and_layout_metrics**: E-05: Trình dịch lời khai Tiếng Việt hỗ trợ đủ 8 mẫu ClueType và bố cục bàn cờ cân đối. (2.31 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e06_puzzle_suite_and_manifest_verification**: E-06: Toàn bộ 9 màn chơi trong puzzles/index.json khớp tính duy nhất nghiệm và thứ tự suy diễn. (673.22 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
- **[PASS] test_e07_web_gui_vietnamese_screens_and_api**: E-07: Giao diện Web Tiếng Việt có đủ 3 màn hình (Bắt đầu, Kho Hồ Sơ, Bàn cờ 3D) và các endpoint API. (48.05 ms)
  - *Bằng chứng / Ghi chú*: Real Module E implementation verified
