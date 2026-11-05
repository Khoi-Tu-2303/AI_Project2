"""Shared type definitions and contracts for the Griductive Solver."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator, Mapping, Sequence, TypeVar

Cell = str

K = TypeVar("K")
V = TypeVar("V")


class FrozenDict(Mapping[K, V]):
    """Immutable mapping wrapper preventing in-place mutations while supporting deepcopy."""

    def __init__(self, data: Mapping[K, V] | None = None) -> None:
        self._data: dict[K, V] = dict(data) if data is not None else {}

    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __iter__(self) -> Iterator[K]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"FrozenDict({self._data!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Mapping):
            return self._data == dict(other)
        return False

    def __hash__(self) -> int:
        return hash(tuple(sorted((k, v) for k, v in self._data.items())))

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> FrozenDict[K, V]:
        memo = memo if memo is not None else {}
        new_data = {
            copy.deepcopy(k, memo): copy.deepcopy(v, memo)
            for k, v in self._data.items()
        }
        return FrozenDict(new_data)

    def __copy__(self) -> FrozenDict[K, V]:
        return FrozenDict(self._data)


def freeze_mapping(m: Mapping[K, V] | None) -> Mapping[K, V]:
    """Create an immutable, defensive read-only mapping copy."""
    if isinstance(m, FrozenDict):
        return m
    return FrozenDict(m)


class Status(Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"


def status_to_bool(status: Status) -> bool:
    """Explicit conversion from Status to bool: True for CRIMINAL, False for INNOCENT."""
    if status is Status.CRIMINAL:
        return True
    if status is Status.INNOCENT:
        return False
    raise TypeError(f"Expected Status enum, got {type(status).__name__}: {status}")


def bool_to_status(value: bool) -> Status:
    """Explicit conversion from bool to Status: True -> CRIMINAL, False -> INNOCENT."""
    if value is True:
        return Status.CRIMINAL
    if value is False:
        return Status.INNOCENT
    raise TypeError(f"Expected strict bool, got {type(value).__name__}: {value}")


class Classification(Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"


class ReasoningStatus(Enum):
    READY = "READY"  # KB consistent; classification completed
    INCONSISTENT = "INCONSISTENT"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


class VerdictResult(Enum):
    ACCEPTED = "ACCEPTED"
    NOT_PROVABLE = "NOT_PROVABLE"
    CONTRADICTED = "CONTRADICTED"


class ClueType(Enum):
    FACT = "FACT"
    SAME = "SAME"
    DIFFERENT = "DIFFERENT"
    EXACTLY = "EXACTLY"
    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"
    PARITY = "PARITY"
    COMPARE = "COMPARE"


class RegionKind(Enum):
    ROW = "ROW"
    COL = "COL"
    NEIGHBORS = "NEIGHBORS"
    EXPLICIT = "EXPLICIT"


class Parity(Enum):
    EVEN = "EVEN"
    ODD = "ODD"


class CompareOp(Enum):
    EQ = "EQ"
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"


@dataclass(frozen=True)
class Region:
    kind: RegionKind
    arg: int | str | tuple[Cell, ...]

    def __post_init__(self) -> None:
        if isinstance(self.arg, list):
            object.__setattr__(self, "arg", tuple(self.arg))


@dataclass(frozen=True)
class Character:
    cell: Cell
    name: str
    profession: str


@dataclass(frozen=True)
class Clue:
    id: str
    type: ClueType
    cells: tuple[Cell, ...] = ()
    region: Region | None = None
    k: int | None = None
    status: Status | None = None
    parity: Parity | None = None
    left: Region | None = None
    right: Region | None = None
    op: CompareOp | None = None

    def __post_init__(self) -> None:
        if isinstance(self.cells, list):
            object.__setattr__(self, "cells", tuple(self.cells))


@dataclass(frozen=True)
class Puzzle:
    schema_version: int
    id: str
    n: int
    characters: tuple[Character, ...]
    clues: Mapping[Cell, Clue]
    initial_revealed: Mapping[Cell, Status]
    solution: Mapping[Cell, Status] | None = None

    def __post_init__(self) -> None:
        if isinstance(self.characters, list):
            object.__setattr__(self, "characters", tuple(self.characters))
        object.__setattr__(self, "clues", freeze_mapping(self.clues))
        object.__setattr__(self, "initial_revealed", freeze_mapping(self.initial_revealed))
        if self.solution is not None:
            object.__setattr__(self, "solution", freeze_mapping(self.solution))


@dataclass(frozen=True)
class StateToken:
    session_id: str
    revision: int


@dataclass(frozen=True)
class PublicState:
    puzzle_id: str
    token: StateToken
    n: int
    characters: tuple[Character, ...]
    known_statuses: Mapping[Cell, Status]
    revealed_clues: Mapping[Cell, Clue]
    unsolved: tuple[Cell, ...]

    def __post_init__(self) -> None:
        if isinstance(self.characters, list):
            object.__setattr__(self, "characters", tuple(self.characters))
        if isinstance(self.unsolved, list):
            object.__setattr__(self, "unsolved", tuple(self.unsolved))
        object.__setattr__(self, "known_statuses", freeze_mapping(self.known_statuses))
        object.__setattr__(self, "revealed_clues", freeze_mapping(self.revealed_clues))


@dataclass(frozen=True)
class ClassificationReport:
    token: StateToken
    status: ReasoningStatus
    by_cell: Mapping[Cell, Classification] = field(default_factory=lambda: FrozenDict({}))
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "by_cell", freeze_mapping(self.by_cell))


@dataclass(frozen=True)
class VerdictOutcome:
    result: VerdictResult
    cell: Cell
    verdict: Status
    before_token: StateToken
    after_token: StateToken
    new_clue: Clue | None = None


@dataclass(frozen=True)
class Hint:
    token: StateToken
    cell: Cell
    verdict: Status
    clue_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.clue_ids, list):
            object.__setattr__(self, "clue_ids", tuple(self.clue_ids))
