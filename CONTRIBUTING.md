# Contributing to py2femm

Thank you for considering a contribution to py2femm! This guide covers
everything you need to get started.

## Development Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/tinix84/py2femm.git
   cd py2femm
   ```

2. **Create a virtual environment** (Python 3.10+):

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   .venv\Scripts\activate      # Windows
   ```

3. **Install in editable mode with all dependencies:**

   ```bash
   pip install -e ".[all]"
   ```

   This pulls in the core library, the REST server (FastAPI, uvicorn),
   and dev tools (pytest, ruff).

4. **FEMM (optional):** Install [FEMM 4.2](https://www.femm.info/wiki/Download)
   on a Windows machine (default path `C:\femm42\`). Integration tests and
   examples require a running FEMM server; unit tests do not.

## Running Tests

```bash
python -m pytest tests/ -v
```

Most tests are pure-Python unit tests that run anywhere. Tests marked with
network or integration fixtures (e.g., `test_integration.py`) require:

- A running py2femm server (`python -m py2femm_server --port 8082`)
- FEMM 4.2 installed on the same Windows machine

These tests are skipped automatically when the server is unreachable.

## Code Style

We use **ruff** for linting and formatting:

```bash
ruff check .          # lint
ruff format .         # auto-format
```

Rules at a glance:

- **Line length:** 120 characters max
- **Type hints:** Required on all public function signatures
- **Imports:** Sorted by ruff (isort-compatible)
- **Docstrings:** Required for public classes and functions; use Google style

The full ruff configuration lives in `pyproject.toml` under `[tool.ruff]`.

## Commit Messages

Follow **Conventional Commits** in imperative mood:

```
feat: add radiation BC for heat flow
fix: correct segment selection in axisymmetric mode
refactor: extract Lua preamble injection into helper
docs: document REST API endpoints
test: add coverage for HeatsinkConfig validation
style: fix import ordering in executor module
```

Keep the subject line under 72 characters. Use the body for context when
the change is non-obvious.

## Pull Request Process

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feat/my-feature
   ```
2. **Make your changes** with tests covering new behaviour.
3. **Run the full check:**
   ```bash
   ruff check . && ruff format --check . && python -m pytest tests/ -v
   ```
4. **Push** and open a PR against `main`.
5. Fill in the PR description: what changed, why, and how to test.

One approval from a maintainer is required before merge.

## Adding a New Example

Follow the pattern in `examples/heatflow/heatsink/`:

1. Create a directory under `examples/<physics>/<name>/`.
2. Write a standalone `.py` script that builds the geometry, generates Lua,
   submits to the server, and parses results. Accept `--start-server` and
   `--no-plot` flags for CI compatibility.
3. Optionally add a `.ipynb` notebook for interactive exploration.
4. Add corresponding tests in `tests/` (at minimum, verify Lua generation
   without a live server).

## Adding a New Boundary Condition or Material

1. Open the appropriate physics module (`heatflow.py`, `magnetics.py`,
   `electrostatics.py`, or `current_flow.py`).
2. Subclass from `general.Boundary` (for BCs) or `general.Material`
   (for materials).
3. Implement `__str__` so it returns the correct FEMM Lua command string
   (e.g., `hi_addboundprop(...)` for heat flow BCs).
4. Wire the new class into `FemmProblem` if it requires special handling
   in `add_boundary()` or `add_material()`.
5. Export it from `py2femm/__init__.py` if it is part of the public API.
6. Add tests verifying the generated Lua matches FEMM documentation.

## Adding a New Physics Module

This is a larger effort. The pattern is:

1. Create `py2femm/<physics>.py` with material and BC classes.
2. Add a `<physics>_problem()` method to `FemmProblem` that emits the
   `<prefix>_probdef(...)` Lua command and sets `self.field`.
3. Verify that geometry operations, block properties, and post-processing
   commands use the correct Lua prefix (`mi_`/`mo_`, `hi_`/`ho_`, etc.).
4. Add at least one end-to-end example under `examples/<physics>/`.
5. Update `README.md` and the supported-physics table.

## Reporting Issues

When filing a bug, please include:

- **Python version** (`python --version`)
- **FEMM version** (e.g., FEMM 4.2, build date if known)
- **Operating system** (Windows 11, WSL2 Ubuntu 22.04, etc.)
- **py2femm version** (`python -c "import py2femm; print(py2femm.__version__)"`)
- **Minimal reproducer** (a short script or Lua snippet that triggers the bug)
- **Expected vs actual behaviour**

For feature requests, describe the use case first, then the proposed solution.

## License

By contributing you agree that your work will be licensed under the
project's **AGPL-3.0-or-later** license.
