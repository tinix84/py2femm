# py2femm Architecture

This document describes the internal architecture of py2femm for contributors
and advanced users. It assumes familiarity with FEMM and basic Python packaging.

---

## Overview

py2femm is split into two cooperating packages:

```
+--------------------------+       HTTP / REST       +--------------------------+
|  py2femm (client)        | ---------------------> |  py2femm_server          |
|  Runs anywhere           | <--------------------- |  Runs on Windows + FEMM  |
|                          |      JSON results       |                          |
|  - Lua script generation |                         |  - FastAPI app           |
|  - Geometry primitives   |                         |  - FEMM subprocess exec  |
|  - Materials & BCs       |                         |  - Job lifecycle mgmt    |
|  - Client (auto/local/   |                         |  - FS watcher (optional) |
|    remote)               |                         |  - Health detection      |
|  - CLI (run, status)     |                         |                          |
+--------------------------+                         +--------------------------+
```

**Why not pyFEMM / ActiveX?**

pyFEMM drives FEMM through COM/ActiveX, which is Windows-only and
single-process. py2femm generates plain-text Lua scripts instead:

- Scripts can be generated on Linux/Mac, transferred to a Windows host, and
  executed there -- enabling Wine, Docker, and WSL workflows.
- A REST server decouples the client from the solver machine, allowing
  multi-client, remote, and CI/CD usage.
- Lua files are human-readable and debuggable outside Python.

---

## Client Library (`py2femm/`)

### FemmProblem -- the Lua accumulator

`py2femm/femm_problem.py` contains `FemmProblem`, the central class.
It maintains an ordered list of Lua command strings (`self.lua_script`)
and provides Python methods that append to that list.

```
problem = FemmProblem(out_file="results.csv")
problem.heat_problem(...)      # appends hi_probdef(...)
problem.create_geometry(geom)  # appends hi_addnode / hi_addsegment / ...
problem.add_material(mat)      # appends hi_addmaterial(...)
...
problem.write("sim.lua")       # flushes list to a .lua file
```

Key attributes:

| Attribute             | Purpose                                       |
|-----------------------|-----------------------------------------------|
| `self.field`          | `FemmFields` enum -- determines Lua prefix     |
| `self.lua_script`     | `list[str]` -- accumulated Lua commands        |
| `self.out_file`       | CSV filename written by the Lua script         |
| `self.integral_counter` | Counter for sequential block integrals       |

When `write()` is called, all accumulated strings are joined with newlines
and written to a file. If `close_after=True` (the default), a
`closefemm()` command and a `PY2FEMM_DONE` sentinel file write are
appended so the server can detect completion.

### Physics modules

Each of the four supported physics has its own module:

| Module               | Lua prefix (input/output) | Key classes                              |
|----------------------|---------------------------|------------------------------------------|
| `magnetics.py`       | `mi_` / `mo_`             | `MagneticMaterial`, `MagneticBoundary`   |
| `electrostatics.py`  | `ei_` / `eo_`             | `ElectrostaticMaterial`, `ElectrostaticBoundary` |
| `heatflow.py`        | `hi_` / `ho_`             | `HeatFlowMaterial`, `HeatFlowConvection`, `HeatFlowHeatFlux`, ... |
| `current_flow.py`    | `ci_` / `co_`             | `CurrentFlowMaterial`, `CurrentFlowBoundary` |

All material classes inherit from `general.Material` (a dataclass with
`material_name`, `auto_mesh`, `mesh_size`). All BC classes inherit from
`general.Boundary` (a dataclass with `name`, `type`, `boundary_edges`).

Each subclass implements `__str__` to return the FEMM Lua command that
defines that material or boundary, e.g.:

```python
str(HeatFlowMaterial("aluminum", kx=200, ky=200, qv=0, kt=0))
# => 'hi_addmaterial("aluminum", 200, 200, 0, 0)'
```

### Geometry primitives

`py2femm/geometry.py` provides physics-independent shape classes:

- **`Node`** -- (x, y) point with arithmetic, rotation, mirroring, clone.
- **`Line`** -- two-node segment with midpoint and distance queries.
- **`CircleArc`** -- three-node arc (start, center, end).
- **`Sector`** -- alternative arc definition (start, end, angle in degrees),
  converts to `CircleArc`.
- **`CubicBezier`** -- Bezier curve with de Casteljau subdivision.
- **`Geometry`** -- container holding lists of nodes, lines, arcs, and
  beziers. Supports `+` (concatenation), `duplicate()`, `mirror()`,
  `rotate_about()`, DXF import, and duplicate-node merging.

Because geometry is separated from physics, the same `Geometry` object can be
reused for magnetic, thermal, and electrostatic analyses of the same shape.

### Client modes

The `py2femm/client/` subpackage provides three client implementations:

```
FemmClientBase (ABC)
    |
    +-- LocalClient    (shared-filesystem bridge via /mnt/c/)
    +-- RemoteClient   (REST API via httpx)
    +-- FemmClient     (auto-detecting wrapper)
```

**`auto.py` / `FemmClient`** -- the default entry point. Detection order:

1. Explicit `mode`/`url` arguments
2. `/mnt/c/` exists --> `LocalClient` (WSL shared filesystem)
3. `PYFEMM_AGENT_URL` environment variable --> `RemoteClient`
4. `~/.py2femm/config.yml` agent URL --> `RemoteClient`
5. Raise `ConnectionError` with setup instructions

**`local.py` / `LocalClient`** -- writes `.lua` files to a shared directory,
polls for a `.csv` result file.

**`remote.py` / `RemoteClient`** -- POSTs Lua scripts to the REST API, polls
`GET /api/v1/jobs/{id}` until completion or timeout.

---

## REST Server (`py2femm_server/`)

### FastAPI app (`server.py`)

`create_app(femm_path, workspace, headless)` returns a FastAPI application
with the following endpoints:

| Method   | Path                   | Purpose                      |
|----------|------------------------|------------------------------|
| `GET`    | `/api/v1/health`       | Server status, queue depth   |
| `POST`   | `/api/v1/jobs`         | Submit Lua script (202)      |
| `GET`    | `/api/v1/jobs/{id}`    | Job status + results         |
| `POST`   | `/api/v1/jobs/batch`   | Submit multiple scripts      |
| `GET`    | `/api/v1/jobs`         | List all jobs                |
| `DELETE` | `/api/v1/jobs/{id}`    | Cancel a pending job         |

Job execution happens in a background `threading.Thread`. The server is
single-threaded for FEMM access (FEMM is single-instance), but the FastAPI
event loop remains responsive for status queries.

### Job store (`job_store.py`)

`JobStore` is an in-memory dict-based store. Each job progresses through:

```
queued --> running --> completed
                  \--> failed
```

Fields per job: `job_id`, `status`, `lua_script`, `timeout_s`, `metadata`,
`submitted_at`, `completed_at`, `csv_data`, `error`.

Job IDs are 12-character hex strings from `uuid4`.

### Executor (`executor.py`)

`FemmExecutor` handles the FEMM subprocess lifecycle:

1. Create a job directory under the workspace (`workspace/job_<uuid>/`).
2. Inject a Lua preamble that sets `py2femm_workdir` and redirects all
   `openfile()` calls into the job directory.
3. Write the patched Lua script to `job.lua`.
4. Launch `femm.exe -lua-script=job.lua` as a subprocess.
5. Poll for a `PY2FEMM_DONE` sentinel file (written by `FemmProblem.close()`
   at the end of every script) instead of using `proc.communicate()`, which
   avoids pipe-buffer deadlocks.
6. Read `results.csv` from the job directory.
7. Return `(csv_data, returncode)`.

The preamble injection also rewrites relative `openfile(...)` paths so that
FEMM's unpredictable working directory does not cause missing output files.

### Health detection (`health.py`)

`find_femm()` searches for `femm.exe` in this order:

1. `FEMM_PATH` environment variable
2. `C:\femm42\bin\femm.exe`
3. `C:\Program Files\femm42\bin\femm.exe`
4. `C:\Program Files (x86)\femm42\bin\femm.exe`

Returns the first existing path, or `None`.

### Filesystem watcher (`watcher.py`)

`FileWatcher` provides the shared-filesystem bridge mode for WSL users.
It polls a directory for new `.lua` files and invokes a callback. This is
the counterpart to `LocalClient` on the server side.

---

## Execution Flow

The full simulation lifecycle, end to end:

```
 Python script             py2femm client           py2femm_server          FEMM
 ============             ==============           ===============         ====
      |                         |                         |                  |
  FemmProblem API               |                         |                  |
  (build geometry,              |                         |                  |
   materials, BCs)              |                         |                  |
      |                         |                         |                  |
  problem.write()               |                         |                  |
      |                         |                         |                  |
  lua_script (string)           |                         |                  |
      |                         |                         |                  |
      +-- client.run(lua) ----->|                         |                  |
                                |                         |                  |
                           POST /api/v1/jobs ------------>|                  |
                                |                   inject preamble          |
                                |                   write job.lua            |
                                |                         |                  |
                                |                   femm.exe -lua-script --->|
                                |                         |             solve FEA
                                |                         |             write CSV
                                |                         |             write DONE
                                |                   poll for DONE  <---------|
                                |                   read results.csv         |
                                |                         |                  |
                           GET /api/v1/jobs/{id}  <-------|                  |
                                |                         |                  |
      <-- ClientResult ---------|                         |                  |
      (csv_data, status)        |                         |                  |
```

For the **local (shared-filesystem) mode**, the REST layer is replaced by
file I/O through `/mnt/c/femm_workspace/`: the client writes `.lua`, the
server's watcher picks it up, and the client polls for the `.csv` result.

---

## Lua Generation Pattern

### Command accumulation

Every `FemmProblem` method that affects the simulation appends one or more
Lua strings to `self.lua_script`. The field prefix is determined by
`self.field.input_to_string()` (returns `"hi"`, `"mi"`, `"ei"`, or `"ci"`)
and `self.field.output_to_string()` (returns `"ho"`, `"mo"`, `"eo"`, `"co"`).

Two templating strategies coexist:

1. **`string.Template`** for geometry commands:
   ```python
   Template("${field}_addnode($x, $y)").substitute(field="hi", x=0.5, y=1.0)
   ```

2. **f-strings** for problem-definition commands:
   ```python
   f"hi_probdef('{units}', '{type}', {precision}, {depth}, {minangle})"
   ```

### Field prefixing

FEMM uses a two-letter prefix convention:

| Physics        | Input prefix | Output prefix |
|----------------|-------------|---------------|
| Magnetics      | `mi_`       | `mo_`         |
| Electrostatics | `ei_`       | `eo_`         |
| Heat Flow      | `hi_`       | `ho_`         |
| Current Flow   | `ci_`       | `co_`         |

The `FemmFields` enum encapsulates this mapping. When `FemmProblem` is set
to heat-flow mode, all geometry commands emit `hi_addnode`, `hi_addsegment`,
etc., and all post-processing commands emit `ho_blockintegral`,
`ho_getpointvalues`, etc.

### Script structure

A typical generated Lua script follows this order:

```lua
-- 1. Open FEMM and create new document
showconsole()
newdocument(2)                          -- 2 = heat flow

-- 2. Problem definition
hi_probdef("millimeters", "planar", 1e-8, 100, 30)

-- 3. Materials
hi_addmaterial("aluminum", 200, 200, 0, 0)

-- 4. Boundary conditions
hi_addboundprop("convection", 2, 0, 0, 298, 10, 0)

-- 5. Geometry (nodes, segments, arcs)
hi_addnode(0, 0)
hi_addnode(50, 0)
hi_addsegment(0, 0, 50, 0)
...

-- 6. Assign materials and BCs to regions/segments
hi_selectlabel(25, 5)
hi_setblockprop("aluminum", 1, 0, 0)
hi_clearselected()
...

-- 7. Save, mesh, analyze
hi_saveas("...")
hi_createmesh()
hi_analyze(0)
hi_loadsolution()

-- 8. Post-processing (extract results to CSV)
file_out = openfile("results.csv", "w")
write(file_out, ho_blockintegral(0), "\n")
closefile(file_out)

-- 9. Close FEMM and write sentinel
closefemm()
-- write PY2FEMM_DONE sentinel
```

---

## Extensibility

### Adding a new boundary condition type

1. Subclass `general.Boundary` in the appropriate physics module.
2. Set `self.type` to the FEMM BC type integer.
3. Implement `__str__` returning the Lua `<prefix>_addboundprop(...)` call.
4. No changes to `FemmProblem` are needed -- `add_boundary()` calls `str()`.

### Adding a new material type

Same pattern: subclass `general.Material`, implement `__str__` with the
appropriate `<prefix>_addmaterial(...)` command.

### Adding a new physics

1. Create `py2femm/<physics>.py` with material and BC classes.
2. Add a `<physics>_problem()` method to `FemmProblem`.
3. Add the new field to the `FemmFields` enum with correct prefixes.
4. Verify all geometry, selection, and post-processing commands use the
   enum-based prefix.
5. Add examples and tests.

### Adding a new analysis metric

Post-processing is done via Lua commands emitted by `FemmProblem`:

- `block_integral(type)` -- appends `<prefix_out>_blockintegral(type)`
- `get_point_values(node)` -- appends `<prefix_out>_getpointvalues(x, y)`
- `line_integral(type)` -- appends `<prefix_out>_lineintegral(type)`

Results are written to CSV by the generated Lua and returned to the client
as a string.

---

## Key Design Decisions

### File-based Lua instead of ActiveX

ActiveX ties the client to Windows and a single running FEMM process.
File-based Lua scripts are portable text -- they can be generated on any OS,
version-controlled, diff'd, and executed later on a separate machine. This
is the foundation that enables Wine, Docker, and CI/CD workflows.

### REST over shared filesystem

Both bridge modes exist because they serve different deployment scenarios:

- **Shared filesystem (WSL):** Zero network overhead, simplest setup for
  developers running WSL alongside native Windows FEMM.
- **REST API:** Required for remote machines, VMs, Docker containers, and
  multi-client scenarios. The REST layer adds job lifecycle tracking,
  health checks, and structured error reporting.

The auto-detecting client abstracts this choice from the user.

### Physics-agnostic geometry

`Geometry` and `Node`/`Line`/`CircleArc` contain no physics-specific code.
The same geometry can be used with `heat_problem()`, `magnetic_problem()`,
etc. This avoids duplication when the same physical shape needs analysis
under multiple physics.

### FEMM Lua 4.0 quirks

FEMM embeds Lua 4.0 (not 5.x), which has notable differences:

- **No `local` scoping** in the global chunk -- all variables are global.
- **1-based table indexing** -- `ho_getpointvalues` returns a Lua table
  where index 1 is temperature, not index 0.
- **`openfile` / `closefile`** instead of `io.open` / `file:close`.
- **`write(handle, ...)`** instead of `handle:write(...)`.

The Lua generation code accounts for these by using the Lua 4.0 API
directly rather than idiomatic Lua 5.x patterns.

### Sentinel-based completion detection

Instead of reading stdout from the FEMM subprocess (which can deadlock on
large outputs), the executor polls for a `PY2FEMM_DONE` file that
`FemmProblem.close()` writes as the last action of every script. This is
more reliable across different FEMM versions and output sizes.
