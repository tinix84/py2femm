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
