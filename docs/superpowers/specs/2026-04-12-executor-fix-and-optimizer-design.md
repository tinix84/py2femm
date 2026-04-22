# Design: FEMM Executor Fix + 2-Chip Optimization Example

**Date:** 2026-04-12
**Status:** Draft

## Problem Statement

Two tasks blocked by one root cause:

1. **FEMM executor reliability** — The `py2femm_server` executor has bugs that cause FEMM jobs to time out or produce empty results. The `heatsink_tutorial.py` works (4s per solve), but sequential or new models fail.
2. **2-chip placement optimizer** — Cannot run because it depends on reliable batch execution.

## Bugs Found (This Session)

### Bug 1: `init_problem` triple-append — FIXED
`FemmProblem.init_problem()` called `self.lua_script.extend(cmd_list)` three times on a growing list, producing triplicated `newdocument()`, `openfile()`, and `remove()` commands. **Fixed** by rewriting to a single `extend()`.

### Bug 2: `close()` missing `closefile(file_out)` — FIXED  
`FemmProblem.close()` only called `closefile(file_out)` when `elements=True`. Without it, the Lua file handle was never flushed. **Fixed** by always calling `closefile(file_out)` and `closefile(point_values)`.

### Bug 3: FEMM process hangs after `quit()` — OPEN / ROOT CAUSE UNCLEAR

**Symptoms:**
- FEMM solves correctly (`.feh` and `.anh` files created in ~3s)
- `results.csv` is 0 bytes (data written by Lua `write()` but never flushed to disk)
- FEMM process doesn't terminate — `proc.communicate()` blocks until timeout (300s)
- After timeout, `proc.kill()` destroys the process and OS buffers are lost

**Observations:**
- The `heatsink_tutorial.py` (144-line Lua, 35mm finned geometry) works reliably (4s)
- The `heatsink_optimize.py` (69-line Lua, simple rectangle) times out every time
- Both produce structurally identical Lua (1 newdocument, 2 openfile, 2 closefile, 1 quit)
- Even running the optimizer's model with a 35mm base times out
- The server shows `running=0` and new jobs appear to not create fresh job directories

**Hypothesis:** The server's thread-based executor may have stale state, or FEMM's `-windowhide` mode has edge cases where `quit()` doesn't terminate the process for certain Lua scripts. The difference between working/broken scripts could be:
- The `remove()` line referencing a non-existent file
- The `ho_getpointvalues()` returning a table and indexing with `[1]` (Lua 4.0 syntax)
- A server-side issue where the thread from a previous job blocks new jobs

## Proposed Approach

### Phase 1: Fix the Executor (must work before optimizer)

**Strategy: File-polling instead of proc.communicate()**

Instead of waiting for FEMM to terminate (which hangs), poll for the output file:

```
1. Start FEMM subprocess (don't wait for it)
2. Poll results.csv every 0.5s for non-zero size
3. Once results.csv has data, read it
4. Kill FEMM process (don't rely on quit())
5. Return results
```

This sidesteps the `quit()` hang entirely. FEMM writes `closefile(file_out)` which flushes to disk, then we kill the process regardless.

**Implementation in `executor.py`:**
```python
def run(self, lua_script, timeout=300):
    job_dir, lua_path = self.prepare_job(lua_script)
    cmd = [str(self.femm_path), f"-lua-script={str(lua_path.resolve())}"]
    if self.headless:
        cmd.append("-windowhide")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    result_path = job_dir / "results.csv"
    deadline = time.time() + timeout
    poll_interval = 0.5
    
    while time.time() < deadline:
        time.sleep(poll_interval)
        # Check if results file has been written AND closed
        if result_path.exists() and result_path.stat().st_size > 0:
            # Wait a beat for file to be fully flushed
            time.sleep(0.2)
            csv_data = result_path.read_text(encoding="utf-8")
            if csv_data.strip():
                proc.kill()
                proc.wait()
                return csv_data, 0
        # Check if process died on its own
        if proc.poll() is not None:
            csv_data = self.read_result(job_dir)
            return csv_data, proc.returncode
    
    # Timeout
    proc.kill()
    proc.wait()
    csv_data = self.read_result(job_dir)
    if csv_data:
        return csv_data, 0
    return None, -1
```

**Also add a sentinel marker** in the Lua script to detect completion reliably. Before `quit()`, write a known marker to results.csv:
```lua
write(file_out, "PY2FEMM_DONE\n")
closefile(file_out)
```
Then poll for `PY2FEMM_DONE` in the file to confirm all writes are complete.

**Validation:** Re-run `heatsink_tutorial.py --no-plot` and the optimizer's single-eval test.

### Phase 2: Debug the Lua Difference

After Phase 1 (file-polling) is working, investigate why the optimizer Lua specifically fails. Test plan:
1. Submit the optimizer's raw Lua (from `_debug_opt.lua`) directly via `FemmClient`
2. Manually run it in FEMM GUI to check for Lua errors (the `T_A[1]` indexing is Lua 4.0, should work but verify)
3. If it works in GUI but not headless, the issue is `-windowhide` specific

### Phase 3: 2-Chip Optimization Example

`heatsink_optimize.py` is already written and structurally correct. Once the executor works:

**Config (dataclasses, all parametric):**
- `ChipConfig`: name, width, height, power
- `HeatsinkConfig`: base_w (210mm A4), base_h (297mm), base_t, fin params, thermal params
- `OptimConfig`: chip_a, chip_b, constraints, weights, grid_n, max_iter, timeout

**Geometry:** Simple rectangle (no fins) — fast mesh. Convection h_conv represents effective fin-enhanced coefficient.

**Design variables:** (x_A, x_B) — chip center positions along the base width. y is fixed at 0 (bottom edge, 2D planar).

**Objective:** `w_A * R_th_A + w_B * R_th_B` (weighted sum, default equal weights)

**Constraints:** chips within base margins, non-overlap with min gap

**Methods:**
1. Brute-force grid (grid_n x grid_n, default 10x10)
2. scipy Nelder-Mead (starting from best grid point)

**Plots:**
1. Objective heatmap (x_A vs x_B colored by objective)
2. Pareto front (R_th_A vs R_th_B)
3. Best placement schematic

**Jupyter notebook:** Thin wrapper importing from `heatsink_optimize.py`, just calls functions and displays plots inline. 5 code cells max.

### Phase 4: Notebook

Minimal notebook importing `heatsink_optimize` functions:
- Cell 0: imports + server check
- Cell 1: run grid search
- Cell 2: run scipy
- Cell 3: plot all results
- Cell 4: display best placement

## Files to Modify

| File | Change |
|---|---|
| `py2femm_server/executor.py` | Rewrite `run()` to use file-polling instead of `proc.communicate()` |
| `py2femm/femm_problem.py` | Add `PY2FEMM_DONE` sentinel before `quit()` in `close()` |
| `examples/heatflow/heatsink/heatsink_optimize.py` | Already written, may need small fixes after executor is working |
| `examples/heatflow/heatsink/heatsink_tutorial.py` | Re-test after executor changes |
| `examples/heatflow/heatsink/heatsink_tutorial.ipynb` | Re-test after executor changes |
| `tests/test_server_executor.py` | Update tests for new polling behavior |

## Execution Order

1. Fix executor (file-polling) + sentinel marker
2. Verify tutorial still works
3. Verify optimizer single-eval works
4. Run optimizer end-to-end (grid 3x3, then 5x5)
5. Build notebook
6. Run tests

## Risk

- File-polling may miss edge cases (partial writes, FEMM crashes before closefile)
- The sentinel marker approach adds a dependency between FemmProblem and the executor
- FEMM 4.2 Lua 4.0 table indexing (`T[1]`) may behave differently than expected
