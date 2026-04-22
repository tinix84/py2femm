# Executor Fix + 2-Chip Optimizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the FEMM executor's process-hang bug by switching from `proc.communicate()` to file-polling, add a sentinel marker for reliable completion detection, then validate the 2-chip optimizer example and create a Jupyter notebook.

**Architecture:** The executor currently blocks on `proc.communicate()` which hangs because FEMM's `quit()` doesn't reliably terminate in `-windowhide` mode. The fix: poll for a sentinel marker (`PY2FEMM_DONE`) in the output file, then kill the process. `FemmProblem.close()` writes the sentinel before `quit()`. The optimizer example already exists and is structurally correct; it just needs the executor fix to work.

**Tech Stack:** Python 3.10+, FEMM 4.2, subprocess, pathlib, pytest, numpy, scipy, matplotlib, Jupyter

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `py2femm/femm_problem.py` | Modify `close()` | Add `PY2FEMM_DONE` sentinel write before `quit()` |
| `py2femm_server/executor.py` | Rewrite `run()` | File-polling with sentinel detection instead of `proc.communicate()` |
| `tests/test_server_executor.py` | Add tests | Test polling, sentinel detection, timeout, process-exit |
| `tests/test_femm_problem.py` | Add test | Test that `close()` emits sentinel |
| `examples/heatflow/heatsink/heatsink_optimize.py` | Minor fix | Ensure `ho_getpointvalues` Lua syntax is correct |
| `examples/heatflow/heatsink/heatsink_optimize.ipynb` | Create | Thin Jupyter wrapper around optimizer functions |

---

### Task 1: Add PY2FEMM_DONE Sentinel to FemmProblem.close()

**Files:**
- Modify: `py2femm/femm_problem.py:123-139`
- Test: `tests/test_femm_problem.py` (create if not exists, or add test)

The sentinel is a known marker that the executor polls for. It's written to `file_out` just before `closefile()` and `quit()`, guaranteeing all prior `write()` calls have been flushed.

- [ ] **Step 1: Write the failing test**

Find or create `tests/test_femm_problem.py` and add:

```python
from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit


def test_close_emits_sentinel():
    """close() must write PY2FEMM_DONE to file_out before quit()."""
    problem = FemmProblem(out_file="test.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS, type="planar",
        precision=1e-8, depth=100, minangle=30,
    )
    problem.close()
    script = "\n".join(problem.lua_script)
    # Sentinel must appear before closefile and quit
    assert 'write(file_out, "PY2FEMM_DONE\\n")' in script
    sentinel_idx = script.index("PY2FEMM_DONE")
    close_idx = script.index("closefile(file_out)")
    quit_idx = script.index("quit()")
    assert sentinel_idx < close_idx < quit_idx
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_femm_problem.py::test_close_emits_sentinel -v`
Expected: FAIL — `PY2FEMM_DONE` not in script

- [ ] **Step 3: Add sentinel to close()**

In `py2femm/femm_problem.py`, modify the `close()` method (line 123):

```python
def close(self, elements=False):

    cmd_list = []

    # Sentinel marker — signals the executor that all writes are complete
    cmd_list.append('write(file_out, "PY2FEMM_DONE\\n")')

    # Always flush the output file handle before closing
    cmd_list.append("closefile(file_out)")
    cmd_list.append("closefile(point_values)")

    if elements:
        cmd_list.append("closefile(mesh_file)")

    cmd_list.append(f"{self.field.output_to_string()}_close()")
    cmd_list.append(f"{self.field.input_to_string()}_close()")
    cmd_list.append("quit()")
    self.lua_script.extend(cmd_list)

    return cmd_list
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_femm_problem.py::test_close_emits_sentinel -v`
Expected: PASS

- [ ] **Step 5: Run all existing tests to check for regressions**

Run: `pytest tests/ -v`
Expected: All existing tests still pass. The sentinel is just an extra `write()` line and doesn't break anything.

- [ ] **Step 6: Commit**

```bash
git add py2femm/femm_problem.py tests/test_femm_problem.py
git commit -m "feat: add PY2FEMM_DONE sentinel to FemmProblem.close()"
```

---

### Task 2: Rewrite executor.run() to Use File-Polling

**Files:**
- Modify: `py2femm_server/executor.py:107-131`

The core fix: instead of `proc.communicate(timeout=timeout)` which blocks until FEMM exits (and FEMM hangs after `quit()` in headless mode), we:
1. Start the process with `Popen`
2. Poll `results.csv` every 0.5s for the `PY2FEMM_DONE` sentinel
3. Once found, read the CSV, kill the process, return results
4. If the process exits on its own, read whatever results exist
5. On timeout, kill and try to salvage results

- [ ] **Step 1: Write failing tests for polling behavior**

Add to `tests/test_server_executor.py`:

```python
def test_executor_run_reads_sentinel_result(tmp_path):
    """run() should detect PY2FEMM_DONE sentinel and return CSV data."""
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")

    # Prepare a job directory with a pre-written result file
    job_dir, lua_path = executor.prepare_job("hi_analyze()")
    result_csv = job_dir / "results.csv"
    result_csv.write_text("T_A_K = 350.5\nPY2FEMM_DONE\n")

    # read_result should return the data
    csv_data = executor.read_result(job_dir)
    assert csv_data is not None
    assert "T_A_K = 350.5" in csv_data
    assert "PY2FEMM_DONE" in csv_data


def test_executor_result_has_sentinel():
    """Verify the sentinel constant is defined."""
    from py2femm_server.executor import SENTINEL
    assert SENTINEL == "PY2FEMM_DONE"


def test_executor_has_sentinel_checks_correctly(tmp_path):
    """has_sentinel() returns True only when sentinel is in the file."""
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")

    job_dir = tmp_path / "jobs" / "test_sentinel"
    job_dir.mkdir(parents=True)
    result_path = job_dir / "results.csv"

    # No file yet
    assert executor.has_sentinel(job_dir) is False

    # Empty file
    result_path.write_text("")
    assert executor.has_sentinel(job_dir) is False

    # Partial data, no sentinel
    result_path.write_text("T_A_K = 350.5\n")
    assert executor.has_sentinel(job_dir) is False

    # With sentinel
    result_path.write_text("T_A_K = 350.5\nPY2FEMM_DONE\n")
    assert executor.has_sentinel(job_dir) is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_server_executor.py::test_executor_result_has_sentinel tests/test_server_executor.py::test_executor_has_sentinel_checks_correctly -v`
Expected: FAIL — `SENTINEL` and `has_sentinel` don't exist yet

- [ ] **Step 3: Implement the polling-based run()**

Replace the `FemmExecutor` class in `py2femm_server/executor.py` (starting at line 88):

```python
SENTINEL = "PY2FEMM_DONE"


class FemmExecutor:
    """Runs FEMM as a subprocess on a Lua script."""

    def __init__(self, femm_path: Path, workspace: Path, headless: bool = True) -> None:
        self.femm_path = Path(femm_path)
        self.workspace = Path(workspace)
        self.headless = headless
        self.workspace.mkdir(parents=True, exist_ok=True)

    def prepare_job(self, lua_script: str) -> PreparedJob:
        """Write Lua script to a job directory, return paths."""
        job_id = uuid.uuid4().hex[:12]
        job_dir = self.workspace / f"job_{job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        lua_path = job_dir / "run.lua"
        injected = inject_preamble(lua_script, job_dir)
        lua_path.write_text(injected, encoding="utf-8")
        return PreparedJob(job_dir=job_dir, lua_path=lua_path)

    def has_sentinel(self, job_dir: Path) -> bool:
        """Check if results.csv contains the PY2FEMM_DONE sentinel."""
        result_path = job_dir / "results.csv"
        if not result_path.exists():
            return False
        try:
            text = result_path.read_text(encoding="utf-8")
            return SENTINEL in text
        except (OSError, UnicodeDecodeError):
            return False

    def run(self, lua_script: str, timeout: int = 300) -> tuple[str | None, int]:
        """Run a Lua script in FEMM. Returns (csv_data, returncode).

        Uses file-polling instead of proc.communicate() because FEMM's
        quit() hangs in -windowhide mode. We poll results.csv for the
        PY2FEMM_DONE sentinel, then kill the process.
        """
        job_dir, lua_path = self.prepare_job(lua_script)
        lua_path_abs = str(lua_path.resolve())
        cmd = [str(self.femm_path), f"-lua-script={lua_path_abs}"]
        if self.headless:
            cmd.append("-windowhide")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        import time

        deadline = time.time() + timeout
        poll_interval = 0.5

        while time.time() < deadline:
            time.sleep(poll_interval)

            # Check if results file has the sentinel (all writes flushed)
            if self.has_sentinel(job_dir):
                csv_data = self.read_result(job_dir)
                proc.kill()
                proc.wait()
                return csv_data, 0

            # Check if process exited on its own
            if proc.poll() is not None:
                csv_data = self.read_result(job_dir)
                return csv_data, proc.returncode

        # Timeout — kill and try to salvage
        proc.kill()
        proc.wait()
        csv_data = self.read_result(job_dir)
        if csv_data and csv_data.strip():
            return csv_data, 0
        return None, -1

    def read_result(self, job_dir: Path) -> str | None:
        """Read the results.csv from a job directory."""
        result_path = job_dir / "results.csv"
        if not result_path.exists():
            return None
        text = result_path.read_text(encoding="utf-8")
        return text if text else None

    def read_error_log(self, job_dir: Path) -> str | None:
        """Read any error logs from a job directory."""
        logs = []
        for name in ["error.log", "stderr.log", "stdout.log"]:
            p = job_dir / name
            if p.exists() and p.stat().st_size > 0:
                logs.append(f"--- {name} ---\n{p.read_text(encoding='utf-8', errors='replace')}")
        return "\n".join(logs) if logs else None
```

Note: move `import time` to the top of the file alongside the other imports.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_server_executor.py -v`
Expected: All tests pass (both new and existing)

- [ ] **Step 5: Commit**

```bash
git add py2femm_server/executor.py tests/test_server_executor.py
git commit -m "feat: rewrite executor to use file-polling instead of proc.communicate()"
```

---

### Task 3: Fix Optimizer Lua Syntax for ho_getpointvalues

**Files:**
- Modify: `examples/heatflow/heatsink/heatsink_optimize.py:262-267`

**Problem:** The optimizer calls `ho_getpointvalues(x, 0)` which returns a Lua table in FEMM's Lua 4.0. It then indexes with `T_A[1]`. In FEMM's Lua 4.0, `ho_getpointvalues` returns **multiple values** (not a table), so the correct pattern is to assign to a single variable (which captures only the first return value — temperature).

The working tutorial avoids this by not calling `ho_getpointvalues` at all — it uses `ho_blockintegral(0)` for average temperature.

**Fix:** Change the Lua to use multiple-return assignment like other FEMM Lua 4.0 patterns: `T_A = ho_getpointvalues(x, 0)` — in Lua 4.0 this captures the first return value (temperature in Kelvin).

- [ ] **Step 1: Write a test for the generated Lua**

Create `tests/test_optimizer_lua.py`:

```python
"""Tests for the optimizer's Lua generation — no FEMM needed."""

from examples.heatflow.heatsink.heatsink_optimize import (
    OptimConfig, ChipConfig, HeatsinkConfig, build_model,
)


def test_build_model_produces_valid_lua():
    """build_model() should produce Lua without table indexing syntax."""
    cfg = OptimConfig(
        chip_a=ChipConfig(name="ChipA", power=5.0),
        chip_b=ChipConfig(name="ChipB", power=15.0),
        heatsink=HeatsinkConfig(base_w=100.0, base_h=100.0, base_t=5.0),
    )
    lua = build_model(cfg, x_a=30.0, y_a=0.0, x_b=70.0, y_b=0.0)

    # Must contain ho_getpointvalues calls
    assert "ho_getpointvalues" in lua

    # Must NOT use table indexing T_A[1] — FEMM Lua 4.0 returns multiple values
    assert "[1]" not in lua

    # Must write temperature values to file_out
    assert "T_A_K" in lua
    assert "T_B_K" in lua

    # Must have PY2FEMM_DONE sentinel (from close())
    assert "PY2FEMM_DONE" in lua

    # Must end with quit()
    lines = lua.strip().splitlines()
    assert lines[-1].strip() == "quit()"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_optimizer_lua.py::test_build_model_produces_valid_lua -v`
Expected: FAIL — `[1]` is in the lua (current code uses `T_A[1]`)

- [ ] **Step 3: Fix the Lua generation in build_model()**

In `examples/heatflow/heatsink/heatsink_optimize.py`, replace lines 262-267:

**Old:**
```python
    for label, chip, x_left, x_right in chips:
        cx = (x_left + x_right) / 2
        problem.lua_script.append(f"T_{label} = ho_getpointvalues({cx}, 0)")
        problem.lua_script.append(
            f'write(file_out, "T_{label}_K = ", T_{label}[1], "\\n")'
        )
```

**New:**
```python
    for label, chip, x_left, x_right in chips:
        cx = (x_left + x_right) / 2
        problem.lua_script.append(f"T_{label} = ho_getpointvalues({cx}, 0)")
        problem.lua_script.append(
            f'write(file_out, "T_{label}_K = ", T_{label}, "\\n")'
        )
```

In FEMM's Lua 4.0, `T_A = ho_getpointvalues(x, y)` assigns the first return value (temperature) to `T_A`. No table indexing needed.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_optimizer_lua.py::test_build_model_produces_valid_lua -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_optimize.py tests/test_optimizer_lua.py
git commit -m "fix: remove Lua table indexing from optimizer ho_getpointvalues calls"
```

---

### Task 4: Add sys.path Setup for Example Imports in Tests

**Files:**
- Modify: `pyproject.toml` (add examples to test path discovery) OR add `conftest.py`

The test in Task 3 imports from `examples.heatflow.heatsink.heatsink_optimize`. This requires the examples directory to be importable. Add a `conftest.py` that puts the examples dir on `sys.path`.

- [ ] **Step 1: Create conftest.py fixture for example imports**

Create `tests/conftest.py` (or add to existing):

```python
import sys
from pathlib import Path

# Make examples importable for tests that validate generated Lua
_examples_dir = str(Path(__file__).resolve().parent.parent / "examples" / "heatflow" / "heatsink")
if _examples_dir not in sys.path:
    sys.path.insert(0, _examples_dir)
```

- [ ] **Step 2: Update the test import**

In `tests/test_optimizer_lua.py`, change the import to use the module directly (since conftest adds the dir to sys.path):

```python
from heatsink_optimize import (
    OptimConfig, ChipConfig, HeatsinkConfig, build_model,
)
```

- [ ] **Step 3: Run the test**

Run: `pytest tests/test_optimizer_lua.py -v`
Expected: PASS

- [ ] **Step 4: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/test_optimizer_lua.py
git commit -m "test: add conftest.py for example imports in test suite"
```

---

### Task 5: Integration Validation — Tutorial Still Works

**Files:**
- No code changes — validation only

After the executor and sentinel changes, verify the existing tutorial still works end-to-end.

- [ ] **Step 1: Start the py2femm server**

Run: `start_femm_server.bat` (manually, in a separate terminal)
Wait for "Uvicorn running on http://0.0.0.0:8082"

- [ ] **Step 2: Run the tutorial with --no-plot**

Run: `python examples/heatflow/heatsink/heatsink_tutorial.py --no-plot --no-parametric`
Expected: Completes in ~4-8s, prints `Average temperature: ~334 K`, `R_th ~ 3.6 K/W`

- [ ] **Step 3: Run the tutorial parametric sweep**

Run: `python examples/heatflow/heatsink/heatsink_tutorial.py --no-plot`
Expected: All 4 fin counts (3, 5, 7, 9) complete successfully

- [ ] **Step 4: Note any issues**

If the tutorial fails, the sentinel or executor changes broke something. Debug before proceeding.

---

### Task 6: Integration Validation — Optimizer Single Eval

**Files:**
- No code changes — validation only

Test the optimizer with a single evaluation before running the full grid.

- [ ] **Step 1: Test single evaluation via Python REPL**

Run:
```bash
python -c "
import sys; sys.path.insert(0, 'examples/heatflow/heatsink')
from heatsink_optimize import OptimConfig, ChipConfig, HeatsinkConfig, build_model, evaluate
from py2femm.client import FemmClient

cfg = OptimConfig(
    chip_a=ChipConfig(name='ChipA', power=5.0),
    chip_b=ChipConfig(name='ChipB', power=15.0),
    heatsink=HeatsinkConfig(base_w=210.0, base_h=297.0, base_t=5.0),
    timeout=60,
)
client = FemmClient(mode='remote', url='http://localhost:8082')
result = evaluate(cfg, client, x_a=70.0, y_a=0.0, x_b=140.0, y_b=0.0)
print(f'Result: {result}')
print(f'R_th_A: {result[\"R_th_A\"]:.3f}, R_th_B: {result[\"R_th_B\"]:.3f}')
"
```
Expected: Returns a dict with `T_A_K`, `T_B_K`, `R_th_A`, `R_th_B`, `objective` — all finite positive numbers.

- [ ] **Step 2: If it fails, debug the generated Lua**

Save the Lua to a file and check for issues:
```bash
python -c "
import sys; sys.path.insert(0, 'examples/heatflow/heatsink')
from heatsink_optimize import OptimConfig, ChipConfig, HeatsinkConfig, build_model
cfg = OptimConfig(
    chip_a=ChipConfig(name='ChipA', power=5.0),
    chip_b=ChipConfig(name='ChipB', power=15.0),
    heatsink=HeatsinkConfig(base_w=210.0, base_h=297.0, base_t=5.0),
)
lua = build_model(cfg, x_a=70.0, y_a=0.0, x_b=140.0, y_b=0.0)
print(lua)
" > _debug_opt.lua
```
Then inspect the Lua for syntax errors, missing `closefile`, or incorrect `ho_getpointvalues` usage.

---

### Task 7: Run Full Optimizer (Small Grid)

**Files:**
- No code changes — validation only

- [ ] **Step 1: Run optimizer with 3x3 grid, no scipy, no plot**

Run: `python examples/heatflow/heatsink/heatsink_optimize.py --grid-n 3 --no-plot --no-scipy --timeout 60`
Expected: 3-6 feasible evaluations complete, each in ~3-8s. Prints `R_thA`, `R_thB`, `obj` for each.

- [ ] **Step 2: Run optimizer with 5x5 grid + scipy**

Run: `python examples/heatflow/heatsink/heatsink_optimize.py --grid-n 5 --max-iter 10 --no-plot --timeout 60`
Expected: Grid search + scipy optimization both complete. Summary shows best placement.

- [ ] **Step 3: Run optimizer with plots**

Run: `python examples/heatflow/heatsink/heatsink_optimize.py --grid-n 5 --max-iter 10 --timeout 60`
Expected: Three matplotlib plots appear: objective heatmap, Pareto front, best placement schematic.

---

### Task 8: Create Optimizer Jupyter Notebook

**Files:**
- Create: `examples/heatflow/heatsink/heatsink_optimize.ipynb`

Thin wrapper importing from `heatsink_optimize.py`. 5 code cells max.

- [ ] **Step 1: Create the notebook**

Create `examples/heatflow/heatsink/heatsink_optimize.ipynb` with this structure:

**Cell 0 (raw/markdown):**
```markdown
# 2-Chip Placement Optimization

Finds optimal chip positions on a heat sink to minimize weighted thermal resistance.

**Prerequisites:** py2femm server running on `localhost:8082`
```

**Cell 1 (code) — Imports + server check:**
```python
import sys
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path.cwd().resolve()
while repo_root.name and not (repo_root / "pyproject.toml").exists():
    repo_root = repo_root.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

example_dir = str(repo_root / "examples" / "heatflow" / "heatsink")
if example_dir not in sys.path:
    sys.path.insert(0, example_dir)

import heatsink_optimize as opt
from py2femm.client import FemmClient

import matplotlib
%matplotlib inline

assert opt.server_is_healthy(), "py2femm server not running on localhost:8082"
print("Server OK")

cfg = opt.OptimConfig(grid_n=5, max_iter=15, timeout=60)
client = FemmClient(mode="remote", url="http://localhost:8082")
print(f"Base: {cfg.heatsink.base_w}x{cfg.heatsink.base_h} mm")
print(f"ChipA: {cfg.chip_a.power}W, ChipB: {cfg.chip_b.power}W")
```

**Cell 2 (code) — Grid search:**
```python
grid_results = opt.brute_force(cfg, client)
print(f"\n{len(grid_results)} feasible points evaluated")
```

**Cell 3 (code) — Scipy refinement:**
```python
scipy_result = None
if grid_results:
    best_grid = min(grid_results, key=lambda r: r["objective"])
    scipy_result = opt.scipy_optimize(cfg, client, x0=(best_grid["x_a"], best_grid["x_b"]))
```

**Cell 4 (code) — Plot all results:**
```python
opt.plot_grid_results(cfg, grid_results, scipy_result)
```

- [ ] **Step 2: Verify notebook structure is valid JSON**

Run: `python -c "import json; json.load(open('examples/heatflow/heatsink/heatsink_optimize.ipynb'))"`
Expected: No error

- [ ] **Step 3: Commit**

```bash
git add examples/heatflow/heatsink/heatsink_optimize.ipynb
git commit -m "feat: add 2-chip optimizer Jupyter notebook"
```

---

### Task 9: Final Test Suite Run

**Files:**
- No code changes — validation only

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Run ruff linter**

Run: `ruff check py2femm/ py2femm_server/ tests/ examples/`
Expected: No errors (or only pre-existing ones)

- [ ] **Step 3: Final commit if any cleanup needed**

Only if previous steps revealed issues that needed small fixes.
