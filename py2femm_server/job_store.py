"""In-memory job state store for the py2femm agent."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


class JobStore:
    """Thread-safe in-memory store for job state."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}

    def create(self, lua_script: str, timeout_s: int = 300, metadata: dict | None = None) -> str:
        """Create a new job, return its ID."""
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "lua_script": lua_script,
            "timeout_s": timeout_s,
            "metadata": metadata or {},
            "submitted_at": datetime.now(timezone.utc),
            "completed_at": None,
            "csv_data": None,
            "error": None,
        }
        return job_id

    def get(self, job_id: str) -> dict | None:
        """Get job by ID, or None."""
        return self._jobs.get(job_id)

    def update_status(self, job_id: str, status: str) -> None:
        """Update job status."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status

    def complete(self, job_id: str, csv_data: str) -> None:
        """Mark job as completed with results."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "completed"
            self._jobs[job_id]["csv_data"] = csv_data
            self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc)

    def fail(self, job_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "failed"
            self._jobs[job_id]["error"] = error
            self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc)

    def list_jobs(self, status: str | None = None) -> list[dict]:
        """List all jobs, optionally filtered by status."""
        jobs = list(self._jobs.values())
        if status is not None:
            jobs = [j for j in jobs if j["status"] == status]
        return jobs
