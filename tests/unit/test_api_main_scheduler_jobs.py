"""
Tests that exercise scheduler-backed endpoints (jobs, recurring controls,
calendar and statistics) by providing fake scheduler/calendar manager
implementations. These tests aim to hit many branches in `src.api.main`.
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
import pytest

from fastapi.testclient import TestClient
from src.api import main


client = TestClient(main.app)


def make_job(id_: str = "j1"):
    return SimpleNamespace(
        id=id_,
        topic="T",
        status=SimpleNamespace(value="queued"),
        progress_percent=0.0,
        current_stage=None,
        scheduled_at=datetime.utcnow(),
        started_at=None,
        completed_at=None,
        script_path=None,
        video_path=None,
        youtube_url=None,
        error_message=None,
        retry_count=0,
    )


def test_create_and_list_jobs_with_scheduler(monkeypatch):
    async def fake_schedule_video(*a, **k):
        return "sched-1"

    def fake_get_all_jobs(*a, **k):
        return [make_job("sched-1")]

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(
        schedule_video=fake_schedule_video,
        get_all_jobs=fake_get_all_jobs,
    ))

    # Create job (this route is unprotected in create_job)
    r = client.post("/api/jobs", json={"topic": "x"})
    assert r.status_code == 201
    assert r.json()["status"] == "scheduled"

    # List jobs
    r2 = client.get("/api/jobs")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


def test_create_job_when_scheduler_raises_returns_500(monkeypatch):
    async def raise_err(*a, **k):
        raise RuntimeError("scheduler failed")

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(schedule_video=raise_err))

    # Replace broadcast_update with no-op to avoid side effects
    async def noop(msg):
        return None

    monkeypatch.setattr(main, "broadcast_update", noop)

    r = client.post("/api/jobs", json={"topic": "x"})
    assert r.status_code == 500


def test_list_recurring_returns_list_when_initialized(monkeypatch):
    job = SimpleNamespace(
        id="jid",
        name="J",
        schedule_rule=SimpleNamespace(pattern=SimpleNamespace(value="daily")),
        topic_template="T",
        enabled=True,
        last_run=None,
        next_run=None,
        run_count=0,
        failure_count=0,
    )

    monkeypatch.setattr(main, "recurring_scheduler", SimpleNamespace(get_all_jobs=lambda: [job]))

    r = client.get("/api/recurring")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_and_cancel_pause_resume_job(monkeypatch):
    job = make_job("j100")

    async def fake_get_job_status(jid):
        if jid == "j100":
            return job
        return None

    async def fake_cancel(jid):
        return None

    async def fake_pause(jid):
        return None

    async def fake_resume(jid):
        return None

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(
        get_job_status=fake_get_job_status,
        cancel_job=fake_cancel,
        pause_job=fake_pause,
        resume_job=fake_resume,
    ))

    # Get existing job
    r = client.get("/api/jobs/j100")
    assert r.status_code == 200

    # Cancel
    r2 = client.post("/api/jobs/j100/cancel")
    assert r2.status_code == 200

    # Pause
    r3 = client.post("/api/jobs/j100/pause")
    assert r3.status_code == 200

    # Resume
    r4 = client.post("/api/jobs/j100/resume")
    assert r4.status_code == 200


def test_recurring_pause_resume_delete(monkeypatch):
    async def fake_pause(jid):
        return None

    async def fake_resume(jid):
        return None

    async def fake_delete(jid):
        return None

    monkeypatch.setattr(main, "recurring_scheduler", SimpleNamespace(
        pause_job=fake_pause,
        resume_job=fake_resume,
        delete_job=fake_delete,
    ))

    r1 = client.post("/api/recurring/j1/pause")
    assert r1.status_code == 200

    r2 = client.post("/api/recurring/j1/resume")
    assert r2.status_code == 200

    r3 = client.delete("/api/recurring/j1")
    assert r3.status_code == 200


def test_calendar_reserve_and_statistics(monkeypatch):
    # Reserve slot
    async def fake_reserve(*a, **k):
        return SimpleNamespace(id="slot-1", status=SimpleNamespace(value="reserved"))

    # Statistics
    def fake_content_stats():
        return {"total_jobs": 5, "active_jobs": 1, "statistics": {"total_completed": 4, "total_failed": 0}}

    def fake_recurring_stats():
        return {"total_jobs": 2}

    def fake_calendar_stats():
        return {"total_slots": 10}

    monkeypatch.setattr(main, "calendar_manager", SimpleNamespace(reserve_slot=fake_reserve, get_statistics=fake_calendar_stats))
    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(get_statistics=fake_content_stats))
    monkeypatch.setattr(main, "recurring_scheduler", SimpleNamespace(get_statistics=fake_recurring_stats))

    body = {"scheduled_at": "2025-10-20T10:00:00", "topic": "X", "duration_minutes": 5}
    r = client.post("/api/calendar/slots", json=body)
    assert r.status_code == 200
    assert r.json()["slot_id"] == "slot-1"

    r2 = client.get("/api/statistics")
    assert r2.status_code == 200
    stats = r2.json()
    assert stats["total_jobs"] == 5
    assert stats["recurring_schedules"] == 2
    assert stats["calendar_slots"] == 10
