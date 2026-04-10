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
