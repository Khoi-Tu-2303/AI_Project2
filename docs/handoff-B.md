# Phần B: Biểu diễn tri thức và CNF

Phần B đã có `logic.varmap.VarMap`, `logic.encoder.CNFEncoder` và
`logic.evaluator.SemanticEvaluator`. Chỉ dùng thư viện chuẩn Python khi chạy;
pytest cần cho bộ nghiệm thu. Chưa triển khai DPLL hoặc agent.

## Dùng từ phần C/D

```python
from logic import CNFEncoder, SemanticEvaluator, VarMap
from common.types import KnowledgeBase

# state là PublicState lấy từ GamePort, không phải Puzzle đầy đủ.
encoder = CNFEncoder(state.n)  # hoặc CNFEncoder(VarMap(state.n))
kb = encoder.build_kb(tuple(state.revealed_clues.values()), state.known_statuses)
# Solver C sẽ nhận kb.clauses, kb.num_vars.
# kb.num_primary, kb.num_aux, kb.num_clauses phục vụ thống kê.
```

Biến chính `1..n*n` theo row-major, True là Criminal. Literal âm là phủ định.
CNF `[]` nghĩa là True; `[[]]` nghĩa là False. `VarMap.cell()` chỉ nhận biến
chính dương, không nhận literal âm hoặc biến phụ.

`build_kb()` reset biến phụ trước mỗi lần dựng lại KB, trả snapshot tuple bất
biến. Các lần `encode_clue()` riêng lẻ tiếp tục cấp biến phụ, nên có thể ghép
kết quả mà không đụng ID. Sau khi reset/build lại, không ghép với CNF cũ dùng
chung VarMap; giữ toàn bộ snapshot KnowledgeBase cũ nếu cần truy vấn cũ.

SemanticEvaluator(n).evaluate(clue, assignment) yêu cầu đầy đủ n*n ô với giá trị
bool thật. Nó đếm và so sánh trực tiếp, không gọi encoder hoặc solver.

## Cách mã hóa

- FACT: unit clause; SAME: `[-a,b]` và `[a,-b]`;
  DIFFERENT: `[a,b]` và `[-a,-b]`.
- Counting: mạch đếm ngưỡng bằng quy hoạch động, mô tả trong
  `report/B-encoding.md`. Có biến phụ và số cổng O(m*k).
- PARITY: chuỗi XOR, tuyến tính theo số ô; ép đầu ra True cho ODD, False cho EVEN.
- COMPARE: triệt tiêu phần giao hai vùng rồi chuyển về ràng buộc đếm trên
  literal dương/âm. Hỗ trợ EQ, LT, LE, GT, GE và hai vùng giống nhau.

## Kiểm chứng

Từ Source:

```bash
python -m pytest tests/test_encoder_acceptance.py -v
python -m tools.verify_project --scope b --require-real --output ../verification
python -m tools.verify_project --scope all --require-real --output ../verification
```

G-B chạy các kiểm tra thật: tất cả 512 assignment trên bảng 3x3 cho các clue
kiểm thử; đối chiếu evaluator với oracle độc lập; kiểm tra tồn tại biến phụ bằng
vét cạn CNF ở ca nhỏ và lan truyền đơn vị với đầu vào cố định trên các mạch lớn.
Thử mẫu 4x4/5x5 kiểm tra kích thước và ngữ nghĩa, không phải vét cạn toàn bộ.
Fault injection bỏ các mệnh đề phải làm G-B FAIL. Các cổng C–E còn là khung
BLOCKED và cần triển khai khi bàn giao module tương ứng.
