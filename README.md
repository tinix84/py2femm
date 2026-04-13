<p align="center">
  <img src="docs/assets/logo.png" alt="py2femm logo" width="280">
</p>

# py2femm

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/license-AGPL--3.0--or--later-green.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.femm.info/wiki/HomePage)
[![Version: 0.2.0](https://img.shields.io/badge/version-0.2.0-orange.svg)](https://github.com/tinix84/py2femm)

Python automation platform for [FEMM](https://www.femm.info/wiki/HomePage) finite element simulations.

py2femm generates Lua scripts from a Python API and executes them in FEMM via a REST server. It supports **magnetics**, **electrostatics**, **heat flow**, and **current flow** problems in 2D planar and axisymmetric geometries.

## Why py2femm?

[pyFEMM](https://www.femm.info/wiki/pyFEMM) uses ActiveX and only works on Windows. py2femm takes a different approach:

- **File-based Lua generation** -- works with Wine on Linux, in Docker, or natively on Windows
- **Geometry separated from physics** -- describe a shape once, reuse it for magnetic, thermal, or electrostatic analysis
- **REST server** -- submit jobs from any client (Python, notebook, CI) to a Windows machine running FEMM
- **Parametric workflows** -- sweep dimensions, materials, or BCs from Python and collect results programmatically

## Architecture

```
┌──────────────────┐       HTTP/REST        ┌──────────────────┐
│  Python client   │  ──────────────────►   │  py2femm_server  │
│  (any platform)  │  ◄──────────────────   │  (Windows+FEMM)  │
│                  │      JSON results      │                  │
│  FemmProblem API │                        │  FastAPI + FEMM  │
│  FemmClient      │                        │  subprocess      │
└──────────────────┘                        └──────────────────┘
```

The **client library** (`py2femm/`) runs anywhere: it builds a `FemmProblem`, serializes it to a Lua script, and hands it to `FemmClient`. The **server** (`py2femm_server/`) runs on Windows where FEMM is installed. It receives Lua scripts over HTTP, launches FEMM as a subprocess, and returns CSV results.

`FemmClient` auto-detects the best transport: shared filesystem (WSL/local), remote REST, or environment variable override.

## Quick Start

### Requirements

- Python >= 3.10
- [FEMM 4.2](https://www.femm.info/wiki/Download) installed on Windows (default: `C:\femm42\`)

### Installation

```bash
# Core library (script generation + client)
pip install -e .

# With REST server dependencies (FastAPI, uvicorn)
pip install -e ".[server]"

# Everything including dev tools
pip install -e ".[server,dev]"
```

Or run the interactive setup on Windows:

```bat
setup_femm.bat
```

### Start the Server

```bat
start_femm_server.bat
```

Or manually:

```bash
python -m py2femm_server --host 0.0.0.0 --port 8082
```

To keep FEMM visible for debugging:

```bash
python -m py2femm_server --host 0.0.0.0 --port 8082 --show-femm
```

### Run an Example

With the server running:

```bash
python examples/heatflow/heatsink/heatsink.py
```

## Usage

### Python API -- Build a Problem

```python
from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Node, Line
from py2femm.heatflow import HeatFlowMaterial, HeatFlowConvection

problem = FemmProblem(out_file="results.csv")
problem.heat_problem(units=LengthUnit.MILLIMETERS, type="planar",
                     precision=1e-8, depth=100, minangle=30)

# Add geometry, materials, BCs...
# Then write the Lua script:
problem.write("my_simulation.lua")
```

### Submit to Server

```python
from py2femm.client import FemmClient

client = FemmClient(mode="remote", url="http://localhost:8082")
result = client.run(lua_script, timeout=120)
print(result.csv_data)
```

### CLI

```bash
# Run a single Lua script
py2femm run my_simulation.lua --output results.csv

# Run all .lua files in a directory
py2femm run-batch simulations/ --output-dir results/

# Check server status
py2femm status
```

## Examples

The `examples/` directory contains worked examples across all four physics domains.

### Heat Flow

| Example | Description |
|---------|-------------|
| [`heatflow/heatsink/heatsink_baseline.ipynb`](examples/heatflow/heatsink/heatsink_baseline.ipynb) | FEMM Tutorial #7 reproduction -- 5-fin aluminum heat sink with fixed BCs and FEMM bitmap capture |
| [`heatflow/heatsink/heatsink_parametric.ipynb`](examples/heatflow/heatsink/heatsink_parametric.ipynb) | 360-config factorial sweep using square-wave fin parametrization (10 base widths x 3 pitch ratios x 3 duty cycles x 4 base ratios), sensitivity analysis, 2D heatmaps, scaling plots, and contact mode comparison |
| [`01_simple_thermal.py`](examples/01_simple_thermal.py) | Minimal heat flow script |

### Electrostatics

| Example | Description |
|---------|-------------|
| [`02_e2e_capacitor_with_plot.py`](examples/02_e2e_capacitor_with_plot.py) | End-to-end capacitor simulation with result plotting |
| [`electrostatics/capacitance/`](examples/electrostatics/capacitance/) | Planar capacitor analysis |
| [`electrostatics/double_l_shape/`](examples/electrostatics/double_l_shape/) | Double L-shaped domain |

### Magnetics

| Example | Description |
|---------|-------------|
| [`magnetics/solenoid/`](examples/magnetics/solenoid/) | Solenoid field analysis |
| [`magnetics/PMDC_motor/`](examples/magnetics/PMDC_motor/) | Permanent magnet DC motor |
| [`magnetics/ISPMSM/`](examples/magnetics/ISPMSM/) | Interior surface-mount PMSM -- torque, cogging, NSGA-II optimization |
| [`magnetics/FI-PMASynRM/`](examples/magnetics/FI-PMASynRM/) | Flux-intensifying PM-assisted SynRM |
| [`magnetics/reluctance_machine/`](examples/magnetics/reluctance_machine/) | Switched reluctance machine studies |
| [`magnetics/toyota_prius/`](examples/magnetics/toyota_prius/) | Toyota Prius motor model |

## Heat Sink Tutorial

The heat sink example is split into two notebooks:

**Baseline** (`heatsink_baseline.ipynb`) reproduces FEMM Tutorial #7:
1. Build a 5-fin aluminum heat sink geometry and plot it
2. Define material (aluminum k=200) and boundary conditions (heat flux + convection)
3. Generate the Lua script and submit it to FEMM
4. Parse results and display FEMM temperature contour bitmap
5. Summary: T_avg, thermal resistance R_th

**Parametric study** (`heatsink_parametric.ipynb`) explores the design space:
1. Define the parameter grid (360 full-factorial combinations, ~176 valid after manufacturability filtering)
2. Run the sweep via FEMM (~10 min runtime)
3. 1D sensitivity plots (R_th and cross-section area vs each parameter)
4. 2D heatmaps of R_th over pitch ratio and duty cycle
5. Scaling analysis: best R_th per base width
6. Contact mode comparison (centered, single-fin aligned, between-fins)
7. Top configurations with geometry overlay

## Supported Physics

| Field | Problem Types | Prefix | Key Outputs |
|-------|--------------|--------|-------------|
| Magnetics | Magnetostatic, time-harmonic | `mi_`/`mo_` | Flux density, force, torque, inductance |
| Electrostatics | Static electric fields | `ei_`/`eo_` | Voltage, energy, capacitance |
| Heat Flow | Steady-state thermal | `hi_`/`ho_` | Temperature, heat flux, thermal resistance |
| Current Flow | DC/AC conduction | `ci_`/`co_` | Current density, resistance, power loss |

## Project Structure

```
py2femm/
├── py2femm/                  # Core library
│   ├── femm_problem.py       #   FemmProblem — Lua script generator
│   ├── geometry.py            #   Node, Line, CircleArc, Geometry
│   ├── magnetics.py           #   Magnetic materials & BCs
│   ├── electrostatics.py      #   Electrostatic materials & BCs
│   ├── heatflow.py            #   Heat flow materials & BCs
│   ├── current_flow.py        #   Current flow materials & BCs
│   ├── general.py             #   FemmFields, LengthUnit, base classes
│   ├── cli.py                 #   CLI (run, status, run-batch)
│   └── client/                #   FemmClient (auto, local, remote)
│
├── py2femm_server/            # REST server (Windows)
│   ├── server.py              #   FastAPI endpoints
│   ├── executor.py            #   FEMM subprocess runner
│   ├── job_store.py           #   In-memory job state
│   ├── health.py              #   FEMM installation detection
│   └── watcher.py             #   Filesystem watcher mode
│
├── examples/
│   ├── heatflow/heatsink/     #   Heat sink tutorials + parametric study
│   ├── electrostatics/        #   Capacitor and field examples
│   └── magnetics/             #   Motor, solenoid, and machine examples
│
├── docs/superpowers/          # Design specs and implementation plans
├── tests/                     # Test suite
├── start_femm_server.bat      # Launch server on Windows
└── setup_femm.bat             # One-time environment setup
```

## Configuration

py2femm reads configuration from `config/default.yml` (generated by `setup_femm.bat`):

```yaml
python:
  env_type: conda       # or venv
  env_name: my_env
  conda_root: C:\ProgramData\Anaconda3
femm:
  exe: C:\femm42\bin\femm.exe
```

Client auto-detection order:
1. Explicit `mode`/`url` arguments
2. `/mnt/c/` exists -- local shared-filesystem mode (WSL)
3. `PYFEMM_AGENT_URL` environment variable -- remote mode
4. `~/.py2femm/config.yml` -- remote mode

## Documentation

Design documents and implementation plans live in `docs/superpowers/`. To browse the documentation site locally:

```bash
pip install mkdocs-material
mkdocs serve
```

Then open <http://localhost:8000> in your browser.

## Testing

```bash
python -m pytest tests/ -v
```

Tests that require a live FEMM server are marked with `pytest.mark.skip` or guarded by server health checks. The unit tests (geometry, config, client mocking) run without FEMM.

## Contributing

Contributions are welcome. Please:

1. Install dev dependencies: `pip install -e ".[server,dev]"`
2. Run `ruff check .` and `ruff format --check .` before submitting
3. Add tests for new features
4. Follow existing code style: type hints, dataclasses, `from __future__ import annotations`

## Acknowledgements

- **[FEMM](https://www.femm.info/wiki/HomePage)** by David Meeker -- the finite element engine that makes this all possible
- **[pyFEMM](https://www.femm.info/wiki/pyFEMM)** -- the original Python-FEMM bridge via ActiveX, which inspired the py2femm approach
- The FEMM community and tutorial authors

## License

[AGPL-3.0-or-later](https://www.gnu.org/licenses/agpl-3.0.html)

Copyright (c) Riccardo Tinivella (<tinix84@gmail.com>)
