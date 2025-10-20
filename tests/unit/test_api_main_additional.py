"""
Additional API tests to exercise more branches in `src.api.main`.

These tests focus on health/scheduler flags, successful auth login,
scheduler-backed job scheduling, weekly recurring schedule creation,
websocket ping/pong behavior, and a create-video path with a fake DB.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from types import SimpleNamespace
from pathlib import Path
import pytest

from src.api import main


client = TestClient(main.app)


def test_api_health_default_schedulers_none():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    sched = body["schedulers"]
    assert sched["content_scheduler"] is False
    assert sched["recurring_scheduler"] is False
    assert sched["calendar_manager"] is False


def test_api_health_with_schedulers(monkeypatch):
    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace())
    monkeypatch.setattr(main, "recurring_scheduler", SimpleNamespace())
    monkeypatch.setattr(main, "calendar_manager", SimpleNamespace())

    r = client.get("/api/health")
    assert r.status_code == 200
    sched = r.json()["schedulers"]
    assert sched["content_scheduler"] is True
    assert sched["recurring_scheduler"] is True
    assert sched["calendar_manager"] is True


def test_auth_login_success(monkeypatch):
    async def fake_auth(u, p):
        return True

    monkeypatch.setattr(main, "authenticate_user", fake_auth)
    monkeypatch.setattr(main, "create_access_token", lambda data, expires_delta=None: "tok")

    r = client.post("/api/auth/login", data={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] == "tok"
    assert body["token_type"] == "bearer"


def test_schedule_video_with_scheduler(monkeypatch):
    async def fake_schedule_video(*a, **k):
        return "job-123"

    monkeypatch.setattr(main, "content_scheduler", SimpleNamespace(schedule_video=fake_schedule_video))

    # Prevent broadcast_update from actually touching any global state
    async def fake_broadcast(msg):
        return None

    monkeypatch.setattr(main, "broadcast_update", fake_broadcast)

    async def fake_get_current_user():
        return "tester"

    main.app.dependency_overrides[main.get_current_user] = fake_get_current_user

    body = {"topic": "Hello", "scheduled_at": "2025-01-01T00:00:00", "style": "educational"}
    r = client.post("/api/jobs/schedule", json=body)
    assert r.status_code == 200
    assert r.json()["job_id"] == "job-123"

    # Clean up override
    main.app.dependency_overrides.pop(main.get_current_user, None)


def test_create_recurring_weekly_success(monkeypatch):
    async def fake_create_weekly(*a, **k):
        return "weekly-job"

    monkeypatch.setattr(main, "recurring_scheduler", SimpleNamespace(create_weekly_schedule=fake_create_weekly))

    body = {
        "name": "Weekly Test",
        "pattern": "weekly",
        "topic_template": "T",
        "days_of_week": ["mon", "tue"],
    }

    r = client.post("/api/recurring/create", json=body)
    assert r.status_code == 200
    assert r.json()["job_id"] == "weekly-job"


def test_websocket_ping_pong():
    with client.websocket_connect("/ws") as ws:
        ws.send_text("ping")
        msg = ws.receive_json()
        assert msg == {"type": "pong"}


def test_create_video_success(monkeypatch):
    # Fake DB session used by the get_db dependency
    class FakeDB:
        def add(self, obj):
            # Simulate DB assigning an id and default empty tags
            setattr(obj, "id", 999)
            # Some ORM models may leave list fields as None until flushed; tests
            # expect a sequence for `tags` so ensure it's present.
            if getattr(obj, "tags", None) is None:
                setattr(obj, "tags", [])

        def commit(self):
            return None

        def refresh(self, obj):
            return None

        def rollback(self):
            return None

    def fake_get_db():
        yield FakeDB()

    # Ensure get_user resolution returns a stable id
    import src.api.auth as auth_mod

    async def fake_get_user_id(username, db=None):
        return 1

    monkeypatch.setattr(auth_mod, "get_user_id_from_username", fake_get_user_id)

    # Override dependencies
    main.app.dependency_overrides[main.get_db] = fake_get_db

    async def fake_current_user():
        return "admin"

    main.app.dependency_overrides[main.get_current_user] = fake_current_user

    body = {"title": "Test Video", "niche": "education"}
    r = client.post("/api/videos", json=body)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Test Video"
    assert data["id"] == 999

    # Clean up dependency overrides
    main.app.dependency_overrides.pop(main.get_db, None)
    main.app.dependency_overrides.pop(main.get_current_user, None)
