"""FastAPI REST server for py2femm."""

from __future__ import annotations

from pathlib import Path
from threading import Thread

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from py2femm_server.executor import FemmExecutor
from py2femm_server.job_store import JobStore


class SubmitRequest(BaseModel):
    lua_script: str
    timeout_s: int = 300
    metadata: dict[str, str] = Field(default_factory=dict)


class BatchSubmitRequest(BaseModel):
    jobs: list[SubmitRequest]


def create_app(femm_path: Path, workspace: Path, headless: bool = True) -> FastAPI:
    """Create FastAPI app with configured executor and store."""
    app = FastAPI(title="py2femm Server", version="0.2.0")
    executor = FemmExecutor(femm_path=femm_path, workspace=workspace, headless=headless)
    store = JobStore()

    def _run_job(job_id: str) -> None:
        """Execute a job in a background thread."""
        job = store.get(job_id)
        if job is None:
            return
        store.update_status(job_id, "running")
        csv_data, returncode = executor.run(
            job["lua_script"], timeout=job["timeout_s"]
        )
        if returncode == 0 and csv_data is not None:
            store.complete(job_id, csv_data)
        else:
            error = "Timeout" if returncode == -1 else f"FEMM exited with code {returncode}"
            if csv_data is None and returncode == 0:
                error = "FEMM completed but no results.csv found"
            store.fail(job_id, error=error)

    @app.get("/api/v1/health")
    def health():
        return {
            "status": "ok",
            "femm_path": str(femm_path),
            "queue_depth": len(store.list_jobs(status="queued")),
            "running": len(store.list_jobs(status="running")),
        }

    @app.post("/api/v1/jobs", status_code=202)
    def submit_job(req: SubmitRequest):
        job_id = store.create(req.lua_script, req.timeout_s, req.metadata)
        Thread(target=_run_job, args=(job_id,), daemon=True).start()
        return {"job_id": job_id, "status": "queued"}

    @app.get("/api/v1/jobs/{job_id}")
    def get_job(job_id: str):
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "submitted_at": job["submitted_at"].isoformat(),
            "completed_at": job["completed_at"].isoformat() if job["completed_at"] else None,
            "result": {"csv_data": job["csv_data"]} if job["csv_data"] else None,
            "error": job["error"],
        }

    @app.delete("/api/v1/jobs/{job_id}")
    def cancel_job(job_id: str):
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job["status"] == "queued":
            store.fail(job_id, error="Cancelled by user")
            return {"status": "cancelled"}
        return {"status": job["status"], "message": "Cannot cancel non-queued job"}

    @app.post("/api/v1/jobs/batch", status_code=202)
    def submit_batch(req: BatchSubmitRequest):
        job_ids = []
        for job_req in req.jobs:
            job_id = store.create(job_req.lua_script, job_req.timeout_s, job_req.metadata)
            Thread(target=_run_job, args=(job_id,), daemon=True).start()
            job_ids.append(job_id)
        return {"job_ids": job_ids, "count": len(job_ids)}

    return app
