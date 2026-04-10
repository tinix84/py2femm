import pytest
from unittest.mock import patch, MagicMock

from py2femm.client.remote import RemoteClient


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


def test_remote_client_submit_and_poll():
    client = RemoteClient(base_url="http://localhost:8082")
    submit_resp = _mock_response(202, {"job_id": "abc123", "status": "queued"})
    poll_resp_running = _mock_response(200, {"job_id": "abc123", "status": "running", "result": None, "error": None})
    poll_resp_done = _mock_response(200, {
        "job_id": "abc123",
        "status": "completed",
        "result": {"csv_data": "point,x,y,T\njunction,0,0,350\n"},
        "error": None,
    })

    with patch.object(client, "_client") as mock_http:
        mock_http.post.return_value = submit_resp
        mock_http.get.side_effect = [poll_resp_running, poll_resp_done]

        result = client.run("hi_analyze()", timeout=10)

    assert result.csv_data is not None
    assert "junction" in result.csv_data


def test_remote_client_status():
    client = RemoteClient(base_url="http://localhost:8082")
    health_resp = _mock_response(200, {"status": "ok", "femm_path": "C:\\femm42\\bin\\femm.exe"})

    with patch.object(client, "_client") as mock_http:
        mock_http.get.return_value = health_resp
        status = client.status()

    assert status["status"] == "ok"


def test_remote_client_handles_failed_job():
    client = RemoteClient(base_url="http://localhost:8082")
    submit_resp = _mock_response(202, {"job_id": "abc123", "status": "queued"})
    poll_resp = _mock_response(200, {
        "job_id": "abc123",
        "status": "failed",
        "result": None,
        "error": "FEMM crashed",
    })

    with patch.object(client, "_client") as mock_http:
        mock_http.post.return_value = submit_resp
        mock_http.get.return_value = poll_resp

        result = client.run("hi_analyze()")

    assert result.error == "FEMM crashed"
    assert result.csv_data is None
