"""
Additional UploadQueue tests: add_batch, priority ordering, clear_completed and clear_all
"""
from __future__ import annotations

from pathlib import Path
import asyncio
import pytest

from src.services.youtube_uploader.queue_manager import (
    UploadQueue,
    QueueConfig,
    QueuePriority,
    QueueStatus,
)
from src.services.youtube_uploader.uploader import VideoMetadata


class FakeAuth:
    async def get_youtube_client(self, account_name: str):
        return object()


class DummyUploader:
    async def upload(self, *args, **kwargs):
        return None


@pytest.mark.asyncio
async def test_add_batch_and_summary(tmp_path: Path):
    auth = FakeAuth()
    uploader = DummyUploader()
    cfg = QueueConfig(auto_start=False)
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=cfg)

    items = [
        {"account_name": "a", "video_path": str(tmp_path / f"v{i}.mp4"), "metadata": VideoMetadata(title=f"t{i}")}
        for i in range(3)
    ]

    ids = await queue.add_batch(items)
    assert len(ids) == 3

    summary = queue.get_queue_summary()
    assert summary["total_items"] == 3


@pytest.mark.asyncio
async def test_get_next_items_priority_sorting(tmp_path: Path):
    auth = FakeAuth()
    uploader = DummyUploader()
    cfg = QueueConfig(auto_start=False)
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=cfg)

    # Add items with different priorities
    ids = []
    ids.append(await queue.add("a", str(tmp_path / "a.mp4"), VideoMetadata(title="a"), priority=QueuePriority.LOW))
    ids.append(await queue.add("a", str(tmp_path / "b.mp4"), VideoMetadata(title="b"), priority=QueuePriority.URGENT))
    ids.append(await queue.add("a", str(tmp_path / "c.mp4"), VideoMetadata(title="c"), priority=QueuePriority.HIGH))

    next_items = queue._get_next_items(3)
    assert len(next_items) == 3
    # Should be ordered URGENT, HIGH, LOW
    priorities = [it.priority for it in next_items]
    assert priorities[0] == QueuePriority.URGENT
    assert priorities[1] == QueuePriority.HIGH
    assert priorities[2] == QueuePriority.LOW


@pytest.mark.asyncio
async def test_clear_completed_and_clear_all(tmp_path: Path):
    auth = FakeAuth()
    uploader = DummyUploader()
    cfg = QueueConfig(auto_start=False)
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=cfg)

    id1 = await queue.add("a", str(tmp_path / "x.mp4"), VideoMetadata(title="x"))
    id2 = await queue.add("a", str(tmp_path / "y.mp4"), VideoMetadata(title="y"))

    # Mark first completed
    item1 = queue.get_item(id1)
    item1.status = QueueStatus.COMPLETED

    await queue.clear_completed()
    assert len(queue.get_all_items()) == 1

    # Test clear_all cancels active uploads and clears queue
    # Add a dummy active upload task
    item2 = queue.get_item(id2)
    async def long_running():
        await asyncio.sleep(10)

    task = asyncio.create_task(long_running())
    queue._active_uploads[item2.id] = task

    await queue.clear_all()
    assert len(queue.get_all_items()) == 0


@pytest.mark.asyncio
async def test_start_and_stop_processing(tmp_path: Path):
    auth = FakeAuth()
    uploader = DummyUploader()
    cfg = QueueConfig(auto_start=False)
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=cfg)

    # Add an item and ensure start creates a processing task
    await queue.add("a", str(tmp_path / "z.mp4"), VideoMetadata(title="z"))

    await queue.start()
    # Allow loop to run briefly
    await asyncio.sleep(0.05)
    assert queue._processing is True

    await queue.stop()
    assert queue._processing is False


def test_cleanup_active_uploads_removes_done_tasks():
    auth = FakeAuth()
    uploader = DummyUploader()
    queue = UploadQueue(auth_manager=auth, uploader=uploader, config=QueueConfig(auto_start=False))

    fut = asyncio.get_event_loop().create_future()
    fut.set_result(None)
    queue._active_uploads["x"] = fut

    queue._cleanup_active_uploads()
    # Should remove the completed future
    assert "x" not in queue._active_uploads
