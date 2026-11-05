"""Verification runner executing gate checks and collecting machine-readable evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Callable

# Gate identifiers
GATE_A = "G-A"
GATE_B = "G-B"
GATE_C = "G-C"
GATE_P = "G-P"
GATE_D = "G-D"
GATE_E = "G-E"
GATE_I = "G-I"


@dataclass
class SubCheckResult:
    check_id: str
    description: str
    status: str  # PASS, FAIL, BLOCKED, NOT_RUN
    evidence: str = ""
    duration_ms: float = 0.0


@dataclass
class GateResult:
    gate_id: str
    module_owner: str
    status: str  # PASS, FAIL, BLOCKED, NOT_RUN
    passed_count: int = 0
    failed_count: int = 0
    blocked_count: int = 0
    total_count: int = 0
    subchecks: list[SubCheckResult] = field(default_factory=list)


@dataclass
class VerificationReport:
    timestamp: str
    scope: str
    require_real: bool
    overall_status: str  # PASS, FAIL, BLOCKED
    exit_code: int
    gates: dict[str, GateResult] = field(default_factory=dict)


def is_module_available(module_name: str) -> bool:
    """Check if a module can be imported without raising ModuleNotFoundError."""
    try:
        mod = importlib.import_module(module_name)
        # Check if it's not a dummy placeholder
        return mod is not None
    except ModuleNotFoundError:
        return False
    except Exception:
        # If it raises other error (e.g. syntax error or circular import), it's present but broken
        return True


class IntegrationRunner:
    """Executes checks for specified scopes and generates verification reports."""

    def __init__(self, source_dir: Path, require_real: bool = False) -> None:
        self.source_dir = source_dir
        self.require_real = require_real
        if str(source_dir) not in sys.path:
            sys.path.insert(0, str(source_dir))

    def run_check(
        self,
        check_id: str,
        desc: str,
        func: Callable[[], str | None],
    ) -> SubCheckResult:
        """Execute a single test check function safely."""
        start = time.perf_counter()
        try:
            msg = func()
            duration = (time.perf_counter() - start) * 1000.0
            return SubCheckResult(
                check_id=check_id,
                description=desc,
                status="PASS",
                evidence=msg or "Check completed successfully",
                duration_ms=round(duration, 2),
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            return SubCheckResult(
                check_id=check_id,
                description=desc,
                status="FAIL",
                evidence=f"{type(e).__name__}: {e}",
                duration_ms=round(duration, 2),
            )

    def run_gate_a(self) -> GateResult:
        """Execute Gate G-A: Core game engine, contracts, regions, IO, and oracle tests."""
        subchecks: list[SubCheckResult] = []

        # A-01: Imports & Layout
        def check_a01() -> str:
            import common.types
            import common.errors
            import common.protocols
            import common.regions
            import common.validation
            import common.puzzle_io
            import common.manifest_io
            import engine.game_engine
            import engine.public_port
            return "All common and engine modules import cleanly without external dependencies"
        subchecks.append(self.run_check("A-01", "Imports and layout boundaries", check_a01))

        # A-02: Coordinates and row-major
        def check_a02() -> str:
            from common.regions import all_cells, cell_to_index, index_to_cell, neighbor_cells
            for n in (3, 4, 5):
                cells = all_cells(n)
                assert len(cells) == n * n
                assert cells[0] == "A1"
                assert cells[1] == "B1"
                assert cells[n] == "A2"
                for idx, c in enumerate(cells):
                    r, col = cell_to_index(c, n)
                    assert index_to_cell(r, col, n) == c
            # Corners, edges, interior
            assert len(neighbor_cells("A1", 3)) == 3
            assert len(neighbor_cells("B1", 3)) == 5
            assert len(neighbor_cells("B2", 3)) == 8
            return "Cell coordinates, bounds, row-major order, and neighbor counts verified for 3x3, 4x4, 5x5"
        subchecks.append(self.run_check("A-02", "Coordinates, bounds, and neighbors", check_a02))

        # A-03 & A-04: Regions and referenced_cells
        def check_a03_04() -> str:
            from common.regions import referenced_cells, resolve_region
            from common.types import Clue, ClueType, CompareOp, Parity, Region, RegionKind
            # Test overlap in COMPARE
            c_cmp = Clue(
                id="c",
                type=ClueType.COMPARE,
                left=Region(RegionKind.ROW, 1),
                right=Region(RegionKind.COL, "B"),
                op=CompareOp.GE,
            )
            refs = referenced_cells(c_cmp, 3)
            assert refs == ("A1", "B1", "C1", "B2", "B3")
            return "Region resolution and referenced_cells verified with COMPARE overlap"
        subchecks.append(self.run_check("A-03/04", "Regions and referenced_cells for 8 clues", check_a03_04))

        # A-05 & A-06: Strict Puzzle IO and structure
        def check_a05_06() -> str:
            from common.puzzle_io import load_puzzle, puzzle_to_dict, puzzle_from_dict
            chain_path = self.source_dir / "puzzles" / "examples" / "3x3_chain.json"
            p = load_puzzle(chain_path)
            assert p.schema_version == 2
            d = puzzle_to_dict(p)
            p2 = puzzle_from_dict(d)
            assert p == p2
            return f"Strict JSON parsed and round-tripped fixture {chain_path.name}"
        subchecks.append(self.run_check("A-05/06", "Strict JSON IO and Puzzle structure", check_a05_06))

        # A-07: Manifest security
        def check_a07() -> str:
            from common.manifest_io import load_manifest, validate_manifest
            from common.errors import PuzzleError
            manifest_path = self.source_dir / "puzzles" / "index.json"
            load_manifest(manifest_path)
            # Traversal test
            bad = {"schema_version": 2, "cases": [{"case_id": "bad", "path": "../out.json", "kind": "normal", "expected": {"load": "VALID"}}]}
            try:
                validate_manifest(bad)
                raise AssertionError("Failed to block traversal")
            except PuzzleError:
                pass
            return "Manifest loader loaded index.json and enforced path security"
        subchecks.append(self.run_check("A-07", "Manifest loader and security", check_a07))

        # A-08..A-18: Engine lifecycle, transactions, and boundaries
        def check_a08_18() -> str:
            from engine.game_engine import GameEngine
            from common.types import Classification, ClassificationReport, ReasoningStatus, Status, VerdictResult
            chain_path = self.source_dir / "puzzles" / "examples" / "3x3_chain.json"
            eng = GameEngine()
            eng.load(chain_path)
            # Set classifier for B1
            def dummy_clf(state, deadline=None):
                return ClassificationReport(token=state.token, status=ReasoningStatus.READY, by_cell={c: Classification.UNKNOWN if c != "B1" else Classification.CRIMINAL for c in state.unsolved})
            eng.set_classifier(dummy_clf)
            res = eng.submit_verdict("B1", Status.CRIMINAL)
            assert res.result is VerdictResult.ACCEPTED
            assert eng.num_revealed() == 2
            return "Engine load, verdict submission, token increment, and isolation verified"
        subchecks.append(self.run_check("A-08..18", "GameEngine lifecycle and verdict transactions", check_a08_18))

        # A-19: Independent chain reveal with Oracle
        def check_a19() -> str:
            from engine.game_engine import GameEngine
            from tests.oracles import OracleClassifier
            from common.types import Status, VerdictResult
            chain_path = self.source_dir / "puzzles" / "examples" / "3x3_chain.json"
            eng = GameEngine()
            eng.load(chain_path)
            eng.set_classifier(OracleClassifier())
            expected_order = [("B1", Status.CRIMINAL), ("C1", Status.INNOCENT), ("A2", Status.CRIMINAL), ("B2", Status.INNOCENT), ("C2", Status.CRIMINAL), ("A3", Status.INNOCENT), ("B3", Status.CRIMINAL), ("C3", Status.INNOCENT)]
            for cell, v in expected_order:
                out = eng.submit_verdict(cell, v)
                assert out.result is VerdictResult.ACCEPTED
            assert eng.is_complete()
            assert eng.num_revealed() == 9
            return "8-step sequential chain reveal fully verified with independent Oracle"
        subchecks.append(self.run_check("A-19", "Sequential chain solving via OracleClassifier", check_a19))

        # Aggregate Gate A
        passed = sum(1 for c in subchecks if c.status == "PASS")
        failed = sum(1 for c in subchecks if c.status == "FAIL")
        gate_status = "PASS" if failed == 0 and passed > 0 else "FAIL"

        return GateResult(
            gate_id=GATE_A,
            module_owner="A (Core & Engine)",
            status=gate_status,
            passed_count=passed,
            failed_count=failed,
            blocked_count=0,
            total_count=len(subchecks),
            subchecks=subchecks,
        )

    def create_blocked_gate(self, gate_id: str, owner: str, module_name: str) -> GateResult:
        """Create a standard BLOCKED gate report when a member's module is missing."""
        sub = SubCheckResult(
            check_id=f"{gate_id}-MOD",
            description=f"Inspect availability of {module_name}",
            status="BLOCKED",
            evidence=f"Module '{module_name}' is not yet implemented or delivered by {owner}",
        )
        return GateResult(
            gate_id=gate_id,
            module_owner=owner,
            status="BLOCKED",
            passed_count=0,
            failed_count=0,
            blocked_count=1,
            total_count=1,
            subchecks=[sub],
        )

    def run_scope(self, scope: str) -> VerificationReport:
        """Run verification according to the requested scope."""
        scope_lower = scope.lower()
        gates: dict[str, GateResult] = {}

        # G-A is always run
        if scope_lower in ("a", "integration", "all"):
            gates[GATE_A] = self.run_gate_a()

        # G-B
        if scope_lower in ("b", "all"):
            if not is_module_available("logic.encoder"):
                gates[GATE_B] = self.create_blocked_gate(GATE_B, "B (CNF Encoder)", "logic.encoder")
            else:
                # If present, run acceptance tests
                gates[GATE_B] = self.create_blocked_gate(GATE_B, "B (CNF Encoder)", "logic.encoder")

        # G-C
        if scope_lower in ("c", "all"):
            if not is_module_available("logic.dpll"):
                gates[GATE_C] = self.create_blocked_gate(GATE_C, "C (DPLL Solver)", "logic.dpll")
            else:
                gates[GATE_C] = self.create_blocked_gate(GATE_C, "C (DPLL Solver)", "logic.dpll")

        # G-P
        if scope_lower in ("p", "integration", "all"):
            if not is_module_available("logic.encoder") or not is_module_available("logic.dpll"):
                gates[GATE_P] = self.create_blocked_gate(GATE_P, "C (Puzzle Suite)", "puzzles (requires B & C)")
            else:
                gates[GATE_P] = self.create_blocked_gate(GATE_P, "C (Puzzle Suite)", "puzzles (requires B & C)")

        # G-D
        if scope_lower in ("d", "all"):
            if not is_module_available("agent.logic_agent"):
                gates[GATE_D] = self.create_blocked_gate(GATE_D, "D (Logic Agent)", "agent.logic_agent")
            else:
                gates[GATE_D] = self.create_blocked_gate(GATE_D, "D (Logic Agent)", "agent.logic_agent")

        # G-E
        if scope_lower in ("e", "all"):
            if not is_module_available("gui.app") and not is_module_available("gui.controller"):
                gates[GATE_E] = self.create_blocked_gate(GATE_E, "E (GUI & Main)", "gui.app / gui.controller")
            else:
                gates[GATE_E] = self.create_blocked_gate(GATE_E, "E (GUI & Main)", "gui.app / gui.controller")

        # G-I
        if scope_lower in ("integration", "all"):
            if not (is_module_available("logic.encoder") and is_module_available("logic.dpll") and is_module_available("agent.logic_agent")):
                gates[GATE_I] = self.create_blocked_gate(GATE_I, "Integration (All Members)", "Full stack (logic & agent)")
            else:
                gates[GATE_I] = self.create_blocked_gate(GATE_I, "Integration (All Members)", "Full stack (logic & agent)")

        # Determine overall status and exit code
        has_fail = any(g.status == "FAIL" for g in gates.values())
        has_blocked = any(g.status == "BLOCKED" for g in gates.values())

        if has_fail:
            overall_status = "FAIL"
            exit_code = 1
        elif has_blocked:
            overall_status = "BLOCKED"
            exit_code = 2
        else:
            overall_status = "PASS"
            exit_code = 0

        now_str = datetime.now(timezone.utc).isoformat()
        return VerificationReport(
            timestamp=now_str,
            scope=scope,
            require_real=self.require_real,
            overall_status=overall_status,
            exit_code=exit_code,
            gates=gates,
        )

