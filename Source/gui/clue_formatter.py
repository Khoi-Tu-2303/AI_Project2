"""Trình dịch lời khai logic mệnh đề sang Tiếng Việt tự nhiên (Module E)."""

from __future__ import annotations

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
