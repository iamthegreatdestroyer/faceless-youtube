"""
Tests for VideoUploader: file-not-found, happy-path flow and progress
callbacks. Use monkeypatch to stub network calls and background work.
"""
from __future__ import annotations

from pathlib import Path
import pytest
from unittest.mock import AsyncMock

from src.services.youtube_uploader.uploader import (
    VideoUploader,
    VideoMetadata,
    UploadResult,
    UploadStatus,
    PrivacyStatus,
)


class FakeAuth:
    async def get_youtube_client(self, account_name: str):
        return object()


@pytest.mark.asyncio
async def test_upload_raises_file_not_found(monkeypatch, tmp_path: Path):
    auth = FakeAuth()
    uploader = VideoUploader(auth_manager=auth)

    metadata = VideoMetadata(title="No file")

    # Path does not exist
    missing = tmp_path / "nope.mp4"

    with pytest.raises(FileNotFoundError):
        await uploader.upload(
            account_name="acct",
            video_path=str(missing),
            metadata=metadata,
        )


@pytest.mark.asyncio
async def test_upload_happy_path_calls_subtasks_and_reports_progress(
    monkeypatch, tmp_path: Path
):
    # Create a fake video file
    video = tmp_path / "v.mp4"
    video.write_bytes(b"data")

    # Prepare uploader with FakeAuth
    auth = FakeAuth()
    uploader = VideoUploader(auth_manager=auth)

    # Stub internal _upload_video to avoid real network operations
    async def _fake_upload_video(self, youtube, video_path, metadata, progress_callback=None):
        # Simulate partial progress
        if progress_callback:
            progress_callback(50)
        return "VID123"

    monkeypatch.setattr(VideoUploader, "_upload_video", _fake_upload_video)

    called = {
        "thumbnail": False,
        "captions": False,
        "playlist": False,
    }

    async def _fake_upload_thumbnail(self, account_name, video_id, thumbnail_path):
        called["thumbnail"] = True
        return "https://thumb.example/123.jpg"

    async def _fake_upload_captions(self, youtube, video_id, captions):
        called["captions"] = True

    async def _fake_add_to_playlist(self, account_name, video_id, playlist_id, position=None):
        called["playlist"] = True

    monkeypatch.setattr(VideoUploader, "upload_thumbnail", _fake_upload_thumbnail)
    monkeypatch.setattr(VideoUploader, "_upload_captions", _fake_upload_captions)
    monkeypatch.setattr(VideoUploader, "add_to_playlist", _fake_add_to_playlist)

    progress_calls = []

    def progress(p: float):
        progress_calls.append(p)

    metadata = VideoMetadata(title="My Title", playlist_id="PL123")

    result = await uploader.upload(
        account_name="acct",
        video_path=str(video),
        metadata=metadata,
        thumbnail_path=str(tmp_path / "t.jpg"),
        captions=[{"file": str(tmp_path / "c.srt"), "language": "en"}],
        progress_callback=progress,
    )

    assert isinstance(result, UploadResult)
    assert result.video_id == "VID123"
    # Progress 0 at start and 100 at end are reported by upload()
    assert 0 in progress_calls
    assert 100 in progress_calls
    assert called["thumbnail"] is True
    assert called["captions"] is True
    assert called["playlist"] is True
