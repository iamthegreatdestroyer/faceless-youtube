"""
Deeper unit tests for VideoRenderer.

These tests exercise transition effects, background music mixing,
watermark composition and the low-level write to disk call. All
external multimedia calls are mocked for speed and determinism.
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
        self.w = size[0]
        self.h = size[1]

    def set_audio(self, audio):
        self.audio = audio
        return self

    def write_videofile(self, *args, **kwargs):
        # Store args for inspection
        self._write_args = (args, kwargs)

    def close(self):
        return None


@pytest.mark.asyncio
async def test_add_transition_out_calls_fadeout(monkeypatch) -> None:
    """Verify fadeout (and dissolve) transition branches call the fx."""

    # Ensure VideoFileClip is available so VideoRenderer can be created
    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    called = {}

    def fake_fadeout(clip, duration):
        called["fadeout"] = duration
        return clip

    monkeypatch.setattr(video_renderer, "fadeout", fake_fadeout, raising=False)

    renderer = video_renderer.VideoRenderer()

    clip = SimpleFakeClip(duration=2.0)
    transition = SimpleNamespace(
        type=video_renderer.TransitionType.FADE,
        duration=0.7,
    )

    out = renderer._add_transition_out(clip, transition)
    assert out is clip
    assert called.get("fadeout") == 0.7


@pytest.mark.asyncio
async def test_add_background_music_loops_and_mixes(
    monkeypatch, tmp_path: Path
) -> None:
    """Background music should loop if shorter than video and be mixed in."""

    # Make VideoFileClip available
    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    # Fake loop that executes functions synchronously
    class FakeLoop:
        async def run_in_executor(self, _exec, func, *args, **kwargs):
            return func(*args, **kwargs)

    monkeypatch.setattr(
        video_renderer.asyncio,
        "get_event_loop",
        lambda: FakeLoop(),
    )

    # Fake AudioFileClip that has a small duration
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
    )

    # Concatenate and audio fx should be identity ops for test
    monkeypatch.setattr(
        video_renderer,
        "concatenate_audioclips",
        lambda clips: FakeAudio(sum(c.duration for c in clips)),
        raising=False,
    )

    def _fake_audio_fade(audio, _d):
        return audio

    monkeypatch.setattr(
        video_renderer, "audio_fadein", _fake_audio_fade, raising=False
    )
    monkeypatch.setattr(
        video_renderer, "audio_fadeout", _fake_audio_fade, raising=False
    )
    monkeypatch.setattr(
        video_renderer,
        "CompositeAudioClip",
        lambda clips: clips[0] if clips else None,
        raising=False,
    )

    renderer = video_renderer.VideoRenderer()

    # Fake video clip without audio
    video = SimpleFakeClip(duration=7.0)

    music = SimpleNamespace(
        path=tmp_path / "m.mp3",
        loop=True,
        volume=0.3,
        fade_in=1.0,
        fade_out=1.0,
    )
    # Create an empty file at music.path to satisfy any path usage
    music.path.write_bytes(b"x")

    out = await renderer._add_background_music(video, music)

    # Output should be original clip (set_audio returns clip) and audio set
    assert out is video
    assert video.audio is not None


@pytest.mark.asyncio
async def test_add_watermark_composes_clip(monkeypatch) -> None:
    """Watermark should produce a Composite clip with watermark."""

    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    # Fake TextClip with width/height attributes and chaining methods
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
            self.w = 200
            self.h = 50

        def set_opacity(self, v):
            return self

        def set_position(self, pos):
            self.pos = pos
            return self

        def set_duration(self, d):
            self.duration = d
            return self

    monkeypatch.setattr(video_renderer, "TextClip", FakeText)

    # Fake CompositeVideoClip that returns a simple object with clips list
    def fake_composite(clips, size=None):
        size_val = size or getattr(clips[0], "size", None)
        return SimpleNamespace(clips=clips, size=size_val)

    monkeypatch.setattr(video_renderer, "CompositeVideoClip", fake_composite)

    renderer = video_renderer.VideoRenderer()

    video = SimpleFakeClip(duration=5.0, size=(1280, 720))

    # Ensure watermark_position is bottom_right by default
    renderer.config.watermark_position = "bottom_right"

    composed = renderer._add_watermark(video, "WM")

    assert hasattr(composed, "clips")
    assert len(composed.clips) == 2


@pytest.mark.asyncio
async def test_write_video_file_invokes_write(monkeypatch, tmp_path) -> None:
    """Ensure _write_video_file calls write_videofile with expected args."""

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

    class ClipWithWrite(SimpleFakeClip):
        def write_videofile(self, *args, **kwargs):
            self._args = args

    clip = ClipWithWrite(duration=2.0)

    renderer = video_renderer.VideoRenderer()

    quality = video_renderer.QualitySettings.from_preset(
        video_renderer.QualityPreset.DRAFT
    )

    out_path = tmp_path / "out.mp4"
    await renderer._write_video_file(clip, out_path, quality)

    # First arg should be the output path string
    assert clip._args[0] == str(out_path)
    assert clip._args[1] == quality.fps


@pytest.mark.asyncio
async def test_build_scene_clip_raises_when_no_visuals(
    monkeypatch, tmp_path
) -> None:
    """If a scene contains only non-visual assets the builder errors."""

    # Ensure VideoFileClip exists so renderer can be created
    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    # Create a dummy text asset file and use AssetType.TEXT so it is skipped
    from src.services.video_assembler.timeline_builder import (
        Asset,
        Scene,
        AssetType,
    )

    path = tmp_path / "dummy.txt"
    path.write_text("ok")

    asset = Asset(path=path, type=AssetType.TEXT, duration=1.0)

    scene = Scene(assets=[asset], start_time=0.0, duration=1.0)

    renderer = video_renderer.VideoRenderer()

    quality = video_renderer.QualitySettings.from_preset(
        video_renderer.QualityPreset.DRAFT
    )

    with pytest.raises(ValueError):
        await renderer._build_scene_clip(scene, quality)


@pytest.mark.asyncio
async def test_add_transition_out_calls_dissolve(monkeypatch) -> None:
    """DISSOLVE transition should also call the fadeout fx."""

    monkeypatch.setattr(
        video_renderer,
        "VideoFileClip",
        lambda p: SimpleFakeClip(),
    )

    called = {}

    def fake_fadeout(clip, duration):
        called["fadeout"] = duration
        return clip

    monkeypatch.setattr(video_renderer, "fadeout", fake_fadeout, raising=False)

    renderer = video_renderer.VideoRenderer()

    clip = SimpleFakeClip(duration=1.0)
    transition = SimpleNamespace(
        type=video_renderer.TransitionType.DISSOLVE,
        duration=1.1,
    )

    out = renderer._add_transition_out(clip, transition)
    assert out is clip
    assert called.get("fadeout") == pytest.approx(1.1)


@pytest.mark.asyncio
async def test_add_background_music_mixes_with_existing_audio(monkeypatch, tmp_path) -> None:
    """When the clip already has audio, CompositeAudioClip should be used."""

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

    class FakeAudio:
        def __init__(self, duration=3.0):
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

    # Return a marker object from CompositeAudioClip so we can assert it's used
    def fake_composite_audio(clips):
        return SimpleNamespace(clips=clips, mixed=True)

    monkeypatch.setattr(
        video_renderer,
        "CompositeAudioClip",
        fake_composite_audio,
        raising=False,
    )

    # Keep other audio fx as no-ops
    monkeypatch.setattr(
        video_renderer,
        "concatenate_audioclips",
        lambda clips: clips[0],
        raising=False,
    )
    monkeypatch.setattr(
        video_renderer,
        "audio_fadein",
        lambda a, d: a,
        raising=False,
    )
    monkeypatch.setattr(
        video_renderer,
        "audio_fadeout",
        lambda a, d: a,
        raising=False,
    )

    renderer = video_renderer.VideoRenderer()

    # Video clip already has an existing audio object
    video = SimpleFakeClip(duration=4.0)
    video.audio = SimpleNamespace(existing=True, duration=4.0)

    music = SimpleNamespace(path=tmp_path / "m2.mp3", loop=False, volume=0.2,
                            fade_in=0.0, fade_out=0.0)
    music.path.write_bytes(b"x")

    out = await renderer._add_background_music(video, music)

    # Ensure returned clip is same and audio is the composite result
    assert out is video
    assert getattr(out.audio, "mixed", False) is True


@pytest.mark.asyncio
async def test_write_video_file_raises_propagates(
    monkeypatch, tmp_path
) -> None:
    """If clip.write_videofile raises, the exception should propagate."""

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

    class ClipThatFails(SimpleFakeClip):
        def write_videofile(self, *args, **kwargs):
            raise RuntimeError("encode failure")

    clip = ClipThatFails(duration=1.0)
    renderer = video_renderer.VideoRenderer()

    quality = video_renderer.QualitySettings.from_preset(
        video_renderer.QualityPreset.DRAFT
    )

    out_path = tmp_path / "fail.mp4"

    with pytest.raises(RuntimeError):
        await renderer._write_video_file(clip, out_path, quality)


@pytest.mark.asyncio
async def test_build_scene_clip_with_image_and_video(
    monkeypatch, tmp_path
) -> None:
    """Positive path: scene with video + image assets composes properly."""

    # Provide marker composite that supports set_duration
    class FakeComposite:
        def __init__(self, clips, size=None):
            self.clips = clips
            self.size = size
            self.duration = None

        def set_duration(self, d):
            self.duration = d
            return self

    monkeypatch.setattr(
        video_renderer,
        "CompositeVideoClip",
        FakeComposite,
        raising=False,
    )

    # Monkeypatch asset loaders to return simple clips
    async def _fake_load_video_asset(self, asset, scene_duration, quality):
        return SimpleFakeClip(duration=scene_duration, size=quality.resolution)

    async def _fake_load_image_asset(self, asset, scene_duration, quality):
        return SimpleFakeClip(duration=scene_duration, size=quality.resolution)

    monkeypatch.setattr(
        video_renderer.VideoRenderer,
        "_load_video_asset",
        _fake_load_video_asset,
        raising=True,
    )
    monkeypatch.setattr(
        video_renderer.VideoRenderer,
        "_load_image_asset",
        _fake_load_image_asset,
        raising=True,
    )

    # Create dummy asset files
    vfile = tmp_path / "v.mp4"
    if not vfile.exists():
        vfile.write_bytes(b"v")

    ifile = tmp_path / "i.png"
    if not ifile.exists():
        ifile.write_bytes(b"i")

    from src.services.video_assembler.timeline_builder import (
        Asset,
        Scene,
        AssetType,
    )

    video_asset = Asset(path=vfile, type=AssetType.VIDEO)
    image_asset = Asset(path=ifile, type=AssetType.IMAGE)

    scene = Scene(assets=[video_asset, image_asset], duration=3.5)

    renderer = video_renderer.VideoRenderer()

    quality = video_renderer.QualitySettings.from_preset(
        video_renderer.QualityPreset.DRAFT
    )

    comp = await renderer._build_scene_clip(scene, quality)

    # Composite should have both clips and correct duration
    assert hasattr(comp, "clips")
    assert len(comp.clips) == 2
    assert comp.duration == pytest.approx(scene.duration)
