import asyncio

import pytest

from src.api import metrics


@pytest.mark.asyncio
async def test_track_video_generation_and_queue_depth():
    """Decorated function should increment counters and update gauges."""
    # Ensure starting value
    labels = metrics.video_generation_requests.labels(
        status="success", niche="unittest"
    )
    before = labels._value.get()

    async def fake_generation(niche: str = "unittest"):
        await asyncio.sleep(0)
        return "ok"

    wrapped = metrics.track_video_generation(fake_generation)
    await wrapped(niche="unittest")

    after = metrics.video_generation_requests.labels(
        status="success", niche="unittest"
    )._value.get()
    assert after >= before + 1

    # Test queue depth gauge
    metrics.update_queue_depth("video_generation", 7)
    q = metrics.queue_depth.labels(queue_type="video_generation")
    assert q._value.get() == 7


@pytest.mark.asyncio
async def test_track_script_generation_and_cache_hit_rate():
    before = metrics.script_generation_requests.labels(
        status="success", niche="unittest"
    )._value.get()

    async def fake_script(niche: str = "unittest"):
        await asyncio.sleep(0)
        return "script"

    wrapped = metrics.track_script_generation(fake_script)
    await wrapped(niche="unittest")

    after = metrics.script_generation_requests.labels(
        status="success", niche="unittest"
    )._value.get()
    assert after >= before + 1

    # Cache hit rate
    metrics.update_cache_hit_rate("redis", 0.95)
    c = metrics.cache_hit_rate.labels(cache_type="redis")
    assert pytest.approx(c._value.get(), rel=1e-6) == 0.95


@pytest.mark.asyncio
async def test_track_duration_decorator():
    @metrics.track_duration(metrics.asset_download_duration)
    async def download_dummy():
        await asyncio.sleep(0)
        return True

    # Should execute without errors and record a duration
    assert await download_dummy() is True
