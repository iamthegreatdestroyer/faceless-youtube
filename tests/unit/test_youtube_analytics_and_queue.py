"""
Tests for YouTube analytics tracker and upload queue manager.

These tests mock the YouTube client and analytics service to exercise
parsing, caching and queue behaviors without contacting external APIs.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from unittest.mock import AsyncMock, Mock

from src.services.youtube_uploader import analytics as analytics_module
from src.services.youtube_uploader.analytics import (
    AnalyticsTracker,
    AnalyticsConfig,
    VideoStats,
)

from src.services.youtube_uploader import queue_manager as queue_module
from src.services.youtube_uploader.queue_manager import (
    UploadQueue,
    QueueConfig,
    QueueStatus,
    QueueItem,
)
from typing import cast

from src.services.youtube_uploader.uploader import (
    VideoMetadata,
    UploadResult,
    UploadStatus,
    PrivacyStatus,
)


@pytest.mark.asyncio
async def test_get_video_stats_and_cache(monkeypatch) -> None:
    """get_video_stats should parse snippet/statistics and cache results."""

    # Prepare fake youtube client with videos().list().execute() response
    video_response = {
        "items": [
            {
                "snippet": {
                    "title": "Test Video",
                    "publishedAt": "2025-10-01T00:00:00Z",
                },
                "statistics": {
                    "viewCount": "100",
                    "likeCount": "10",
                    "commentCount": "2",
                    "dislikeCount": "0",
                },
            }
        ]
    }

    class FakeVideoList:
        def execute(self):
            return video_response

    class FakeYouTube:
        def videos(self):
            return SimpleNamespace(list=lambda part, id: FakeVideoList())

    auth = Mock()
    auth.get_youtube_client = AsyncMock(return_value=FakeYouTube())

    tracker = AnalyticsTracker(
        auth_manager=auth, config=AnalyticsConfig(include_revenue=True)
    )

    # Patch asyncio.to_thread used to call execute() so it runs inline
    async def _fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(analytics_module.asyncio, "to_thread", _fake_to_thread)

    # Patch _get_video_analytics to return deterministic analytic values
    monkeypatch.setattr(
        tracker, "_get_video_analytics", AsyncMock(return_value={
            "watch_time_minutes": 50,
            "average_view_duration": 30,
            "traffic_sources": {"search": 60},
            "top_countries": {"US": 40},
            "average_percentage_viewed": 70.0,
            "revenue": 12.34,
        })
    )

    # First call should compute values and populate cache
    stats = await tracker.get_video_stats("acct", "vid123", use_cache=False)

    assert isinstance(stats, VideoStats)
    assert stats.views == 100
    assert stats.likes == 10
    assert stats.comments == 2
    assert stats.engagement_rate == pytest.approx((10 + 2) / 100)
    assert stats.watch_time_minutes == 50
    assert stats.estimated_revenue == pytest.approx(12.34)

    # Second call should return the cached object; client not called.
    auth.get_youtube_client.reset_mock()
    cached = await tracker.get_video_stats(
        "acct", "vid123", use_cache=True
    )
    assert cached is stats
    auth.get_youtube_client.assert_not_called()


@pytest.mark.asyncio
async def test_get_video_analytics_parsing(monkeypatch) -> None:
    """Validate parsing of analytics rows into totals and series."""

    auth = Mock()
    # Provide dummy credentials so the build path continues
    auth.get_credentials = AsyncMock(return_value=object())

    tracker = AnalyticsTracker(auth_manager=auth, config=AnalyticsConfig())

    # Fake build() returns reports().query().execute() rows
    def fake_build(service, version, credentials=None, cache_discovery=False):
        class FakeReports:
            def query(self, **kwargs):
                class Exec:
                    def execute(self):
                        # rows: date, views, watch_time_min, likes,
                        # comments, shares, subs_gained
                        return {
                            "rows": [
                                ["2025-10-01", 1, 10, 0, 0, 0, 0],
                                ["2025-10-02", 2, 20, 1, 0, 0, 0],
                            ]
                        }
                return Exec()

        class FakeService:
            def reports(self):
                return FakeReports()

        return FakeService()

    monkeypatch.setattr("googleapiclient.discovery.build", fake_build)

    analytics_data = await tracker._get_video_analytics(
        "acct", "vid123", days=2
    )

    assert "rows" in analytics_data or "time_series" in analytics_data
    # totals should be present when rows exist
    assert analytics_data["totals"]["views"] == 3


@pytest.mark.asyncio
async def test_queue_add_start_and_retry_success(monkeypatch) -> None:
    """Test queue add, _upload_with_retry success and retry behavior."""

    # Fake uploader that simulates progress and returns an UploadResult
    async def fake_upload(
        account_name,
        video_path,
        metadata,
        thumbnail_path=None,
        captions=None,
        progress_callback=None,
    ):
        if progress_callback:
            progress_callback(55.5)
        return UploadResult(
            video_id="vid1",
            url="https://youtube.com/watch?v=vid1",
            title=metadata.title,
            status=UploadStatus.COMPLETED,
            file_size_bytes=1024,
            upload_time_seconds=1.2,
            privacy_status=PrivacyStatus.PRIVATE,
        )

    auth = Mock()
    uploader = Mock()
    uploader.upload = fake_upload

    queue = UploadQueue(
        auth_manager=auth,
        uploader=uploader,
        config=QueueConfig(auto_start=False),
    )

    metadata = VideoMetadata(title="QTest", description="desc")

    item_id = await queue.add("acct", "video.mp4", metadata)
    item = queue.get_item(item_id)
    assert item is not None
    item = cast(QueueItem, item)

    # Call upload_with_retry directly
    await queue._upload_with_retry(item)

    assert item.status == QueueStatus.COMPLETED
    assert item.upload_result is not None
    assert item.progress_percent == 55.5

    # Failure path: uploader raises; item should end as FAILED
    async def failing_upload(*args, **kwargs):
        raise RuntimeError("upload failure")

    uploader.upload = failing_upload

    # Add new failing item
    item2_id = await queue.add("acct", "video2.mp4", metadata)
    item2 = queue.get_item(item2_id)
    assert item2 is not None
    item2 = cast(QueueItem, item2)

    # Speed up retry loop by patching sleep to no-op
    async def _no_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr(queue_module.asyncio, "sleep", _no_sleep)

    # Reduce retries for test speed
    queue.config.max_retries = 2
    queue.config.retry_failed_uploads = True

    await queue._upload_with_retry(item2)

    assert item2.status == QueueStatus.FAILED


@pytest.mark.asyncio
async def test_queue_controls_and_summary() -> None:
    """Test queue cancellation, retry reset, and summary reporting."""

    auth = Mock()
    uploader = Mock()
    uploader.upload = AsyncMock()

    queue = UploadQueue(
        auth_manager=auth,
        uploader=uploader,
        config=QueueConfig(auto_start=False),
    )

    metadata = VideoMetadata(title="QTest2", description=None)
    id1 = await queue.add("acct", "a.mp4", metadata)
    id2 = await queue.add("acct", "b.mp4", metadata)

    # Cancel id1
    # Add a dummy active task to simulate running upload
    class DummyTask:
        def __init__(self):
            self._cancelled = False

        def cancel(self):
            self._cancelled = True

        def done(self):
            return True

    queue._active_uploads[id1] = cast(asyncio.Task, DummyTask())

    await queue.cancel(id1)

    it = queue.get_item(id1)
    assert it is not None
    it = cast(QueueItem, it)
    assert it.status == QueueStatus.CANCELLED

    # Mark id2 as failed and call retry
    it2 = queue.get_item(id2)
    assert it2 is not None
    it2 = cast(QueueItem, it2)
    it2.status = QueueStatus.FAILED
    it2.retry_count = 2
    await queue.retry(id2)

    assert it2.status == QueueStatus.QUEUED
    assert it2.retry_count == 0

    summary = queue.get_queue_summary()
    assert summary["total_items"] == 2
    assert "queued" in summary["status_counts"]
