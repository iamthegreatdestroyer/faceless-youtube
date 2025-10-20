"""
Crossfade and overlay edge-case tests for VideoRenderer.

These tests verify composite creation for overlapping transitions
and handle long/multi-line text overlays.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import pytest

from src.services.video_assembler import video_renderer
from src.services.video_assembler.timeline_builder import Scene, Transition, TransitionType


def make_dummy_clip(duration: float = 2.0):
    class Dummy:
        def __init__(self, d):
            self.duration = d

        def crossfadeout(self, dur):
            self._cf_out = dur
            return self

        def crossfadein(self, dur):
            self._cf_in = dur
            return self

    return Dummy(duration)


@pytest.mark.asyncio
async def test_crossfade_composite_created_with_clip_level_methods(monkeypatch):
    # Allow renderer construction
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)

    # Fake CompositeVideoClip which records set_duration calls
    class FakeComposite:
        def __init__(self, clips, size=None):
            self.clips = clips
            self.size = size
            self.set_dur = None

        def set_duration(self, d):
            self.set_dur = d
            return self

    monkeypatch.setattr(video_renderer, "CompositeVideoClip", FakeComposite, raising=False)

    # Monkeypatch _build_scene_clip to return controlled dummy clips
    async def fake_build_scene(self, scene, quality):
        # Duration chosen so composite duration calculation is deterministic
        return make_dummy_clip(2.0 if scene is scenes[0] else 3.0)

    monkeypatch.setattr(video_renderer.VideoRenderer, "_build_scene_clip", fake_build_scene)

    # Build timeline with two scenes; prev has a FADE transition
    scenes = [
        Scene(narration_path=Path("x"), assets=[], duration=2.0, transition_out=Transition(type=TransitionType.FADE, duration=0.5)),
        Scene(narration_path=Path("x"), assets=[], duration=3.0),
    ]

    # Create timeline model manually to avoid Timeline.from_scenes complexity
    from src.services.video_assembler.timeline_builder import Timeline as TLModel

    tl = TLModel(scenes=scenes, total_duration=5.0, scene_count=2, resolution=(1280,720), fps=30)

    renderer = video_renderer.VideoRenderer()
    clips = await renderer._build_video_clips(tl, renderer.config.get_quality_settings())

    # Composite should be returned in place of two separate clips
    assert len(clips) == 1
    comp = clips[0]
    assert hasattr(comp, "set_dur")
    # Expected composite duration = prev.duration + cur.duration - transition.duration
    assert comp.set_dur == pytest.approx(2.0 + 3.0 - 0.5)


def test_create_text_overlay_long_text(monkeypatch):
    # Make TextClip a simple fake that records text and methods
    class FakeTextClip:
        def __init__(self, text, fontsize=None, font=None, color=None, bg_color=None, method=None, size=None):
            self.text = text
            self.w = 100
            self.h = 40

        def set_opacity(self, v):
            return self

        def set_position(self, pos):
            return self

        def set_duration(self, d):
            self._dur = d
            return self

    monkeypatch.setattr(video_renderer, "TextClip", FakeTextClip)

    # Fake fade functions
    monkeypatch.setattr(video_renderer, "fadein", lambda c, d: c, raising=False)
    monkeypatch.setattr(video_renderer, "fadeout", lambda c, d: c, raising=False)

    # Build a long overlay
    from src.services.video_assembler.timeline_builder import TextOverlay, TextPosition

    overlay = TextOverlay(
        text=("This is a very long overlay text " * 20),
        fade_in=0.2,
        fade_out=0.2,
        position=TextPosition.CENTER,
        duration=2.0,
    )

    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)
    renderer = video_renderer.VideoRenderer()

    clip = renderer._create_text_overlay(overlay, (1280, 720))
    assert hasattr(clip, "text")
    assert getattr(clip, "_dur", None) == pytest.approx(2.0)
