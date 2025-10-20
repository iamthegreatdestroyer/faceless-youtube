"""
Tests for VideoUploader action methods: _upload_video flow, metadata updates,
playlist management, and mimetype detection.
"""
from __future__ import annotations

from pathlib import Path
import asyncio
import pytest

from src.services.youtube_uploader.uploader import (
    VideoUploader,
    VideoMetadata,
    UploadStatus,
    PrivacyStatus,
)


class FakeReq:
    def __init__(self, execute_response=None, next_chunk_fn=None):
        self._execute_response = execute_response
        self._next_chunk_fn = next_chunk_fn

    def execute(self):
        return self._execute_response

    def next_chunk(self):
        if not self._next_chunk_fn:
            return (None, {"id": "VID"})
        return self._next_chunk_fn()


class FakeStatus:
    def __init__(self, prog: float):
        self._prog = prog

    def progress(self):
        return self._prog


class FakeVideos:
    def __init__(self, req: FakeReq):
        self._req = req

    def insert(self, part=None, body=None, media_body=None, notifySubscribers=None):
        return self._req

    def update(self, part=None, body=None):
        return self._req

    def delete(self, id=None):
        return self._req


class FakeYoutube:
    def __init__(self, req: FakeReq):
        self._req = req

    def videos(self):
        return FakeVideos(self._req)

    def playlistItems(self):
        outer = self._req
        class P:
            def insert(self, part=None, body=None):
                return outer
        return P()

    def playlists(self):
        outer = self._req
        class PL:
            def insert(self, part=None, body=None):
                return outer
        return PL()


class FakeAuth:
    async def get_youtube_client(self, account_name: str):
        return self.fake_youtube


@pytest.mark.asyncio
async def test__upload_video_success(tmp_path: Path):
    # Create temp video file
    video = tmp_path / "v.mp4"
    video.write_bytes(b"video-data")

    # Setup next_chunk to yield progress then response
    calls = {"n": 0}

    def next_chunk():
        calls["n"] += 1
        if calls["n"] == 1:
            return (FakeStatus(0.5), None)
        return (None, {"id": "VID_SUCCESS"})

    req = FakeReq(next_chunk_fn=next_chunk)
    fy = FakeYoutube(req)

    auth = FakeAuth()
    auth.fake_youtube = fy

    uploader = VideoUploader(auth_manager=auth)
    metadata = VideoMetadata(title="UpTest")

    vid = await uploader._upload_video(fy, video, metadata)
    assert vid == "VID_SUCCESS"


@pytest.mark.asyncio
async def test__upload_video_with_optional_fields_and_progress(tmp_path: Path):
    # Create temp video file
    video = tmp_path / "vo.mp4"
    video.write_bytes(b"video-data")

    # Setup next_chunk to yield progress then response
    calls = {"n": 0}

    def next_chunk():
        calls["n"] += 1
        if calls["n"] == 1:
            return (FakeStatus(0.3), None)
        return (FakeStatus(0.95), {"id": "VID_OPT"})

    req = FakeReq(next_chunk_fn=next_chunk)
    fy = FakeYoutube(req)

    auth = FakeAuth()
    auth.fake_youtube = fy

    uploader = VideoUploader(auth_manager=auth)
    import datetime

    metadata = VideoMetadata(
        title="OptTest",
        default_audio_language="en",
        recording_date=datetime.datetime.utcnow(),
        publish_at=datetime.datetime.utcnow(),
    )

    progress_events = []

    def progress(p: float):
        progress_events.append(p)

    vid = await uploader._upload_video(fy, video, metadata, progress_callback=progress)
    assert vid == "VID_OPT"
    assert any(p > 0 for p in progress_events)


@pytest.mark.asyncio
async def test_update_delete_add_to_playlist_and_create_playlist(tmp_path: Path):
    req = FakeReq(execute_response={"result": "ok"})
    fy = FakeYoutube(req)

    auth = FakeAuth()
    auth.fake_youtube = fy

    uploader = VideoUploader(auth_manager=auth)

    # update_metadata should call execute (no exception)
    metadata = VideoMetadata(title="MetaTest")
    await uploader.update_metadata("acct", "VID1", metadata)

    # delete_video should call execute
    await uploader.delete_video("acct", "VID1")

    # add_to_playlist should call execute
    await uploader.add_to_playlist("acct", "VID1", "PL1")

    # create_playlist should return ID when present
    req2 = FakeReq(execute_response={"id": "PL123"})
    fy2 = FakeYoutube(req2)
    auth.fake_youtube = fy2

    plid = await uploader.create_playlist("acct", "MyList", "desc", privacy_status=PrivacyStatus.PRIVATE)
    assert plid == "PL123"


@pytest.mark.asyncio
async def test_upload_thumbnail_large_size_raises(tmp_path: Path):
    tp = tmp_path / "big.jpg"
    # Create a file larger than 2MB
    tp.write_bytes(b"0" * (2 * 1024 * 1024 + 10))

    auth = FakeAuth()
    uploader = VideoUploader(auth_manager=auth)

    with pytest.raises(ValueError):
        await uploader.upload_thumbnail("acct", "VIDX", str(tp))


@pytest.mark.asyncio
async def test_upload_captions_handles_insert_exception(tmp_path: Path):
    # Create one caption file
    existing = tmp_path / "c1.srt"
    existing.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello")

    captions = [{"file": str(existing), "language": "en"}]

    class BrokenYoutube:
        def captions(self):
            class C:
                def insert(self, part=None, body=None, media_body=None):
                    raise RuntimeError("upload failed")
            return C()

    auth = FakeAuth()
    uploader = VideoUploader(auth_manager=auth)

    # Should not raise despite the inner insert raising
    await uploader._upload_captions(BrokenYoutube(), "VIDY", captions)


def test_get_mimetype_for_known_and_unknown(tmp_path: Path):
    f_mp4 = tmp_path / "a.mp4"
    f_mp4.write_bytes(b"x")
    f_unknown = tmp_path / "a.unknownext"
    f_unknown.write_bytes(b"x")

    uploader = VideoUploader(auth_manager=FakeAuth())
    mt1 = uploader._get_mimetype(f_mp4)
    mt2 = uploader._get_mimetype(f_unknown)

    assert "video" in mt1 or "mp4" in mt1
    assert mt2 == "application/octet-stream"
