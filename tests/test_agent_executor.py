from pathlib import Path

from py2femm_agent.executor import FemmExecutor, inject_preamble


def test_inject_preamble():
    lua = 'hi_probdef("meters","planar")\nhi_analyze()'
    workdir = Path("C:/femm_workspace/jobs/abc123")
    result = inject_preamble(lua, workdir)
    assert "py2femm_workdir" in result
    assert "py2femm_outfile" in result
    assert 'hi_probdef("meters","planar")' in result
    assert result.index("py2femm_workdir") < result.index("hi_probdef")


def test_inject_preamble_preserves_original():
    lua = "line1\nline2\nline3"
    workdir = Path("C:/jobs/test")
    result = inject_preamble(lua, workdir)
    assert "line1\nline2\nline3" in result


def test_inject_preamble_escapes_backslashes():
    workdir = Path("C:\\femm_workspace\\jobs\\abc123")
    result = inject_preamble("hi_analyze()", workdir)
    assert "\\\\" in result or "/" in result  # Lua-safe path separators


def test_executor_init_with_femm_path(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")
    assert executor.femm_path == femm_exe


def test_executor_init_creates_workspace(tmp_path):
    workspace = tmp_path / "jobs"
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=workspace)
    assert workspace.exists()


def test_executor_prepare_job_writes_lua(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")
    job_dir, lua_path = executor.prepare_job("hi_analyze()")
    assert lua_path.exists()
    content = lua_path.read_text()
    assert "py2femm_outfile" in content
    assert "hi_analyze()" in content


def test_executor_parse_result_csv(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")
    job_dir = tmp_path / "jobs" / "test-job"
    job_dir.mkdir(parents=True)
    result_csv = job_dir / "results.csv"
    result_csv.write_text("point,x,y,temperature_K\njunction,0,0,350.5\n")
    csv_data = executor.read_result(job_dir)
    assert "junction" in csv_data
    assert "350.5" in csv_data


def test_executor_read_result_missing_file(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    executor = FemmExecutor(femm_path=femm_exe, workspace=tmp_path / "jobs")
    job_dir = tmp_path / "jobs" / "no-result"
    job_dir.mkdir(parents=True)
    csv_data = executor.read_result(job_dir)
    assert csv_data is None
