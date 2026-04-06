import json
from datetime import datetime, timezone

from py2femm.client.models import JobRequest, JobResult, JobStatus


def test_job_request_serialization():
    req = JobRequest(
        lua_script='hi_probdef("meters","planar")',
        timeout_s=300,
        metadata={"model": "extruded-fin"},
    )
    data = req.model_dump()
    assert data["lua_script"] == 'hi_probdef("meters","planar")'
    assert data["timeout_s"] == 300
    assert data["metadata"] == {"model": "extruded-fin"}


def test_job_request_defaults():
    req = JobRequest(lua_script="hi_analyze()")
    assert req.timeout_s == 300
    assert req.metadata == {}


def test_job_status_lifecycle():
    status = JobStatus(
        job_id="abc-123",
        status="completed",
        submitted_at=datetime(2026, 4, 5, 10, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 4, 5, 10, 0, 12, tzinfo=timezone.utc),
    )
    assert status.status == "completed"
    assert status.elapsed_s == 12.0


def test_job_status_queued_has_no_elapsed():
    status = JobStatus(
        job_id="abc-123",
        status="queued",
        submitted_at=datetime(2026, 4, 5, 10, 0, 0, tzinfo=timezone.utc),
    )
    assert status.elapsed_s is None


def test_job_result_with_csv():
    result = JobResult(
        csv_data="point,x,y,temperature_K\njunction,0,0,350.5\n",
    )
    df = result.to_dataframe()
    assert len(df) == 1
    assert df.iloc[0]["point"] == "junction"
    assert df.iloc[0]["temperature_K"] == 350.5


def test_job_result_empty_csv():
    result = JobResult(csv_data="")
    df = result.to_dataframe()
    assert len(df) == 0


def test_job_status_json_roundtrip():
    status = JobStatus(
        job_id="abc-123",
        status="completed",
        submitted_at=datetime(2026, 4, 5, 10, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 4, 5, 10, 0, 12, tzinfo=timezone.utc),
        result=JobResult(csv_data="point,x,y,temperature_K\n"),
    )
    json_str = status.model_dump_json()
    restored = JobStatus.model_validate_json(json_str)
    assert restored.job_id == "abc-123"
    assert restored.result.csv_data == "point,x,y,temperature_K\n"
