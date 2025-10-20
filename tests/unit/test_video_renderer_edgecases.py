"""
Edge-case tests for VideoRenderer: write retry failure and audio normalization.

These tests mock MoviePy internals and focus on logic in
`_write_video_file` and `_normalize_audio_tracks`.
"""
from __future__ import annotations

from pathlib import Path
import pytest

from src.services.video_assembler import video_renderer


@pytest.mark.asyncio
async def test_write_video_file_raises_after_retries(monkeypatch, tmp_path: Path):
    # Ensure the renderer can be instantiated
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)

    class ClipAlwaysFail:
        def write_videofile(self, *a, **k):
            raise OSError("permanent failure")

    # Fake event loop that runs the callable synchronously
    class FakeLoop:
        async def run_in_executor(self, _exec, func, *args, **kwargs):
            return func(*args, **kwargs)

    monkeypatch.setattr(video_renderer.asyncio, "get_event_loop", lambda: FakeLoop())

    renderer = video_renderer.VideoRenderer()

    clip = ClipAlwaysFail()

    with pytest.raises(OSError):
        await renderer._write_video_file(clip, tmp_path / "out.mp4", renderer.config.get_quality_settings())


def test_normalize_audio_multi_track(monkeypatch):
    # Allow instantiation
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)

    # Fake CompositeAudioClip to capture its input
    def fake_composite(clips):
        return type("C", (), {"clips": clips, "normalized": True})()

    monkeypatch.setattr(video_renderer, "CompositeAudioClip", fake_composite, raising=False)

    class FakeSubclip:
        def __init__(self):
            self.last_vol = None

        def volumex(self, v):
            self.last_vol = v
            return type("S", (), {"vol": v})()

    audio_obj = type("A", (), {"clips": [FakeSubclip(), FakeSubclip()]})()

    renderer = video_renderer.VideoRenderer()

    out = renderer._normalize_audio_tracks(audio_obj)

    # CompositeAudioClip (our fake) should have been returned and each
    # subclip should have had volumex called with 1/2
    assert getattr(out, "normalized", False) is True
    assert len(out.clips) == 2
    assert out.clips[0].vol == pytest.approx(0.5)
    assert out.clips[1].vol == pytest.approx(0.5)
