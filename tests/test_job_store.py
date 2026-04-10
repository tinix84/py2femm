from datetime import datetime, timezone

from py2femm_agent.job_store import JobStore


def test_create_job():
    store = JobStore()
    job_id = store.create("hi_analyze()", timeout_s=300)
    assert isinstance(job_id, str)
    assert len(job_id) > 0


def test_get_job():
    store = JobStore()
    job_id = store.create("hi_analyze()")
    job = store.get(job_id)
    assert job["status"] == "queued"
    assert job["lua_script"] == "hi_analyze()"


def test_get_nonexistent_job():
    store = JobStore()
    assert store.get("nonexistent") is None


def test_update_status():
    store = JobStore()
    job_id = store.create("hi_analyze()")
    store.update_status(job_id, "running")
    job = store.get(job_id)
    assert job["status"] == "running"


def test_complete_job():
    store = JobStore()
    job_id = store.create("hi_analyze()")
    store.update_status(job_id, "running")
    store.complete(job_id, csv_data="point,x,y,T\n")
    job = store.get(job_id)
    assert job["status"] == "completed"
    assert job["csv_data"] == "point,x,y,T\n"
    assert job["completed_at"] is not None


def test_fail_job():
    store = JobStore()
    job_id = store.create("hi_analyze()")
    store.fail(job_id, error="FEMM crashed")
    job = store.get(job_id)
    assert job["status"] == "failed"
    assert job["error"] == "FEMM crashed"


def test_list_jobs():
    store = JobStore()
    id1 = store.create("script1")
    id2 = store.create("script2")
    jobs = store.list_jobs()
    assert len(jobs) == 2


def test_list_jobs_by_status():
    store = JobStore()
    id1 = store.create("script1")
    id2 = store.create("script2")
    store.update_status(id1, "running")
    running = store.list_jobs(status="running")
    assert len(running) == 1
    assert running[0]["job_id"] == id1
