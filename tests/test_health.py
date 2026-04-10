import os
from pathlib import Path
from unittest.mock import patch

from py2femm_agent.health import find_femm, check_femm_health


def test_find_femm_from_env_var(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    with patch.dict(os.environ, {"FEMM_PATH": str(femm_exe)}):
        result = find_femm()
    assert result == femm_exe


def test_find_femm_returns_none_when_not_found():
    with patch.dict(os.environ, {}, clear=True):
        with patch("py2femm_agent.health._FEMM_SEARCH_PATHS", []):
            result = find_femm()
    assert result is None


def test_find_femm_scans_common_paths(tmp_path):
    femm_dir = tmp_path / "femm42" / "bin"
    femm_dir.mkdir(parents=True)
    femm_exe = femm_dir / "femm.exe"
    femm_exe.touch()
    with patch.dict(os.environ, {}, clear=True):
        with patch("py2femm_agent.health._FEMM_SEARCH_PATHS", [femm_exe]):
            result = find_femm()
    assert result == femm_exe


def test_check_femm_health_ok(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    with patch("py2femm_agent.health.find_femm", return_value=femm_exe):
        health = check_femm_health()
    assert health["status"] == "ok"
    assert health["femm_path"] == str(femm_exe)


def test_check_femm_health_not_found():
    with patch("py2femm_agent.health.find_femm", return_value=None):
        health = check_femm_health()
    assert health["status"] == "error"
    assert "not found" in health["message"]
