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
    """Inject py2femm output path variables and error logging at the top of a Lua script."""
    # Use forward slashes for Lua compatibility, resolve to absolute path
    workdir_lua = str(workdir.resolve()).replace("\\", "/")
    preamble = (
        "-- Injected by py2femm agent\n"
        f'py2femm_workdir = "{workdir_lua}/"\n'
        f'py2femm_outfile = py2femm_workdir .. "results.csv"\n'
        f'py2femm_errlog = py2femm_workdir .. "error.log"\n'
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
        lua_path_abs = str(lua_path.resolve())
        cmd = [str(self.femm_path), f"-lua-script={lua_path_abs}", "-windowhide"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            # Write stderr to error.log in job dir for debugging
            if stderr:
                (job_dir / "stderr.log").write_bytes(stderr)
            if stdout:
                (job_dir / "stdout.log").write_bytes(stdout)
            csv_data = self.read_result(job_dir)
            return csv_data, proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            return None, -1

    def read_result(self, job_dir: Path) -> str | None:
        """Read the results.csv from a job directory."""
        result_path = job_dir / "results.csv"
        if not result_path.exists():
            return None
        return result_path.read_text(encoding="utf-8")

    def read_error_log(self, job_dir: Path) -> str | None:
        """Read any error logs from a job directory."""
        logs = []
        for name in ["error.log", "stderr.log", "stdout.log"]:
            p = job_dir / name
            if p.exists() and p.stat().st_size > 0:
                logs.append(f"--- {name} ---\n{p.read_text(encoding='utf-8', errors='replace')}")
        return "\n".join(logs) if logs else None
