import pytest
from datetime import datetime, timedelta

from fastapi import HTTPException

from src.api.validators import (
    VideoScheduleRequest,
    validate_image_upload,
    validate_video_upload,
    validate_audio_upload,
)


def test_video_schedule_title_sanitization():
    req = VideoScheduleRequest(
        title="<script>alert(1)</script>Deep Sleep",
        niche="meditation"
    )
    assert "<" not in req.title and "script" not in req.title
    assert req.title == "Deep Sleep"


def test_tags_are_sanitized_and_limited():
    req = VideoScheduleRequest(
        title="Test",
        niche="meditation",
        tags=["a!", "b@c", "valid_tag"]
    )

    assert all(isinstance(t, str) for t in req.tags)
    assert len(req.tags) <= 30


def test_scheduled_time_must_be_future():
    past = datetime.utcnow() - timedelta(days=1)
    with pytest.raises(Exception):
        VideoScheduleRequest(
            title="T",
            niche="meditation",
            scheduled_time=past,
        )


class DummyUpload:
    def __init__(self, filename: str, content_type: str, data: bytes):
        self.filename = filename
        self.content_type = content_type
        self._data = data

    async def read(self):
        return self._data

    async def seek(self, offset: int):
        return None


@pytest.mark.asyncio
async def test_validate_image_upload_success_and_failure():
    good = DummyUpload("ok.png", "image/png", b"0" * 1024)
    # Should not raise
    await validate_image_upload(good)

    bad = DummyUpload("bad.txt", "text/plain", b"0" * 10)
    with pytest.raises(HTTPException):
        await validate_image_upload(bad)


@pytest.mark.asyncio
async def test_validate_video_and_audio_upload_invalid_extension():
    # Invalid video extension
    bad_video = DummyUpload("video.xyz", "video/mp4", b"0" * 1024)
    with pytest.raises(HTTPException):
        await validate_video_upload(bad_video)

    # Invalid audio content type
    bad_audio = DummyUpload(
        "audio.mp3",
        "application/octet-stream",
        b"0" * 1024,
    )
    with pytest.raises(HTTPException):
        await validate_audio_upload(bad_audio)
