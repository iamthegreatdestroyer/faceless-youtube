"""
Additional focused API tests to raise coverage for `src.api.main`.

Tests added:
- readiness positive (DB connected)
- schedule_video returns empty mapping when scheduler missing
- create_recurring_schedule for daily and monthly patterns
- list_recurring when scheduler initialized
- create_job returns generated id when scheduler missing
"""
from fastapi.testclient import TestClient
from types import SimpleNamespace

from src.api import main


client = TestClient(main.app)


def test_readiness_reports_db_connected(monkeypatch):
    class FakeSession:
        def execute(self, *a, **k):
            return None

        def close(self):
            return None

    import src.core.database as coredb

    monkeypatch.setattr(coredb, "SessionLocal", lambda: FakeSession())

    r = client.get("/ready")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ready"
    assert payload["database"] == "connected"


def test_schedule_video_returns_empty_when_scheduler_missing(monkeypatch):
    # Bypass authentication dependency via FastAPI dependency overrides
    async def fake_get_current_user():
        return "testuser"

    # Use dependency_overrides so FastAPI uses our fake during the request
    main.app.dependency_overrides[main.get_current_user] = fake_get_current_user

    body = {
        "topic": "Hello",
        "scheduled_at": "2025-01-01T00:00:00",
        "style": "educational",
    }

    r = client.post("/api/jobs/schedule", json=body)
    assert r.status_code == 200
    assert r.json() == {}

    # Clean up override to avoid affecting other tests
    main.app.dependency_overrides.pop(main.get_current_user, None)


def test_create_recurring_daily_and_monthly(monkeypatch):
    async def fake_create_daily(*a, **k):
        return "daily-job-id"

    async def fake_create_monthly(*a, **k):
        return "monthly-job-id"

    monkeypatch.setattr(
        main,
        "recurring_scheduler",
        SimpleNamespace(
            create_daily_schedule=fake_create_daily,
            create_monthly_schedule=fake_create_monthly,
        ),
    )

    daily_body = {
        "name": "Daily Test",
        "pattern": "daily",
        "topic_template": "T",
    }

    r1 = client.post("/api/recurring/create", json=daily_body)
    assert r1.status_code == 200
    assert r1.json()["job_id"] == "daily-job-id"

    monthly_body = {
        "name": "Monthly Test",
        "pattern": "monthly",
        "topic_template": "M",
        "days_of_month": [1, 15],
    }

    r2 = client.post("/api/recurring/create", json=monthly_body)
    assert r2.status_code == 200
    assert r2.json()["job_id"] == "monthly-job-id"


def test_list_recurring_when_initialized(monkeypatch):
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
    data = r.json()
    assert isinstance(data, list)
    assert data[0]["id"] == "jid"


def test_create_job_returns_generated_id_when_no_scheduler():
    r = client.post("/api/jobs", json={"topic": "x"})
    # create_job returns 201 Created on success
    assert r.status_code == 201
    assert "job_id" in r.json()
    assert r.json()["status"] == "scheduled"
