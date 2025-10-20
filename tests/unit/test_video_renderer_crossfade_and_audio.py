"""
Tests for cross-clip crossfades and audio normalization behavior.
"""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import pytest

from src.services.video_assembler import video_renderer
from src.services.video_assembler import timeline_builder


class SimpleFakeClip:
    def __init__(self, duration=1.0, size=(640, 480)):
        self.duration = duration
        self.size = size

    def crossfadeout(self, d):
        self.crossfaded_out = d
        return self

    def crossfadein(self, d):
        self.crossfaded_in = d
        return self


class FakeComposite:
    def __init__(self, clips, size=None):
        self.clips = clips
        self.size = size
        self.duration = None

    def set_duration(self, d):
        self.duration = d
        return self


@pytest.mark.asyncio
async def test_crossfade_composes_prev_and_current(monkeypatch, tmp_path: Path) -> None:
    """When previous scene requests a FADE transition, the builder
    should create a CompositeVideoClip that overlaps the two clips."""

    # Create dummy asset files required by Scene/Asset constructors
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    a.write_bytes(b"x")
    b.write_bytes(b"x")

    Asset = timeline_builder.Asset
    Scene = timeline_builder.Scene
    Transition = timeline_builder.Transition
    TransitionType = timeline_builder.TransitionType

    scene1 = Scene(assets=[Asset(path=a, type=timeline_builder.AssetType.IMAGE)], duration=4.0)
    scene1.transition_out = Transition(type=TransitionType.FADE, duration=1.0)
    scene2 = Scene(assets=[Asset(path=b, type=timeline_builder.AssetType.IMAGE)], duration=3.0)

    config = timeline_builder.TimelineConfig()
    timeline = timeline_builder.Timeline.from_scenes([scene1, scene2], config=config)

    # Monkeypatch scene builder to return fake clips of known durations
    async def fake_build_scene_clip(self, scene, quality):
        if scene is scene1:
            return SimpleFakeClip(duration=4.0)
        return SimpleFakeClip(duration=3.0)

    monkeypatch.setattr(
        video_renderer.VideoRenderer,
        "_build_scene_clip",
        fake_build_scene_clip,
        raising=True,
    )

    # Capture CompositeVideoClip creation
    monkeypatch.setattr(
        video_renderer,
        "CompositeVideoClip",
        lambda clips, size=None: FakeComposite(clips, size=size),
        raising=False,
    )

    renderer = video_renderer.VideoRenderer()

    quality = video_renderer.QualitySettings.from_preset(video_renderer.QualityPreset.DRAFT)

    clips = await renderer._build_video_clips(timeline, quality)

    # Expect a single composite replacing the first two clips
    assert len(clips) == 1
    comp = clips[0]
    assert isinstance(comp, FakeComposite)
    # duration should equal sum minus transition duration
    assert comp.duration == pytest.approx(4.0 + 3.0 - 1.0)


@pytest.mark.asyncio
async def test_normalize_audio_tracks_applies_per_track_scaling(monkeypatch, tmp_path: Path) -> None:
    """When normalize_audio is enabled, each subclip volume is scaled."""

    monkeypatch.setattr(
        video_renderer,
        "CompositeAudioClip",
        lambda clips: SimpleNamespace(clips=clips, mixed=True),
        raising=False,
    )

    class FakeSub:
        def __init__(self):
            self.ducked = None

        def volumex(self, v):
            self.ducked = v
            return self

    # Create a composite audio object with 3 subclips
    sub1 = FakeSub()
    sub2 = FakeSub()
    sub3 = FakeSub()

    comp = SimpleNamespace(clips=[sub1, sub2, sub3])

    renderer = video_renderer.VideoRenderer()
    renderer.config.normalize_audio = True

    normalized = renderer._normalize_audio_tracks(comp)

    # After normalization each subclip should have been volumex'd to 1/3
    assert normalized.clips[0].ducked == pytest.approx(1.0 / 3.0)
    assert normalized.clips[1].ducked == pytest.approx(1.0 / 3.0)
    assert normalized.clips[2].ducked == pytest.approx(1.0 / 3.0)
