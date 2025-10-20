"""
Additional tests for VideoUploader behaviors:
- upload_thumbnail missing file and successful upload
- _upload_captions skips missing files and uploads existing ones
- get_video_status raises when not found and returns mapping when found
- wait_for_processing returns True/False for succeeded/failed flows
"""
from __future__ import annotations

from pathlib import Path
import asyncio
import pytest

from src.services.youtube_uploader.uploader import (
    VideoUploader,
    VideoMetadata,
    UploadResult,
    UploadStatus,
    PrivacyStatus,
)


class FakeAuth:
    async def get_youtube_client(self, account_name: str):
        return self.fake_youtube


class FakeReq:
    def __init__(self, response=None, executed_counter: dict | None = None):
        self._response = response
        self._executed_counter = executed_counter

    def execute(self):
        if self._executed_counter is not None:
            self._executed_counter["count"] += 1
        return self._response


def make_fake_youtube_for_thumbnail(executed_counter: dict):
    class FY:
        def thumbnails(self):
            class T:
                def set(self, videoId=None, media_body=None):
                    return FakeReq(response={"status": "ok"}, executed_counter=executed_counter)
            return T()

    return FY()


def make_fake_youtube_for_captions(executed_counter: dict):
    class FY:
        def captions(self):
            class C:
                def insert(self, part=None, body=None, media_body=None):
                    return FakeReq(response={"id": "cap"}, executed_counter=executed_counter)
            return C()

    return FY()


def make_fake_youtube_for_videos(response_items):
    class FY:
        def videos(self):
            class V:
                def list(self, part=None, id=None):
                    return FakeReq(response={"items": response_items})
            return V()
    return FY()


@pytest.mark.asyncio
async def test_upload_thumbnail_file_not_found():
    auth = FakeAuth()
    uploader = VideoUploader(auth_manager=auth)

    with pytest.raises(FileNotFoundError):
        await uploader.upload_thumbnail("acct", "VID", "no-such-file.jpg")


@pytest.mark.asyncio
async def test_upload_thumbnail_success(tmp_path: Path):
    # Create thumbnail
    tp = tmp_path / "t.jpg"
    tp.write_bytes(b"thumb")

    auth = FakeAuth()
    executed = {"count": 0}
    auth.fake_youtube = make_fake_youtube_for_thumbnail(executed)

    uploader = VideoUploader(auth_manager=auth)
    url = await uploader.upload_thumbnail("acct", "VID123", str(tp))
    assert url.endswith("VID123/maxresdefault.jpg")
    assert executed["count"] == 1


@pytest.mark.asyncio
async def test_upload_captions_skips_missing_and_uploads_existing(tmp_path: Path):
    # Create one caption file and one missing
    existing = tmp_path / "c1.srt"
    existing.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello")

    captions = [
        {"file": str(tmp_path / "missing.srt"), "language": "en"},
        {"file": str(existing), "language": "en"},
    ]

    executed = {"count": 0}
    auth = FakeAuth()
    auth.fake_youtube = make_fake_youtube_for_captions(executed)

    uploader = VideoUploader(auth_manager=auth)

    # Should not raise and should have executed exactly once for the existing file
    await uploader._upload_captions(auth.fake_youtube, "VIDX", captions)
    assert executed["count"] == 1


@pytest.mark.asyncio
async def test_get_video_status_video_not_found_raises():
    auth = FakeAuth()
    auth.fake_youtube = make_fake_youtube_for_videos([])
    uploader = VideoUploader(auth_manager=auth)

    with pytest.raises(ValueError):
        await uploader.get_video_status("acct", "noid")


@pytest.mark.asyncio
async def test_get_video_status_returns_expected_mapping():
    # Provide a response item with expected structure
    item = {
        "status": {
            "uploadStatus": "uploaded",
            "privacyStatus": "private",
            "license": "youtube",
            "embeddable": True,
            "publicStatsViewable": True,
        },
        "processingDetails": {"processingStatus": "succeeded", "processingProgress": 100}
    }

    auth = FakeAuth()
    auth.fake_youtube = make_fake_youtube_for_videos([item])
    uploader = VideoUploader(auth_manager=auth)

    res = await uploader.get_video_status("acct", "VID")
    assert res["upload_status"] == "uploaded"
    assert res["processing_status"] == "succeeded"


@pytest.mark.asyncio
async def test_wait_for_processing_success_and_failure(monkeypatch):
    auth = FakeAuth()
    uploader = VideoUploader(auth_manager=auth)

    async def one_shot_success(self, account_name, video_id):
        return {"processing_status": "succeeded"}

    async def immediate_failure(self, account_name, video_id):
        return {"processing_status": "failed"}

    monkeypatch.setattr(VideoUploader, "get_video_status", one_shot_success)
    ok = await uploader.wait_for_processing("acct", "VID", max_wait_seconds=1, check_interval_seconds=0)
    assert ok is True

    monkeypatch.setattr(VideoUploader, "get_video_status", immediate_failure)
    failed = await uploader.wait_for_processing("acct", "VID", max_wait_seconds=1, check_interval_seconds=0)
    assert failed is False
