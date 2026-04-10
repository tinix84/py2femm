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
