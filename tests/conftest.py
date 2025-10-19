"""Top-level test fixtures used across unit/integration/e2e tests.

This file provides utilities for detecting whether required services are
available in the test environment (typically provided by
`docker-compose.test.yml`) and small helpers such as generating minimal
temporary video files for tests that require a video file.
"""

from __future__ import annotations

import os
import socket
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

import pytest


@dataclass
class ServiceEndpoints:
    """Simple container for discovered service endpoints.

    Attributes are intentionally simple (host, port) so tests can reference
    them easily.
    """

    ffmpeg_available: bool
    postgres_host: str
    postgres_port: int
    mongodb_host: str
    mongodb_port: int
    redis_host: str
    redis_port: int


def _port_is_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def docker_services() -> ServiceEndpoints:
    """Detect docker-provided test services by reading environment variables

    The test runner (see `docker-compose.test.yml`) will set environment
    variables referencing the service host names. When running tests locally
    without Docker the fixtures will default to localhost and conservative
    ports.
    """
    # Prefer explicit test environment variables set by the harness
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = int(os.getenv("POSTGRES_PORT", "5432"))

    mongo_host = os.getenv("MONGO_HOST", "localhost")
    mongo_port = int(os.getenv("MONGO_PORT", "27017"))

    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(
        os.getenv("REDIS_PORT", os.getenv("REDIS_PORT_6379_TCP_PORT", "6379"))
    )

    # Detect ffmpeg on PATH as primary indicator
    ffmpeg_on_path = shutil.which("ffmpeg") is not None

    # Try quick port checks to see if the services are reachable
    pg_up = _port_is_open(pg_host, pg_port)
    mongo_up = _port_is_open(mongo_host, mongo_port)
    redis_up = _port_is_open(redis_host, redis_port)

    endpoints = ServiceEndpoints(
        ffmpeg_available=ffmpeg_on_path,
        postgres_host=pg_host if pg_up else pg_host,
        postgres_port=pg_port,
        mongodb_host=mongo_host if mongo_up else mongo_host,
        mongodb_port=mongo_port,
        redis_host=redis_host if redis_up else redis_host,
        redis_port=redis_port,
    )

    return endpoints


@pytest.fixture(scope="session")
def ffmpeg_available(docker_services: ServiceEndpoints) -> bool:
    """Indicates whether FFmpeg is available for use in tests.

    Tests that require FFmpeg should accept this fixture and either skip or
    perform FFmpeg-backed work depending on its value.
    """
    return docker_services.ffmpeg_available


@pytest.fixture(scope="function")
def temp_video_files(
    tmp_path: Path,
    ffmpeg_available: bool,
) -> Generator[Path, None, None]:
    """Create minimal temporary video files for tests.

    If FFmpeg is available the fixture will use a small lavfi input to
    generate a 1-second MP4 file suitable for exercising video assembly
    logic. When FFmpeg is not available a small placeholder file is created
    instead (some consumer tests may still skip when FFmpeg is absent).
    """
    out_dir = tmp_path / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    video_path = out_dir / "minimal_test_video.mp4"

    if ffmpeg_available:
        try:
            # Generate a minimal test pattern video (1 second)
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc=duration=1:size=320x240:rate=10",
                "-c:v",
                "libx264",
                "-t",
                "1",
                str(video_path),
            ]
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # Fall back to a tiny placeholder file if ffmpeg invocation fails
            video_path.write_bytes(b"placeholder")
    else:
        # Create a tiny placeholder file
        video_path.write_bytes(b"placeholder")

    yield video_path

    # Cleanup happens automatically when tmp_path fixture is torn down


def pytest_collection_modifyitems(config, items):
    """Skip tests marked as requiring FFmpeg or filesystem when unavailable.

    This collection-time hook allows tests to be marked with
    `@pytest.mark.ffmpeg` and for them to be automatically skipped if
    ffmpeg is not available in the environment. It also provides a similar
    facility for `filesystem`.
    """
    import shutil

    ffmpeg_env = os.getenv("FFMPEG_AVAILABLE")
    ffmpeg_on_path = shutil.which("ffmpeg") is not None
    ffmpeg_ok = bool(ffmpeg_env) or ffmpeg_on_path

    filesystem_env = os.getenv("FILESYSTEM_AVAILABLE")
    filesystem_ok = bool(filesystem_env) or True  # default True for local

    for item in items:
        if "ffmpeg" in item.keywords and not ffmpeg_ok:
            ff_reason = (
                "requires FFmpeg (enable in docker test environment or set "
                "FFMPEG_AVAILABLE=1)"
            )
            item.add_marker(pytest.mark.skip(reason=ff_reason))

        if "filesystem" in item.keywords and not filesystem_ok:
            item.add_marker(
                pytest.mark.skip(reason="requires real filesystem access")
            )
