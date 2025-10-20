"""
Tests for UploadQueue: add/get_status, retry logic and cancellation.
"""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
import asyncio
import pytest

from src.services.youtube_uploader.queue_manager import (
    UploadQueue,
    QueueConfig,
    QueueItem,
    QueueStatus,
    QueuePriority,
)
from src.services.youtube_uploader.uploader import (
    UploadResult,
    UploadStatus,
    VideoMetadata,
    PrivacyStatus,
)


class FakeAuth:
    async def get_youtube_client(self, account_name: str):
        return object()


class FlakyUploader:
    def __init__(self):
        self.calls = 0

    async def upload(self, account_name, video_path, metadata, thumbnail_path=None, captions=None, progress_callback=None):
        self.calls += 1
        if self.calls == 1:
            raise Exception("transient")
        return UploadResult(
            video_id="VIDX",
            url="https://youtu.be/VIDX",
            title=metadata.title,
            status=UploadStatus.COMPLETED,
            file_size_bytes=123,
            upload_time_seconds=1.2,
            privacy_status=PrivacyStatus.PRIVATE,
        )


@pytest.mark.asyncio
async def test_add_and_get_status(tmp_path: Path):
    auth = FakeAuth()
    uploader = FlakyUploader()
    cfg = QueueConfig(auto_start=False)
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=cfg)

    metadata = VideoMetadata(title="QTest")

    item_id = await queue.add(
        account_name="acct",
        video_path=str(tmp_path / "v.mp4"),
        metadata=metadata,
        priority=QueuePriority.HIGH,
    )

    status = queue.get_status(item_id)
    assert status is not None
    assert status["status"] in (QueueStatus.QUEUED.value, QueueStatus.SCHEDULED.value)


@pytest.mark.asyncio
async def test_upload_with_retry_succeeds_after_transient_failure(tmp_path: Path):
    auth = FakeAuth()
    uploader = FlakyUploader()

    # Fast retries and no auto-start
    cfg = QueueConfig(auto_start=False, retry_failed_uploads=True, max_retries=3, retry_delay_minutes=0)
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=cfg)

    metadata = VideoMetadata(title="RetryTest")
    item_id = await queue.add(
        account_name="acct",
        video_path=str(tmp_path / "v2.mp4"),
        metadata=metadata,
        priority=QueuePriority.NORMAL,
    )

    item = queue.get_item(item_id)
    assert item is not None

    # Directly invoke upload-with-retry
    await queue._upload_with_retry(item)

    assert item.status == QueueStatus.COMPLETED
    assert item.retry_count == 1
    assert queue._stats["total_completed"] >= 1


@pytest.mark.asyncio
async def test_cancel_cancels_active_task(tmp_path: Path):
    auth = FakeAuth()
    uploader = FlakyUploader()
    cfg = QueueConfig(auto_start=False)
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=cfg)

    metadata = VideoMetadata(title="CancelTest")
    item_id = await queue.add(
        account_name="acct",
        video_path=str(tmp_path / "v3.mp4"),
        metadata=metadata,
    )

    item = queue.get_item(item_id)
    assert item is not None

    # Create a dummy long-running task and register as active
    async def long_running():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            return

    task = asyncio.create_task(long_running())
    queue._active_uploads[item_id] = task

    await queue.cancel(item_id)

    assert item.status == QueueStatus.CANCELLED
    assert queue._stats["total_cancelled"] >= 1


@pytest.mark.asyncio
async def test_retry_resets_failed_item(tmp_path: Path):
    auth = FakeAuth()
    uploader = FlakyUploader()
    cfg = QueueConfig(auto_start=False)
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=cfg)

    metadata = VideoMetadata(title="RetryReset")
    item_id = await queue.add(
        account_name="acct",
        video_path=str(tmp_path / "v4.mp4"),
        metadata=metadata,
    )

    item = queue.get_item(item_id)
    item.status = QueueStatus.FAILED
    item.retry_count = 2

    await queue.retry(item_id)

    assert item.status == QueueStatus.QUEUED
    assert item.retry_count == 0


@pytest.mark.asyncio
async def test_wait_for_completion_returns_result(tmp_path: Path):
    auth = FakeAuth()
    uploader = FlakyUploader()
    cfg = QueueConfig(auto_start=False)
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=cfg)

    metadata = VideoMetadata(title="WaitTest")
    item_id = await queue.add(
        account_name="acct",
        video_path=str(tmp_path / "v5.mp4"),
        metadata=metadata,
    )

    item = queue.get_item(item_id)
    result = UploadResult(
        video_id="X",
        url="https://youtu.be/X",
        title=metadata.title,
        status=UploadStatus.COMPLETED,
        file_size_bytes=10,
        upload_time_seconds=0.1,
        privacy_status=PrivacyStatus.PRIVATE,
    )

    item.status = QueueStatus.COMPLETED
    item.upload_result = result

    out = await queue.wait_for_completion(item_id, timeout_seconds=1)
    assert out is not None
    assert out.video_id == "X"
