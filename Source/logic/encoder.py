"""CNF encoding using reified counting circuits and XOR chains.

Every circuit gate is an equivalence, so fixing the primary variables determines
all auxiliary variables. CNF satisfiability projects exactly onto clue semantics.
No SAT solver, hidden puzzle, or test oracle is used here.
"""

from typing import Mapping, Sequence

from common.errors import ClueError
from common.regions import resolve_region
from common.types import (
    Cell, Clue, ClueType, CompareOp, KnowledgeBase, Parity, Status,
    status_to_bool,
)
from common.validation import validate_clue
from logic.varmap import VarMap

# Constants are strict bool; nonzero ints are signed CNF literals.
Signal = int | bool


def _neg(signal: Signal) -> Signal:
    return not signal if type(signal) is bool else -signal


class CNFEncoder:
    def __init__(self, n: int | VarMap) -> None:
        self.varmap = n if isinstance(n, VarMap) else VarMap(n)

    @property
    def n(self) -> int:
        return self.varmap.n

    @staticmethod
    def _clause(out: list[list[int]], *signals: Signal) -> None:
        if any(s is True for s in signals):
            return
        literals = list(dict.fromkeys(s for s in signals if s is not False))
        if any(-lit in literals for lit in literals):
            return
        out.append(literals)

    def _gate(self, out: list[list[int]], a: Signal, b: Signal, *, and_: bool) -> Signal:
        identity, absorbing = (True, False) if and_ else (False, True)
        if a is absorbing or b is absorbing:
            return absorbing
        if a is identity:
            return b
        if b is identity or a == b:
            return a
        if a == _neg(b):
            return absorbing
        z = self.varmap.new_aux()
        if and_:
            self._clause(out, -z, a)
            self._clause(out, -z, b)
            self._clause(out, z, _neg(a), _neg(b))
        else:
            self._clause(out, z, _neg(a))
            self._clause(out, z, _neg(b))
            self._clause(out, -z, a, b)
        return z

    def _at_least(self, out: list[list[int]], literals: list[int], k: int) -> Signal:
        """DP: S(i,j) <-> S(i-1,j) OR (x_i AND S(i-1,j-1)).

        At most O(m*k) gates, avoiding exponential subset enumeration.
        """
        if k <= 0:
            return True
        if k > len(literals):
            return False
        previous: list[Signal] = [True] + [False] * k
        for i, literal in enumerate(literals, 1):
            current: list[Signal] = [True] + [False] * k
            for j in range(1, min(i, k) + 1):
                term = self._gate(out, literal, previous[j - 1], and_=True)
                current[j] = self._gate(out, previous[j], term, and_=False)
            previous = current
        return previous[k]

    def _bounds(self, out: list[list[int]], literals: list[int], *,
                lower: int | None = None, upper: int | None = None) -> None:
        if lower is not None:
            self._clause(out, self._at_least(out, literals, lower))
        if upper is not None:
            self._clause(out, _neg(self._at_least(out, literals, upper + 1)))

    def unit_clause(self, cell: Cell, status: Status) -> list[int]:
        var = self.varmap.var(cell)
        return [var if status_to_bool(status) else -var]

    def encode_clue(self, clue: Clue) -> list[list[int]]:
        validate_clue(clue, self.n)
        out: list[list[int]] = []
        kind = clue.type
        if kind is ClueType.FACT:
            return [self.unit_clause(clue.cells[0], clue.status)]
        if kind in (ClueType.SAME, ClueType.DIFFERENT):
            a, b = (self.varmap.var(c) for c in clue.cells)
            return [[-a, b], [a, -b]] if kind is ClueType.SAME else [[a, b], [-a, -b]]
        if kind is ClueType.COMPARE:
            left = set(resolve_region(clue.left, self.n))
            right = set(resolve_region(clue.right, self.n))
            # Cancel overlap; L-R = sum(L-only) + sum(not R-only) - |R-only|.
            # Sort by primary ID for deterministic output.
            literals = sorted(self.varmap.var(c) for c in left - right)
            literals += [-v for v in sorted(self.varmap.var(c) for c in right - left)]
            k = len(right - left)
            lower, upper = {
                CompareOp.EQ: (k, k),
                CompareOp.LT: (None, k - 1),
                CompareOp.LE: (None, k),
                CompareOp.GT: (k + 1, None),
                CompareOp.GE: (k, None),
            }[clue.op]
            self._bounds(out, literals, lower=lower, upper=upper)
            return out

        literals = [self.varmap.var(c) for c in resolve_region(clue.region, self.n)]
        if kind is ClueType.PARITY:
            parity = literals[0]
            for literal in literals[1:]:
                z = self.varmap.new_aux()
                # z <-> parity XOR literal
                out.extend([[parity, literal, -z], [-parity, -literal, -z],
                            [parity, -literal, z], [-parity, literal, z]])
                parity = z
            out.append([parity if clue.parity is Parity.ODD else -parity])
        else:
            self._bounds(out, literals,
                         lower=clue.k if kind in (ClueType.EXACTLY, ClueType.AT_LEAST) else None,
                         upper=clue.k if kind in (ClueType.EXACTLY, ClueType.AT_MOST) else None)
        return out

    def build_kb(self, clues: Sequence[Clue], known_statuses: Mapping[Cell, Status]) -> KnowledgeBase:
        """Build only from caller-supplied PUBLIC clues and known statuses.

        Reset auxiliary allocation once per complete rebuild. Standalone
        encode_clue calls retain allocation so their outputs can be conjoined.
        """
        clues = tuple(clues)
        for clue in clues:
            validate_clue(clue, self.n)
        units = [self.unit_clause(cell, known_statuses[cell])
                 for cell in sorted(known_statuses, key=self.varmap.var)]
        if len({clue.id for clue in clues}) != len(clues):
            raise ClueError("Active clues must have distinct IDs")
        self.varmap.reset_aux()
        clauses = [clause for clue in clues for clause in self.encode_clue(clue)]
        clauses.extend(units)
        return KnowledgeBase(self.n, tuple(tuple(c) for c in clauses),
                             self.varmap.num_primary, self.varmap.num_aux)
