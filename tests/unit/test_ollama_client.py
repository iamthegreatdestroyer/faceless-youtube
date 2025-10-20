"""
Unit tests for the OllamaClient.

These tests mock the aiohttp session and response objects to verify the
client logic (payload assembly, streaming parsing, embeddings, and health
checks) without requiring a running Ollama server.
"""
from __future__ import annotations

import json
from typing import List, Optional

import pytest

from src.services.script_generator.ollama_client import (
    OllamaClient,
    OllamaConfig,
)


class DummyContent:
    """Async iterable that yields provided byte lines."""

    def __init__(self, lines: Optional[List[bytes]] = None) -> None:
        self._lines = lines or []

    def __aiter__(self):
        async def _gen():
            for line in self._lines:
                yield line

        return _gen()


class DummyResponse:
    """Simplified stand-in for aiohttp response used with `async with`.

    The object exposes async-context manager methods and `json()`.
    """

    def __init__(
        self,
        status: int = 200,
        json_data: Optional[dict] = None,
        content_lines: Optional[List[bytes]] = None,
    ) -> None:
        self.status = status
        self._json = json_data or {}
        self.content = DummyContent(content_lines)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._json

    def raise_for_status(self):
        if self.status >= 400:
            raise Exception(f"HTTP {self.status}")


class FakeSession:
    """Fake aiohttp.ClientSession-like object with configurable responses."""

    def __init__(
        self,
        post_resp: Optional[DummyResponse] = None,
        get_resp: Optional[DummyResponse] = None,
    ) -> None:
        self._post = post_resp or DummyResponse()
        self._get = get_resp or DummyResponse()

    def post(self, url: str, json=None):
        return self._post

    def get(self, url: str):
        return self._get


@pytest.mark.asyncio
async def test_generate_preserves_context(monkeypatch) -> None:
    """Ensure generate() parses response JSON and optionally stores context."""

    # Prepare a fake response that includes a context vector
    fake_json = {
        "model": "mistral",
        "created_at": "2025-01-01T00:00:00Z",
        "response": "Hello from Ollama",
        "done": True,
        "context": [1, 2, 3],
    }

    session = FakeSession(post_resp=DummyResponse(json_data=fake_json))

    client = OllamaClient(OllamaConfig())

    async def _fake_get_session():
        return session

    monkeypatch.setattr(client, "_get_session", _fake_get_session)

    result = await client.generate("Say hi", preserve_context=True)

    assert result == "Hello from Ollama"
    assert client._context == [1, 2, 3]


@pytest.mark.asyncio
async def test_generate_stream_yields_chunks(monkeypatch) -> None:
    """Streaming responses are yielded progressively as JSON lines."""

    lines = [
        json.dumps({"response": "part1"}).encode("utf-8"),
        json.dumps({"response": "part2"}).encode("utf-8"),
    ]

    session = FakeSession(post_resp=DummyResponse(content_lines=lines))

    client = OllamaClient()

    async def _fake_get_session2():
        return session

    monkeypatch.setattr(client, "_get_session", _fake_get_session2)

    collected: List[str] = []
    async for chunk in client.generate_stream("stream me"):
        collected.append(chunk)

    assert collected == ["part1", "part2"]


@pytest.mark.asyncio
async def test_embeddings_and_list_models_and_health(monkeypatch) -> None:
    """Embeddings and model listing return expected values and health_check.

    This test combines several related short checks to avoid repeated session
    setup overhead.
    """

    # embeddings
    emb_resp = DummyResponse(json_data={"embedding": [0.1, 0.2, 0.3]})
    list_resp = DummyResponse(json_data={"models": [{"name": "mistral"}]})
    ok_resp = DummyResponse(status=200, json_data={})

    # First, embeddings
    client = OllamaClient()
    
    async def _fake_get_session3():
        return FakeSession(post_resp=emb_resp, get_resp=ok_resp)

    monkeypatch.setattr(client, "_get_session", _fake_get_session3)
    emb = await client.embeddings("hello world")
    assert isinstance(emb, list) and len(emb) == 3

    # list_models
    async def _fake_get_session4():
        return FakeSession(get_resp=list_resp)

    monkeypatch.setattr(client, "_get_session", _fake_get_session4)
    models = await client.list_models()
    assert isinstance(models, list) and models[0]["name"] == "mistral"

    # health check true
    async def _fake_get_session5():
        return FakeSession(get_resp=ok_resp)

    monkeypatch.setattr(client, "_get_session", _fake_get_session5)
    healthy = await client.health_check()
    assert healthy is True

    # health check false on exception
    async def raise_session():
        raise Exception("no server")

    monkeypatch.setattr(client, "_get_session", raise_session)
    healthy = await client.health_check()
    assert healthy is False
