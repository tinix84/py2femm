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
