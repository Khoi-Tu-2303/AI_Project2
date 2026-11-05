# Griductive Solver — Tài liệu bàn giao phần A (docs/handoff-A.md)

Tài liệu này hướng dẫn chi tiết cách các thành viên B, C, D, E sử dụng nền tảng Phần A đã hoàn thiện, nhập khẩu (import) các kiểu dữ liệu dùng chung, và tự kiểm tra mã nguồn của mình trước khi nghiệm thu tích hợp.

Cập nhật 2026-11-05: phần B đã có triển khai và G-B PASS. API thực tế, constructor và hướng dẫn ghép với C/D xem [handoff-B.md](handoff-B.md). Các mục "cần cài đặt" dưới đây giữ lại phân công ban đầu.

---

## 1. Bàn giao cho Thành viên B (Biểu diễn logic, CNF Encoder & Evaluator)

### Gói cần import
```python
from common.types import (
    Cell, Status, Classification, Clue, ClueType, Region, RegionKind, 
    Parity, CompareOp, status_to_bool, bool_to_status
)
from common.regions import all_cells, resolve_region, cell_to_index, index_to_cell
from common.validation import validate_clue
```

### Các lớp và phương thức cần cài đặt trong `Source/logic/`
1. `VarMap` trong `logic/varmap.py`:
   - `__init__(self, n: int)`: Thiết lập ánh xạ song ánh giữa $n^2$ ô và các biến nguyên $1 \dots n^2$.
   - `var(self, cell: Cell) -> int`: Trả về biến chính $1 \dots n^2$.
   - `cell(self, var: int) -> Cell`: Ánh xạ ngược (từ chối biến phụ).
   - `new_aux(self) -> int`: Cấp phát biến phụ mới tăng dần.
   - `reset_aux(self) -> None`: Đặt lại vùng biến phụ cho mỗi lần dựng KB mới.
2. `CNFEncoder` trong `logic/encoder.py`:
   - `encode_clue(self, clue: Clue) -> list[list[int]]`: Mã hóa 8 loại clue (6 core + PARITY + COMPARE) sang CNF.
   - `unit_clause(self, cell: Cell, status: Status) -> list[int]`: Tạo mệnh đề đơn vị ($C_i$ nếu Criminal, $\neg C_i$ nếu Innocent).
   - `build_kb(self, clues: Sequence[Clue], known_statuses: Mapping[Cell, Status]) -> KnowledgeBase`.
3. `SemanticEvaluator` trong `logic/evaluator.py`:
   - `evaluate(self, clue: Clue, assignment: Mapping[Cell, bool]) -> bool`: Đánh giá trực tiếp giá trị chân trị mà không gọi encoder.

### Lệnh tự kiểm tra của B
```bash
cd Source
python -m pytest tests/test_encoder_acceptance.py -v
python -m tools.verify_project --scope b --require-real --output ../verification
```

---

## 2. Bàn giao cho Thành viên C (DPLL Solver, Entailment & Puzzle Suite)

### Gói cần import
```python
from common.types import Cell, Status, Classification, ReasoningStatus
```

### Các lớp và phương thức cần cài đặt trong `Source/logic/`
1. `DPLLSolver` trong `logic/dpll.py`:
   - `solve(self, clauses, num_vars, assumptions=(), *, deadline=None, purpose="GAMEPLAY") -> SolveResult`.
   - Lưu sổ cái `ledger: tuple[SolveCall, ...]`.
   - Hỗ trợ deadline kiểu `time.monotonic()` xuyên suốt đệ quy.
2. `EntailmentChecker` trong `logic/entailment.py`:
   - `classify_all(self, kb, cells, *, deadline=None) -> EntailmentBatch`.
   - Luôn kiểm tra tính thỏa được của KB gốc (BASE) trước. Nếu BASE UNSAT trả về `INCONSISTENT`.
3. Bộ màn trong `Source/puzzles/`:
   - Đăng ký các màn 3x3, 4x4 (và tùy chọn 5x5) vào `Source/puzzles/index.json`.

### Lệnh tự kiểm tra của C
```bash
cd Source
python -m pytest tests/test_solver_acceptance.py -v
python -m tools.verify_project --scope c --require-real --output ../verification
```

---

## 3. Bàn giao cho Thành viên D (LogicAgent, Uniqueness & Thí nghiệm)

### Gói cần import
```python
from common.protocols import GamePort
from common.types import PublicState, ClassificationReport, Hint, StateToken, Status, Cell
```

### Ranh giới kiến trúc quan trọng cho D:
- **Tuyệt đối không nhận hoặc import `Puzzle` ẩn, `solution`, hoặc `GameEngine`**.
- Chỉ nhận `GamePort` với 2 thao tác: `get_public_state()` và `submit_verdict()`.
- Phương thức `classify_state(self, state: PublicState, *, deadline=None) -> ClassificationReport`:
  Hàm suy luận thuần túy dựa trên snapshot public.
- `step(self, port: GamePort, *, deadline=None) -> StepResult`:
  1. Lấy snapshot từ port.
  2. Phân loại trạng thái; nếu có ô forced, chọn ô đầu tiên theo thứ tự row-major.
  3. Gửi verdict kèm `expected_token=state.token`.
- `check_uniqueness(clues, n, *, solver=None, deadline=None)`:
  Kiểm tra tính duy nhất ngoại tuyến trên toàn bộ clue mà không nhận hidden solution.

### Lệnh tự kiểm tra của D
```bash
cd Source
python -m pytest tests/test_agent_acceptance.py -v
python -m tools.verify_project --scope d --require-real --output ../verification
```

---

## 4. Bàn giao cho Thành viên E (Giao diện người dùng & main.py)

### Gói cần import
```python
from engine.game_engine import GameEngine
from common.regions import referenced_cells
from common.types import PublicState, Status, Cell
```

### Ranh giới cho GUI:
- Controller nắm `GameEngine` để thực hiện `load(path)` và `restart()`.
- View chỉ nhận `PublicState`. Không bao giờ yêu cầu Engine cung cấp solution ẩn để hiển thị.
- Tính năng **Highlight Clue**: Khi người chơi chọn 1 clue đã lộ, gọi `referenced_cells(clue, n)` từ `common.regions` để nhận danh sách các ô cần làm nổi bật (hỗ trợ đầy đủ cả 8 loại clue và các vùng chồng lấn trong `COMPARE`).
- **Hint**: Gọi `agent.hint(state)`. Hint chỉ gợi ý ô và clue liên quan, không tự động lật bài.
- **Auto Solve**: Lặp qua `agent.step(port)` có cập nhật tiến trình trên giao diện, tránh làm đóng băng (freeze) UI.

### Lệnh tự kiểm tra của E
```bash
cd Source
python -m pytest tests/test_gui_acceptance.py -v
python -m tools.verify_project --scope e --require-real --output ../verification
```

---

## 5. Lệnh nghiệm thu chung toàn dự án

Khi tất cả các module B, C, D, E đã hoàn thành và sẵn sàng ghép nối:

```bash
cd Source
python -m tools.verify_project --scope all --require-real --output ../verification
```

Lệnh này sẽ chạy kiểm tra toàn diện và chỉ trả về Exit Code `0` khi tất cả các cổng G-A, G-B, G-C, G-P, G-D, G-E, G-I đều đạt **PASS**.

