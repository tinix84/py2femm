# py2femm Product Requirements Document

## Problem Statement

[FEMM](https://www.femm.info/wiki/HomePage) is a widely used open-source 2D
finite element solver for magnetics, electrostatics, heat flow, and current
flow. Its official Python binding, [pyFEMM](https://www.femm.info/wiki/pyFEMM),
drives FEMM through Windows COM/ActiveX, which creates several pain points:

- **Windows-only:** ActiveX does not work on Linux, Mac, WSL, or Docker.
  Engineers on those platforms must manually copy Lua scripts and CSV results
  back and forth.
- **Single-user, single-process:** Only one Python process can control FEMM
  at a time. Teams sharing a Windows license server have no way to queue jobs.
- **No parametric workflow:** Running a parameter sweep requires hand-written
  loops around pyFEMM calls with no caching, batching, or result management.
- **No CI/CD integration:** ActiveX cannot run headlessly in a GitHub Actions
  runner or a Docker container.

py2femm replaces the ActiveX dependency with file-based Lua generation and a
REST server, removing the platform lock-in while adding remote execution,
job management, and parametric sweep infrastructure.

---

## Target Users

| Persona | Need |
|---------|------|
| **Electrical / thermal engineer** | Run parametric FEMM studies from a Jupyter notebook without touching Lua or the FEMM GUI directly |
| **Design automation team** | Submit FEMM jobs from CI/CD pipelines or shared scripts to a central Windows machine running FEMM |
| **Single-license team** | Queue jobs from multiple laptops to one FEMM server, avoiding license conflicts |
| **Linux / WSL developer** | Generate and debug FEMM simulations without leaving the Linux environment |
| **Docker / Wine user** | Run FEMM inside a container for reproducible, headless simulation |

---

## Goals

### G1. File-based Lua generation (cross-platform)

Generate complete, self-contained Lua scripts from Python without any ActiveX
or COM dependency. Scripts are plain text, debuggable, and diffable.

### G2. REST server for remote and multi-client execution

A lightweight FastAPI server on the Windows FEMM host accepts Lua scripts
over HTTP, runs them in FEMM, and returns CSV results. Any HTTP client --
Python, curl, a notebook, or a CI step -- can submit jobs.

### G3. Unified API across four physics

One `FemmProblem` class with a consistent interface for magnetics,
electrostatics, heat flow, and current flow. Geometry is defined once and
reused across physics types.

### G4. Reusable geometry separated from physics

`Geometry`, `Node`, `Line`, and `CircleArc` carry no physics-specific state.
The same shape description can drive magnetic, thermal, and electrostatic
analyses without duplication.

### G5. First-class parametric sweeps

Provide data structures (e.g., `HeatsinkConfig`) and sweep engines
(`build_sweep_grid`, `run_sweep`) that make factorial parameter studies a
few lines of Python. Results are returned as pandas DataFrames with built-in
plotting helpers.

---

## Non-Goals

| Non-goal | Rationale |
|----------|-----------|
| **GUI for FEMM** | FEMM already has a capable GUI. py2femm is a scripting and automation layer. |
| **Replacing FEMM's solver** | py2femm generates input for FEMM and parses output. It does not implement FEA. |
| **Mesh editing** | Mesh control is limited to FEMM's auto-mesher settings (`meshsize`, `minangle`). Manual mesh editing is out of scope. |
| **Cloud / SaaS hosting** | The server is designed for self-hosted deployment on a machine where FEMM is installed. Cloud orchestration (auto-scaling, multi-node) is out of scope. |
| **3D simulation** | FEMM is a 2D (planar + axisymmetric) solver. py2femm does not extend beyond FEMM's capabilities. |
| **Real-time interactive control** | py2femm is batch-oriented. It does not provide a live REPL into a running FEMM session. |

---

## User Journeys

### Journey 1: Capacitance tuning

An engineer designs a parallel-plate capacitor and wants to understand how
plate spacing affects capacitance.

1. Define plate geometry in Python using `Node` and `Line`.
2. Assign dielectric material and voltage BCs via `electrostatics.py`.
3. Call `FemmProblem.write()` to generate a Lua script.
4. Submit to the server with `FemmClient.run()`.
5. Parse the returned CSV to extract stored energy and compute capacitance.
6. Wrap steps 1--5 in a loop over plate spacings; collect results into a
   DataFrame and plot capacitance vs. gap.

### Journey 2: Motor torque sweep

A motor designer wants to characterize torque vs. rotor angle for a
synchronous reluctance machine.

1. Build the stator/rotor geometry using `Geometry` operations (arcs,
   mirroring, rotation).
2. Assign iron and copper materials, winding circuits, and periodic BCs
   via `magnetics.py`.
3. Generate one Lua script per rotor position (e.g., 0--90 degrees in
   1-degree steps).
4. Submit all 90 scripts via the batch endpoint.
5. Parse torque from each result CSV; plot torque ripple and average torque.

### Journey 3: Thermal management parametric study

A power-electronics engineer needs to find the optimal heatsink geometry for
a given power dissipation and convection environment.

1. Define a `HeatsinkConfig` with parametric dimensions (base width, pitch,
   duty cycle, base ratio).
2. Call `build_sweep_grid()` to generate all valid configurations.
3. Run `run_sweep()` to submit each configuration to the server and collect
   thermal resistance, average temperature, and cross-section area.
4. Use built-in plotting functions to visualize sensitivity, heatmaps, and
   scaling behaviour.
5. Select the Pareto-optimal design (lowest thermal resistance for acceptable
   material cost).

### Journey 4: CI/CD regression testing

A team maintains a library of FEMM models and wants to catch regressions
when geometry or material code changes.

1. Each model has a test script that generates Lua via `FemmProblem`.
2. `pytest` submits the Lua to a Windows runner with FEMM installed.
3. Results are compared against reference CSV files (golden values).
4. A failing test means the solver output changed beyond tolerance,
   flagging a review.

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Physics coverage | Examples and tests for all 4 physics (magnetics, electrostatics, heat flow, current flow) |
| Platform support | Client runs on Windows, Linux, Mac; server runs on Windows natively and via Wine |
| Parametric workflow | At least one end-to-end parametric sweep example with >= 100 configurations |
| Test coverage | Unit tests pass without a live FEMM server; integration tests run on Windows CI |
| Documentation | README, contributing guide, architecture doc, and at least 3 annotated examples |
| Community adoption | Published on PyPI; external contributors submit at least 1 PR within 6 months of release |

---

## Roadmap

### Short-term (current -- v0.3)

- Polish existing examples and improve test coverage
- Stabilize the executor (edge cases around FEMM timeouts and large outputs)
- Add type stubs and improve type-hint coverage across the codebase
- Publish to PyPI with automated release workflow
- Add GitHub Actions CI for lint + unit tests (no FEMM required)

### Medium-term (v0.4 -- v0.5)

- **Linux + Wine CI:** GitHub Actions workflow that installs FEMM under Wine
  and runs integration tests headlessly
- **Dockerfile:** Pre-built image with Wine + FEMM + py2femm_server for
  one-command deployment
- **More examples:** Motor torque sweep (magnetics), capacitor optimization
  (electrostatics), PCB via thermal (current flow)
- **Result caching:** SHA256-based Lua script cache to skip re-runs of
  identical simulations
- **Batch endpoint improvements:** Progress callbacks, partial results,
  priority ordering

### Long-term (v1.0+)

- **Job queue persistence:** Replace in-memory `JobStore` with SQLite or
  Redis for crash recovery and history
- **Distributed execution:** Support multiple FEMM instances on separate
  machines behind a load balancer
- **Auto-generated API client:** OpenAPI spec exported from the FastAPI
  server, with generated clients for JavaScript, MATLAB, and other languages
- **Web dashboard:** Minimal HTML + SSE page showing queue status, running
  jobs, and result history
- **Parquet output format:** Optional columnar storage for large sweep
  result sets
- **Plugin system:** Allow third-party physics modules or post-processing
  extensions without forking the core library
