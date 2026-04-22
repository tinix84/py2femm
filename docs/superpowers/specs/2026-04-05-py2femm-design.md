# py2femm Design Spec

**Date:** 2026-04-05
**Status:** Approved
**Author:** tinix84 + Claude

## Overview

Fork of [tamasorosz/py2femm](https://github.com/tamasorosz/py2femm) into `tinix84/py2femm`, extended with pyplecs-style orchestration, caching, REST API, and a WSL-to-Windows bridge for running FEMM simulations remotely.

**License:** AGPL-3.0 (inherited from upstream)
**Upstream strategy:** Diverge freely, may rename in the future
**Target audience:** Open-source community (PyPI, docs, CI/CD)

## Problem Statement

FEMM is a Windows-only FEA solver. Users on WSL/Linux/Mac must manually:
1. Generate Lua scripts
2. Copy them to Windows
3. Run FEMM manually
4. Copy CSV results back

py2femm automates this entire pipeline with two bridge modes and adds caching, batching, and orchestration on top.

## Architecture

### Two-Component Model

```
+---------------------------+     +----------------------------+
|  WSL / Linux / Mac        |     |  Windows (FEMM installed)  |
|                           |     |                            |
|  py2femm client           |     |  py2femm server             |
|  - Lua generation         |     |  - FastAPI REST server     |
|  - Cache (SHA256)         |     |  - Filesystem watcher      |
|  - Orchestration          |     |  - FEMM subprocess exec    |
|  - CLI (py2femm run)      |     |  - Health monitoring       |
|                           |     |                            |
|  Bridge modes:            |     |                            |
|  1. Shared FS (/mnt/c/)   |     |                            |
|  2. REST API (HTTP)       |     |                            |
+---------------------------+     +----------------------------+
```

### Package Structure

```
py2femm/
├── pyproject.toml
├── setup_femm.bat              # One-time Windows setup
├── start_femm_server.bat        # Launch agent on Windows
├── py2femm/                    # Client library (runs anywhere)
│   ├── __init__.py
│   ├── core/                   # Lua generation engine
│   │   ├── problem.py          # FemmProblem (refactored from upstream monolith)
│   │   ├── geometry.py         # Node, Line, CircleArc, CubicBezier
│   │   ├── materials.py        # Base + per-physics material classes
│   │   ├── boundaries.py       # Base + per-physics BC classes
│   │   └── lua_writer.py       # Lua string builder, script assembly
│   ├── heatflow/               # Thermal-specific extensions
│   │   ├── materials.py        # HeatFlowMaterial (kx, ky, qv)
│   │   ├── boundaries.py       # Convection, radiation, flux, fixed-T
│   │   └── postprocess.py      # Thermal result extraction
│   ├── client/                 # Runs anywhere
│   │   ├── base.py             # Abstract client interface
│   │   ├── local.py            # Shared-filesystem mode (WSL /mnt/c/)
│   │   ├── remote.py           # REST client (HTTP to agent)
│   │   └── auto.py             # Auto-detect mode
│   ├── cache/                  # Phase 2
│   │   ├── hasher.py           # SHA256 of Lua script content
│   │   ├── store.py            # CSV/Parquet result storage
│   │   └── manager.py          # Cache-aware simulation dispatch
│   ├── orchestration/          # Phase 3
│   │   ├── queue.py            # Priority queue
│   │   ├── batch.py            # Batch parameter sweeps
│   │   └── executor.py         # Async orchestrator loop
│   └── config/                 # Hierarchical YAML config
│       ├── schema.py           # Dataclass-based config model
│       └── loader.py           # YAML discovery (cwd -> home -> package)
├── py2femm_server/              # Agent server (Windows only)
│   ├── __init__.py
│   ├── server.py               # FastAPI REST endpoints
│   ├── executor.py             # FEMM subprocess launcher
│   ├── watcher.py              # Shared-fs file watcher
│   └── health.py               # Health check, FEMM version detection
├── tests/
├── examples/
└── docs/
```

### Installation

```bash
pip install py2femm              # Client only (WSL/Linux/Mac)
pip install py2femm[agent]       # + FastAPI, uvicorn (Windows)
pip install py2femm[dev]         # + pytest, ruff
pip install py2femm[all]         # Everything
```

## Communication Protocol

### Bridge Mode 1: Shared Filesystem (WSL local)

```
WSL                              Windows
1. Client writes                 
   /mnt/c/femm_workspace/       
   jobs/job_<uuid>.lua           
                                 2. Agent watcher detects .lua
                                 3. femm.exe -lua-script=job.lua
                                 4. FEMM writes job_<uuid>.csv
5. Client polls for .csv,
   reads result, cleans up
```

- Default workspace: `/mnt/c/femm_workspace/`
- Atomic writes: `.tmp` then rename to `.lua`
- Client polls for result with configurable timeout (default 300s)
- Agent runs as `python -m py2femm_server watch` or via `start_femm_server.bat`

### Bridge Mode 2: REST API (remote/VM)

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/jobs` | Submit Lua script, returns `job_id` |
| `GET` | `/api/v1/jobs/{job_id}` | Job status + results |
| `POST` | `/api/v1/jobs/batch` | Submit multiple Lua scripts |
| `GET` | `/api/v1/health` | FEMM version, agent status, queue depth |
| `DELETE` | `/api/v1/jobs/{job_id}` | Cancel pending job |

**Job lifecycle:** `submitted -> queued -> running -> completed | failed`

**Request (POST /api/v1/jobs):**
```json
{
  "lua_script": "hi_probdef(...)...",
  "timeout_s": 300,
  "result_format": "csv",
  "metadata": {"model": "extruded-fin", "source": "thermal-cli"}
}
```

**Response (GET /api/v1/jobs/{id}):**
```json
{
  "job_id": "abc-123",
  "status": "completed",
  "submitted_at": "2026-04-05T10:00:00Z",
  "completed_at": "2026-04-05T10:00:12Z",
  "result": {
    "csv_data": "point,x,y,temperature_K\n..."
  },
  "error": null
}
```

### Auto-Detection

```python
from py2femm.client import FemmClient

client = FemmClient()  # auto-detects mode
# 1. /mnt/c/ exists -> shared filesystem
# 2. PYFEMM_AGENT_URL env var -> REST
# 3. ~/.py2femm/config.yml -> configured URL
# 4. Raises ConnectionError with setup instructions
```

## Windows Batch Files

### setup_femm.bat (one-time)

1. Scan for Python + conda (PATH + common install dirs)
2. Choose env (existing conda env or new venv)
3. Activate env + `pip install py2femm[agent]`
4. Auto-detect FEMM path (scan `C:\femm42\`, `C:\Program Files\femm42\`, etc.)
5. Configure shared workspace directory (default `C:\femm_workspace\`)
6. Save settings to `config/default.yml`

### start_femm_server.bat (launcher)

1. Read env config from `config/default.yml`
2. Bootstrap conda if needed
3. Activate environment
4. Read FEMM path from config
5. Start: `python -m py2femm_server serve --host 0.0.0.0 --port 8082`
6. Agent serves both REST API and shared-filesystem watcher

## Python API

### Lua Generation

```python
from py2femm.core import FemmProblem
from py2femm.heatflow import HeatFlowMaterial, ConvectionBC, HeatFluxBC

problem = FemmProblem(problem_type="heatflow", units="meters", mode="planar")

# Geometry
problem.add_node(0, 0)
problem.add_node(0.05, 0)
problem.add_node(0.05, 0.01)
problem.add_node(0, 0.01)
problem.add_segment(0, 1)
problem.add_segment(1, 2)
problem.add_segment(2, 3)
problem.add_segment(3, 0)

# Materials & BCs
problem.add_material(HeatFlowMaterial("aluminum", kx=200, ky=200))
problem.add_boundary(HeatFluxBC("source", flux=5000))
problem.add_boundary(ConvectionBC("cooling", h=50, t_ambient=300))

# Assign
problem.set_block_material(0.025, 0.005, "aluminum")
problem.set_segment_bc(0, "source")
problem.set_segment_bc(2, "cooling")

lua_script = problem.to_lua()
```

### Running Simulations

```python
from py2femm.client import FemmClient

client = FemmClient()
result = client.run(lua_script, timeout=300)
print(result.csv_data)
print(result.to_dataframe())

# Or run pre-built Lua from Octave
with open("drofenik_heatsink.lua") as f:
    result = client.run(f.read())
```

### Batch Sweep (Phase 2)

```python
from py2femm.cache import CachedClient

client = CachedClient(FemmClient())
scripts = [build_problem(h=h).to_lua() for h in [25, 50, 100, 200]]
results = client.run_batch(scripts)  # cached ones skip FEMM
```

## CLI

```bash
py2femm run <script.lua>          # Run single Lua, print results
py2femm run-batch <dir/>          # Run all .lua in directory
py2femm status                    # Agent status, queue depth
py2femm config                    # Show/edit configuration
py2femm cache stats               # Cache hit rate, disk usage
py2femm cache clear               # Clear cache
py2femm server serve               # Start REST agent (Windows)
py2femm server watch               # Start filesystem watcher (Windows)
```

### Integration with Octave thermal_cli

```bash
# Generate Lua in Octave (existing workflow, unchanged)
octave thermal_cli.m gen-femm --model drofenik --config cfg.m --output job.lua

# Submit to py2femm
py2femm run job.lua --output results.csv
```

## Agent Executor

### FEMM Launch

```python
class FemmExecutor:
    def run(self, lua_script: str, timeout: int = 300) -> ExecutionResult:
        # 1. Write Lua to temp file in job directory
        # 2. Inject preamble with output path variable
        # 3. Launch: femm.exe -lua-script=<path>
        # 4. Wait for completion (subprocess with timeout)
        # 5. Read CSV output
        # 6. Clean up temp files
        # 7. Return ExecutionResult(csv_data, elapsed_s, returncode)
```

### Lua Preamble Injection

Agent injects output path into every Lua script:

```lua
-- Injected by py2femm server
py2femm_workdir = "C:\\femm_workspace\\jobs\\abc123\\"
py2femm_outfile = py2femm_workdir .. "results.csv"
```

User Lua scripts use `py2femm_outfile` for output. Octave generators need minimal change: use `py2femm_outfile` if defined, else fall back to hardcoded name.

### Error Handling

| Failure | Detection | Response |
|---------|-----------|----------|
| FEMM not found | `shutil.which()` at startup | Agent refuses to start |
| FEMM crashes | Non-zero returncode | Job `failed`, stderr captured |
| Timeout | `subprocess.TimeoutExpired` | Process killed, job `failed` |
| No CSV output | File missing after exit | Job `failed`, descriptive error |
| Malformed CSV | Parse error | Job `failed`, raw file preserved |

## Caching (Phase 2)

### Strategy

- **Key:** `SHA256(lua_script_content)`
- **Lookup:** Client-side, before contacting agent
- **Storage:** `~/.py2femm/cache/` with 2-level directory sharding

```
~/.py2femm/cache/
├── index.json
├── ab/cd/abcd1234.csv
└── ab/cd/abcd1234.meta.json
```

- `py2femm run --no-cache` to bypass
- Configurable max cache size (default 5 GB)

## Configuration

### Hierarchical YAML Discovery

```
1. ./py2femm.yml          # project-local
2. ../py2femm.yml         # parent dirs (walk up)
3. ~/.py2femm/config.yml  # user global
4. package defaults       # built-in
```

### Schema

```yaml
agent:
  mode: auto              # auto | local | remote
  url: http://localhost:8082
  workspace: /mnt/c/femm_workspace

femm:
  path: C:\femm42\bin\femm.exe
  timeout: 300
  headless: true

cache:
  enabled: true
  dir: ~/.py2femm/cache
  max_size_gb: 5

results:
  format: csv             # csv | parquet
  dir: ./results
```

## Orchestration (Phase 3)

```python
from py2femm.orchestration import Orchestrator, Priority

orch = Orchestrator(client)
task_id = orch.submit(lua_script, priority=Priority.HIGH)

orch.submit_batch(scripts, on_complete=callback)
orch.wait_all()
```

- Priority queue: CRITICAL > HIGH > NORMAL > LOW
- Max concurrent: 1 (FEMM is single-instance)
- Retry: up to 2 times on failure
- Batch grouping: N scripts managed as one unit

## Web GUI (Phase 4)

Minimal HTML + SSE dashboard at `http://localhost:8082/dashboard`:

- Queue status (pending/running/completed/failed)
- Current job details and elapsed time
- Job history (last 50)
- Cache statistics (hit rate, disk usage)
- Agent health (FEMM path, version, uptime)

No JavaScript framework. Plain HTML + Server-Sent Events.

## CI/CD & Publishing

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `lint.yml` | Every push | ruff + mypy |
| `test.yml` | Every push | pytest unit tests (no FEMM) |
| `test-integration.yml` | Manual / weekly | Windows runner + FEMM |
| `release.yml` | Tag `v*` | Build wheel, publish to PyPI |

## Phasing

| Phase | Scope | Dependencies |
|-------|-------|-------------|
| **1 - Core MVP** | Lua generation (heat flow), local executor, REST agent, REST client, basic result parsing, bat files, CLI | Fork py2femm, refactor |
| **2 - Automation** | SHA256 caching, batch parameter sweeps, hierarchical YAML config | Phase 1 |
| **3 - Orchestration** | Priority queue, async callbacks, Parquet storage | Phase 2 |
| **4 - Polish** | Web GUI, magnetics/electrostatics/current-flow support, CI/CD, docs, PyPI publish | Phase 3 |

## Relationship to thermal repo

- **Coexist:** Octave thermal_cli generates Lua, py2femm executes it
- Lua generators in thermal repo remain unchanged (minor addition: use `py2femm_outfile` if defined)
- `thermal_cli.m compare-femm` continues to work with CSV results from py2femm

## Non-Goals

- 3D support (FEMM is 2D/axisymmetric only)
- Replacing FEMM's own GUI
- Real-time interactive control of FEMM (batch-oriented only)
- Multi-instance FEMM parallelism (FEMM is single-instance)
