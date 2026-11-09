# Griductive Solver — Mã nguồn dự án (Source)

Dự án phát triển hệ thống giải bài toán suy luận logic **Griductive** dựa trên logic mệnh đề, mã hóa CNF và bộ giải DPLL SAT (môn CSC14003 - Nhập môn Trí tuệ Nhân tạo).

---

## 1. Yêu cầu môi trường

- **Ngôn ngữ**: Python >= 3.11
- **Hệ điều hành**: Windows, Linux, macOS
- **Môi trường ảo khuyến nghị**: `venv`

### Cài đặt môi trường

Từ thư mục gốc dự án:

```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# Hoặc trên Linux/macOS:
# source .venv/bin/activate

# Cài đặt công cụ kiểm thử (Dev dependencies)
pip install -r Source/requirements-dev.txt
```

---

## 2. Cấu trúc thư mục mã nguồn

```text
Source/
  common/                   # Module A: Types, errors, protocols, regions, IO, validation
    types.py                # Dataclasses, Enums, FrozenDict
    errors.py               # Exception hierarchy (PuzzleError, ReasoningFailure, etc.)
    protocols.py            # Interfaces Classifier, GamePort
    regions.py              # Tọa độ, vùng và referenced_cells (8 loại clue)
    validation.py           # Bộ kiểm tra tính hợp lệ dữ liệu và clue
    puzzle_io.py            # Parser JSON nghiêm ngặt & ghi file atomic
    manifest_io.py          # Parser & validator manifest các bộ puzzle
  engine/                   # Module A: Lõi trò chơi & phân phối quyền
    game_engine.py          # Quản lý vòng đời trò chơi, StateToken, commit verdict
    public_port.py          # Facade GamePort chỉ mở 2 phương thức công khai
  logic/                    # B đã có varmap/encoder/evaluator; C chưa có DPLL/Entailment
  agent/                    # Module D: LogicAgent, Uniqueness, Deduction Loop
  gui/                      # Module E: Giao diện đồ họa người dùng
  puzzles/                  # Bộ câu đố & màn chơi thử nghiệm
    examples/3x3_chain.json # Fixture mẫu chuẩn v2
    index.json              # Manifest đăng ký các ca kiểm thử
  tools/                    # Công cụ chạy nghiệm thu & đo lường
    verify_project.py       # CLI runner nghiệm thu theo cổng
    integration_runner.py   # Máy chạy và tổng hợp kết quả
  tests/                    # Bộ kiểm thử đơn vị & chấp nhận
    oracles.py              # Oracle độc lập duyệt chân trị (test-only)
    test_regions.py         # Kiểm tra tọa độ, vùng, 8 clue
    test_puzzle_io.py       # Kiểm tra JSON parser strict & ghi atomic
    test_manifest_io.py     # Kiểm tra manifest & chống path traversal
    test_engine.py          # Kiểm tra GameEngine, token, snapshot, verdict
    test_boundary.py        # Kiểm tra chuỗi suy luận Oracle & cách ly
    test_contracts.py       # Kiểm tra hợp đồng kiểu và cấu trúc puzzle
    test_harness_faults.py  # Kiểm tra độ tin cậy của test harness
    test_*_acceptance.py    # Các adapter nghiệm thu cho B, C, D, E
```

---

## 3. Chạy kiểm thử và nghiệm thu

Tất cả các lệnh được chạy từ thư mục `Source/`:

```bash
cd Source

# 1. Chạy toàn bộ kiểm thử đơn vị với pytest
python -m pytest tests -v

# 2. Chạy nghiệm thu riêng phần A (Lõi game & Engine)
python -m tools.verify_project --scope a --output ../verification

# 3. Chạy nghiệm thu toàn bộ hệ thống (khi ghép mã B–E)
python -m tools.verify_project --scope all --require-real --output ../verification
```

### Mã thoát (Exit Codes) của verify_project:
- `0`: Tất cả các cổng trong phạm vi đều đạt (**PASS**).
- `1`: Có ít nhất một kiểm tra bị lỗi (**FAIL**).
- `2`: Không có kiểm tra nào FAIL, nhưng có module chưa có mã nguồn (**BLOCKED**).

---

## 4. Định dạng dữ liệu Puzzle (JSON Schema v2)

Mỗi file puzzle là file JSON UTF-8 với cấu trúc chuẩn:

```json
{
  "schema_version": 2,
  "id": "3x3_chain",
  "n": 3,
  "characters": [
    {"cell": "A1", "name": "Alice", "profession": "Baker"},
    ...
  ],
  "clues": {
    "A1": {"id": "c_A1", "type": "FACT", "cells": ["B1"], "status": "CRIMINAL"},
    ...
  },
  "initial_revealed": {
    "A1": "INNOCENT"
  },
  "solution": {
    "A1": "INNOCENT",
    ...
  }
}
```

---

## 5. Danh sách 8 loại Clue hỗ trợ

1. `FACT`: Xác nhận status của 1 ô (`cells: [cell]`, `status: CRIMINAL/INNOCENT`).
2. `SAME`: Hai ô có cùng status (`cells: [cell1, cell2]`).
3. `DIFFERENT`: Hai ô có status khác nhau (`cells: [cell1, cell2]`).
4. `EXACTLY`: Có đúng $k$ người là Criminal trong vùng (`region`, `k`).
5. `AT_LEAST`: Có ít nhất $k$ người là Criminal trong vùng (`region`, `k`).
6. `AT_MOST`: Có nhiều nhất $k$ người là Criminal trong vùng (`region`, `k`).
7. `PARITY`: Tính chẵn lẻ của tổng Criminal trong vùng (`region`, `parity: EVEN/ODD`).
8. `COMPARE`: So sánh số Criminal giữa 2 vùng (`left`, `right`, `op: EQ/LT/LE/GT/GE`).

## 6. Phần B đã triển khai

```python
from logic import CNFEncoder

# state lấy từ GamePort.get_public_state()
encoder = CNFEncoder(state.n)
kb = encoder.build_kb(tuple(state.revealed_clues.values()), state.known_statuses)
print(kb.num_primary, kb.num_aux, kb.num_clauses)
# Phần C sẽ nhận kb.clauses và kb.num_vars để chạy SAT.
```

CNFEncoder hỗ trợ đủ 8 clue bằng mạch đếm ngưỡng và chuỗi XOR.
SemanticEvaluator(n) đánh giá clue trực tiếp trên assignment đầy đủ, độc lập với encoder.
Chạy `python -m tools.verify_project --scope b --require-real` để nghiệm thu B.
Xem `../docs/handoff-B.md` và `../report/B-encoding.md` để biết API và phép biến đổi.


---

## 7. Khởi chạy Giao diện Web Tiếng Việt (`main.py`)

Chương trình không yêu cầu cài đặt thêm thư viện ngoài cho lúc chạy (chỉ sử dụng thư viện chuẩn Python 3.11+):

```bash
# Chạy từ thư mục gốc dự án (tự động mở trình duyệt tại http://127.0.0.1:8080):
python Source/main.py

# Hoặc chạy từ bên trong thư mục Source/:
cd Source
python main.py

# Tùy chọn dòng lệnh:
python main.py --port 8080                                   # Đổi cổng Web Server
python main.py --puzzle puzzles/examples/4x4_detective.json  # Mở sẵn một hồ sơ cụ thể
python main.py --desktop                                     # Mở giao diện Tkinter Desktop
```
