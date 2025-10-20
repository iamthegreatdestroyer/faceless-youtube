"""
Focused API tests to cover additional branches in `src.api.main`.

Tests included:
- create_recurring_schedule: weekly missing days should return 400 (preserve HTTPException)
- list_jobs: ensure status filter is passed to scheduler as JobStatus
- job management endpoints (cancel/pause/resume): ValueError -> 404, generic error -> 500
- get_job: not found -> 404
- create_job: invalid scheduled_at falls back to datetime and still succeeds
- schedule_video: broadcasts should include the requested topic
"""
from __future__ import annotations

from datetime import datetime as dt
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from src.api import main


client = TestClient(main.app)


def test_create_recurring_weekly_missing_days_returns_400():
    # Ensure a recurring_scheduler is present so validation runs
    prev = main.recurring_scheduler
    main.recurring_scheduler = SimpleNamespace()
    try:
        body = {"name": "Weekly Test", "pattern": "weekly", "topic_template": "T"}
        r = client.post("/api/recurring/create", json=body)
        assert r.status_code == 400
        assert "days_of_week required" in r.json().get("detail", "")
    finally:
        main.recurring_scheduler = prev


def test_list_jobs_with_status_filter(monkeypatch):
    called = {}

    job = SimpleNamespace(
        id="j-filter",
        topic="T",
        status=SimpleNamespace(value="scheduled"),
        progress_percent=0.0,
        current_stage=None,
        scheduled_at=dt.utcnow(),
        started_at=None,
        completed_at=None,
        script_path=None,
        video_path=None,
        youtube_url=None,
        error_message=None,
        retry_count=0,
    )

    def fake_get_all_jobs(status_filter=None):
        called["status_filter"] = status_filter
        return [job]

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(get_all_jobs=fake_get_all_jobs))

    r = client.get("/api/jobs?status=scheduled")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    # Ensure the route parsed the status and passed a JobStatus-like object
    assert "status_filter" in called and called["status_filter"] is not None
    assert getattr(called["status_filter"], "value", None) == "scheduled"


def test_cancel_pause_resume_return_404_on_value_error(monkeypatch):
    async def raise_not_found(*a, **k):
        raise ValueError("not found")

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(
        cancel_job=raise_not_found,
        pause_job=raise_not_found,
        resume_job=raise_not_found,
    ))

    r1 = client.post("/api/jobs/does-not-exist/cancel")
    assert r1.status_code == 404

    r2 = client.post("/api/jobs/does-not-exist/pause")
    assert r2.status_code == 404

    r3 = client.post("/api/jobs/does-not-exist/resume")
    assert r3.status_code == 404


def test_cancel_pause_resume_return_500_on_generic_error(monkeypatch):
    async def raise_err(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(
        cancel_job=raise_err,
        pause_job=raise_err,
        resume_job=raise_err,
    ))

    r1 = client.post("/api/jobs/x/cancel")
    assert r1.status_code == 500

    r2 = client.post("/api/jobs/x/pause")
    assert r2.status_code == 500

    r3 = client.post("/api/jobs/x/resume")
    assert r3.status_code == 500


def test_get_job_not_found_returns_404(monkeypatch):
    async def fake_get_job_status(jid):
        return None

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(get_job_status=fake_get_job_status))

    r = client.get("/api/jobs/missing-job")
    assert r.status_code == 404


def test_create_job_invalid_scheduled_at_falls_back_to_datetime(monkeypatch):
    called = {}

    async def fake_schedule_video(topic=None, scheduled_at=None, style=None, duration_minutes=None, tags=None):
        called["scheduled_at_type"] = type(scheduled_at)
        return "job-fallback"

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(schedule_video=fake_schedule_video))

    r = client.post("/api/jobs", json={"topic": "x", "scheduled_at": "not-a-datetime"})
    assert r.status_code == 201
    assert r.json()["job_id"] == "job-fallback"
    # The scheduled_at passed to scheduler should be a datetime instance
    assert called.get("scheduled_at_type") is dt


def test_schedule_video_broadcasts_topic(monkeypatch):
    captured = {}

    async def fake_schedule_video(*a, **k):
        return "job-xyz"

    async def fake_broadcast(msg):
        captured["msg"] = msg

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(schedule_video=fake_schedule_video))
    monkeypatch.setattr(main, "broadcast_update", fake_broadcast)

    async def fake_get_current_user():
        return "tester"

    main.app.dependency_overrides[main.get_current_user] = fake_get_current_user

    try:
        body = {"topic": "Broadcast Topic", "scheduled_at": "2025-01-01T00:00:00", "style": "educational"}
        r = client.post("/api/jobs/schedule", json=body)
        assert r.status_code == 200
        assert r.json()["job_id"] == "job-xyz"
        assert captured.get("msg") and captured["msg"].get("topic") == body["topic"]
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)


def test_metrics_fallback_disabled_and_enabled():
    # Default disabled
    prev = main.METRICS_ENABLED
    try:
        main.METRICS_ENABLED = False
        r = client.get("/metrics")
        assert r.status_code == 200
        assert r.json() == {"metrics": "disabled"}

        # When metrics enabled the fallback returns enabled payload
        main.METRICS_ENABLED = True
        r2 = client.get("/metrics")
        assert r2.status_code == 200
        assert r2.json() == {"metrics": "enabled"}
    finally:
        main.METRICS_ENABLED = prev


def test_auth_login_and_alias_failure_cases(monkeypatch):
    # Login with invalid credentials should return 401
    async def fake_auth_fail(u, p):
        return False

    monkeypatch.setattr(main, "authenticate_user", fake_auth_fail)

    r = client.post("/api/auth/login", data={"username": "u", "password": "bad"}, headers={"X-Forwarded-For": "10.0.0.1"})
    assert r.status_code == 401

    # Alias requires either email or username; missing both returns 400
    r2 = client.post("/auth/login", data={"password": "x"}, headers={"X-Forwarded-For": "10.0.0.2"})
    assert r2.status_code == 400

    # Alias with credentials that fail should also return 401
    r3 = client.post("/auth/login", data={"username": "u", "password": "bad"}, headers={"X-Forwarded-For": "10.0.0.3"})
    assert r3.status_code == 401


def test_websocket_initial_stats_sent(monkeypatch):
    # Provide small synchronous get_statistics so websocket initial send
    # doesn't try to await the async route function.
    from src.api.main import StatisticsResponse

    def fake_get_statistics():
        return StatisticsResponse(
            total_jobs=1,
            active_jobs=0,
            completed_jobs=0,
            failed_jobs=0,
            recurring_schedules=0,
            calendar_slots=0,
        )

    prev_cs = main.content_scheduler
    prev_rs = main.recurring_scheduler
    prev_cm = main.calendar_manager
    prev_get_stats = main.get_statistics

    try:
        # Make scheduler subsystems present so websocket will call get_statistics
        main.content_scheduler = SimpleNamespace()
        main.recurring_scheduler = SimpleNamespace()
        main.calendar_manager = SimpleNamespace()
        monkeypatch.setattr(main, "get_statistics", fake_get_statistics)

        with client.websocket_connect("/ws") as ws:
            # The server should send an initial_stats message on connect
            msg = ws.receive_json()
            assert msg["type"] == "initial_stats"
            assert "data" in msg

            # Ensure ping/pong still works afterwards
            ws.send_text("ping")
            pong = ws.receive_json()
            assert pong == {"type": "pong"}
    finally:
        main.content_scheduler = prev_cs
        main.recurring_scheduler = prev_rs
        main.calendar_manager = prev_cm
        monkeypatch.setattr(main, "get_statistics", prev_get_stats)


@pytest.mark.asyncio
async def test_startup_initializes_schedulers(monkeypatch):
    """Call startup_event with fake scheduler classes to exercise
    the initialization branch that creates and starts schedulers.
    """
    # Simple fake classes that emulate the real schedulers but are
    # lightweight and deterministic for testing.
    class FakeScheduleConfig:
        def __init__(self, **_):
            pass

    class FakeContentScheduler:
        def __init__(self, config=None):
            self.config = config
            self.loaded = False
            self.started = False

        async def load_jobs(self):
            self.loaded = True

        async def start(self):
            self.started = True

        async def stop(self):
            self.started = False

        def get_statistics(self):
            return {"total_jobs": 0, "active_jobs": 0, "statistics": {"total_completed": 0, "total_failed": 0}, "running": False}

    class FakeRecurringScheduler:
        def __init__(self, content_scheduler=None, config=None):
            self.started = False

        async def start(self):
            self.started = True

        async def stop(self):
            self.started = False

    class FakeRecurringConfig:
        pass

    class FakeCalendarManager:
        def __init__(self, config=None):
            self.config = config

    # Preserve existing objects so test can restore them
    prev_cs_class = main.ContentScheduler
    prev_sc = main.ScheduleConfig
    prev_rs_class = main.RecurringScheduler
    prev_rc = main.RecurringConfig
    prev_cm_class = main.CalendarManager
    prev_cc = main.CalendarConfig
    prev_cs = main.content_scheduler
    prev_rs = main.recurring_scheduler
    prev_cm = main.calendar_manager

    try:
        # Patch the module-level scheduler classes to our fakes
        monkeypatch.setattr(main, "ContentScheduler", FakeContentScheduler)
        monkeypatch.setattr(main, "ScheduleConfig", FakeScheduleConfig)
        monkeypatch.setattr(main, "RecurringScheduler", FakeRecurringScheduler)
        monkeypatch.setattr(main, "RecurringConfig", FakeRecurringConfig)
        monkeypatch.setattr(main, "CalendarManager", FakeCalendarManager)
        monkeypatch.setattr(main, "CalendarConfig", lambda: object())

        # Ensure globals are cleared before startup
        main.content_scheduler = None
        main.recurring_scheduler = None
        main.calendar_manager = None

        # Call the startup event directly
        await main.startup_event()

        # Verify instances were created and started/loaded
        assert isinstance(main.content_scheduler, FakeContentScheduler)
        assert main.content_scheduler.loaded is True
        assert main.content_scheduler.started is True
        assert isinstance(main.recurring_scheduler, FakeRecurringScheduler)
        assert main.recurring_scheduler.started is True
        assert isinstance(main.calendar_manager, FakeCalendarManager)

    finally:
        # Restore previous module-level objects
        monkeypatch.setattr(main, "ContentScheduler", prev_cs_class)
        monkeypatch.setattr(main, "ScheduleConfig", prev_sc)
        monkeypatch.setattr(main, "RecurringScheduler", prev_rs_class)
        monkeypatch.setattr(main, "RecurringConfig", prev_rc)
        monkeypatch.setattr(main, "CalendarManager", prev_cm_class)
        monkeypatch.setattr(main, "CalendarConfig", prev_cc)
        main.content_scheduler = prev_cs
        main.recurring_scheduler = prev_rs
        main.calendar_manager = prev_cm


@pytest.mark.asyncio
async def test_broadcast_update_cleans_disconnected_and_keeps_connected():
    # Preserve state
    prev = list(main.active_websockets)

    class BadWS:
        async def send_json(self, msg):
            raise RuntimeError("send failed")

    class GoodWS:
        def __init__(self, collector):
            self.collector = collector

        async def send_json(self, msg):
            self.collector.append(msg)

    try:
        # Case 1: disconnected WS is removed
        main.active_websockets.clear()
        main.active_websockets.append(BadWS())
        await main.broadcast_update({"t": 1})
        assert main.active_websockets == []

        # Case 2: connected WS stays and receives message
        collector = []
        ws = GoodWS(collector)
        main.active_websockets.clear()
        main.active_websockets.append(ws)

        await main.broadcast_update({"hello": "world"})
        assert len(main.active_websockets) == 1
        assert collector and collector[0]["hello"] == "world"

    finally:
        main.active_websockets.clear()
        main.active_websockets.extend(prev)


def test_recurring_pause_resume_delete_error_paths(monkeypatch):
    prev = main.recurring_scheduler

    async def raise_not_found(*a, **k):
        raise ValueError("missing")

    async def raise_err(*a, **k):
        raise RuntimeError("boom")

    try:
        # ValueError -> 404
        main.recurring_scheduler = SimpleNamespace(
            pause_job=raise_not_found,
            resume_job=raise_not_found,
            delete_job=raise_not_found,
        )

        r1 = client.post("/api/recurring/x/pause")
        assert r1.status_code == 404

        r2 = client.post("/api/recurring/x/resume")
        assert r2.status_code == 404

        r3 = client.delete("/api/recurring/x")
        assert r3.status_code == 404

        # Generic error -> 500
        main.recurring_scheduler = SimpleNamespace(
            pause_job=raise_err,
            resume_job=raise_err,
            delete_job=raise_err,
        )

        r4 = client.post("/api/recurring/x/pause")
        assert r4.status_code == 500

        r5 = client.post("/api/recurring/x/resume")
        assert r5.status_code == 500

        r6 = client.delete("/api/recurring/x")
        assert r6.status_code == 500

    finally:
        main.recurring_scheduler = prev


def test_create_video_user_lookup_failure_returns_500(monkeypatch):
    # Fake DB used by get_db dependency
    class FakeDB:
        def add(self, obj):
            setattr(obj, "id", 1001)

        def commit(self):
            return None

        def refresh(self, obj):
            return None

        def rollback(self):
            return None

    def fake_get_db():
        yield FakeDB()

    main.app.dependency_overrides[main.get_db] = fake_get_db
    async def fake_current_user():
        return "admin"

    main.app.dependency_overrides[main.get_current_user] = fake_current_user

    # Make user lookup raise
    async def raise_lookup(u, db=None):
        raise RuntimeError("lookup failed")

    monkeypatch.setattr("src.api.auth.get_user_id_from_username", raise_lookup)

    try:
        r = client.post("/api/videos", json={"title": "X", "niche": "n"})
        assert r.status_code == 500
    finally:
        main.app.dependency_overrides.pop(main.get_db, None)
        main.app.dependency_overrides.pop(main.get_current_user, None)


def test_get_statistics_defaults_to_zeros():
    # Ensure scheduler subsystems are cleared so route returns zeroed stats
    prev_cs = main.content_scheduler
    prev_rs = main.recurring_scheduler
    prev_cm = main.calendar_manager

    try:
        main.content_scheduler = None
        main.recurring_scheduler = None
        main.calendar_manager = None

        r = client.get("/api/statistics")
        assert r.status_code == 200
        data = r.json()
        assert data["total_jobs"] == 0
        assert data["recurring_schedules"] == 0
        assert data["calendar_slots"] == 0
    finally:
        main.content_scheduler = prev_cs
        main.recurring_scheduler = prev_rs
        main.calendar_manager = prev_cm


def test_login_alias_accepts_email_success(monkeypatch):
    async def fake_auth_ok(u, p):
        return True

    monkeypatch.setattr(main, "authenticate_user", fake_auth_ok)
    monkeypatch.setattr(main, "create_access_token", lambda data, expires_delta=None: "tok-email")

    r = client.post("/auth/login", data={"email": "me@test", "password": "x"}, headers={"X-Forwarded-For": "10.0.0.4"})
    assert r.status_code == 200
    assert r.json()["access_token"] == "tok-email"


def test_update_video_user_not_found_returns_401():
    # Fake DB returns a video but no user record
    from src.core.models import Video

    class FakeDB:
        def query(self, model):
            if model == Video:
                v = Video(user_id=1, title="T", duration_seconds=1, file_path="/tmp/v", niche="n", style="s", resolution="1080p", fps=30, aspect_ratio="16:9")
                v.id = 1
                v.tags = []
                return SimpleNamespace(filter=lambda *a, **k: SimpleNamespace(first=lambda: v))
            return SimpleNamespace(filter=lambda *a, **k: SimpleNamespace(first=lambda: None))

    def fake_get_db():
        yield FakeDB()

    main.app.dependency_overrides[main.get_db] = fake_get_db

    async def fake_current_user():
        return "no-such-user"

    main.app.dependency_overrides[main.get_current_user] = fake_current_user

    try:
        r = client.put("/api/videos/1", json={"title": "X"})
        assert r.status_code == 401
    finally:
        main.app.dependency_overrides.pop(main.get_db, None)
        main.app.dependency_overrides.pop(main.get_current_user, None)


def test_start_monitoring_creates_background_task(monkeypatch):
    created = {}

    def fake_create_task(coro):
        # Capture that a coroutine was scheduled
        created["coro"] = coro
        class Dummy:
            pass
        return Dummy()

    monkeypatch.setattr("asyncio.create_task", fake_create_task)

    # Call the startup hook that schedules the monitor task
    import asyncio as _asyncio

    # Call the coroutine directly (it does not await monitor_jobs)
    _asyncio.get_event_loop().run_until_complete(main.start_monitoring())

    assert "coro" in created


def test_get_job_includes_current_stage_value(monkeypatch):
    from datetime import datetime

    job = SimpleNamespace(
        id="j-stage",
        topic="T",
        status=SimpleNamespace(value="generating_script"),
        progress_percent=10.0,
        current_stage=SimpleNamespace(value="script_generation"),
        scheduled_at=datetime.utcnow(),
        started_at=None,
        completed_at=None,
        script_path=None,
        video_path=None,
        youtube_url=None,
        error_message=None,
        retry_count=0,
    )

    async def fake_get_job_status(jid):
        return job

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(get_job_status=fake_get_job_status))

    r = client.get("/api/jobs/j-stage")
    assert r.status_code == 200
    assert r.json().get("current_stage") == "script_generation"
