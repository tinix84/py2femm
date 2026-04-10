import time
from pathlib import Path
from threading import Thread
from unittest.mock import patch

from py2femm.client.base import FemmClientBase
from py2femm.client.local import LocalClient


def test_base_is_abstract():
    """FemmClientBase cannot be instantiated directly."""
    import pytest
    with pytest.raises(TypeError):
        FemmClientBase()


def test_local_client_writes_lua_to_workspace(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()
    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=5)

    def fake_femm():
        """Simulate FEMM: wait for .lua, write .csv result."""
        time.sleep(0.2)
        lua_files = list(workspace.glob("*.lua"))
        if lua_files:
            job_stem = lua_files[0].stem
            result_path = workspace / f"{job_stem}.csv"
            result_path.write_text("point,x,y,temperature_K\njunction,0,0,350\n")

    thread = Thread(target=fake_femm, daemon=True)
    thread.start()

    result = client.run("hi_analyze()")
    assert result.csv_data is not None
    assert "junction" in result.csv_data


def test_local_client_timeout(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()
    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=0.5)

    result = client.run("hi_analyze()")
    assert result.csv_data is None
    assert result.error is not None
    assert "timeout" in result.error.lower()


def test_local_client_atomic_write(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()
    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=5)

    # Start the run in background, just check that it writes .lua atomically
    from threading import Thread

    def do_run():
        client.run("hi_analyze()")

    t = Thread(target=do_run, daemon=True)
    t.start()
    time.sleep(0.2)

    # Should have a .lua file (not .tmp)
    lua_files = list(workspace.glob("*.lua"))
    tmp_files = list(workspace.glob("*.tmp"))
    assert len(lua_files) >= 1
    assert len(tmp_files) == 0  # .tmp already renamed
