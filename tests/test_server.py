import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from py2femm_server.server import create_app


@pytest.fixture
def client(tmp_path):
    femm_exe = tmp_path / "femm.exe"
    femm_exe.touch()
    app = create_app(femm_path=femm_exe, workspace=tmp_path / "jobs")
    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "femm_path" in data


def test_submit_job(client):
    resp = client.post("/api/v1/jobs", json={
        "lua_script": "hi_analyze()",
        "timeout_s": 60,
    })
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_submit_job_missing_script(client):
    resp = client.post("/api/v1/jobs", json={})
    assert resp.status_code == 422


def test_get_job_status(client):
    # Submit first
    resp = client.post("/api/v1/jobs", json={"lua_script": "hi_analyze()"})
    job_id = resp.json()["job_id"]
    # Get status
    resp = client.get(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["job_id"] == job_id


def test_get_nonexistent_job(client):
    resp = client.get("/api/v1/jobs/nonexistent")
    assert resp.status_code == 404


def test_submit_batch(client):
    resp = client.post("/api/v1/jobs/batch", json={
        "jobs": [
            {"lua_script": "script1()"},
            {"lua_script": "script2()"},
        ]
    })
    assert resp.status_code == 202
    data = resp.json()
    assert len(data["job_ids"]) == 2
