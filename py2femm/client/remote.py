"""REST API client for remote py2femm agent."""

from __future__ import annotations

import time

import httpx

from py2femm.client.base import ClientResult, FemmClientBase


class RemoteClient(FemmClientBase):
    """Client that communicates with py2femm agent via REST API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8082",
        poll_interval: float = 2.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval
        self._client = httpx.Client(base_url=self.base_url, timeout=30)

    def run(self, lua_script: str, timeout: int = 300) -> ClientResult:
        """Submit Lua script via REST API, poll until complete."""
        start = time.monotonic()

        # Submit
        resp = self._client.post(
            "/api/v1/jobs",
            json={"lua_script": lua_script, "timeout_s": timeout},
        )
        resp.raise_for_status()
        job_id = resp.json()["job_id"]

        # Poll
        while time.monotonic() - start < timeout:
            resp = self._client.get(f"/api/v1/jobs/{job_id}")
            resp.raise_for_status()
            data = resp.json()

            if data["status"] == "completed":
                elapsed = time.monotonic() - start
                csv_data = data.get("result", {}).get("csv_data") if data.get("result") else None
                return ClientResult(csv_data=csv_data, elapsed_s=elapsed)

            if data["status"] == "failed":
                elapsed = time.monotonic() - start
                return ClientResult(error=data.get("error", "Unknown error"), elapsed_s=elapsed)

            time.sleep(self.poll_interval)

        elapsed = time.monotonic() - start
        return ClientResult(error=f"Timeout after {elapsed:.1f}s", elapsed_s=elapsed)

    def status(self) -> dict:
        """Get agent health status."""
        resp = self._client.get("/api/v1/health")
        resp.raise_for_status()
        return resp.json()
