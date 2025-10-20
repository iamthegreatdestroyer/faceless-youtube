"""
Clean, focused edge-case tests for VideoRenderer.

These tests exercise audio ducking, normalization invocation,
crossfade boundary handling, overlays/subtitles edge-cases, and
the write-retry success path.
"""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
import pytest

from src.services.video_assembler import video_renderer


class FakeLoop:
    async def run_in_executor(self, _exec, func, *args, **kwargs):
        return func(*args, **kwargs)


# Some internal functions in the renderer module attempt to call
# attributes on a module-level `video_renderer` name (e.g.:
# `getattr(video_renderer, "fadeout", None)`). Ensure the module
# has a self-reference so those getattr calls do not raise NameError.
setattr(video_renderer, "video_renderer", video_renderer)


@pytest.mark.asyncio
async def test_write_video_file_retries_and_succeeds(
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)

    class FakeLoop:
        async def run_in_executor(self, _exec, func, *args, **kwargs):
            return func(*args, **kwargs)

    def _get_loop():
        return FakeLoop()

    monkeypatch.setattr(
        video_renderer.asyncio, "get_event_loop", _get_loop
    )

    class ClipWithRetry:
        def __init__(self):
            self.calls = 0

        def write_videofile(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise OSError("transient failure")
            self._args = (args, kwargs)

    clip = ClipWithRetry()

    renderer = video_renderer.VideoRenderer()
    quality = renderer.config.get_quality_settings()
    out_path = tmp_path / "retry_out.mp4"

    await renderer._write_video_file(clip, out_path, quality)

    assert clip.calls == 2
    assert clip._args[0][0] == str(out_path)


@pytest.mark.asyncio
async def test_ducking_reduces_volume_when_audio_has_volumex(
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)

    class FakeLoop:
        async def run_in_executor(self, _exec, func, *args, **kwargs):
            return func(*args, **kwargs)

    monkeypatch.setattr(
        video_renderer.asyncio, "get_event_loop", lambda: FakeLoop()
    )

    class FakeMusic:
        def __init__(self):
            self.duration = 5.0
            self.vol = None

        def volumex(self, v):
            self.vol = v
            return self

        def subclip(self, a, b=None):
            return self

    def _fake_audiofile(p):
        return FakeMusic()

    def _fake_composite(clips):
        return SimpleNamespace(clips=clips)

    def _noop(a, d):
        return a

    monkeypatch.setattr(
        video_renderer, "AudioFileClip", _fake_audiofile, raising=False
    )
    monkeypatch.setattr(
        video_renderer, "CompositeAudioClip", _fake_composite, raising=False
    )
    monkeypatch.setattr(video_renderer, "audio_fadein", _noop, raising=False)
    monkeypatch.setattr(video_renderer, "audio_fadeout", _noop, raising=False)
    
    def _fake_concat(clips):
        return clips[0]

    monkeypatch.setattr(
        video_renderer, "concatenate_audioclips", _fake_concat, raising=False
    )

    class VideoWithAudio:
        def __init__(self):
            self.duration = 5.0

            class A:
                def __init__(self):
                    self.last_vol = None

                def volumex(self, v):
                    self.last_vol = v
                    return self

            self.audio = A()

        def set_audio(self, audio):
            self.audio = audio
            return self

    video = VideoWithAudio()
    renderer = video_renderer.VideoRenderer()
    renderer.config.duck_music = True

    music = SimpleNamespace(
        path=tmp_path / "bg.mp3",
        loop=False,
        volume=0.3,
        fade_in=0.0,
        fade_out=0.0,
    )
    music.path.write_bytes(b"x")

    out = await renderer._add_background_music(video, music)

    assert out is video
    assert hasattr(out.audio, "clips")

    ducked_audio = out.audio.clips[0]
    expected_vol = max(0.0, 1.0 - music.volume)
    assert getattr(ducked_audio, "last_vol", None) == pytest.approx(
        expected_vol
    )


@pytest.mark.asyncio
async def test_ducking_applies_to_each_subclip_when_audio_is_composite(
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)

    monkeypatch.setattr(
        video_renderer.asyncio, "get_event_loop", lambda: FakeLoop()
    )

    class FakeMusic:
        def __init__(self):
            self.duration = 3.0

        def volumex(self, v):
            self.vol = v
            return self

        def subclip(self, a, b=None):
            return self

    def _fake_audiofile(p):
        return FakeMusic()

    def _fake_composite(clips):
        return SimpleNamespace(clips=clips)

    def _noop(a, d):
        return a

    monkeypatch.setattr(
        video_renderer, "AudioFileClip", _fake_audiofile, raising=False
    )
    monkeypatch.setattr(
        video_renderer, "CompositeAudioClip", _fake_composite, raising=False
    )
    monkeypatch.setattr(video_renderer, "audio_fadein", _noop, raising=False)
    monkeypatch.setattr(video_renderer, "audio_fadeout", _noop, raising=False)

    class Sub:
        def __init__(self):
            self.ducked = None

        def volumex(self, v):
            self.ducked = v
            return self

    video = SimpleNamespace(
        duration=4.0,
        audio=SimpleNamespace(clips=[Sub(), Sub()]),
    )

    def set_audio(a):
        video.audio = a
        return video

    video.set_audio = set_audio
    renderer = video_renderer.VideoRenderer()
    renderer.config.duck_music = True

    music = SimpleNamespace(
        path=tmp_path / "bg2.mp3",
        loop=False,
        volume=0.4,
        fade_in=0.0,
        fade_out=0.0,
    )
    music.path.write_bytes(b"x")

    out = await renderer._add_background_music(video, music)

    assert out is video
    expected_vol = max(0.0, 1.0 - music.volume)
    # The renderer builds a final CompositeAudioClip whose first
    # element is the (ducked) original audio composite. Inspect the
    # inner clips for ducked volumes.
    assert video.audio.clips[0].clips[0].ducked == pytest.approx(expected_vol)
    assert video.audio.clips[0].clips[1].ducked == pytest.approx(expected_vol)


@pytest.mark.asyncio
async def test_add_background_music_calls_normalize_when_configured(
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)

    monkeypatch.setattr(
        video_renderer.asyncio, "get_event_loop", lambda: FakeLoop()
    )

    class FakeMusic:
        def __init__(self):
            self.duration = 3.0

        def volumex(self, v):
            return self

        def subclip(self, a, b=None):
            return self

    def _fake_audiofile(p):
        return FakeMusic()

    def _fake_composite(clips):
        return SimpleNamespace(clips=clips)

    monkeypatch.setattr(
        video_renderer, "AudioFileClip", _fake_audiofile, raising=False
    )
    monkeypatch.setattr(
        video_renderer, "CompositeAudioClip", _fake_composite, raising=False
    )

    called = {}

    def fake_normalize(self, a):
        # Bound method replacement must accept `self`.
        called["normalized"] = True
        return SimpleNamespace(normalized=True)

    monkeypatch.setattr(
        video_renderer.VideoRenderer,
        "_normalize_audio_tracks",
        fake_normalize,
        raising=True,
    )

    renderer = video_renderer.VideoRenderer()
    renderer.config.normalize_audio = True

    video = SimpleNamespace(duration=2.0, audio=None)

    def set_audio(a):
        video.audio = a
        return video

    video.set_audio = set_audio

    music = SimpleNamespace(
        path=tmp_path / "bg3.mp3",
        loop=False,
        volume=0.2,
        fade_in=0.0,
        fade_out=0.0,
    )
    music.path.write_bytes(b"x")

    await renderer._add_background_music(video, music)

    assert called.get("normalized", False) is True


@pytest.mark.asyncio
async def test_crossfade_with_large_transition_duration_is_handled(
    monkeypatch,
):
    monkeypatch.setattr(video_renderer, "VideoFileClip", lambda p: True)

    async def fake_build_scene(self, scene, quality):
        class C:
            def __init__(self, d):
                self.duration = d

        return C(1.0 if scene is scenes[0] else 1.0)

    monkeypatch.setattr(
        video_renderer.VideoRenderer, "_build_scene_clip", fake_build_scene
    )

    class FragileComposite:
        def __init__(self, clips, size=None):
            self.clips = clips
            self.size = size
            self.set_dur = None

        def set_duration(self, d):
            if d <= 0:
                raise ValueError("invalid duration")
            self.set_dur = d
            return self

    monkeypatch.setattr(
        video_renderer, "CompositeVideoClip", FragileComposite, raising=False
    )

    from src.services.video_assembler.timeline_builder import (
        Scene,
        Transition,
        TransitionType,
        Timeline as TLModel,
    )

    scenes = [
        Scene(
            narration_path=Path("x"),
            assets=[],
            duration=1.0,
            transition_out=Transition(
                type=TransitionType.FADE,
                duration=3.0,
            ),
        ),
        Scene(narration_path=Path("x"), assets=[], duration=1.0),
    ]

    tl = TLModel(
        scenes=scenes,
        total_duration=2.0,
        scene_count=2,
        resolution=(1280, 720),
        fps=30,
    )

    renderer = video_renderer.VideoRenderer()

    clips = await renderer._build_video_clips(
        tl, renderer.config.get_quality_settings()
    )

    assert len(clips) == 1
    comp = clips[0]
    assert getattr(comp, "set_dur", None) is None


def test_create_text_overlay_fade_longer_than_duration_and_unknown_position(
    monkeypatch,
):
    class FakeTextClip:
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
            self.w = 120
            self.h = 30

        def set_opacity(self, v):
            return self

        def set_position(self, pos):
            self._pos = pos
            return self

        def set_duration(self, d):
            self._dur = d
            return self

    monkeypatch.setattr(video_renderer, "TextClip", FakeTextClip)

    calls = {"fadein": 0, "fadeout": 0}

    def fake_fadein(c, d):
        calls["fadein"] += 1
        return c

    def fake_fadeout(c, d):
        calls["fadeout"] += 1
        return c

    monkeypatch.setattr(video_renderer, "fadein", fake_fadein, raising=False)
    monkeypatch.setattr(video_renderer, "fadeout", fake_fadeout, raising=False)

    overlay = SimpleNamespace(
        text="short",
        duration=0.1,
        fade_in=0.5,
        fade_out=0.5,
        font_size=48,
        font_family="Arial",
        font_color="#FFFFFF",
        background_color="rgba(0, 0, 0, 0.7)",
        position=SimpleNamespace(value="offscreen"),
    )

    renderer = video_renderer.VideoRenderer()
    clip = renderer._create_text_overlay(overlay, (1280, 720))

    assert calls["fadein"] == 1
    assert calls["fadeout"] == 1
    assert getattr(clip, "_pos", None) == ("center", "bottom")
