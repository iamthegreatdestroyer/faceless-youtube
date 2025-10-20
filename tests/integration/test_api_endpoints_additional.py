"""Additional API integration tests for main endpoints.

These tests exercise fallback behavior when scheduler/calendar subsystems
are not initialized (the common lightweight test environment). They
verify endpoints return safe defaults rather than 500 errors where
appropriate and ensure WebSocket ping/pong behavior works.
"""

from datetime import datetime, timedelta
from typing import Dict

# pytest is available via fixtures; imported here for markers if needed


def test_create_job_returns_id_and_status_when_no_scheduler(test_client):
    """POST /api/jobs should return a generated job id when scheduler is
    not initialized.
    """
    resp = test_client.post(
        "/api/jobs",
        json={"topic": "integration test job"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data, dict)
    assert "job_id" in data and data["status"] == "scheduled"


def test_schedule_video_returns_empty_list_when_no_scheduler(
    test_client, auth_headers: Dict[str, str]
):
    """Authenticated POST /api/jobs/schedule should return an empty list
    when content_scheduler is not available (safe fallback).
    """
    payload = {
        "topic": "Schedule Test",
        "scheduled_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        "duration_minutes": 5,
    }

    resp = test_client.post(
        "/api/jobs/schedule",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {}


def test_list_jobs_raises_500_when_scheduler_missing(test_client):
    """GET /api/jobs should return 500 if the scheduler subsystem is
    not initialized (explicit error case).
    """
    resp = test_client.get("/api/jobs")
    assert resp.status_code == 500


def test_get_statistics_returns_zeroed_payload_when_no_schedulers(test_client):
    """GET /api/statistics should return zeroed statistics when the
    schedulers and calendar manager are not initialized.
    """
    resp = test_client.get("/api/statistics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_jobs"] == 0
    assert data["active_jobs"] == 0
    assert data["completed_jobs"] == 0


def test_calendar_root_returns_empty_dict_when_missing(test_client):
    """GET /api/calendar should return an empty dict when the
    calendar manager is not available (smoke/sanity check).
    """
    resp = test_client.get("/api/calendar")
    assert resp.status_code == 200
    assert resp.json() == {}


def test_metrics_endpoint_returns_disabled_by_default(test_client):
    """/metrics fallback should return a JSON payload indicating metrics
    are disabled in the test environment.
    """
    resp = test_client.get("/metrics")
    assert resp.status_code == 200
    assert "metrics" in resp.json()


def test_websocket_ping_pong(test_client):
    """Basic websocket behavior: server should respond to a ping with a
    pong JSON payload while connected.
    """
    with test_client.websocket_connect("/ws") as ws:
        ws.send_text("ping")
        data = ws.receive_json()
        assert isinstance(data, dict)
        assert data.get("type") == "pong"
