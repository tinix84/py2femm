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
