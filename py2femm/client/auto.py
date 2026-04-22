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
    """Try to read server URL from ~/.py2femm/config.yml."""
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
