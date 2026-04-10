import os
from pathlib import Path
from unittest.mock import patch

from py2femm.client.auto import FemmClient


def test_auto_detects_local_when_mnt_c_exists(tmp_path):
    workspace = tmp_path / "mnt" / "c" / "femm_workspace"
    workspace.mkdir(parents=True)
    with patch("py2femm.client.auto._DEFAULT_LOCAL_WORKSPACE", workspace):
        with patch("py2femm.client.auto._LOCAL_MARKER", workspace.parent):
            client = FemmClient()
    assert client._mode == "local"


def test_auto_detects_remote_from_env():
    with patch("py2femm.client.auto._LOCAL_MARKER", Path("/nonexistent")):
        with patch.dict(os.environ, {"PYFEMM_AGENT_URL": "http://192.168.1.10:8082"}):
            client = FemmClient()
    assert client._mode == "remote"
    assert client._remote_url == "http://192.168.1.10:8082"


def test_auto_raises_when_nothing_found():
    import pytest
    with patch("py2femm.client.auto._LOCAL_MARKER", Path("/nonexistent")):
        with patch.dict(os.environ, {}, clear=True):
            with patch("py2femm.client.auto._load_config_url", return_value=None):
                with pytest.raises(ConnectionError, match="(?i)setup instructions"):
                    FemmClient()


def test_explicit_mode_local(tmp_path):
    client = FemmClient(mode="local", workspace=tmp_path)
    assert client._mode == "local"


def test_explicit_mode_remote():
    client = FemmClient(mode="remote", url="http://myhost:8082")
    assert client._mode == "remote"
