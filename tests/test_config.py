from pathlib import Path

import yaml

from py2femm.config.schema import Py2FemmConfig
from py2femm.config.loader import load_config, find_config_files


def test_default_config():
    cfg = Py2FemmConfig()
    assert cfg.agent_mode == "auto"
    assert cfg.agent_url == "http://localhost:8082"
    assert cfg.femm_timeout == 300
    assert cfg.cache_enabled is True


def test_config_from_dict():
    cfg = Py2FemmConfig.from_dict({
        "agent": {"mode": "remote", "url": "http://myhost:9090"},
        "femm": {"timeout": 600},
    })
    assert cfg.agent_mode == "remote"
    assert cfg.agent_url == "http://myhost:9090"
    assert cfg.femm_timeout == 600


def test_config_merge():
    base = Py2FemmConfig()
    override = {"agent": {"mode": "local"}}
    merged = base.merge(override)
    assert merged.agent_mode == "local"
    assert merged.agent_url == "http://localhost:8082"  # unchanged


def test_find_config_files_discovers_local(tmp_path):
    config_file = tmp_path / "py2femm.yml"
    config_file.write_text("agent:\n  mode: local\n")
    files = find_config_files(start_dir=tmp_path)
    assert config_file in files


def test_find_config_files_walks_up(tmp_path):
    config_file = tmp_path / "py2femm.yml"
    config_file.write_text("agent:\n  mode: local\n")
    subdir = tmp_path / "sub" / "deep"
    subdir.mkdir(parents=True)
    files = find_config_files(start_dir=subdir)
    assert config_file in files


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "py2femm.yml"
    config_file.write_text("agent:\n  mode: remote\n  url: http://10.0.0.1:8082\n")
    cfg = load_config(start_dir=tmp_path)
    assert cfg.agent_mode == "remote"
    assert cfg.agent_url == "http://10.0.0.1:8082"


def test_load_config_defaults_when_no_file(tmp_path):
    cfg = load_config(start_dir=tmp_path)
    assert cfg.agent_mode == "auto"
