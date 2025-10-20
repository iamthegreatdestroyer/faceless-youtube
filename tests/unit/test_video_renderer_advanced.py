"""
Advanced unit tests for VideoRenderer transition and error-recovery behaviors.

These tests focus on wipe/slide fx invocation, composite-audio mixing, and
retry behavior of the write path. All external calls are mocked to keep
tests deterministic and fast.
"""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import pytest

from src.services.video_assembler import video_renderer


class SimpleFakeClip:
    def __init__(self, duration: float = 1.0, size=(640, 480)) -> None:
        self.duration = duration
        self.size = size
        self.audio = None

    def set_audio(self, audio):
        self.audio = audio
        return self

    def write_videofile(self, *args, **kwargs):
        self._args = args


@pytest.mark.asyncio
async def test_wipe_and_slide_transitions_invoke_fx(monkeypatch) -> None:
    """WIPE and SLIDE transitions should call their respective fx functions."""

    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    called = {}

    def fake_wipe(clip, duration):
        called["wipe"] = duration
        return clip

    def fake_slide(clip, duration):
        called["slide"] = duration
        return clip

    monkeypatch.setattr(video_renderer, "wipe", fake_wipe, raising=False)
    monkeypatch.setattr(video_renderer, "slide", fake_slide, raising=False)

    renderer = video_renderer.VideoRenderer()

    clip = SimpleFakeClip(duration=1.5)

    t_wipe = SimpleNamespace(
        type=video_renderer.TransitionType.WIPE,
        duration=0.45,
    )
    out = renderer._add_transition_out(clip, t_wipe)
    assert out is clip
    assert called.get("wipe") == pytest.approx(0.45)

    t_slide = SimpleNamespace(
        type=video_renderer.TransitionType.SLIDE,
        duration=0.6,
    )
    out2 = renderer._add_transition_out(clip, t_slide)
    assert out2 is clip
    assert called.get("slide") == pytest.approx(0.6)


@pytest.mark.asyncio
async def test_composite_existing_audio_is_passed_through(
    monkeypatch, tmp_path: Path
) -> None:
    """If the clip already has a composite audio, combine it with music."""

    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    # Record the argument passed into CompositeAudioClip
    recorded = {}

    def fake_composite_audio(clips):
        recorded["clips"] = clips
        return SimpleNamespace(clips=clips, mixed=True)

    monkeypatch.setattr(
        video_renderer,
        "CompositeAudioClip",
        fake_composite_audio,
        raising=False,
    )

    class FakeAudio:
        def __init__(self, duration=2.0):
            self.duration = duration

        def volumex(self, v):
            self.volume = v
            return self

        def subclip(self, a, b=None):
            return self

    monkeypatch.setattr(
        video_renderer,
        "AudioFileClip",
        lambda p: FakeAudio(2.0),
        raising=False,
    )

    renderer = video_renderer.VideoRenderer()

    # Simulate a clip whose audio is already a composite object
    video = SimpleFakeClip(duration=5.0)
    existing_audio = SimpleNamespace(
        clips=[SimpleNamespace(id="a1"), SimpleNamespace(id="a2")]
    )
    video.audio = existing_audio

    music = SimpleNamespace(
        path=tmp_path / "mix.mp3",
        loop=False,
        volume=0.2,
        fade_in=0.0,
        fade_out=0.0,
    )
    music.path.write_bytes(b"x")

    out = await renderer._add_background_music(video, music)

    assert out is video
    assert getattr(out.audio, "mixed", False) is True
    assert recorded["clips"][0] is existing_audio
    # second clip should be the music clip object (not a path)
    assert len(recorded["clips"]) == 2


@pytest.mark.asyncio
async def test_prefers_clip_crossfade_method(monkeypatch) -> None:
    """If a clip implements crossfadeout, it is preferred over fx fadeout."""

    class ClipWithCrossfade(SimpleFakeClip):
        def __init__(self, duration=1.0):
            super().__init__(duration=duration)
            self.crossfade_called = None

        def crossfadeout(self, duration):
            self.crossfade_called = duration
            return self

    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: ClipWithCrossfade(),
    )

    renderer = video_renderer.VideoRenderer()

    clip = ClipWithCrossfade(duration=2.0)
    transition = SimpleNamespace(
        type=video_renderer.TransitionType.FADE,
        duration=0.9,
    )

    out = renderer._add_transition_out(clip, transition)
    assert out is clip
    assert getattr(clip, "crossfade_called") == pytest.approx(0.9)


@pytest.mark.asyncio
async def test_text_overlay_fade_calls_fx(monkeypatch) -> None:
    """Verify overlay fadein/fadeout fx are invoked when overlay has fades."""

    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    # Fake TextClip type
    class FakeText:
        def __init__(
            self,
            text,
            fontsize=None,
            font=None,
            color=None,
            bg_color=None,
            method=None,
            size=None,
        ):
            self.text = text
            self.w = 100
            self.h = 40

        def set_opacity(self, v):
            return self

        def set_position(self, pos):
            return self

        def set_duration(self, d):
            return self

    monkeypatch.setattr(video_renderer, "TextClip", FakeText)

    called = {"in": False, "out": False}

    def fake_fadein(clip, d):
        called["in"] = True
        return clip

    def fake_fadeout(clip, d):
        called["out"] = True
        return clip

    monkeypatch.setattr(video_renderer, "fadein", fake_fadein, raising=False)
    monkeypatch.setattr(video_renderer, "fadeout", fake_fadeout, raising=False)

    from src.services.video_assembler.timeline_builder import (
        TextOverlay,
        TextPosition,
    )

    overlay = TextOverlay(
        text="hi",
        fade_in=0.5,
        fade_out=0.8,
        position=TextPosition.TOP,
    )

    renderer = video_renderer.VideoRenderer()

    _ = renderer._create_text_overlay(overlay, (1280, 720))

    assert called["in"] is True
    assert called["out"] is True


@pytest.mark.asyncio
async def test_duck_music_reduces_original_audio(
    monkeypatch, tmp_path
) -> None:
    """When `duck_music` is enabled the original audio volume is reduced."""

    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    class FakeOriginalAudio:
        def __init__(self):
            self.ducked = None

        def volumex(self, v):
            self.ducked = v
            return self

    # Simple music fake
    class FakeAudio:
        def __init__(self, duration=2.0):
            self.duration = duration

        def volumex(self, v):
            self.volume = v
            return self

        def subclip(self, a, b=None):
            return self

    monkeypatch.setattr(
        video_renderer,
        "AudioFileClip",
        lambda p: FakeAudio(2.0),
        raising=False,
    )

    # CompositeAudioClip returns a marker object
    monkeypatch.setattr(
        video_renderer,
        "CompositeAudioClip",
        lambda clips: SimpleNamespace(clips=clips, mixed=True),
        raising=False,
    )

    renderer = video_renderer.VideoRenderer()
    renderer.config.duck_music = True

    video = SimpleFakeClip(duration=5.0)
    video.audio = FakeOriginalAudio()

    music = SimpleNamespace(
        path=tmp_path / "music.mp3",
        loop=False,
        volume=0.25,
        fade_in=0.0,
        fade_out=0.0,
    )
    music.path.write_bytes(b"x")

    out = await renderer._add_background_music(video, music)

    assert out is video
    # Original audio should have had volumex called with (1 - music.volume)
    comp = out.audio
    assert comp.clips[0].ducked == pytest.approx(0.75)


@pytest.mark.asyncio
async def test_write_video_file_retries_and_succeeds(
    monkeypatch, tmp_path
) -> None:
    """Transient first-write failure is retried once by the renderer."""

    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    class FakeLoop:
        async def run_in_executor(self, _exec, func, *args, **kwargs):
            return func(*args, **kwargs)

    monkeypatch.setattr(
        video_renderer.asyncio,
        "get_event_loop",
        lambda: FakeLoop(),
    )

    class ClipFlaky(SimpleFakeClip):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.calls = 0

        def write_videofile(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise OSError("temporary encoding error")
            self._args = args

    clip = ClipFlaky(duration=1.0)

    renderer = video_renderer.VideoRenderer()

    quality = video_renderer.QualitySettings.from_preset(
        video_renderer.QualityPreset.DRAFT
    )

    out_path = tmp_path / "retry.mp4"

    # Should not raise because the second attempt succeeds
    await renderer._write_video_file(clip, out_path, quality)

    assert clip.calls == 2
    assert clip._args[0] == str(out_path)
    assert clip._args[1] == quality.fps
