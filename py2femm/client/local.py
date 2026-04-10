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
