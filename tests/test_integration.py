"""Integration test: full round-trip without real FEMM.

Simulates the server-side by watching for .lua files and writing
fake .csv results. Tests the client -> filesystem -> server -> result
pipeline end-to-end.
"""

import time
from pathlib import Path
from threading import Thread

from py2femm.client.local import LocalClient


def _fake_femm_server(workspace: Path, stop_after: int = 1):
    """Watch for .lua files and write fake CSV results."""
    processed = 0
    for _ in range(50):  # max 5 seconds
        for lua_file in workspace.glob("*.lua"):
            csv_name = lua_file.stem + ".csv"
            csv_path = workspace / csv_name
            if not csv_path.exists():
                csv_path.write_text(
                    "point,x,y,temperature_K\n"
                    "base_center,0.025,0,355.2\n"
                    "fin_tip,0.025,0.03,310.8\n"
                )
                processed += 1
                if processed >= stop_after:
                    return
        time.sleep(0.1)


def test_full_roundtrip(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()

    # Start fake agent in background
    server_thread = Thread(target=_fake_femm_server, args=(workspace,), daemon=True)
    server_thread.start()

    # Run client
    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=10)
    result = client.run("hi_analyze()")

    assert result.csv_data is not None
    assert "base_center" in result.csv_data
    assert "355.2" in result.csv_data
    assert result.error is None
    assert result.elapsed_s > 0


def test_full_roundtrip_csv_to_dataframe(tmp_path):
    workspace = tmp_path / "femm_workspace"
    workspace.mkdir()

    server_thread = Thread(target=_fake_femm_server, args=(workspace,), daemon=True)
    server_thread.start()

    client = LocalClient(workspace=workspace, poll_interval=0.1, timeout=10)
    result = client.run("hi_analyze()")

    from py2femm.client.models import JobResult

    job_result = JobResult(csv_data=result.csv_data)
    df = job_result.to_dataframe()
    assert len(df) == 2
    assert set(df.columns) == {"point", "x", "y", "temperature_K"}
    assert df.iloc[0]["temperature_K"] == 355.2
