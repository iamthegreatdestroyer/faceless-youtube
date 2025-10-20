"""
Focused tests for Video CRUD and Calendar endpoints in `src.api.main`.

These tests exercise not-found, auth, forbidden, invalid status, and
success paths for update/delete/get video endpoints and calendar date
parsing error branches.
"""
from __future__ import annotations

from datetime import datetime, date
from types import SimpleNamespace
from typing import Any, Dict
import pytest

from fastapi.testclient import TestClient

from src.api import main
from src.core.models import Video, User, VideoStatus


client = TestClient(main.app)


class FakeQuery:
    def __init__(self, result: Any):
        self._result = result

    def filter(self, *a, **k):
        return self

    def first(self):
        if isinstance(self._result, list):
            return self._result[0] if self._result else None
        return self._result

    def all(self):
        if isinstance(self._result, list):
            return self._result
        return [self._result] if self._result is not None else []

    def offset(self, n):
        return self

    def limit(self, n):
        return self


class FakeDB:
    def __init__(self, model_map: Dict[Any, Any]):
        # model_map: {ModelClass: result}
        self._map = model_map

    def query(self, model):
        return FakeQuery(self._map.get(model, None))

    def add(self, obj):
        setattr(obj, "id", getattr(obj, "id", 1))

    def commit(self):
        return None

    def refresh(self, obj):
        return None

    def rollback(self):
        return None

    def delete(self, obj):
        return None


def make_video(owner_id: int = 1) -> Video:
    v = Video(
        user_id=owner_id,
        title="T",
        duration_seconds=1,
        file_path="/tmp/v.mp4",
        niche="n",
        style="s",
        resolution="1080p",
        fps=30,
        aspect_ratio="16:9",
    )
    v.id = 1
    v.tags = []
    v.status = VideoStatus.QUEUED
    v.created_at = datetime.utcnow()
    v.updated_at = datetime.utcnow()
    return v


def make_user(id_: int = 1, username: str = "u1") -> User:
    u = User(username=username, email=f"{username}@test", password_hash="x")
    u.id = id_
    return u


def override_db(db: FakeDB):
    def _get_db():
        yield db

    main.app.dependency_overrides[main.get_db] = _get_db


def cleanup_db_override():
    main.app.dependency_overrides.pop(main.get_db, None)


def override_user(username: str):
    async def _cu():
        return username

    main.app.dependency_overrides[main.get_current_user] = _cu


def cleanup_user_override():
    main.app.dependency_overrides.pop(main.get_current_user, None)


def test_get_video_not_found():
    db = FakeDB({Video: None})
    override_db(db)

    # Protected endpoint; provide a fake authenticated user so the
    # route reaches the DB-not-found branch instead of returning 401.
    override_user("anon")
    try:
        r = client.get("/api/videos/123")
        assert r.status_code == 404
    finally:
        cleanup_db_override()
        cleanup_user_override()


def test_get_video_user_not_found():
    vid = make_video(owner_id=1)
    db = FakeDB({Video: vid, User: None})
    override_db(db)
    override_user("someone")

    r = client.get("/api/videos/1")
    assert r.status_code == 401

    cleanup_db_override()
    cleanup_user_override()


def test_get_video_forbidden():
    vid = make_video(owner_id=2)
    user = make_user(id_=1, username="u1")
    db = FakeDB({Video: vid, User: user})
    override_db(db)
    override_user("u1")

    r = client.get("/api/videos/1")
    assert r.status_code == 403

    cleanup_db_override()
    cleanup_user_override()


def test_update_video_invalid_status():
    vid = make_video(owner_id=1)
    user = make_user(id_=1, username="u1")
    db = FakeDB({Video: vid, User: user})
    override_db(db)
    override_user("u1")

    r = client.put("/api/videos/1", json={"status": "not-a-status"})
    assert r.status_code == 400

    cleanup_db_override()
    cleanup_user_override()


def test_update_video_success():
    vid = make_video(owner_id=1)
    user = make_user(id_=1, username="jdoe")
    db = FakeDB({Video: vid, User: user})
    override_db(db)
    override_user("jdoe")

    r = client.put("/api/videos/1", json={"title": "New Title"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "New Title"

    cleanup_db_override()
    cleanup_user_override()


def test_delete_video_not_found():
    db = FakeDB({Video: None})
    override_db(db)

    async def cu():
        return "u"

    main.app.dependency_overrides[main.get_current_user] = cu

    r = client.delete("/api/videos/1")
    assert r.status_code == 404

    cleanup_db_override()
    main.app.dependency_overrides.pop(main.get_current_user, None)


def test_delete_video_forbidden():
    vid = make_video(owner_id=2)
    user = make_user(id_=1, username="u1")
    db = FakeDB({Video: vid, User: user})
    override_db(db)
    override_user("u1")

    r = client.delete("/api/videos/1")
    assert r.status_code == 403

    cleanup_db_override()
    cleanup_user_override()


def test_delete_video_success():
    vid = make_video(owner_id=1)
    user = make_user(id_=1, username="owner")
    db = FakeDB({Video: vid, User: user})
    override_db(db)
    override_user("owner")

    r = client.delete("/api/videos/1")
    assert r.status_code == 204

    cleanup_db_override()
    cleanup_user_override()


def test_create_recurring_invalid_pattern_returns_400():
    # Ensure the recurring scheduler is present so the view validates the
    # pattern string (otherwise the handler returns 500 for missing scheduler).
    prev = main.recurring_scheduler
    main.recurring_scheduler = SimpleNamespace()
    try:
        body = {"name": "X", "pattern": "yearly", "topic_template": "T"}
        r = client.post("/api/recurring/create", json=body)
        assert r.status_code == 400
    finally:
        main.recurring_scheduler = prev


def test_calendar_day_week_invalid_date_returns_400():
    # Ensure calendar manager is present so the endpoints attempt to parse
    # the date string and raise a 400 on invalid format. Otherwise the
    # endpoints return 500 when calendar manager is not initialized.
    prev = main.calendar_manager
    main.calendar_manager = SimpleNamespace()
    try:
        r1 = client.get("/api/calendar/day/not-a-date")
        assert r1.status_code == 400

        r2 = client.get("/api/calendar/week/not-a-date")
        assert r2.status_code == 400
    finally:
        main.calendar_manager = prev


def test_list_videos_success(monkeypatch):
    # Return two videos for the current user
    v1 = make_video(owner_id=1)
    v2 = make_video(owner_id=1)
    v2.id = 2
    user = make_user(id_=1, username="viewer")
    db = FakeDB({Video: [v1, v2], User: user})
    override_db(db)
    override_user("viewer")

    async def fake_get_user_id(username, db=None):
        return 1

    monkeypatch.setattr("src.api.auth.get_user_id_from_username", fake_get_user_id)

    r = client.get("/api/videos")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2

    cleanup_db_override()
    cleanup_user_override()


def test_get_video_success():
    vid = make_video(owner_id=1)
    user = make_user(id_=1, username="owner")
    db = FakeDB({Video: vid, User: user})
    override_db(db)
    override_user("owner")

    r = client.get("/api/videos/1")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert data["title"] == vid.title

    cleanup_db_override()
    cleanup_user_override()


def test_calendar_day_week_and_suggestions_conflicts_success():
    # Fake day entry and slot
    class Slot:
        def __init__(self):
            self.id = "s1"
            self.scheduled_at = datetime.utcnow()
            self.topic = "T"
            self.status = SimpleNamespace(value="reserved")
            self.duration_minutes = 5

    class DayEntry:
        def __init__(self):
            self.date = date.today()
            self.total_slots = 1
            self.available_slots = 0
            self.scheduled_slots = 1
            self.slots = [Slot()]

    async def fake_get_day(target_date):
        return DayEntry()

    async def fake_get_week(start_date):
        return [DayEntry(), DayEntry()]

    async def fake_suggest(count, start_date, days):
        return [datetime.utcnow()]

    async def fake_conflicts():
        return [{"conflict": True}]

    prev = main.calendar_manager
    main.calendar_manager = SimpleNamespace(
        get_day_view=fake_get_day,
        get_week_view=fake_get_week,
        suggest_optimal_slots=fake_suggest,
        detect_conflicts=fake_conflicts,
        get_statistics=lambda: {},
    )

    try:
        rday = client.get(f"/api/calendar/day/{date.today().isoformat()}")
        assert rday.status_code == 200

        rweek = client.get(f"/api/calendar/week/{date.today().isoformat()}")
        assert rweek.status_code == 200

        rs = client.get("/api/calendar/suggestions")
        assert rs.status_code == 200
        assert "suggestions" in rs.json()

        rc = client.get("/api/calendar/conflicts")
        assert rc.status_code == 200
        assert "conflicts" in rc.json()
    finally:
        main.calendar_manager = prev
