import time
from pathlib import Path
from unittest.mock import MagicMock

from py2femm_agent.watcher import FileWatcher


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
