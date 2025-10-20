"""
Tests for the uploader internals that exercise the resumable upload
flow, thumbnail validation and video status polling without contacting
the real YouTube API.

These tests replace `asyncio.to_thread` with a synchronous helper and
provide lightweight fake objects for the Google API client request
objects so the upload loop can be exercised deterministically.
"""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from src.services.youtube_uploader import uploader as uploader_module


class FakeStatus:
    def __init__(self, progress: float) -> None:
        self._progress = progress

    def progress(self) -> float:
        return self._progress


class FakeRequest:
    def __init__(self, sequence):
        # sequence is a list of values or Exceptions to be returned/raised
        self._seq = list(sequence)

    def next_chunk(self):
        if not self._seq:
            return None, {"id": "unexpected"}

        item = self._seq.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeVideosResource:
    def __init__(self, request: FakeRequest) -> None:
        self._request = request

    def insert(self, part, body, media_body, notifySubscribers=True):
        return self._request


class FakeYouTubeClient:
    def __init__(self, request: FakeRequest) -> None:
        self._request = request

    def videos(self):
        return FakeVideosResource(self._request)


@pytest.mark.asyncio
async def test_upload_progress_and_completion(
    tmp_path: Path, monkeypatch
) -> None:
    """Ensure _upload_video path emits progress updates and returns id."""

    # Create a small fake video file
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"0" * 2048)

    # Build status sequence: two progress updates then final response
    sequence = [
        (FakeStatus(0.2), None),
        (FakeStatus(0.6), None),
        (None, {"id": "vid123"}),
    ]

    request = FakeRequest(sequence)
    youtube = FakeYouTubeClient(request)

    # Auth manager returns our fake client
    auth = Mock()
    auth.get_youtube_client = AsyncMock(return_value=youtube)

    # Monkeypatch asyncio.to_thread to call the function directly
    async def _fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(uploader_module.asyncio, "to_thread", _fake_to_thread)

    # Replace MediaFileUpload with a noop stub so construction is cheap
    class FakeMediaFileUpload:
        def __init__(
            self, path, chunksize=None, resumable=None, mimetype=None
        ):
            self.path = path

    monkeypatch.setattr(
        uploader_module, "MediaFileUpload", FakeMediaFileUpload
    )

    uploader = uploader_module.VideoUploader(auth)

    metadata = uploader_module.VideoMetadata(title="T", description="d")

    progress_calls = []

    def progress_cb(p: float) -> None:
        progress_calls.append(p)

    result = await uploader.upload(
        account_name="acct",
        video_path=str(video_path),
        metadata=metadata,
        progress_callback=progress_cb,
    )

    assert result.video_id == "vid123"
    assert result.status == uploader_module.UploadStatus.COMPLETED
    # Callback invoked at start and end
    assert progress_calls[0] == 0
    assert progress_calls[-1] == 100
    # Intermediate progress updates should be present
    assert any(0 < p < 100 for p in progress_calls[1:-1])


@pytest.mark.asyncio
async def test_upload_inner_raises_http_error(
    monkeypatch, tmp_path: Path
) -> None:
    """Validate that the upload loop surfaces HttpError when raised.

    We call the undecorated function (`__wrapped__`) to avoid Tenacity
    retry delays during the unit test.
    """

    video_path = tmp_path / "video2.mp4"
    video_path.write_bytes(b"1" * 1024)

    # Patch the instance upload helper to raise HttpError so the outer
    # upload() surface the exception without triggering retries.
    auth = Mock()
    auth.get_youtube_client = AsyncMock()

    uploader = uploader_module.VideoUploader(auth)

    err = uploader_module.HttpError(
        SimpleNamespace(status=400, reason="Bad Request"), b"bad"
    )

    monkeypatch.setattr(
        uploader, "_upload_video", AsyncMock(side_effect=err)
    )

    with pytest.raises(uploader_module.HttpError):
        await uploader.upload(
            account_name="acct",
            video_path=str(video_path),
            metadata=uploader_module.VideoMetadata(
                title="X", description=None
            ),
        )


@pytest.mark.asyncio
async def test_upload_thumbnail_validations(tmp_path: Path) -> None:
    """Thumbnail upload validation: missing and oversized files raise."""

    auth = Mock()
    auth.get_youtube_client = AsyncMock(return_value=Mock())

    uploader = uploader_module.VideoUploader(auth)

    # Missing file
    with pytest.raises(FileNotFoundError):
        await uploader.upload_thumbnail(
            "acct", "vid", str(tmp_path / "nope.jpg")
        )

    # Oversized file (>2MB)
    large = tmp_path / "big.jpg"
    large.write_bytes(b"x" * (2 * 1024 * 1024 + 1))

    with pytest.raises(ValueError, match="2MB"):
        await uploader.upload_thumbnail("acct", "vid", str(large))


@pytest.mark.asyncio
async def test_get_video_status_and_wait(monkeypatch) -> None:
    """get_video_status raises when no items; wait_for_processing stops.

    Short-circuit the poll loop by returning 'succeeded' immediately.
    """

    auth = Mock()
    auth.get_youtube_client = AsyncMock(return_value=Mock())

    uploader = uploader_module.VideoUploader(auth)

    # Create a fake youtube client whose videos().list(...).execute()
    # returns an empty items list so get_video_status raises.
    class ExecResp:
        def __init__(self, data):
            self._data = data

        def execute(self):
            return self._data

    fake_videos = Mock()
    fake_videos.list = lambda part, id: ExecResp({"items": []})

    fake_youtube = Mock()
    fake_youtube.videos = lambda: fake_videos

    auth.get_youtube_client = AsyncMock(return_value=fake_youtube)

    with pytest.raises(ValueError):
        await uploader.get_video_status("acct", "missing")

    # Now test wait_for_processing short-circuit when status 'succeeded'
    # Make get_video_status resolve immediately to 'succeeded'
    uploader.get_video_status = AsyncMock(
        return_value={"processing_status": "succeeded"}
    )

    ok = await uploader.wait_for_processing(
        "acct", "vid", max_wait_seconds=1
    )
    assert ok is True
