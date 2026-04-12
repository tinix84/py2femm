"""FEMM subprocess executor with Lua preamble injection."""

from __future__ import annotations

import subprocess
import time
import uuid
from pathlib import Path
from typing import NamedTuple


class PreparedJob(NamedTuple):
    job_dir: Path
    lua_path: Path


def inject_preamble(lua_script: str, workdir: Path) -> str:
    """Inject py2femm output path variables and redirect file outputs to the job directory.

    The FemmProblem class generates ``openfile("some_name.csv", "w")`` with
    relative paths.  FEMM resolves those relative to its own working directory
    which is unpredictable when launched headlessly.  We rewrite every
    ``openfile("…", "w")`` call so the file is created inside *workdir*
    (the agent's job directory) where ``read_result`` can find it.

    The canonical output is always ``results.csv`` — the **first**
    ``openfile`` targeting the problem's ``out_file`` is rewritten to
    ``results.csv`` so the agent picks it up.
    """
    import re

    workdir_lua = str(workdir.resolve()).replace("\\", "/")
    preamble = (
        "-- Injected by py2femm agent\n"
        f'py2femm_workdir = "{workdir_lua}/"\n'
        f'py2femm_outfile = py2femm_workdir .. "results.csv"\n'
        f'py2femm_errlog = py2femm_workdir .. "error.log"\n'
        "\n"
    )

    # Detect the problem's out_file: the first openfile target that ends in .csv
    # and is assigned to file_out.  We need its name so we can rewrite *every*
    # occurrence (FemmProblem.init_problem emits duplicate openfile lines).
    out_file_name = None
    m0 = re.search(r'file_out\s*=\s*openfile\("([^"]+\.csv)"', lua_script)
    if m0:
        out_file_name = m0.group(1)

    def _rewrite_openfile(m: re.Match) -> str:
        filename = m.group(1)
        mode = m.group(2)
        # Already absolute — leave it alone
        if "/" in filename or "\\" in filename:
            return m.group(0)
        # The problem's main output file → always map to results.csv
        if out_file_name and filename == out_file_name:
            return f'openfile(py2femm_workdir .. "results.csv", "{mode}")'
        return f'openfile(py2femm_workdir .. "{filename}", "{mode}")'

    patched = re.sub(
        r'openfile\("([^"]+)",\s*"([^"]+)"\)', _rewrite_openfile, lua_script
    )

    # Also rewrite remove("relative.csv") so it doesn't fail on missing files elsewhere
    def _rewrite_remove(m: re.Match) -> str:
        filename = m.group(1)
        if "/" in filename or "\\" in filename:
            return m.group(0)
        return f'remove(py2femm_workdir .. "{filename}")'

    patched = re.sub(r'remove\("([^"]+)"\)', _rewrite_remove, patched)

    # Rewrite saveas("absolute/path.feh") → saveas("<workdir>/problem.feh")
    # so the .feh file lands in the job directory for debugging
    def _rewrite_saveas(m: re.Match) -> str:
        prefix = m.group(1)   # e.g. hi_saveas or mi_saveas
        filepath = m.group(2)
        # Extract just the filename
        fname = filepath.replace("\\", "/").rsplit("/", 1)[-1] if "/" in filepath or "\\" in filepath else filepath
        return f'{prefix}(py2femm_workdir .. "{fname}")'

    patched = re.sub(
        r'(\w+_saveas)\("([^"]+)"\)', _rewrite_saveas, patched
    )

    return preamble + patched


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
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
