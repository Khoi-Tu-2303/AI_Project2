"""Trình dịch lời khai logic mệnh đề sang Tiếng Việt tự nhiên & Công thức Toán học / CNF (Module E)."""

from __future__ import annotations

from typing import Any

from common.regions import resolve_region
from common.types import (
    Clue,
    ClueType,
    CompareOp,
    Parity,
    PublicState,
    Region,
    RegionKind,
    Status,
)
from logic.encoder import CNFEncoder


def _char_label(cell: str, state: PublicState | None, *, compact: bool = False) -> str:
    """Hiển thị tên nhân vật kèm tọa độ, ví dụ 'An (A1)'."""
    if state is None:
        return cell
    for ch in state.characters:
        if ch.cell == cell:
            return f"{ch.name} ({cell})"
    return cell


def format_region(region: Region, state: PublicState | None = None, *, compact: bool = False) -> str:
    """Mô tả vùng tham chiếu (Region.kind + Region.arg) bằng Tiếng Việt tự nhiên."""
    if region.kind is RegionKind.ROW:
        return f"Hàng {region.arg}"
    if region.kind is RegionKind.COL:
        return f"Cột {region.arg}"
    if region.kind is RegionKind.NEIGHBORS:
        center = str(region.arg)
        if compact:
            return f"các ô xung quanh {center}"
        who = _char_label(center, state, compact=True)
        return f"các ô xung quanh {who}"
    if region.kind is RegionKind.EXPLICIT:
        cells = tuple(region.arg) if isinstance(region.arg, (tuple, list)) else ()
        if compact or len(cells) > 3:
            return "nhóm ô {" + ", ".join(cells) + "}"
        labels = [_char_label(c, state, compact=True) for c in cells]
        return "nhóm {" + ", ".join(labels) + "}"
    return "vùng chỉ định"


def format_clue(clue: Clue, state: PublicState | None = None, *, compact: bool = False) -> str:
    """Chuyển đổi cấu trúc Clue sang câu lời khai Tiếng Việt tự nhiên, kết thúc bằng dấu chấm."""
    ctype = clue.type

    if ctype is ClueType.FACT:
        cell = clue.cells[0] if clue.cells else "?"
        who = _char_label(cell, state, compact=compact)
        st_vn = "là Thủ phạm" if clue.status is Status.CRIMINAL else "là người Vô tội"
        return f"Tôi khẳng định {who} chắc chắn {st_vn}."

    if ctype is ClueType.SAME:
        c1 = clue.cells[0] if clue.cells and len(clue.cells) > 0 else "?"
        c2 = clue.cells[1] if clue.cells and len(clue.cells) > 1 else "?"
        w1 = _char_label(c1, state, compact=compact)
        w2 = _char_label(c2, state, compact=compact)
        if compact:
            return f"{w1} và {w2} cùng phe (cùng Vô tội hoặc cùng Thủ phạm)."
        return f"{w1} và {w2} có cùng thân phận (cả hai cùng Vô tội hoặc cùng là Thủ phạm)."

    if ctype is ClueType.DIFFERENT:
        c1 = clue.cells[0] if clue.cells and len(clue.cells) > 0 else "?"
        c2 = clue.cells[1] if clue.cells and len(clue.cells) > 1 else "?"
        w1 = _char_label(c1, state, compact=compact)
        w2 = _char_label(c2, state, compact=compact)
        if compact:
            return f"{w1} và {w2} khác phe (1 Vô tội, 1 Thủ phạm)."
        return f"{w1} và {w2} đối lập nhau: một người Vô tội và người kia là Thủ phạm."

    if ctype is ClueType.EXACTLY:
        assert clue.region is not None
        reg_str = format_region(clue.region, state, compact=compact)
        k = int(clue.k or 0)
        if k == 0:
            return f"Trong {reg_str} hoàn toàn không có Thủ phạm nào (0 Thủ phạm)."
        return f"Trong {reg_str} có đúng {k} Thủ phạm."

    if ctype is ClueType.AT_LEAST:
        assert clue.region is not None
        reg_str = format_region(clue.region, state, compact=compact)
        k = int(clue.k or 0)
        return f"Trong {reg_str} có ít nhất {k} Thủ phạm."

    if ctype is ClueType.AT_MOST:
        assert clue.region is not None
        reg_str = format_region(clue.region, state, compact=compact)
        k = int(clue.k or 0)
        return f"Trong {reg_str} có tối đa {k} Thủ phạm."

    if ctype is ClueType.PARITY:
        assert clue.region is not None
        reg_str = format_region(clue.region, state, compact=compact)
        par_str = "số chẵn" if clue.parity is Parity.EVEN else "số lẻ"
        return f"Tổng số Thủ phạm trong {reg_str} là một {par_str}."

    if ctype is ClueType.COMPARE:
        assert clue.left is not None and clue.right is not None
        left_str = format_region(clue.left, state, compact=compact)
        right_str = format_region(clue.right, state, compact=compact)
        op_map = {
            CompareOp.GT: "nhiều hơn",
            CompareOp.GE: "lớn hơn hoặc bằng",
            CompareOp.LT: "ít hơn",
            CompareOp.LE: "ít hơn hoặc bằng",
            CompareOp.EQ: "bằng đúng",
        }
        op_vn = op_map.get(clue.op, "so với")
        return f"Số Thủ phạm ở {left_str} {op_vn} số Thủ phạm ở {right_str}."

    return f"Lời khai mã {clue.id}."


def _format_literal(lit: int, encoder: CNFEncoder) -> str:
    sign = "¬" if lit < 0 else ""
    v = abs(lit)
    if v <= encoder.varmap.num_primary:
        cell = encoder.varmap.cell(v)
        return f"{sign}C_{cell}"
    return f"{sign}aux_{v - encoder.varmap.num_primary}"


def format_clue_formula(clue: Clue, n: int) -> dict[str, Any]:
    """Biểu diễn lời khai dưới dạng công thức logic mệnh đề (Section 3.2) và mệnh đề CNF thực tế."""
    ctype = clue.type
    math_formula = ""

    if ctype is ClueType.FACT:
        cell = clue.cells[0] if clue.cells else "?"
        math_formula = f"C_{cell}" if clue.status is Status.CRIMINAL else f"¬C_{cell}"
    elif ctype is ClueType.SAME:
        c1, c2 = clue.cells[0], clue.cells[1]
        math_formula = f"C_{c1} ↔ C_{c2}"
    elif ctype is ClueType.DIFFERENT:
        c1, c2 = clue.cells[0], clue.cells[1]
        math_formula = f"C_{c1} ⊕ C_{c2}"
    elif ctype in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        assert clue.region is not None
        rcells = resolve_region(clue.region, n)
        op_sym = "=" if ctype is ClueType.EXACTLY else ("≥" if ctype is ClueType.AT_LEAST else "≤")
        sum_terms = " + ".join(f"C_{c}" for c in rcells)
        math_formula = f"({sum_terms}) {op_sym} {clue.k}"
    elif ctype is ClueType.PARITY:
        assert clue.region is not None
        rcells = resolve_region(clue.region, n)
        xor_terms = " ⊕ ".join(f"C_{c}" for c in rcells)
        rem = 0 if clue.parity is Parity.EVEN else 1
        par_lbl = "Chẵn" if rem == 0 else "Lẻ"
        math_formula = f"({xor_terms}) ≡ {rem} (mod 2) [{par_lbl}]"
    elif ctype is ClueType.COMPARE:
        assert clue.left is not None and clue.right is not None
        lcells = resolve_region(clue.left, n)
        rcells = resolve_region(clue.right, n)
        op_map = {
            CompareOp.EQ: "=",
            CompareOp.LT: "<",
            CompareOp.LE: "≤",
            CompareOp.GT: ">",
            CompareOp.GE: "≥",
        }
        op_sym = op_map.get(clue.op, "=")
        l_sum = "+".join(f"C_{c}" for c in lcells)
        r_sum = "+".join(f"C_{c}" for c in rcells)
        math_formula = f"({l_sum}) {op_sym} ({r_sum})"

    enc = CNFEncoder(n)
    raw_clauses = enc.encode_clue(clue)
    formatted_clauses = [
        "(" + " ∨ ".join(_format_literal(lit, enc) for lit in cl) + ")"
        for cl in raw_clauses
    ]
    if len(formatted_clauses) <= 4:
        cnf_preview = " ∧ ".join(formatted_clauses)
    else:
        cnf_preview = " ∧ ".join(formatted_clauses[:3]) + f" ∧ ... (+{len(formatted_clauses) - 3} mệnh đề)"

    return {
        "math_formula": math_formula,
        "cnf_preview": cnf_preview,
        "clause_count": len(raw_clauses),
        "aux_count": enc.varmap.num_aux,
    }
