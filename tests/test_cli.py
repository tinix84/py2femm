import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from py2femm.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "py2femm" in result.output.lower()


def test_cli_run_with_file(runner, tmp_path):
    lua_file = tmp_path / "test.lua"
    lua_file.write_text("hi_analyze()")

    mock_result = MagicMock()
    mock_result.csv_data = "point,x,y,T\njunction,0,0,350\n"
    mock_result.error = None

    with patch("py2femm.cli.FemmClient") as MockClient:
        MockClient.return_value.run.return_value = mock_result
        result = runner.invoke(main, ["run", str(lua_file)])

    assert result.exit_code == 0
    assert "junction" in result.output


def test_cli_run_missing_file(runner):
    result = runner.invoke(main, ["run", "/nonexistent/file.lua"])
    assert result.exit_code != 0


def test_cli_run_with_output(runner, tmp_path):
    lua_file = tmp_path / "test.lua"
    lua_file.write_text("hi_analyze()")
    output_file = tmp_path / "result.csv"

    mock_result = MagicMock()
    mock_result.csv_data = "point,x,y,T\njunction,0,0,350\n"
    mock_result.error = None

    with patch("py2femm.cli.FemmClient") as MockClient:
        MockClient.return_value.run.return_value = mock_result
        result = runner.invoke(main, ["run", str(lua_file), "--output", str(output_file)])

    assert result.exit_code == 0
    assert output_file.read_text() == "point,x,y,T\njunction,0,0,350\n"


def test_cli_status(runner):
    with patch("py2femm.cli.FemmClient") as MockClient:
        MockClient.return_value.status.return_value = {
            "mode": "remote",
            "status": "ok",
            "femm_path": "C:\\femm42\\bin\\femm.exe",
        }
        result = runner.invoke(main, ["status"])

    assert result.exit_code == 0
    assert "ok" in result.output
