# py2femm Phase 1 (Core MVP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fork py2femm, restructure into client/agent architecture, add REST API and shared-filesystem bridge so FEMM simulations can be submitted from WSL/Linux and executed on Windows.

**Architecture:** Monorepo with two components: `py2femm/` (client library, runs anywhere) and `py2femm_server/` (FastAPI server + filesystem watcher, runs on Windows where FEMM is installed). Communication via shared filesystem (`/mnt/c/`) or REST API (HTTP).

**Tech Stack:** Python 3.10+, FastAPI, uvicorn, pydantic, click, pyyaml, pandas

**Spec:** `docs/superpowers/specs/2026-04-05-py2femm-design.md`

**Upstream fork:** `tamasorosz/py2femm` -> `tinix84/py2femm` (AGPL-3.0, diverge freely)

---

## File Map

### New files (client library)

| File | Responsibility |
|------|---------------|
| `py2femm/client/__init__.py` | Re-export `FemmClient` |
| `py2femm/client/base.py` | `FemmClientBase` ABC: `run()`, `run_batch()`, `status()` |
| `py2femm/client/local.py` | `LocalClient` — shared-filesystem bridge via `/mnt/c/` |
| `py2femm/client/remote.py` | `RemoteClient` — REST API client via `httpx` |
| `py2femm/client/auto.py` | `FemmClient` — auto-detect local vs remote |
| `py2femm/client/models.py` | `JobRequest`, `JobStatus`, `JobResult`, `ExecutionResult` pydantic models |
| `py2femm/cli.py` | Click CLI: `py2femm run`, `py2femm status`, `py2femm server` |
| `py2femm/config/schema.py` | `Py2FemmConfig` dataclass |
| `py2femm/config/loader.py` | `load_config()` — hierarchical YAML discovery |
| `py2femm/config/defaults.yml` | Default config values |

### New files (agent)

| File | Responsibility |
|------|---------------|
| `py2femm_server/__init__.py` | Package init |
| `py2femm_server/__main__.py` | `python -m py2femm_server` entry point |
| `py2femm_server/server.py` | FastAPI app with `/api/v1/jobs` and `/api/v1/health` |
| `py2femm_server/executor.py` | `FemmExecutor` — subprocess FEMM launch, preamble injection, CSV extraction |
| `py2femm_server/watcher.py` | `FileWatcher` — poll directory for `.lua` files, trigger executor |
| `py2femm_server/health.py` | `check_femm()` — detect FEMM path, version |
| `py2femm_server/job_store.py` | In-memory job state store (pending/running/completed/failed) |

### New files (project root)

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Replace upstream Poetry config with setuptools + extras |
| `setup_femm.bat` | One-time Windows setup (Python env + FEMM detection) |
| `start_femm_server.bat` | Launch agent on Windows |
| `config/default.yml` | Agent-side YAML config (FEMM path, workspace) |

### Existing files to keep (from upstream py2femm)

| File | Status |
|------|--------|
| `py2femm/femm_problem.py` | Keep as-is for now (refactor to `core/` in Phase 2) |
| `py2femm/geometry.py` | Keep as-is |
| `py2femm/heatflow.py` | Keep as-is |
| `py2femm/executor.py` | Keep as reference, superseded by `py2femm_server/executor.py` |
| `py2femm/general.py` | Keep as-is |
| `tests/` | Keep existing tests |

### Test files

| File | Tests |
|------|-------|
| `tests/test_client_models.py` | Pydantic model serialization |
| `tests/test_executor.py` | Preamble injection, CSV parsing, timeout handling |
| `tests/test_watcher.py` | File detection, atomic write handling |
| `tests/test_server.py` | FastAPI endpoint contracts |
| `tests/test_local_client.py` | Shared-filesystem round-trip |
| `tests/test_remote_client.py` | REST client with mocked server |
| `tests/test_auto_client.py` | Auto-detection logic |
| `tests/test_config.py` | YAML loading, merge, defaults |
| `tests/test_cli.py` | Click CLI commands |
| `tests/test_health.py` | FEMM path detection |

---

## Task 0: Fork and Set Up Repository

**Files:**
- Create: `pyproject.toml` (replace upstream)
- Create: `.gitignore`
- Create: `README.md`
- Modify: `py2femm/__init__.py`

- [ ] **Step 1: Fork py2femm on GitHub**

Go to https://github.com/tamasorosz/py2femm and click Fork to `tinix84/py2femm`.
Then clone locally:

```bash
cd ~/claude_wsl
git clone git@github.com:tinix84/py2femm.git
cd py2femm
git remote add upstream https://github.com/tamasorosz/py2femm.git
```

- [ ] **Step 2: Create new pyproject.toml**

Replace the upstream Poetry-based `pyproject.toml` with setuptools:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "py2femm"
version = "0.2.0"
description = "Python automation platform for FEMM finite element simulations"
readme = "README.md"
authors = [{ name = "Riccardo Tinivella", email = "tinix84@gmail.com" }]
license = { text = "AGPL-3.0-or-later" }
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "click>=8.0",
    "pandas>=1.5",
    "httpx>=0.24",
]

[project.optional-dependencies]
agent = [
    "fastapi>=0.100",
    "uvicorn[standard]>=0.20",
]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "ruff>=0.1",
    "httpx>=0.24",
]
all = ["py2femm[agent,dev]"]

[project.scripts]
py2femm = "py2femm.cli:main"

[tool.setuptools.packages.find]
include = ["py2femm*", "py2femm_server*"]

[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 3: Update .gitignore**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
.env
*.fem
*.ans
config/default.yml
!config/defaults.yml
```

- [ ] **Step 4: Create package directories**

```bash
mkdir -p py2femm/client py2femm/config py2femm_server tests examples config
touch py2femm/client/__init__.py py2femm/config/__init__.py
touch py2femm_server/__init__.py
```

- [ ] **Step 5: Install in editable mode and verify**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -c "import py2femm; print('OK')"
```

- [ ] **Step 6: Run existing upstream tests**

```bash
pytest tests/ -v
```

Expect: existing py2femm tests should still pass (geometry, materials, etc.).

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore py2femm/client/__init__.py py2femm/config/__init__.py py2femm_server/__init__.py
git commit -m "feat: restructure project for client/agent architecture

Replace Poetry with setuptools, add extras (agent, dev), create
client/, config/, and py2femm_server/ package directories."
```

---

## Task 1: Shared Data Models

**Files:**
- Create: `py2femm/client/models.py`
- Test: `tests/test_client_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_client_models.py`:

```python
import json
from datetime import datetime, timezone

from py2femm.client.models import JobRequest, JobResult, JobStatus


def test_job_request_serialization():
    req = JobRequest(
        lua_script='hi_probdef("meters","planar")',
        timeout_s=300,
        metadata={"model": "extruded-fin"},
    )
    data = req.model_dump()
    assert data["lua_script"] == 'hi_probdef("meters","planar")'
    assert data["timeout_s"] == 300
    assert data["metadata"] == {"model": "extruded-fin"}


def test_job_request_defaults():
    req = JobRequest(lua_script="hi_analyze()")
    assert req.timeout_s == 300
    assert req.metadata == {}


def test_job_status_lifecycle():
    status = JobStatus(
        job_id="abc-123",
        status="completed",
        submitted_at=datetime(2026, 4, 5, 10, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 4, 5, 10, 0, 12, tzinfo=timezone.utc),
    )
    assert status.status == "completed"
    assert status.elapsed_s == 12.0


def test_job_status_pending_has_no_elapsed():
    status = JobStatus(
        job_id="abc-123",
        status="pending",
        submitted_at=datetime(2026, 4, 5, 10, 0, 0, tzinfo=timezone.utc),
    )
    assert status.elapsed_s is None


def test_job_result_with_csv():
    result = JobResult(
        csv_data="point,x,y,temperature_K\njunction,0,0,350.5\n",
    )
    df = result.to_dataframe()
    assert len(df) == 1
    assert df.iloc[0]["point"] == "junction"
    assert df.iloc[0]["temperature_K"] == 350.5


def test_job_result_empty_csv():
    result = JobResult(csv_data="")
    df = result.to_dataframe()
    assert len(df) == 0


def test_job_status_json_roundtrip():
    status = JobStatus(
        job_id="abc-123",
        status="completed",
        submitted_at=datetime(2026, 4, 5, 10, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 4, 5, 10, 0, 12, tzinfo=timezone.utc),
        result=JobResult(csv_data="point,x,y,temperature_K\n"),
    )
    json_str = status.model_dump_json()
    restored = JobStatus.model_validate_json(json_str)
    assert restored.job_id == "abc-123"
    assert restored.result.csv_data == "point,x,y,temperature_K\n"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_client_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm.client.models'`

- [ ] **Step 3: Write the implementation**

Create `py2femm/client/models.py`:

```python
"""Shared data models for py2femm client-agent communication."""

from __future__ import annotations

from datetime import datetime
from io import StringIO
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field


class JobRequest(BaseModel):
    """Request to run a FEMM Lua script."""

    lua_script: str
    timeout_s: int = 300
    metadata: dict[str, str] = Field(default_factory=dict)


class JobResult(BaseModel):
    """Result of a completed FEMM simulation."""

    csv_data: str = ""

    def to_dataframe(self) -> pd.DataFrame:
        """Parse CSV data into a pandas DataFrame."""
        if not self.csv_data.strip():
            return pd.DataFrame()
        return pd.read_csv(StringIO(self.csv_data))


class JobStatus(BaseModel):
    """Status of a FEMM simulation job."""

    job_id: str
    status: Literal["submitted", "queued", "running", "completed", "failed"]
    submitted_at: datetime
    completed_at: datetime | None = None
    result: JobResult | None = None
    error: str | None = None

    @property
    def elapsed_s(self) -> float | None:
        """Elapsed time in seconds, or None if not completed."""
        if self.completed_at is None or self.submitted_at is None:
            return None
        return (self.completed_at - self.submitted_at).total_seconds()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_client_models.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add py2femm/client/models.py tests/test_client_models.py
git commit -m "feat: add shared data models for client-agent communication

JobRequest, JobResult (with CSV->DataFrame), and JobStatus with
elapsed time calculation and JSON serialization."
```

---

## Task 2: FEMM Health Check

**Files:**
- Create: `py2femm_server/health.py`
- Test: `tests/test_health.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_health.py`:

```python
import os
from pathlib import Path
from unittest.mock import patch

from py2femm_server.health import find_femm, check_femm_health


def test_find_femm_from_env_var(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    with patch.dict(os.environ, {"FEMM_PATH": str(femm_exe)}):
        result = find_femm()
    assert result == femm_exe


def test_find_femm_returns_none_when_not_found():
    with patch.dict(os.environ, {}, clear=True):
        with patch("py2femm_server.health._FEMM_SEARCH_PATHS", []):
            result = find_femm()
    assert result is None


def test_find_femm_scans_common_paths(tmp_path):
    femm_dir = tmp_path / "femm42" / "bin"
    femm_dir.mkdir(parents=True)
    femm_exe = femm_dir / "femm.exe"
    femm_exe.touch()
    with patch.dict(os.environ, {}, clear=True):
        with patch("py2femm_server.health._FEMM_SEARCH_PATHS", [femm_exe]):
            result = find_femm()
    assert result == femm_exe


def test_check_femm_health_ok(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    with patch("py2femm_server.health.find_femm", return_value=femm_exe):
        health = check_femm_health()
    assert health["status"] == "ok"
    assert health["femm_path"] == str(femm_exe)


def test_check_femm_health_not_found():
    with patch("py2femm_server.health.find_femm", return_value=None):
        health = check_femm_health()
    assert health["status"] == "error"
    assert "not found" in health["message"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_health.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm_server.health'`

- [ ] **Step 3: Write the implementation**

Create `py2femm_server/health.py`:

```python
"""FEMM installation detection and health check."""

from __future__ import annotations

import os
from pathlib import Path

_FEMM_SEARCH_PATHS = [
    Path(r"C:\femm42\bin\femm.exe"),
    Path(r"C:\Program Files\femm42\bin\femm.exe"),
    Path(r"C:\Program Files (x86)\femm42\bin\femm.exe"),
]


def find_femm() -> Path | None:
    """Find FEMM executable. Checks FEMM_PATH env var, then common locations."""
    env_path = os.environ.get("FEMM_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    for candidate in _FEMM_SEARCH_PATHS:
        if candidate.exists():
            return candidate

    return None


def check_femm_health() -> dict:
    """Return health status dict for the agent."""
    femm_path = find_femm()
    if femm_path is None:
        return {
            "status": "error",
            "message": "FEMM not found. Set FEMM_PATH or install to C:\\femm42\\",
        }
    return {
        "status": "ok",
        "femm_path": str(femm_path),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_health.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add py2femm_server/health.py tests/test_health.py
git commit -m "feat: add FEMM health check and path detection

Scans FEMM_PATH env var and common Windows install locations.
Returns structured health dict for agent startup validation."
```

---

## Task 3: FEMM Executor

**Files:**
- Create: `py2femm_server/executor.py`
- Test: `tests/test_executor.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_executor.py`:

```python
from pathlib import Path

from py2femm_server.executor import FemmExecutor, inject_preamble


def test_inject_preamble():
    lua = 'hi_probdef("meters","planar")\nhi_analyze()'
    workdir = Path("C:/femm_workspace/jobs/abc123")
    result = inject_preamble(lua, workdir)
    assert "py2femm_workdir" in result
    assert "py2femm_outfile" in result
    assert 'hi_probdef("meters","planar")' in result
    assert result.index("py2femm_workdir") < result.index("hi_probdef")


def test_inject_preamble_preserves_original():
    lua = "line1\nline2\nline3"
    workdir = Path("C:/jobs/test")
    result = inject_preamble(lua, workdir)
    assert "line1\nline2\nline3" in result


def test_inject_preamble_escapes_backslashes():
    workdir = Path("C:\\femm_workspace\\jobs\\abc123")
    result = inject_preamble("hi_analyze()", workdir)
    assert "\\\\" in result or "/" in result  # Lua-safe path separators


def test_executor_init_with_femm_path(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")
    assert executor.femm_path == femm_exe


def test_executor_init_creates_workspace(tmp_path):
    workspace = tmp_path / "jobs"
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=workspace)
    assert workspace.exists()


def test_executor_prepare_job_writes_lua(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")
    job_dir, lua_path = executor.prepare_job("hi_analyze()")
    assert lua_path.exists()
    content = lua_path.read_text()
    assert "py2femm_outfile" in content
    assert "hi_analyze()" in content


def test_executor_parse_result_csv(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")
    job_dir = tmp_path / "jobs" / "test-job"
    job_dir.mkdir(parents=True)
    result_csv = job_dir / "results.csv"
    result_csv.write_text("point,x,y,temperature_K\njunction,0,0,350.5\n")
    csv_data = executor.read_result(job_dir)
    assert "junction" in csv_data
    assert "350.5" in csv_data


def test_executor_read_result_missing_file(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")
    job_dir = tmp_path / "jobs" / "no-result"
    job_dir.mkdir(parents=True)
    csv_data = executor.read_result(job_dir)
    assert csv_data is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_executor.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm_server.executor'`

- [ ] **Step 3: Write the implementation**

Create `py2femm_server/executor.py`:

```python
"""FEMM subprocess executor with Lua preamble injection."""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path
from typing import NamedTuple


class PreparedJob(NamedTuple):
    job_dir: Path
    lua_path: Path


def inject_preamble(lua_script: str, workdir: Path) -> str:
    """Inject py2femm output path variables at the top of a Lua script."""
    # Use forward slashes for Lua compatibility
    workdir_lua = str(workdir).replace("\\", "/")
    preamble = (
        "-- Injected by py2femm server\n"
        f'py2femm_workdir = "{workdir_lua}/"\n'
        f'py2femm_outfile = py2femm_workdir .. "results.csv"\n'
        "\n"
    )
    return preamble + lua_script


class FemmExecutor:
    """Runs FEMM as a subprocess on a Lua script."""

    def __init__(self, femm_path: Path, workspace: Path) -> None:
        self.femm_path = Path(femm_path)
        self.workspace = Path(workspace)
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

    def run(self, lua_script: str, timeout: int = 300) -> tuple[str | None, int]:
        """Run a Lua script in FEMM. Returns (csv_data, returncode)."""
        job_dir, lua_path = self.prepare_job(lua_script)
        try:
            result = subprocess.run(
                [str(self.femm_path), "-lua-script", str(lua_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            csv_data = self.read_result(job_dir)
            return csv_data, result.returncode
        except subprocess.TimeoutExpired:
            return None, -1

    def read_result(self, job_dir: Path) -> str | None:
        """Read the results.csv from a job directory."""
        result_path = job_dir / "results.csv"
        if not result_path.exists():
            return None
        return result_path.read_text(encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_executor.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add py2femm_server/executor.py tests/test_executor.py
git commit -m "feat: add FEMM subprocess executor with Lua preamble injection

Prepares job directories, injects py2femm_outfile variable into Lua
scripts, runs FEMM via subprocess, reads CSV results."
```

---

## Task 4: Job Store

**Files:**
- Create: `py2femm_server/job_store.py`
- Test: `tests/test_job_store.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_job_store.py`:

```python
from datetime import datetime, timezone

from py2femm_server.job_store import JobStore


def test_create_job():
    store = JobStore()
    job_id = store.create("hi_analyze()", timeout_s=300)
    assert isinstance(job_id, str)
    assert len(job_id) > 0


def test_get_job():
    store = JobStore()
    job_id = store.create("hi_analyze()")
    job = store.get(job_id)
    assert job["status"] == "queued"
    assert job["lua_script"] == "hi_analyze()"


def test_get_nonexistent_job():
    store = JobStore()
    assert store.get("nonexistent") is None


def test_update_status():
    store = JobStore()
    job_id = store.create("hi_analyze()")
    store.update_status(job_id, "running")
    job = store.get(job_id)
    assert job["status"] == "running"


def test_complete_job():
    store = JobStore()
    job_id = store.create("hi_analyze()")
    store.update_status(job_id, "running")
    store.complete(job_id, csv_data="point,x,y,T\n")
    job = store.get(job_id)
    assert job["status"] == "completed"
    assert job["csv_data"] == "point,x,y,T\n"
    assert job["completed_at"] is not None


def test_fail_job():
    store = JobStore()
    job_id = store.create("hi_analyze()")
    store.fail(job_id, error="FEMM crashed")
    job = store.get(job_id)
    assert job["status"] == "failed"
    assert job["error"] == "FEMM crashed"


def test_list_jobs():
    store = JobStore()
    id1 = store.create("script1")
    id2 = store.create("script2")
    jobs = store.list_jobs()
    assert len(jobs) == 2


def test_list_jobs_by_status():
    store = JobStore()
    id1 = store.create("script1")
    id2 = store.create("script2")
    store.update_status(id1, "running")
    running = store.list_jobs(status="running")
    assert len(running) == 1
    assert running[0]["job_id"] == id1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_job_store.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm_server.job_store'`

- [ ] **Step 3: Write the implementation**

Create `py2femm_server/job_store.py`:

```python
"""In-memory job state store for the py2femm server."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


class JobStore:
    """Thread-safe in-memory store for job state."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}

    def create(self, lua_script: str, timeout_s: int = 300, metadata: dict | None = None) -> str:
        """Create a new job, return its ID."""
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "lua_script": lua_script,
            "timeout_s": timeout_s,
            "metadata": metadata or {},
            "submitted_at": datetime.now(timezone.utc),
            "completed_at": None,
            "csv_data": None,
            "error": None,
        }
        return job_id

    def get(self, job_id: str) -> dict | None:
        """Get job by ID, or None."""
        return self._jobs.get(job_id)

    def update_status(self, job_id: str, status: str) -> None:
        """Update job status."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status

    def complete(self, job_id: str, csv_data: str) -> None:
        """Mark job as completed with results."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "completed"
            self._jobs[job_id]["csv_data"] = csv_data
            self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc)

    def fail(self, job_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "failed"
            self._jobs[job_id]["error"] = error
            self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc)

    def list_jobs(self, status: str | None = None) -> list[dict]:
        """List all jobs, optionally filtered by status."""
        jobs = list(self._jobs.values())
        if status is not None:
            jobs = [j for j in jobs if j["status"] == status]
        return jobs
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_job_store.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add py2femm_server/job_store.py tests/test_job_store.py
git commit -m "feat: add in-memory job store for agent state management

Tracks job lifecycle (queued -> running -> completed/failed) with
timestamps, Lua scripts, CSV results, and error messages."
```

---

## Task 5: FastAPI Agent Server

**Files:**
- Create: `py2femm_server/server.py`
- Create: `py2femm_server/__main__.py`
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_server.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from py2femm_server.server import create_app


@pytest.fixture
def client(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    app = create_app(femm_path=femm_exe, workspace=tmp_path / "jobs")
    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "femm_path" in data


def test_submit_job(client):
    resp = client.post("/api/v1/jobs", json={
        "lua_script": "hi_analyze()",
        "timeout_s": 60,
    })
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_submit_job_missing_script(client):
    resp = client.post("/api/v1/jobs", json={})
    assert resp.status_code == 422


def test_get_job_status(client):
    # Submit first
    resp = client.post("/api/v1/jobs", json={"lua_script": "hi_analyze()"})
    job_id = resp.json()["job_id"]
    # Get status
    resp = client.get(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["job_id"] == job_id


def test_get_nonexistent_job(client):
    resp = client.get("/api/v1/jobs/nonexistent")
    assert resp.status_code == 404


def test_submit_batch(client):
    resp = client.post("/api/v1/jobs/batch", json={
        "jobs": [
            {"lua_script": "script1()"},
            {"lua_script": "script2()"},
        ]
    })
    assert resp.status_code == 202
    data = resp.json()
    assert len(data["job_ids"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_server.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm_server.server'`

- [ ] **Step 3: Write the implementation**

Create `py2femm_server/server.py`:

```python
"""FastAPI REST server for the py2femm server."""

from __future__ import annotations

from pathlib import Path
from threading import Thread

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from py2femm_server.executor import FemmExecutor
from py2femm_server.job_store import JobStore


class SubmitRequest(BaseModel):
    lua_script: str
    timeout_s: int = 300
    metadata: dict[str, str] = Field(default_factory=dict)


class BatchSubmitRequest(BaseModel):
    jobs: list[SubmitRequest]


def create_app(femm_path: Path, workspace: Path) -> FastAPI:
    """Create FastAPI app with configured executor and store."""
    app = FastAPI(title="py2femm Server", version="0.2.0")
    executor = FemmExecutor(femm_path=femm_path, workspace=workspace)
    store = JobStore()

    def _run_job(job_id: str) -> None:
        """Execute a job in a background thread."""
        job = store.get(job_id)
        if job is None:
            return
        store.update_status(job_id, "running")
        csv_data, returncode = executor.run(
            job["lua_script"], timeout=job["timeout_s"]
        )
        if returncode == 0 and csv_data is not None:
            store.complete(job_id, csv_data)
        else:
            error = "Timeout" if returncode == -1 else f"FEMM exited with code {returncode}"
            if csv_data is None and returncode == 0:
                error = "FEMM completed but no results.csv found"
            store.fail(job_id, error=error)

    @app.get("/api/v1/health")
    def health():
        return {
            "status": "ok",
            "femm_path": str(femm_path),
            "queue_depth": len(store.list_jobs(status="queued")),
            "running": len(store.list_jobs(status="running")),
        }

    @app.post("/api/v1/jobs", status_code=202)
    def submit_job(req: SubmitRequest):
        job_id = store.create(req.lua_script, req.timeout_s, req.metadata)
        Thread(target=_run_job, args=(job_id,), daemon=True).start()
        return {"job_id": job_id, "status": "queued"}

    @app.get("/api/v1/jobs/{job_id}")
    def get_job(job_id: str):
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "submitted_at": job["submitted_at"].isoformat(),
            "completed_at": job["completed_at"].isoformat() if job["completed_at"] else None,
            "result": {"csv_data": job["csv_data"]} if job["csv_data"] else None,
            "error": job["error"],
        }

    @app.delete("/api/v1/jobs/{job_id}")
    def cancel_job(job_id: str):
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job["status"] == "queued":
            store.fail(job_id, error="Cancelled by user")
            return {"status": "cancelled"}
        return {"status": job["status"], "message": "Cannot cancel non-queued job"}

    @app.post("/api/v1/jobs/batch", status_code=202)
    def submit_batch(req: BatchSubmitRequest):
        job_ids = []
        for job_req in req.jobs:
            job_id = store.create(job_req.lua_script, job_req.timeout_s, job_req.metadata)
            Thread(target=_run_job, args=(job_id,), daemon=True).start()
            job_ids.append(job_id)
        return {"job_ids": job_ids, "count": len(job_ids)}

    return app
```

- [ ] **Step 4: Create `__main__.py` entry point**

Create `py2femm_server/__main__.py`:

```python
"""Entry point for `python -m py2femm_server`."""

import sys
from pathlib import Path

import click
import uvicorn

from py2femm_server.health import find_femm
from py2femm_server.server import create_app


@click.command()
@click.option("--host", default="0.0.0.0", help="Bind address")
@click.option("--port", default=8082, help="Port number")
@click.option("--femm-path", default=None, help="Path to femm.exe")
@click.option("--workspace", default=None, help="Job workspace directory")
def serve(host: str, port: int, femm_path: str | None, workspace: str | None):
    """Start the py2femm server REST server."""
    if femm_path:
        femm = Path(femm_path)
    else:
        femm = find_femm()
    if femm is None or not femm.exists():
        click.echo("Error: FEMM not found. Use --femm-path or set FEMM_PATH env var.", err=True)
        sys.exit(1)

    ws = Path(workspace) if workspace else Path("C:/femm_workspace")
    click.echo(f"FEMM path: {femm}")
    click.echo(f"Workspace: {ws}")
    click.echo(f"Starting py2femm server on {host}:{port}")

    app = create_app(femm_path=femm, workspace=ws)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    serve()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_server.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add py2femm_server/server.py py2femm_server/__main__.py tests/test_server.py
git commit -m "feat: add FastAPI agent server with REST endpoints

POST/GET/DELETE /api/v1/jobs, batch submit, health check.
Background thread execution. Entry point via python -m py2femm_server."
```

---

## Task 6: Filesystem Watcher

**Files:**
- Create: `py2femm_server/watcher.py`
- Test: `tests/test_watcher.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_watcher.py`:

```python
import time
from pathlib import Path
from unittest.mock import MagicMock

from py2femm_server.watcher import FileWatcher


def test_watcher_detects_new_lua_file(tmp_path):
    detected = []
    watcher = FileWatcher(
        watch_dir=tmp_path,
        on_file=lambda p: detected.append(p),
        poll_interval=0.1,
    )
    # Write a .tmp file first, then rename to .lua (atomic)
    tmp_file = tmp_path / "job_001.tmp"
    tmp_file.write_text("hi_analyze()")
    lua_file = tmp_path / "job_001.lua"
    tmp_file.rename(lua_file)

    watcher.poll_once()
    assert len(detected) == 1
    assert detected[0] == lua_file


def test_watcher_ignores_non_lua_files(tmp_path):
    detected = []
    watcher = FileWatcher(
        watch_dir=tmp_path,
        on_file=lambda p: detected.append(p),
    )
    (tmp_path / "readme.txt").write_text("hello")
    (tmp_path / "data.csv").write_text("a,b")

    watcher.poll_once()
    assert len(detected) == 0


def test_watcher_does_not_reprocess_same_file(tmp_path):
    detected = []
    watcher = FileWatcher(
        watch_dir=tmp_path,
        on_file=lambda p: detected.append(p),
    )
    (tmp_path / "job_001.lua").write_text("hi_analyze()")

    watcher.poll_once()
    watcher.poll_once()
    assert len(detected) == 1


def test_watcher_ignores_tmp_files(tmp_path):
    detected = []
    watcher = FileWatcher(
        watch_dir=tmp_path,
        on_file=lambda p: detected.append(p),
    )
    (tmp_path / "job_001.tmp").write_text("not ready yet")

    watcher.poll_once()
    assert len(detected) == 0


def test_watcher_creates_watch_dir_if_missing(tmp_path):
    watch_dir = tmp_path / "nonexistent" / "subdir"
    watcher = FileWatcher(watch_dir=watch_dir, on_file=lambda p: None)
    assert watch_dir.exists()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_watcher.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm_server.watcher'`

- [ ] **Step 3: Write the implementation**

Create `py2femm_server/watcher.py`:

```python
"""Filesystem watcher for shared-filesystem bridge mode."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable


class FileWatcher:
    """Polls a directory for new .lua files and triggers a callback."""

    def __init__(
        self,
        watch_dir: Path,
        on_file: Callable[[Path], None],
        poll_interval: float = 1.0,
    ) -> None:
        self.watch_dir = Path(watch_dir)
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.on_file = on_file
        self.poll_interval = poll_interval
        self._seen: set[str] = set()

    def poll_once(self) -> None:
        """Check for new .lua files and process them."""
        for lua_file in sorted(self.watch_dir.glob("*.lua")):
            if lua_file.name not in self._seen:
                self._seen.add(lua_file.name)
                self.on_file(lua_file)

    def run(self) -> None:
        """Run the watcher loop indefinitely."""
        while True:
            self.poll_once()
            time.sleep(self.poll_interval)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_watcher.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add py2femm_server/watcher.py tests/test_watcher.py
git commit -m "feat: add filesystem watcher for shared-fs bridge mode

Polls directory for new .lua files, triggers callback, tracks
processed files to avoid reprocessing. Atomic write safe."
```

---

## Task 7: Client Base and Local Client

**Files:**
- Create: `py2femm/client/base.py`
- Create: `py2femm/client/local.py`
- Test: `tests/test_local_client.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_local_client.py`:

```python
import time
from pathlib import Path
from threading import Thread
from unittest.mock import patch

from py2femm.client.base import FemmClientBase
from py2femm.client.local import LocalClient


def test_base_is_abstract():
    """FemmClientBase cannot be instantiated directly."""
    import pytest
    with pytest.raises(TypeError):
        FemmClientBase()


def test_local_client_writes_lua_to_workspace(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()
    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=5)

    def fake_femm():
        """Simulate FEMM: wait for .lua, write .csv result."""
        time.sleep(0.2)
        lua_files = list(workspace.glob("*.lua"))
        if lua_files:
            job_stem = lua_files[0].stem
            result_path = workspace / f"{job_stem}.csv"
            result_path.write_text("point,x,y,temperature_K\njunction,0,0,350\n")

    thread = Thread(target=fake_femm, daemon=True)
    thread.start()

    result = client.run("hi_analyze()")
    assert result.csv_data is not None
    assert "junction" in result.csv_data


def test_local_client_timeout(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()
    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=0.5)

    result = client.run("hi_analyze()")
    assert result.csv_data is None
    assert result.error is not None
    assert "timeout" in result.error.lower()


def test_local_client_atomic_write(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()
    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=5)

    # Start the run in background, just check that it writes .lua atomically
    from threading import Thread

    def do_run():
        client.run("hi_analyze()")

    t = Thread(target=do_run, daemon=True)
    t.start()
    time.sleep(0.2)

    # Should have a .lua file (not .tmp)
    lua_files = list(workspace.glob("*.lua"))
    tmp_files = list(workspace.glob("*.tmp"))
    assert len(lua_files) >= 1
    assert len(tmp_files) == 0  # .tmp already renamed
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_local_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm.client.base'`

- [ ] **Step 3: Write the base class**

Create `py2femm/client/base.py`:

```python
"""Abstract base class for py2femm clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ClientResult:
    """Result from a client.run() call."""

    csv_data: str | None = None
    error: str | None = None
    elapsed_s: float = 0.0


class FemmClientBase(ABC):
    """Abstract interface for FEMM simulation clients."""

    @abstractmethod
    def run(self, lua_script: str, timeout: int = 300) -> ClientResult:
        """Submit a Lua script and wait for results."""

    @abstractmethod
    def status(self) -> dict:
        """Return agent/connection status."""
```

- [ ] **Step 4: Write the local client**

Create `py2femm/client/local.py`:

```python
"""Shared-filesystem client for WSL-to-Windows bridge."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from py2femm.client.base import ClientResult, FemmClientBase


class LocalClient(FemmClientBase):
    """Client that communicates via shared filesystem (e.g., /mnt/c/)."""

    def __init__(
        self,
        workspace: Path | str,
        poll_interval: float = 1.0,
        timeout: int = 300,
    ) -> None:
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.poll_interval = poll_interval
        self.timeout = timeout

    def run(self, lua_script: str, timeout: int | None = None) -> ClientResult:
        """Write Lua to workspace, poll for CSV result."""
        timeout = timeout or self.timeout
        job_id = uuid.uuid4().hex[:12]
        lua_name = f"job_{job_id}"

        # Atomic write: .tmp then rename to .lua
        tmp_path = self.workspace / f"{lua_name}.tmp"
        lua_path = self.workspace / f"{lua_name}.lua"
        csv_path = self.workspace / f"{lua_name}.csv"

        tmp_path.write_text(lua_script, encoding="utf-8")
        tmp_path.rename(lua_path)

        # Poll for result
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if csv_path.exists():
                csv_data = csv_path.read_text(encoding="utf-8")
                elapsed = time.monotonic() - start
                # Clean up
                lua_path.unlink(missing_ok=True)
                csv_path.unlink(missing_ok=True)
                return ClientResult(csv_data=csv_data, elapsed_s=elapsed)
            time.sleep(self.poll_interval)

        elapsed = time.monotonic() - start
        lua_path.unlink(missing_ok=True)
        return ClientResult(error=f"Timeout after {elapsed:.1f}s waiting for results", elapsed_s=elapsed)

    def status(self) -> dict:
        """Check workspace accessibility."""
        return {
            "mode": "local",
            "workspace": str(self.workspace),
            "accessible": self.workspace.exists(),
        }
```

- [ ] **Step 5: Update `py2femm/client/__init__.py`**

```python
"""py2femm client package."""

from py2femm.client.base import ClientResult, FemmClientBase

__all__ = ["ClientResult", "FemmClientBase"]
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_local_client.py -v
```

Expected: All 3 tests PASS (timeout test may take ~0.5s).

- [ ] **Step 7: Commit**

```bash
git add py2femm/client/base.py py2femm/client/local.py py2femm/client/__init__.py tests/test_local_client.py
git commit -m "feat: add local client for shared-filesystem bridge

Abstract FemmClientBase with run()/status(). LocalClient writes
Lua to shared workspace, polls for CSV result with timeout."
```

---

## Task 8: Remote Client (REST)

**Files:**
- Create: `py2femm/client/remote.py`
- Test: `tests/test_remote_client.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_remote_client.py`:

```python
import pytest
from unittest.mock import patch, MagicMock

from py2femm.client.remote import RemoteClient


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


def test_remote_client_submit_and_poll():
    client = RemoteClient(base_url="http://localhost:8082")
    submit_resp = _mock_response(202, {"job_id": "abc123", "status": "queued"})
    poll_resp_running = _mock_response(200, {"job_id": "abc123", "status": "running", "result": None, "error": None})
    poll_resp_done = _mock_response(200, {
        "job_id": "abc123",
        "status": "completed",
        "result": {"csv_data": "point,x,y,T\njunction,0,0,350\n"},
        "error": None,
    })

    with patch("httpx.Client") as MockClient:
        mock_http = MockClient.return_value.__enter__ = MagicMock(return_value=MagicMock())
        instance = MockClient.return_value
        instance.post.return_value = submit_resp
        instance.get.side_effect = [poll_resp_running, poll_resp_done]

        result = client.run("hi_analyze()", timeout=10)

    assert result.csv_data is not None
    assert "junction" in result.csv_data


def test_remote_client_status():
    client = RemoteClient(base_url="http://localhost:8082")
    health_resp = _mock_response(200, {"status": "ok", "femm_path": "C:\\femm42\\bin\\femm.exe"})

    with patch.object(client, "_client") as mock_http:
        mock_http.get.return_value = health_resp
        status = client.status()

    assert status["status"] == "ok"


def test_remote_client_handles_failed_job():
    client = RemoteClient(base_url="http://localhost:8082")
    submit_resp = _mock_response(202, {"job_id": "abc123", "status": "queued"})
    poll_resp = _mock_response(200, {
        "job_id": "abc123",
        "status": "failed",
        "result": None,
        "error": "FEMM crashed",
    })

    with patch("httpx.Client") as MockClient:
        instance = MockClient.return_value
        instance.post.return_value = submit_resp
        instance.get.return_value = poll_resp

        result = client.run("hi_analyze()")

    assert result.error == "FEMM crashed"
    assert result.csv_data is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_remote_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm.client.remote'`

- [ ] **Step 3: Write the implementation**

Create `py2femm/client/remote.py`:

```python
"""REST API client for remote py2femm server."""

from __future__ import annotations

import time

import httpx

from py2femm.client.base import ClientResult, FemmClientBase


class RemoteClient(FemmClientBase):
    """Client that communicates with py2femm server via REST API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8082",
        poll_interval: float = 2.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval
        self._client = httpx.Client(base_url=self.base_url, timeout=30)

    def run(self, lua_script: str, timeout: int = 300) -> ClientResult:
        """Submit Lua script via REST API, poll until complete."""
        start = time.monotonic()

        # Submit
        resp = self._client.post(
            "/api/v1/jobs",
            json={"lua_script": lua_script, "timeout_s": timeout},
        )
        resp.raise_for_status()
        job_id = resp.json()["job_id"]

        # Poll
        while time.monotonic() - start < timeout:
            resp = self._client.get(f"/api/v1/jobs/{job_id}")
            resp.raise_for_status()
            data = resp.json()

            if data["status"] == "completed":
                elapsed = time.monotonic() - start
                csv_data = data.get("result", {}).get("csv_data") if data.get("result") else None
                return ClientResult(csv_data=csv_data, elapsed_s=elapsed)

            if data["status"] == "failed":
                elapsed = time.monotonic() - start
                return ClientResult(error=data.get("error", "Unknown error"), elapsed_s=elapsed)

            time.sleep(self.poll_interval)

        elapsed = time.monotonic() - start
        return ClientResult(error=f"Timeout after {elapsed:.1f}s", elapsed_s=elapsed)

    def status(self) -> dict:
        """Get agent health status."""
        resp = self._client.get("/api/v1/health")
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_remote_client.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add py2femm/client/remote.py tests/test_remote_client.py
git commit -m "feat: add REST client for remote agent communication

Submit Lua via POST, poll GET until completed/failed. Configurable
base URL and poll interval. Uses httpx for HTTP."
```

---

## Task 9: Auto-Detect Client

**Files:**
- Create: `py2femm/client/auto.py`
- Modify: `py2femm/client/__init__.py`
- Test: `tests/test_auto_client.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_auto_client.py`:

```python
import os
from pathlib import Path
from unittest.mock import patch

from py2femm.client.auto import FemmClient


def test_auto_detects_local_when_mnt_c_exists(tmp_path):
    workspace = tmp_path / "mnt" / "c" / "femm_workspace"
    workspace.mkdir(parents=True)
    with patch("py2femm.client.auto._DEFAULT_LOCAL_WORKSPACE", workspace):
        with patch("py2femm.client.auto._LOCAL_MARKER", workspace.parent):
            client = FemmClient()
    assert client._mode == "local"


def test_auto_detects_remote_from_env():
    with patch("py2femm.client.auto._LOCAL_MARKER", Path("/nonexistent")):
        with patch.dict(os.environ, {"PYFEMM_AGENT_URL": "http://192.168.1.10:8082"}):
            client = FemmClient()
    assert client._mode == "remote"
    assert client._remote_url == "http://192.168.1.10:8082"


def test_auto_raises_when_nothing_found():
    import pytest
    with patch("py2femm.client.auto._LOCAL_MARKER", Path("/nonexistent")):
        with patch.dict(os.environ, {}, clear=True):
            with patch("py2femm.client.auto._load_config_url", return_value=None):
                with pytest.raises(ConnectionError, match="setup instructions"):
                    FemmClient()


def test_explicit_mode_local(tmp_path):
    client = FemmClient(mode="local", workspace=tmp_path)
    assert client._mode == "local"


def test_explicit_mode_remote():
    client = FemmClient(mode="remote", url="http://myhost:8082")
    assert client._mode == "remote"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_auto_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm.client.auto'`

- [ ] **Step 3: Write the implementation**

Create `py2femm/client/auto.py`:

```python
"""Auto-detecting FEMM client — picks local or remote mode."""

from __future__ import annotations

import os
from pathlib import Path

from py2femm.client.base import ClientResult, FemmClientBase
from py2femm.client.local import LocalClient
from py2femm.client.remote import RemoteClient

_LOCAL_MARKER = Path("/mnt/c")
_DEFAULT_LOCAL_WORKSPACE = Path("/mnt/c/femm_workspace")


def _load_config_url() -> str | None:
    """Try to read agent URL from ~/.py2femm/config.yml."""
    config_path = Path.home() / ".py2femm" / "config.yml"
    if not config_path.exists():
        return None
    try:
        import yaml

        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        return cfg.get("agent", {}).get("url")
    except Exception:
        return None


class FemmClient(FemmClientBase):
    """Auto-detecting client: local (shared FS) or remote (REST API).

    Detection order:
    1. Explicit mode/url/workspace arguments
    2. /mnt/c/ exists -> local mode
    3. PYFEMM_AGENT_URL env var -> remote mode
    4. ~/.py2femm/config.yml -> remote mode
    5. Raise ConnectionError
    """

    def __init__(
        self,
        mode: str | None = None,
        url: str | None = None,
        workspace: Path | str | None = None,
    ) -> None:
        self._mode: str
        self._remote_url: str | None = None
        self._delegate: FemmClientBase

        if mode == "local":
            ws = Path(workspace) if workspace else _DEFAULT_LOCAL_WORKSPACE
            self._mode = "local"
            self._delegate = LocalClient(workspace=ws)
            return

        if mode == "remote":
            self._mode = "remote"
            self._remote_url = url or "http://localhost:8082"
            self._delegate = RemoteClient(base_url=self._remote_url)
            return

        # Auto-detect
        if _LOCAL_MARKER.exists():
            ws = Path(workspace) if workspace else _DEFAULT_LOCAL_WORKSPACE
            self._mode = "local"
            self._delegate = LocalClient(workspace=ws)
            return

        env_url = os.environ.get("PYFEMM_AGENT_URL")
        if env_url:
            self._mode = "remote"
            self._remote_url = env_url
            self._delegate = RemoteClient(base_url=env_url)
            return

        config_url = _load_config_url()
        if config_url:
            self._mode = "remote"
            self._remote_url = config_url
            self._delegate = RemoteClient(base_url=config_url)
            return

        raise ConnectionError(
            "Could not detect py2femm server. Setup instructions:\n"
            "  Local (WSL):  Ensure /mnt/c/ is accessible and run start_femm_server.bat on Windows\n"
            "  Remote:       Set PYFEMM_AGENT_URL=http://<host>:8082\n"
            "  Config:       Create ~/.py2femm/config.yml with agent.url"
        )

    def run(self, lua_script: str, timeout: int = 300) -> ClientResult:
        return self._delegate.run(lua_script, timeout=timeout)

    def status(self) -> dict:
        result = self._delegate.status()
        result["mode"] = self._mode
        return result
```

- [ ] **Step 4: Update `py2femm/client/__init__.py`**

```python
"""py2femm client package."""

from py2femm.client.auto import FemmClient
from py2femm.client.base import ClientResult, FemmClientBase

__all__ = ["FemmClient", "ClientResult", "FemmClientBase"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_auto_client.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add py2femm/client/auto.py py2femm/client/__init__.py tests/test_auto_client.py
git commit -m "feat: add auto-detecting FemmClient

Checks /mnt/c/ for local mode, PYFEMM_AGENT_URL env var or
~/.py2femm/config.yml for remote mode. Explicit override via
mode='local'|'remote' constructor args."
```

---

## Task 10: Configuration System

**Files:**
- Create: `py2femm/config/schema.py`
- Create: `py2femm/config/loader.py`
- Create: `py2femm/config/defaults.yml`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_config.py`:

```python
from pathlib import Path

import yaml

from py2femm.config.schema import Py2FemmConfig
from py2femm.config.loader import load_config, find_config_files


def test_default_config():
    cfg = Py2FemmConfig()
    assert cfg.agent_mode == "auto"
    assert cfg.agent_url == "http://localhost:8082"
    assert cfg.femm_timeout == 300
    assert cfg.cache_enabled is True


def test_config_from_dict():
    cfg = Py2FemmConfig.from_dict({
        "agent": {"mode": "remote", "url": "http://myhost:9090"},
        "femm": {"timeout": 600},
    })
    assert cfg.agent_mode == "remote"
    assert cfg.agent_url == "http://myhost:9090"
    assert cfg.femm_timeout == 600


def test_config_merge():
    base = Py2FemmConfig()
    override = {"agent": {"mode": "local"}}
    merged = base.merge(override)
    assert merged.agent_mode == "local"
    assert merged.agent_url == "http://localhost:8082"  # unchanged


def test_find_config_files_discovers_local(tmp_path):
    config_file = tmp_path / "py2femm.yml"
    config_file.write_text("agent:\n  mode: local\n")
    files = find_config_files(start_dir=tmp_path)
    assert config_file in files


def test_find_config_files_walks_up(tmp_path):
    config_file = tmp_path / "py2femm.yml"
    config_file.write_text("agent:\n  mode: local\n")
    subdir = tmp_path / "sub" / "deep"
    subdir.mkdir(parents=True)
    files = find_config_files(start_dir=subdir)
    assert config_file in files


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "py2femm.yml"
    config_file.write_text("agent:\n  mode: remote\n  url: http://10.0.0.1:8082\n")
    cfg = load_config(start_dir=tmp_path)
    assert cfg.agent_mode == "remote"
    assert cfg.agent_url == "http://10.0.0.1:8082"


def test_load_config_defaults_when_no_file(tmp_path):
    cfg = load_config(start_dir=tmp_path)
    assert cfg.agent_mode == "auto"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm.config.schema'`

- [ ] **Step 3: Write config schema**

Create `py2femm/config/schema.py`:

```python
"""Configuration schema for py2femm."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Py2FemmConfig:
    """py2femm configuration with defaults."""

    agent_mode: str = "auto"
    agent_url: str = "http://localhost:8082"
    agent_workspace: str = "/mnt/c/femm_workspace"
    femm_path: str = ""
    femm_timeout: int = 300
    femm_headless: bool = True
    cache_enabled: bool = True
    cache_dir: str = "~/.py2femm/cache"
    cache_max_size_gb: int = 5
    results_format: str = "csv"
    results_dir: str = "./results"

    @classmethod
    def from_dict(cls, data: dict) -> Py2FemmConfig:
        """Create config from nested YAML-style dict."""
        flat = {}
        for section_key, section in data.items():
            if isinstance(section, dict):
                for key, value in section.items():
                    flat_key = f"{section_key}_{key}"
                    flat[flat_key] = value
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in flat.items() if k in valid_fields}
        return cls(**filtered)

    def merge(self, overrides: dict) -> Py2FemmConfig:
        """Return new config with overrides applied."""
        base = self.to_dict()
        for section_key, section in overrides.items():
            if isinstance(section, dict):
                if section_key not in base:
                    base[section_key] = {}
                base[section_key].update(section)
            else:
                base[section_key] = section
        return Py2FemmConfig.from_dict(base)

    def to_dict(self) -> dict:
        """Convert to nested dict matching YAML structure."""
        return {
            "agent": {
                "mode": self.agent_mode,
                "url": self.agent_url,
                "workspace": self.agent_workspace,
            },
            "femm": {
                "path": self.femm_path,
                "timeout": self.femm_timeout,
                "headless": self.femm_headless,
            },
            "cache": {
                "enabled": self.cache_enabled,
                "dir": self.cache_dir,
                "max_size_gb": self.cache_max_size_gb,
            },
            "results": {
                "format": self.results_format,
                "dir": self.results_dir,
            },
        }
```

- [ ] **Step 4: Write config loader**

Create `py2femm/config/loader.py`:

```python
"""Hierarchical YAML config loader."""

from __future__ import annotations

from pathlib import Path

import yaml

from py2femm.config.schema import Py2FemmConfig

_CONFIG_FILENAME = "py2femm.yml"


def find_config_files(start_dir: Path | None = None) -> list[Path]:
    """Find py2femm.yml files walking up from start_dir, plus user global."""
    found = []
    if start_dir is None:
        start_dir = Path.cwd()
    start_dir = Path(start_dir).resolve()

    # Walk up directory tree
    current = start_dir
    while True:
        candidate = current / _CONFIG_FILENAME
        if candidate.exists():
            found.append(candidate)
        parent = current.parent
        if parent == current:
            break
        current = parent

    # User global
    user_config = Path.home() / ".py2femm" / "config.yml"
    if user_config.exists():
        found.append(user_config)

    return found


def load_config(start_dir: Path | None = None) -> Py2FemmConfig:
    """Load and merge config from all discovered files. Closest file wins."""
    files = find_config_files(start_dir)
    cfg = Py2FemmConfig()

    # Apply in reverse order (global first, local last = local wins)
    for config_file in reversed(files):
        with open(config_file) as f:
            data = yaml.safe_load(f) or {}
        cfg = cfg.merge(data)

    return cfg
```

- [ ] **Step 5: Create defaults file**

Create `py2femm/config/defaults.yml`:

```yaml
agent:
  mode: auto
  url: http://localhost:8082
  workspace: /mnt/c/femm_workspace

femm:
  path: ""
  timeout: 300
  headless: true

cache:
  enabled: true
  dir: ~/.py2femm/cache
  max_size_gb: 5

results:
  format: csv
  dir: ./results
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add py2femm/config/schema.py py2femm/config/loader.py py2femm/config/defaults.yml tests/test_config.py
git commit -m "feat: add hierarchical YAML config with merge

Py2FemmConfig dataclass with from_dict/merge/to_dict. Loader walks
up directory tree for py2femm.yml, merges with user global."
```

---

## Task 11: CLI

**Files:**
- Create: `py2femm/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli.py`:

```python
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from py2femm.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "py2femm" in result.output.lower()


def test_cli_run_with_file(runner, tmp_path):
    lua_file = tmp_path / "test.lua"
    lua_file.write_text("hi_analyze()")

    mock_result = MagicMock()
    mock_result.csv_data = "point,x,y,T\njunction,0,0,350\n"
    mock_result.error = None

    with patch("py2femm.cli.FemmClient") as MockClient:
        MockClient.return_value.run.return_value = mock_result
        result = runner.invoke(main, ["run", str(lua_file)])

    assert result.exit_code == 0
    assert "junction" in result.output


def test_cli_run_missing_file(runner):
    result = runner.invoke(main, ["run", "/nonexistent/file.lua"])
    assert result.exit_code != 0


def test_cli_run_with_output(runner, tmp_path):
    lua_file = tmp_path / "test.lua"
    lua_file.write_text("hi_analyze()")
    output_file = tmp_path / "result.csv"

    mock_result = MagicMock()
    mock_result.csv_data = "point,x,y,T\njunction,0,0,350\n"
    mock_result.error = None

    with patch("py2femm.cli.FemmClient") as MockClient:
        MockClient.return_value.run.return_value = mock_result
        result = runner.invoke(main, ["run", str(lua_file), "--output", str(output_file)])

    assert result.exit_code == 0
    assert output_file.read_text() == "point,x,y,T\njunction,0,0,350\n"


def test_cli_status(runner):
    with patch("py2femm.cli.FemmClient") as MockClient:
        MockClient.return_value.status.return_value = {
            "mode": "remote",
            "status": "ok",
            "femm_path": "C:\\femm42\\bin\\femm.exe",
        }
        result = runner.invoke(main, ["status"])

    assert result.exit_code == 0
    assert "ok" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cli.py -v
```

Expected: `ModuleNotFoundError: No module named 'py2femm.cli'`

- [ ] **Step 3: Write the implementation**

Create `py2femm/cli.py`:

```python
"""py2femm CLI — command-line interface for FEMM simulation automation."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from py2femm.client import FemmClient


@click.group()
def main():
    """py2femm — Python automation for FEMM simulations."""


@main.command()
@click.argument("lua_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="Save results to file")
@click.option("--timeout", "-t", type=int, default=300, help="Timeout in seconds")
@click.option("--mode", type=click.Choice(["auto", "local", "remote"]), default="auto")
@click.option("--url", default=None, help="Agent URL for remote mode")
def run(lua_file: str, output: str | None, timeout: int, mode: str, url: str | None):
    """Run a FEMM Lua script and return results."""
    lua_script = Path(lua_file).read_text(encoding="utf-8")

    kwargs = {}
    if mode != "auto":
        kwargs["mode"] = mode
    if url:
        kwargs["url"] = url

    try:
        client = FemmClient(**kwargs)
    except ConnectionError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    result = client.run(lua_script, timeout=timeout)

    if result.error:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

    if output:
        Path(output).write_text(result.csv_data, encoding="utf-8")
        click.echo(f"Results saved to {output}")
    else:
        click.echo(result.csv_data)


@main.command()
@click.option("--mode", type=click.Choice(["auto", "local", "remote"]), default="auto")
@click.option("--url", default=None, help="Agent URL for remote mode")
def status(mode: str, url: str | None):
    """Check py2femm server status."""
    kwargs = {}
    if mode != "auto":
        kwargs["mode"] = mode
    if url:
        kwargs["url"] = url

    try:
        client = FemmClient(**kwargs)
        info = client.status()
        for key, value in info.items():
            click.echo(f"  {key}: {value}")
    except ConnectionError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@main.command("run-batch")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--output-dir", "-o", type=click.Path(), default=None, help="Directory for results")
@click.option("--timeout", "-t", type=int, default=300, help="Timeout per script")
def run_batch(directory: str, output_dir: str | None, timeout: int):
    """Run all .lua files in a directory."""
    lua_dir = Path(directory)
    lua_files = sorted(lua_dir.glob("*.lua"))

    if not lua_files:
        click.echo(f"No .lua files found in {directory}")
        return

    out_dir = Path(output_dir) if output_dir else lua_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        client = FemmClient()
    except ConnectionError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    for lua_file in lua_files:
        click.echo(f"Running {lua_file.name}...", nl=False)
        lua_script = lua_file.read_text(encoding="utf-8")
        result = client.run(lua_script, timeout=timeout)

        if result.error:
            click.echo(f" FAILED: {result.error}")
        else:
            csv_path = out_dir / f"{lua_file.stem}.csv"
            csv_path.write_text(result.csv_data, encoding="utf-8")
            click.echo(f" OK ({result.elapsed_s:.1f}s) -> {csv_path.name}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add py2femm/cli.py tests/test_cli.py
git commit -m "feat: add Click CLI with run, run-batch, and status commands

py2femm run <script.lua> submits to agent and prints results.
py2femm run-batch <dir/> processes all .lua files.
py2femm status checks agent connectivity."
```

---

## Task 12: Windows Batch Files

**Files:**
- Create: `setup_femm.bat`
- Create: `start_femm_server.bat`
- Create: `config/defaults.yml`
- Create: `tools/configure_femm.py`

- [ ] **Step 1: Create `tools/configure_femm.py`**

```bash
mkdir -p tools
```

Create `tools/configure_femm.py`:

```python
"""Interactive FEMM path configuration (called by setup_femm.bat)."""

from pathlib import Path

import yaml

FEMM_SEARCH_PATHS = [
    Path(r"C:\femm42\bin\femm.exe"),
    Path(r"C:\Program Files\femm42\bin\femm.exe"),
    Path(r"C:\Program Files (x86)\femm42\bin\femm.exe"),
]

CONFIG_PATH = Path("config/default.yml")


def main():
    # Auto-detect
    femm_path = None
    for candidate in FEMM_SEARCH_PATHS:
        if candidate.exists():
            femm_path = candidate
            print(f"  [OK] FEMM found: {femm_path}")
            break

    if femm_path is None:
        print("  FEMM not found in standard locations.")
        user_path = input("  Enter path to femm.exe: ").strip()
        if not user_path:
            print("  [ERROR] No path provided.")
            raise SystemExit(1)
        femm_path = Path(user_path)
        if not femm_path.exists():
            print(f"  [ERROR] File not found: {femm_path}")
            raise SystemExit(1)

    # Workspace
    default_ws = r"C:\femm_workspace"
    ws = input(f"  Workspace directory [{default_ws}]: ").strip() or default_ws

    # Save config
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if CONFIG_PATH.exists():
        cfg = yaml.safe_load(CONFIG_PATH.read_text()) or {}

    cfg.setdefault("femm", {})
    cfg["femm"]["path"] = str(femm_path)
    cfg.setdefault("agent", {})
    cfg["agent"]["workspace"] = ws

    CONFIG_PATH.write_text(yaml.dump(cfg, default_flow_style=False, sort_keys=False))
    print(f"  Configuration saved to {CONFIG_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create `setup_femm.bat`**

Create `setup_femm.bat`:

```batch
@echo off
REM ──────────────────────────────────────────────────────────
REM  py2femm Setup — One-time environment configuration
REM
REM  Steps:
REM    1. Scan for Python + conda
REM    2. Choose Python environment
REM    3. Activate env + install dependencies
REM    4. Configure FEMM path and workspace
REM
REM  Settings saved to config/default.yml.
REM  Run this ONCE before using start_femm_server.bat.
REM ──────────────────────────────────────────────────────────

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   py2femm Server Setup
echo ============================================================

REM ══════════════════════════════════════════════════════════
REM  Step 1: Scan for Python and conda
REM ══════════════════════════════════════════════════════════
echo.
echo [1/4] Scanning for Python and conda...

set "HAS_PYTHON=0"
set "HAS_CONDA=0"
set "CONDA_ROOT="

call conda --version >nul 2>&1
if not errorlevel 1 (
    set "HAS_CONDA=1"
    for /f "delims=" %%V in ('call conda --version 2^>^&1') do echo       [OK] %%V
    for /f "delims=" %%P in ('where conda.bat 2^>nul') do (
        for %%Q in ("%%~dpP..") do set "CONDA_ROOT=%%~fQ"
    )
    goto :conda_found
)

echo       conda not on PATH, scanning...
for %%D in (
    "%USERPROFILE%\miniconda3"
    "%USERPROFILE%\anaconda3"
    "%LOCALAPPDATA%\miniconda3"
    "%LOCALAPPDATA%\anaconda3"
    "C:\miniconda3"
    "C:\anaconda3"
) do (
    if exist "%%~D\condabin\conda.bat" (
        set "HAS_CONDA=1"
        set "CONDA_ROOT=%%~D"
        echo       [OK] conda found: %%~D
        goto :conda_found
    )
)
echo       conda not found.

:conda_found

if defined CONDA_ROOT (
    if exist "!CONDA_ROOT!\condabin\conda_hook.bat" (
        call "!CONDA_ROOT!\condabin\conda_hook.bat"
    )
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "HAS_PYTHON=1"
    for /f "delims=" %%V in ('python --version 2^>^&1') do echo       [OK] %%V
    goto :python_found
)

for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
) do (
    if exist "%%~D\python.exe" (
        set "HAS_PYTHON=1"
        set "PATH=%%~D;%%~D\Scripts;!PATH!"
        echo       [OK] Python found: %%~D
        goto :python_found
    )
)

if "%HAS_CONDA%"=="1" set "HAS_PYTHON=1"

:python_found

if "%HAS_PYTHON%"=="0" if "%HAS_CONDA%"=="0" (
    echo [ERROR] No Python or conda found.
    echo   Install from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM ══════════════════════════════════════════════════════════
REM  Step 2: Choose environment
REM ══════════════════════════════════════════════════════════
echo.
echo [2/4] Python environment...

set "ENV_TYPE=venv"

if "%HAS_CONDA%"=="1" (
    set /p "USE_CONDA=  Use conda environment? [y/N]: "
    if /i "!USE_CONDA!"=="y" (
        set "ENV_TYPE=conda"
        set /p "ENV_NAME=  Conda env name [py2femm]: "
        if not defined ENV_NAME set "ENV_NAME=py2femm"
    )
)

REM ══════════════════════════════════════════════════════════
REM  Step 3: Activate + install
REM ══════════════════════════════════════════════════════════
echo.
echo [3/4] Installing dependencies...

if "%ENV_TYPE%"=="conda" (
    call conda activate %ENV_NAME% 2>nul || (
        echo       Creating conda env %ENV_NAME%...
        call conda create -n %ENV_NAME% python=3.11 -y
        call conda activate %ENV_NAME%
    )
) else (
    if not exist ".venv\Scripts\activate.bat" (
        echo       Creating .venv...
        python -m venv .venv
    )
    call .venv\Scripts\activate.bat
)

python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e ".[agent]"
echo       [OK] py2femm[agent] installed.

REM ══════════════════════════════════════════════════════════
REM  Step 4: Configure FEMM
REM ══════════════════════════════════════════════════════════
echo.
echo [4/4] Configuring FEMM...

REM Save env config
python -c "import yaml; from pathlib import Path; p=Path('config/default.yml'); p.parent.mkdir(exist_ok=True); cfg=yaml.safe_load(p.read_text()) if p.exists() else {}; cfg.setdefault('python',{}); cfg['python']['env_type']='%ENV_TYPE%'; cfg['python']['env_name']='%ENV_NAME%'; cfg['python']['conda_root']=r'%CONDA_ROOT%'; p.write_text(yaml.dump(cfg,default_flow_style=False,sort_keys=False))"

python tools\configure_femm.py
if errorlevel 1 (
    echo [ERROR] FEMM configuration failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Setup complete! Run start_femm_server.bat to launch.
echo ============================================================
echo.
pause
```

- [ ] **Step 3: Create `start_femm_server.bat`**

Create `start_femm_server.bat`:

```batch
@echo off
REM ──────────────────────────────────────────────────────────
REM  Start py2femm Server (REST API + Filesystem Watcher)
REM
REM  Reads config from config/default.yml (set by setup_femm.bat).
REM  Run setup_femm.bat first.
REM ──────────────────────────────────────────────────────────

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ── Read Python environment config ───────────────────────
set "ENV_TYPE=venv"
set "ENV_NAME="
set "CONDA_ROOT="
if exist "config\default.yml" (
    for /f "usebackq tokens=2 delims=: " %%V in (`findstr "env_type:" "config\default.yml"`) do set "ENV_TYPE=%%V"
    for /f "usebackq tokens=2 delims=: " %%V in (`findstr "env_name:" "config\default.yml"`) do set "ENV_NAME=%%V"
    for /f "usebackq tokens=1,* delims=: " %%A in (`findstr "conda_root:" "config\default.yml"`) do set "CONDA_ROOT=%%B"
    if defined CONDA_ROOT for /f "tokens=*" %%T in ("!CONDA_ROOT!") do set "CONDA_ROOT=%%T"
)

REM ── Bootstrap conda if needed ────────────────────────────
call conda --version >nul 2>&1
if errorlevel 1 (
    if defined CONDA_ROOT (
        if exist "!CONDA_ROOT!\condabin\conda_hook.bat" (
            call "!CONDA_ROOT!\condabin\conda_hook.bat"
            goto :conda_ready
        )
    )
    for %%D in (
        "%USERPROFILE%\miniconda3"
        "%USERPROFILE%\anaconda3"
        "%LOCALAPPDATA%\miniconda3"
        "%LOCALAPPDATA%\anaconda3"
        "C:\miniconda3"
        "C:\anaconda3"
    ) do (
        if exist "%%~D\condabin\conda_hook.bat" (
            call "%%~D\condabin\conda_hook.bat"
            goto :conda_ready
        )
    )
)
:conda_ready

if "%ENV_TYPE%"=="conda" (
    echo Activating conda env: !ENV_NAME!
    call conda activate !ENV_NAME!
    if errorlevel 1 (
        echo [ERROR] Failed to activate conda env. Run setup_femm.bat.
        pause
        exit /b 1
    )
) else (
    if not exist ".venv\Scripts\activate.bat" (
        echo [ERROR] .venv not found. Run setup_femm.bat first.
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
)

REM ── Launch py2femm server ─────────────────────────────────
echo.
echo Starting py2femm server on 0.0.0.0:8082...
echo (Press Ctrl+C to stop)
echo.
python -m py2femm_server --host 0.0.0.0 --port 8082

echo.
echo py2femm server stopped. Press any key to exit.
pause
```

- [ ] **Step 4: Create agent-side config defaults**

Create `config/defaults.yml`:

```yaml
# py2femm server defaults (Windows side)
# Overwritten by setup_femm.bat

femm:
  path: ""
  timeout: 300
  headless: true

agent:
  workspace: "C:\\femm_workspace"
  host: "0.0.0.0"
  port: 8082
```

- [ ] **Step 5: Commit**

```bash
git add setup_femm.bat start_femm_server.bat tools/configure_femm.py config/defaults.yml
git commit -m "feat: add Windows batch files for agent setup and launch

setup_femm.bat: one-time env + FEMM detection + dependency install.
start_femm_server.bat: activate env + launch REST agent on port 8082.
Mirrors pyplecs setup_env.bat / start_plecs.bat pattern."
```

---

## Task 13: Integration Test — Full Round-Trip

**Files:**
- Create: `tests/test_integration.py`
- Create: `examples/01_simple_thermal.py`

- [ ] **Step 1: Write integration test (agent + local client)**

Create `tests/test_integration.py`:

```python
"""Integration test: full round-trip without real FEMM.

Simulates the agent-side by watching for .lua files and writing
fake .csv results. Tests the client -> filesystem -> agent -> result
pipeline end-to-end.
"""

import time
from pathlib import Path
from threading import Thread

from py2femm.client.local import LocalClient


def _fake_femm_agent(workspace: Path, stop_after: int = 1):
    """Watch for .lua files and write fake CSV results."""
    processed = 0
    for _ in range(50):  # max 5 seconds
        for lua_file in workspace.glob("*.lua"):
            csv_name = lua_file.stem + ".csv"
            csv_path = workspace / csv_name
            if not csv_path.exists():
                csv_path.write_text(
                    "point,x,y,temperature_K\n"
                    "base_center,0.025,0,355.2\n"
                    "fin_tip,0.025,0.03,310.8\n"
                )
                processed += 1
                if processed >= stop_after:
                    return
        time.sleep(0.1)


def test_full_roundtrip(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()

    # Start fake agent in background
    agent_thread = Thread(target=_fake_femm_agent, args=(workspace,), daemon=True)
    agent_thread.start()

    # Run client
    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=10)
    result = client.run("hi_analyze()")

    assert result.csv_data is not None
    assert "base_center" in result.csv_data
    assert "355.2" in result.csv_data
    assert result.error is None
    assert result.elapsed_s > 0


def test_full_roundtrip_csv_to_dataframe(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()

    agent_thread = Thread(target=_fake_femm_agent, args=(workspace,), daemon=True)
    agent_thread.start()

    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=10)
    result = client.run("hi_analyze()")

    from py2femm.client.models import JobResult

    job_result = JobResult(csv_data=result.csv_data)
    df = job_result.to_dataframe()
    assert len(df) == 2
    assert set(df.columns) == {"point", "x", "y", "temperature_K"}
    assert df.iloc[0]["temperature_K"] == 355.2
```

- [ ] **Step 2: Run integration test**

```bash
pytest tests/test_integration.py -v
```

Expected: All 2 tests PASS.

- [ ] **Step 3: Create example script**

Create `examples/01_simple_thermal.py`:

```python
"""Example: Submit a pre-built Lua script to py2femm server.

Usage:
    # From WSL with agent running on Windows:
    python examples/01_simple_thermal.py

    # Or with explicit mode:
    PYFEMM_AGENT_URL=http://localhost:8082 python examples/01_simple_thermal.py
"""

from py2femm.client import FemmClient
from py2femm.client.models import JobResult

# A minimal FEMM heat flow Lua script
LUA_SCRIPT = """\
showconsole()
newdocument(2)
hi_probdef("meters", "planar", 1e-8, 0, 30)

-- Simple aluminum block 50mm x 10mm
hi_addnode(0, 0)
hi_addnode(0.05, 0)
hi_addnode(0.05, 0.01)
hi_addnode(0, 0.01)
hi_addsegment(0, 0, 0.05, 0)
hi_addsegment(0.05, 0, 0.05, 0.01)
hi_addsegment(0.05, 0.01, 0, 0.01)
hi_addsegment(0, 0.01, 0, 0)

-- Material: aluminum (k=200 W/mK)
hi_addmaterial("aluminum", 200, 200, 0)
hi_addblocklabel(0.025, 0.005)
hi_selectlabel(0.025, 0.005)
hi_setblockprop("aluminum", 1, 0, 0)
hi_clearselected()

-- BC: heat flux on bottom (5000 W/m2), convection on top (h=50, T=300K)
hi_addboundprop("source", 1, 0, 5000)
hi_addboundprop("cooling", 2, 0, 0, 300, 50)

hi_selectsegment(0.025, 0)
hi_setsegmentprop("source", 0, 1, 0, 0, "")
hi_clearselected()

hi_selectsegment(0.025, 0.01)
hi_setsegmentprop("cooling", 0, 1, 0, 0, "")
hi_clearselected()

-- Solve
hi_analyze()
hi_loadsolution()

-- Extract results
if py2femm_outfile then
    outfile = openfile(py2femm_outfile, "w")
else
    outfile = openfile("results.csv", "w")
end
write(outfile, "point,x,y,temperature_K\\n")
T1 = ho_getpointvalues(0.025, 0)
write(outfile, string.format("base_center,0.025,0,%.4f\\n", T1[1]))
T2 = ho_getpointvalues(0.025, 0.01)
write(outfile, string.format("top_center,0.025,0.01,%.4f\\n", T2[1]))
closefile(outfile)
"""


def main():
    print("Connecting to py2femm server...")
    try:
        client = FemmClient()
    except ConnectionError as e:
        print(f"Error: {e}")
        print("\nMake sure the py2femm server is running on Windows.")
        print("  1. Run setup_femm.bat (one-time)")
        print("  2. Run start_femm_server.bat")
        return

    print(f"Agent mode: {client._mode}")
    print("Submitting Lua script...")

    result = client.run(LUA_SCRIPT, timeout=120)

    if result.error:
        print(f"Error: {result.error}")
        return

    print(f"Completed in {result.elapsed_s:.1f}s")
    print()

    # Parse results
    job_result = JobResult(csv_data=result.csv_data)
    df = job_result.to_dataframe()
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py examples/01_simple_thermal.py
git commit -m "feat: add integration test and thermal example script

End-to-end test with fake FEMM agent. Example shows full workflow:
generate Lua, submit to agent, parse CSV results to DataFrame."
```

---

## Task 14: README and Final Polish

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

Create `README.md`:

```markdown
# py2femm

Python automation platform for [FEMM](https://www.femm.info/) finite element simulations.

Fork of [tamasorosz/py2femm](https://github.com/tamasorosz/py2femm) with added:
- **WSL-to-Windows bridge** — run FEMM from Linux/WSL via shared filesystem or REST API
- **REST agent** — FastAPI server on Windows, accepts Lua scripts, returns CSV results
- **CLI** — `py2femm run script.lua` from any OS
- **Batch execution** — `py2femm run-batch dir/` for parameter sweeps

## Quick Start

### 1. Install (WSL / Linux / Mac)

```bash
pip install py2femm
```

### 2. Setup Agent (Windows)

```
setup_femm.bat          # One-time: detect Python, FEMM, create env
start_femm_server.bat    # Launch REST API on port 8082
```

### 3. Run Simulations

```bash
# From WSL:
py2femm run my_thermal_model.lua
py2femm run my_model.lua --output results.csv
py2femm run-batch ./lua_scripts/
py2femm status
```

### Python API

```python
from py2femm.client import FemmClient

client = FemmClient()  # auto-detects local or remote
result = client.run(open("model.lua").read())
print(result.csv_data)
```

## Architecture

```
WSL / Linux / Mac              Windows
┌────────────────┐             ┌──────────────────┐
│  py2femm       │  REST API   │  py2femm server   │
│  client + CLI  │────────────>│  FastAPI server   │
│                │  or shared  │  FEMM executor    │
│                │  filesystem │  File watcher     │
└────────────────┘             └──────────────────┘
```

## License

AGPL-3.0 (inherited from upstream py2femm)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with quick start and architecture overview"
```

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 4: Final commit if any fixes needed**

If any tests fail, fix and commit:

```bash
git add -u
git commit -m "fix: test suite fixes for Phase 1 MVP"
```
