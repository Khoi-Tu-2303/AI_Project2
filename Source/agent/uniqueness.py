"""Offline uniqueness checking for complete clue sets (Module D)."""

from __future__ import annotations

from typing import Sequence

from common.types import Clue
from logic.encoder import CNFEncoder
from logic.entailment import EntailmentChecker, Uniqueness, UniquenessReport


def check_uniqueness(
    clues: Sequence[Clue],
    n: int,
    *,
    deadline: float | None = None,
) -> UniquenessReport:
    """Determine whether a complete set of clues admits zero, one, or multiple solutions.

    Operates completely offline without any hidden solution or game engine instance.
    """
    encoder = CNFEncoder(n)
    kb = encoder.build_kb(clues, {})
    checker = EntailmentChecker(kb)
    return checker.check_uniqueness(deadline=deadline)


__all__ = ["check_uniqueness", "Uniqueness", "UniquenessReport"]
