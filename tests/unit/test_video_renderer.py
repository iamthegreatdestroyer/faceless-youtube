"""
Unit tests for the VideoRenderer module.

These tests mock out heavy MoviePy behavior and ensure core logic
paths (quality presets, render flow, and estimate calculations) are
covered without requiring a full MoviePy installation or real media files.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from src.services.video_assembler import video_renderer


class DummyClip:
    """Minimal stub implementing the interface used by VideoRenderer.

    Only methods/attributes referenced by the test-substituted code are
    implemented.
    """

    def __init__(self, duration: float = 5.0, size=(640, 480)) -> None:
        self.duration = duration
        self.size = size
        self.audio = None

    def close(self) -> None:
        return None

    def set_audio(self, audio):
        self.audio = audio
        return self


@pytest.mark.asyncio
async def test_render_progress_and_result(
    tmp_path: Path, monkeypatch
) -> None:
    """Verify render() invokes progress callbacks and returns a valid result.

    The heavy MoviePy internals are mocked so the test focuses on orchestration
    (callback points, file output creation and result metadata).
    """

    # Ensure VideoFileClip is non-None so VideoRenderer.__init__ does not raise
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: DummyClip())

    # Stub concatenation/compositing helpers to return a DummyClip
    def _fake_concatenate(clips, method: str = "compose"):
        total = sum(getattr(c, "duration", 0) for c in clips)
        return DummyClip(duration=total)

    monkeypatch.setattr(
        video_renderer, "concatenate_videoclips", _fake_concatenate
    )

    # Replace internal methods to avoid real codec work
    async def fake_build_video_clips(
        self, timeline, quality
    ) -> List[DummyClip]:
        return [DummyClip(duration=2.0), DummyClip(duration=3.0)]

    async def fake_add_background_music(self, video_clip, music):
        return video_clip

    def _fake_add_watermark(self, clip, text):
        return clip

    monkeypatch.setattr(
        video_renderer.VideoRenderer,
        "_build_video_clips",
        fake_build_video_clips,
    )
    monkeypatch.setattr(
        video_renderer.VideoRenderer,
        "_add_background_music",
        fake_add_background_music,
    )
    monkeypatch.setattr(
        video_renderer.VideoRenderer, "_add_watermark", _fake_add_watermark
    )

    # The write step should create a file so render can compute file_size
    async def fake_write_video_file(
        self, clip, output_path: Path, quality
    ) -> None:
        output_path.write_bytes(b"0" * 1024)

    monkeypatch.setattr(
        video_renderer.VideoRenderer,
        "_write_video_file",
        fake_write_video_file,
    )

    # Instantiate renderer (VideoFileClip was set above to a non-None stub)
    renderer = video_renderer.VideoRenderer()

    # Capture progress callback invocations
    progress_calls: List[float] = []

    def progress_cb(p: float) -> None:
        progress_calls.append(p)

    # Minimal timeline value is sufficient for this orchestration test
    timeline = video_renderer.Timeline(
        scenes=[],
        total_duration=5.0,
        scene_count=2,
        resolution=(640, 480),
        fps=30,
    )

    out_path = tmp_path / "out.mp4"

    result = await renderer.render(
        timeline, out_path, progress_callback=progress_cb
    )

    # Validate expected callback checkpoints and returned metadata
    assert progress_calls == [0.3, 0.5, 1.0]
    assert result.output_path == str(out_path)
    assert out_path.exists() and out_path.stat().st_size == 1024
    assert result.scene_count == timeline.scene_count


def test_quality_settings_from_preset() -> None:
    """Quality presets map to expected resolution/bitrate values."""

    settings = video_renderer.QualitySettings.from_preset(
        video_renderer.QualityPreset.HD_1080P
    )
    assert settings.resolution == (1920, 1080)
    assert settings.bitrate == "8000k"


def test_render_config_custom_settings(monkeypatch) -> None:
    """Custom QualitySettings in RenderConfig are returned as-is."""

    # Make VideoFileClip non-None so construction is allowed
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)

    custom = video_renderer.QualitySettings(
        resolution=(800, 600), fps=24, bitrate="2000k"
    )
    cfg = video_renderer.RenderConfig(custom_settings=custom)

    assert cfg.get_quality_settings() is custom


def test_estimate_render_time(monkeypatch) -> None:
    """Estimate calculation follows the documented multiplier math."""

    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)
    renderer = video_renderer.VideoRenderer()

    timeline = video_renderer.Timeline(
        scenes=[],
        total_duration=10.0,
        scene_count=3,
        resolution=(1920, 1080),
        fps=30,
    )

    estimate = renderer.estimate_render_time(
        timeline, video_renderer.QualityPreset.HD_1080P
    )
    # For HD_1080P multiplier=2.0 -> 10 * 2.0 * (1 + 3*0.05) = 23.0
    assert abs(estimate - 23.0) < 1e-6
