# CLAUDE.md — py2femm

## Project Overview

py2femm is a Python automation platform for FEMM (Finite Element Method Magnetics) 2D finite element simulations. It generates Lua scripts from a Python API and executes them via a FastAPI REST server that subprocess-launches FEMM on Windows. Supports four physics domains: magnetics, electrostatics, heat flow, and current flow, in both planar and axisymmetric geometries. License: AGPL-3.0-or-later.

## Architecture at a Glance

```
py2femm/ (client library, any platform)     py2femm_server/ (Windows + FEMM)
─────────────────────────────────────────    ────────────────────────────────
FemmProblem  →  builds Lua script string     server.py (FastAPI)
FemmClient   →  sends Lua over HTTP    ───►  executor.py (subprocess femm.exe)
                 receives CSV results  ◄───  job_store.py (in-memory state)
```

- `FemmProblem` accumulates Lua commands in `self.lua_script` (a list of strings). Call `.write(path)` to save or `"\n".join(problem.lua_script)` to get the script.
- `FemmClient` (in `py2femm/client/auto.py`) auto-detects transport: local shared-filesystem (WSL `/mnt/c/`), remote REST (`PYFEMM_AGENT_URL` env var), or `~/.py2femm/config.yml`. Explicit `mode="remote"` / `mode="local"` overrides auto-detection.
- The server receives Lua via `POST /submit`, runs FEMM in a temp directory, and returns CSV output via `GET /result/{job_id}`.

## Key Entry Points

| Symbol | Location | Purpose |
|--------|----------|---------|
| `FemmProblem` | `py2femm/femm_problem.py` | Lua script generator — geometry, materials, BCs, analysis |
| `FemmClient` | `py2femm/client/auto.py` | Auto-detecting client (also re-exported from `py2femm.client`) |
| `ClientResult` | `py2femm/client/base.py` | Result dataclass: `.csv_data`, `.error`, `.job_id` |
| `create_app()` | `py2femm_server/server.py` | FastAPI app factory — pass `femm_path`, `workspace`, `headless` |
| `FemmExecutor` | `py2femm_server/executor.py` | Subprocess runner — launches `femm.exe -lua-script=<path>` |
| `Geometry` | `py2femm/geometry.py` | `Node`, `Line`, `CircleArc`, `Geometry` container |
| Physics modules | `py2femm/{magnetics,electrostatics,heatflow,current_flow}.py` | Material and BC dataclasses per physics domain |

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_geometry.py -v
```

- **Unit tests** (geometry, config, client mocking, parametric config): run without FEMM
- **Integration tests** (`test_integration.py`, `test_server_executor.py`): require a live FEMM server on `localhost:8082`; these are guarded by health-check skips
- New test files go in `tests/` with the naming pattern `test_<module>.py`
- Use `pytest.mark.skipif` with a server health check for tests that need FEMM

## Code Style

- **Type hints** on all function signatures
- **Dataclasses** for data (materials, BCs, configs); Pydantic models for API request/response
- `from __future__ import annotations` at the top of every module
- **ruff** config: `line-length = 120`, `target-version = "py310"`, lint rules `E, F, W, I`
- Import order: stdlib / third-party / first-party (enforced by ruff `I` rule)
- No `E501` enforcement (long lines tolerated where readability is better)

## Gotchas

### FEMM Lua 4.0 (not 5.x)
FEMM uses Lua 4.0. There is no table indexing on multi-return values. Do NOT write `local t = {func()}; t[1]`. Instead assign the first return value directly: `val = func(x, y)`.

### `get_point_values()` limitation
`FemmProblem.get_point_values()` only works for magnetic and electrostatic problems. For heat flow post-processing, emit raw Lua: `ho_getpointvalues(x, y)` returns temperature as the first value.

### `ho_savebitmap` — no underscore
The FEMM 4.2 Lua reference uses `ho_savebitmap(filename)`, not `ho_save_bitmap`. Similarly for other `ho_*` functions. Check the FEMM 4.2 manual before adding new Lua commands.

### Bottom segments default to insulated
In FEMM, segments with no assigned BC default to zero flux (insulated). Bottom segments at y=0 should NOT have convection assigned unless the physical setup requires it. This was a past bug that caused T_avg to read ~334K instead of ~339K (verified against analytical energy balance: h×A×ΔT ≈ 10W).

### Node deduplication
When building polygon outlines programmatically (e.g., fin zigzag patterns), consecutive duplicate nodes can occur. Deduplicate with a 1e-6 tolerance before creating `Line` segments, or FEMM will reject the geometry.

### Coordinate system
FEMM 2D models use (x, y) for planar problems and (r, z) for axisymmetric. The `type` parameter in `heat_problem()` / `mag_problem()` controls this. Label points for `define_block_label()` must be strictly inside the region.

## Common Tasks

### Add a new physics field
1. Create `py2femm/<field>.py` with material and BC dataclasses (follow `heatflow.py` pattern)
2. Add `<field>_problem()` method to `FemmProblem` in `femm_problem.py`
3. Add Lua prefix constants (`xi_`/`xo_` for preprocessor/postprocessor)
4. Add tests in `tests/test_<field>_problem.py`
5. Update the physics table in `README.md`

### Add a new example
1. Create a directory under `examples/<physics>/<name>/`
2. Add a `.py` module with the simulation logic
3. Optionally add a `.ipynb` notebook that imports the module
4. List it in the Examples section of `README.md`

### Add a new BC type
1. Add a dataclass to the relevant physics module (e.g., `heatflow.py`)
2. Implement `to_lua()` or the equivalent Lua emission in `FemmProblem`
3. Add a test verifying the generated Lua string

### Run examples locally
1. Start the server: `start_femm_server.bat` (or `python -m py2femm_server --port 8082`)
2. Run a script: `python examples/heatflow/heatsink/heatsink.py`
3. For notebooks: `jupyter lab` and open from `examples/`

## File Layout

```
py2femm/
├── py2femm/                     # Client library (runs anywhere)
│   ├── __init__.py              #   Version string
│   ├── femm_problem.py          #   FemmProblem — central Lua builder
│   ├── geometry.py              #   Node, Line, CircleArc, Geometry
│   ├── general.py               #   FemmFields enum, LengthUnit, base classes
│   ├── magnetics.py             #   Magnetic materials & BCs
│   ├── electrostatics.py        #   Electrostatic materials & BCs
│   ├── heatflow.py              #   Heat flow materials & BCs
│   ├── current_flow.py          #   Current flow materials & BCs
│   ├── cli.py                   #   Click CLI (run, run-batch, status)
│   └── client/                  #   Client package
│       ├── auto.py              #     FemmClient (auto-detecting)
│       ├── base.py              #     FemmClientBase, ClientResult
│       ├── local.py             #     LocalClient (shared filesystem)
│       └── remote.py            #     RemoteClient (HTTP)
│
├── py2femm_server/              # REST server (Windows only)
│   ├── server.py                #   FastAPI app factory
│   ├── executor.py              #   FEMM subprocess launcher
│   ├── job_store.py             #   In-memory job tracking
│   ├── health.py                #   FEMM installation checks
│   └── watcher.py               #   Filesystem watcher mode
│
├── examples/                    # Worked examples
│   ├── heatflow/heatsink/       #   Heat sink baseline + parametric study
│   ├── electrostatics/          #   Capacitor, double-L domain
│   └── magnetics/               #   Motors, solenoids, reluctance machines
│
├── tests/                       # pytest suite
├── docs/superpowers/            # Design specs and implementation plans
│   ├── specs/                   #   Design documents
│   └── plans/                   #   Step-by-step implementation plans
│
├── pyproject.toml               # Package metadata, ruff config, pytest config
├── setup_femm.bat               # Windows environment setup
└── start_femm_server.bat        # Server launcher
```

## Links to Design Documents

- **Phase 1 MVP spec:** `docs/superpowers/specs/2026-04-05-py2femm-design.md`
- **Phase 1 MVP plan:** `docs/superpowers/plans/2026-04-05-py2femm-phase1-mvp.md`
- **Executor fix + optimizer:** `docs/superpowers/specs/2026-04-12-executor-fix-and-optimizer-design.md`
- **Heatsink parametric design:** `docs/superpowers/specs/2026-04-12-heatsink-parametric-design.md`
- **Heatsink parametric plan:** `docs/superpowers/plans/2026-04-12-heatsink-parametric-study.md`
