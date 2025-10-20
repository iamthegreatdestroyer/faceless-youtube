"""
Tests for VideoRenderer asset loading and thumbnail creation.

These tests mock MoviePy clip constructors and PIL Image so the
functions can be exercised in isolation without heavy media deps.
"""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
from typing import Any

import pytest

from src.services.video_assembler import video_renderer


class FakeVideoClip:
    def __init__(self, duration: float = 1.0, size=(640, 480)) -> None:
        self.duration = duration
        self.size = size
        self.audio = None

    def subclip(self, start: float, end: float) -> "FakeVideoClip":
        return FakeVideoClip(duration=end - start, size=self.size)

    def resize(self, size: Any) -> "FakeVideoClip":
        self.size = size
        return self

    def set_opacity(self, opacity: float) -> "FakeVideoClip":
        self.opacity = opacity
        return self

    def close(self) -> None:
        return None

    def get_frame(self, t: float):
        # Return a dummy frame object; PIL.fromarray will be mocked
        return [[0]]


class FakeImage:
    LANCZOS = "LANCZOS"

    def __init__(self, *_a, **_k):
        self._saved = False

    @staticmethod
    def fromarray(_arr):
        return FakeImage()

    def resize(self, size, resample=None):
        self.size = size
        return self

    def save(self, path):
        Path(path).write_bytes(b"thumb")


@pytest.mark.asyncio
async def test_load_video_asset_loops_and_trims(
    monkeypatch, tmp_path: Path
) -> None:
    """When source clip is shorter than scene, it should be looped and
    trimmed.
    """

    # Make VideoFileClip return a tiny clip
    def _fake_vfc(p):
        return FakeVideoClip(1.0)

    monkeypatch.setattr(video_renderer, "VideoFileClip", _fake_vfc)

    # Concatenate should sum durations
    def _concat(clips, method: str = "compose"):
        total = sum(getattr(c, "duration", 0) for c in clips)
        return FakeVideoClip(duration=total)

    monkeypatch.setattr(video_renderer, "concatenate_videoclips", _concat)

    # Instantiate renderer (VideoFileClip available)
    renderer = video_renderer.VideoRenderer()

    # Build a minimal asset-like object
    asset = SimpleNamespace(
        path=tmp_path / "a.mp4",
        video_start=0.0,
        video_end=None,
        opacity=1.0,
    )

    quality = video_renderer.QualitySettings.from_preset(
        video_renderer.QualityPreset.DRAFT
    )

    clip = await renderer._load_video_asset(asset, 3.0, quality)

    # The returned clip should be the scene duration (3s)
    assert getattr(clip, "duration", None) == 3.0


@pytest.mark.asyncio
async def test_load_image_asset_sets_duration_and_resizes(
    monkeypatch, tmp_path: Path
) -> None:
    """Image assets become clips with scene duration and resized."""

    # ImageClip factory returns simple object with set_duration and resize
    class FakeImageClip:
        def __init__(self, path):
            self.path = path
            self.duration = 0
            self.size = None

        def set_duration(self, d):
            self.duration = d
            return self

        def resize(self, size):
            self.size = size
            return self

        def set_opacity(self, opacity):
            self.opacity = opacity
            return self

    monkeypatch.setattr(video_renderer, "ImageClip", FakeImageClip)

    renderer = video_renderer.VideoRenderer()

    asset = SimpleNamespace(
        path=tmp_path / "img.png",
        video_start=0,
        video_end=None,
        opacity=0.5,
    )

    quality = video_renderer.QualitySettings.from_preset(
        video_renderer.QualityPreset.DRAFT
    )

    clip = await renderer._load_image_asset(asset, 4.0, quality)

    assert getattr(clip, "duration", None) == 4.0
    assert getattr(clip, "size", None) == quality.resolution
    assert getattr(clip, "opacity", None) == 0.5


@pytest.mark.asyncio
async def test_create_thumbnail_writes_file(
    monkeypatch, tmp_path: Path
) -> None:
    """create_thumbnail should ask the clip for a frame and save file."""

    # VideoFileClip.get_frame should return something PIL.fromarray ignores
    class FakeV(FakeVideoClip):
        def __init__(self):
            super().__init__(duration=5.0)

    def _fake_vfc(p):
        return FakeV()

    monkeypatch.setattr(video_renderer, "VideoFileClip", _fake_vfc)

    # Patch PIL Image.fromarray used inside create_thumbnail
    # Patch PIL.Image.fromarray to return our fake image object
    monkeypatch.setattr(
        "PIL.Image.fromarray", lambda arr: FakeImage()
    )

    # Ensure LANCZOS exists so the resize call can use it
    monkeypatch.setattr("PIL.Image.LANCZOS", "LANCZOS", raising=False)

    renderer = video_renderer.VideoRenderer()

    src = tmp_path / "v.mp4"
    src.write_bytes(b"x")
    out = tmp_path / "thumb.jpg"

    await renderer.create_thumbnail(src, out, 1.0, (1280, 720))

    assert out.exists() and out.stat().st_size > 0
