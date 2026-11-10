# Module D (LogicAgent, Uniqueness) & Experiments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Module D (`agent.logic_agent`, `agent.uniqueness`), the experiment benchmark suite (`experiments/run_experiments.py`), acceptance tests (`test_agent_acceptance.py`, `test_integration.py`), and wire Gates `G-D` & `G-I` in `tools/integration_runner.py` to achieve 100% PASS across the entire project.

**Architecture:** 
- `LogicAgent` interacts exclusively with `GamePort` (`get_public_state()`, `submit_verdict()`) and uses `EntailmentClassifier` (CNFEncoder + DPLL) to deduce forced cells in row-major order without guessing.
- `agent.uniqueness` wraps `EntailmentChecker` to provide offline uniqueness analysis for full clue sets without hidden solutions.
- `experiments/run_experiments.py` executes all manifest test cases, gathering statistics (vars, clauses, SAT calls, decisions, propagations, backtracks, steps, runtime) and generating tables for the report.
- `integration_runner.py` runs Gates `G-D` and `G-I` to certify full stack verification.

**Tech Stack:** Python 3.11+, pytest, standard library (`dataclasses`, `time`, `json`, `pathlib`).

**Spec:** Section 4.4 & 4.5 of `AI - Project 2.pdf`, `docs/handoff-A.md` (Section 3), `docs/decisions.md`.

---

## Global Constraints

- Python >= 3.11 standard library only for runtime.
- No access to hidden `Puzzle`, `solution`, or private `GameEngine` inside `LogicAgent` — communication only via `GamePort`.
- Deterministic forced cell selection: row-major order (`A1`, `B1`, ..., `A2`, `B2`, ...).
- Deduction trace must capture: step number, active clue IDs, SAT queries, verdict, and newly revealed clue.
- `verify_project.py --scope all --require-real` must pass with exit code 0.

## Review Focus

1. **Security & Isolation**: Agent must never receive hidden solution or inspect unrevealed clues.
2. **No-Guess Policy**: If no cells are forced (`Classification.UNKNOWN`), agent stops with status `STUCK` and never submits a speculative verdict.
3. **Transaction Safety**: All verdicts submitted must include `expected_token=state.token`.
4. **Offline Uniqueness**: `check_uniqueness` operates only on complete clue list and board size $n$, completely blind to `solution`.
5. **Experiment Metrics**: Benchmark must measure all 6 metrics required by Section 4.5 of the course specification.

---

### Task 1: Implement `Source/agent/uniqueness.py` and `Source/agent/logic_agent.py`

**Files:**
- Create: `Source/agent/__init__.py`
- Create: `Source/agent/uniqueness.py`
- Create: `Source/agent/logic_agent.py`

- [ ] **Step 1.1**: Create `Source/agent/__init__.py` exposing `LogicAgent`, `StepResult`, `RunResult`, `check_uniqueness`, `UniquenessReport`, `Uniqueness`.
- [ ] **Step 1.2**: Implement `Source/agent/uniqueness.py` with `check_uniqueness(clues: Sequence[Clue], n: int, *, deadline: float | None = None) -> UniquenessReport`.
- [ ] **Step 1.3**: Implement `Source/agent/logic_agent.py` containing dataclasses `StepResult`, `RunResult`, `AgentStatus` and class `LogicAgent`:
  - `classify_state(self, state: PublicState, *, deadline=None) -> ClassificationReport`
  - `hint(self, state: PublicState, *, deadline=None) -> Hint | None`
  - `step(self, port: GamePort, *, deadline=None) -> StepResult | None`
  - `run(self, port: GamePort, *, deadline=None, max_steps=100) -> RunResult`

---

### Task 2: Implement Acceptance Tests for Module D and Integration (G-I)

**Files:**
- Modify: `Source/tests/test_agent_acceptance.py`
- Modify: `Source/tests/test_integration.py`

- [ ] **Step 2.1**: Implement `test_agent_acceptance.py`:
  - `test_d01_no_guess_entailment_only`: Verifies step-by-step row-major solving on `3x3_chain.json`.
  - `test_d02_hint_identifies_forced_cell`: Verifies `agent.hint` identifies forced cells without mutating game state.
  - `test_d03_stuck_puzzle_stops_cleanly`: Verifies agent stops with `STUCK` on `3x3_stuck.json`.
  - `test_d04_inconsistent_puzzle`: Verifies agent detects `INCONSISTENT` on `3x3_inconsistent.json`.
  - `test_d05_deduction_trace`: Verifies trace records active clue IDs and SAT queries.
  - `test_d08_offline_uniqueness`: Verifies offline uniqueness check on UNIQUE, MULTIPLE, and UNSAT puzzles.
- [ ] **Step 2.2**: Implement `test_integration.py`:
  - `test_full_chain_solve_real`: End-to-end solve of `3x3_chain.json` with real GameEngine, GamePort, LogicAgent, CNFEncoder, DPLLSolver.
  - `test_full_stack_5x5_stress`: End-to-end solve of 5x5 puzzle using full stack.

---

### Task 3: Update `integration_runner.py` to Implement Gate `G-D` and Gate `G-I`

**Files:**
- Modify: `Source/tools/integration_runner.py`

- [ ] **Step 3.1**: Implement `run_gate_d(self) -> GateResult` to run all test functions in `tests/test_agent_acceptance.py`.
- [ ] **Step 3.2**: Implement `run_gate_i(self) -> GateResult` to run all test functions in `tests/test_integration.py`.
- [ ] **Step 3.3**: Update `run_scope()` to call `run_gate_d()` and `run_gate_i()` when modules are available.

---

### Task 4: Implement Experiment Benchmark Suite `Source/experiments/`

**Files:**
- Create: `Source/experiments/__init__.py`
- Create: `Source/experiments/run_experiments.py`

- [ ] **Step 4.1**: Implement `Source/experiments/run_experiments.py` to iterate through all puzzles in `Source/puzzles/index.json`.
  - Record:
    1. Primary & Auxiliary variables
    2. Number of CNF clauses
    3. SAT calls
    4. Decisions, propagations, backtracks
    5. Deduction steps
    6. Runtime (seconds)
  - Generate Markdown table (`Source/experiments/benchmark_table.md`) and JSON report (`Source/experiments/benchmark_results.json`).
- [ ] **Step 4.2**: Run `python -m experiments.run_experiments` and verify it produces benchmark tables cleanly.

---

### Task 5: System-wide Verification and Report Updates

**Files:**
- Run: `pytest Source/tests`
- Run: `tools.verify_project --scope all --require-real`
- Update: `docs/status.md`

- [ ] **Step 5.1**: Run full test suite with `pytest Source/tests -v`. Confirm 0 skipped, 0 failed.
- [ ] **Step 5.2**: Run `python -m tools.verify_project --scope all --require-real --output ../verification`. Confirm Exit Code 0 and ALL GATES PASS (G-A, G-B, G-C, G-P, G-D, G-E, G-I).
- [ ] **Step 5.3**: Update `docs/status.md` and `report/contribution-tracker.md` to reflect 100% project completion.
