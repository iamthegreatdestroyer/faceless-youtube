"""
Unit tests for YouTube AuthManager behaviors.

Focus areas:
- credential save/load with encryption
- refresh token error handling
- auto-refresh behavior
- account listing and removal
- building YouTube client from cache
- validation API error handling
- keyring fallback when keyring fails
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import json

import pytest

from src.services.youtube_uploader import auth_manager


@pytest.mark.asyncio
async def test_save_and_load_credentials_with_encryption(tmp_path, monkeypatch):
    token_dir = tmp_path / "tokens"

    # Fake Fernet implementation to avoid cryptography dependency
    class FakeFernet:
        def __init__(self, key: bytes):
            self.key = key

        def encrypt(self, data: bytes) -> bytes:
            return b"ENCRYPTED:" + data

        def decrypt(self, enc: bytes) -> bytes:
            if not enc.startswith(b"ENCRYPTED:"):
                raise ValueError("bad")
            return enc[len(b"ENCRYPTED:"):]

        @classmethod
        def generate_key(cls):
            return b"fake-key"

    monkeypatch.setattr(auth_manager, "Fernet", FakeFernet)

    # Ensure keyring record path returns None so AuthManager generates and stores
    monkeypatch.setattr(auth_manager.keyring, "get_password", lambda s, n: None)
    monkeypatch.setattr(auth_manager.keyring, "set_password", lambda s, n, v: None)

    cfg = auth_manager.AuthConfig(client_secrets_path="/does/not/matter", token_storage_path=str(token_dir), auto_refresh=False)
    mgr = auth_manager.AuthManager(cfg)

    creds = auth_manager.YouTubeCredentials(
        account_name="acct1",
        email="me@test",
        channel_id="C123",
        channel_title="TestChannel",
        token="tok-123",
        refresh_token="r-123",
        token_uri="uri",
        client_id="cid",
        client_secret="csec",
        scopes=["s1"],
        expiry=datetime.utcnow() + timedelta(hours=1),
    )

    await mgr.save_credentials(creds)

    loaded = await mgr.load_credentials("acct1")

    assert loaded.account_name == "acct1"
    assert loaded.token == "tok-123"


@pytest.mark.asyncio
async def test_refresh_token_raises_if_no_refresh_token(monkeypatch):
    cfg = auth_manager.AuthConfig(client_secrets_path="x", token_storage_path="./tokens", auto_refresh=False)
    mgr = auth_manager.AuthManager(cfg)

    # Monkeypatch load_credentials to return creds without refresh_token
    async def fake_load(_):
        return auth_manager.YouTubeCredentials(
            account_name="a",
            token="t",
            client_id="cid",
            client_secret="sec",
            scopes=["s"],
            refresh_token=None,
        )

    monkeypatch.setattr(mgr, "load_credentials", fake_load)

    with pytest.raises(ValueError):
        await mgr.refresh_token("a")


@pytest.mark.asyncio
async def test_auto_refresh_triggers_refresh(monkeypatch):
    cfg = auth_manager.AuthConfig(client_secrets_path="x", token_storage_path="./tokens", auto_refresh=True, refresh_threshold_minutes=10)
    mgr = auth_manager.AuthManager(cfg)

    # Create a credentials object that is expiring soon
    creds = auth_manager.YouTubeCredentials(
        account_name="a",
        token="t",
        client_id="cid",
        client_secret="sec",
        scopes=["s"],
        refresh_token="r",
        expiry=datetime.utcnow() + timedelta(minutes=1),
    )

    called = {}

    async def fake_refresh(account_name):
        called["refreshed"] = True
        creds.token = "new-tok"
        return creds

    monkeypatch.setattr(mgr, "refresh_token", fake_refresh)

    out = await mgr._auto_refresh(creds)
    assert called.get("refreshed") is True
    assert out.token == "new-tok"


@pytest.mark.asyncio
async def test_get_auth_status_not_found(tmp_path):
    cfg = auth_manager.AuthConfig(client_secrets_path="x", token_storage_path=str(tmp_path / "tokens"))
    mgr = auth_manager.AuthManager(cfg)

    status = await mgr.get_auth_status("no-such")
    assert status == auth_manager.AuthStatus.NOT_AUTHENTICATED


@pytest.mark.asyncio
async def test_list_and_remove_accounts(tmp_path):
    token_dir = tmp_path / "tokens"
    token_dir.mkdir()

    (token_dir / "a.json").write_text("x")
    (token_dir / "b.json").write_text("y")

    cfg = auth_manager.AuthConfig(client_secrets_path="x", token_storage_path=str(token_dir))
    mgr = auth_manager.AuthManager(cfg)

    accounts = await mgr.list_accounts()
    assert set(accounts) == {"a", "b"}

    # Add cache and then remove one account
    mgr.credentials_cache["a"] = object()
    await mgr.remove_account("a")
    assert "a" not in mgr.credentials_cache
    assert not (token_dir / "a.json").exists()


@pytest.mark.asyncio
async def test_get_youtube_client_uses_cache_and_build(monkeypatch):
    cfg = auth_manager.AuthConfig(client_secrets_path="x", token_storage_path="./tokens")
    mgr = auth_manager.AuthManager(cfg)

    # Put object in cache to avoid file I/O
    sentinel_creds = object()
    mgr.credentials_cache["acct"] = sentinel_creds

    captured = {}

    def fake_build(name, version, credentials=None):
        captured["called_with"] = (name, version, credentials)
        return "youtube-client"

    monkeypatch.setattr(auth_manager, "build", fake_build)

    client = await mgr.get_youtube_client("acct")
    assert client == "youtube-client"
    assert captured["called_with"][0] == "youtube"


@pytest.mark.asyncio
async def test_validate_credentials_handles_api_errors(monkeypatch):
    cfg = auth_manager.AuthConfig(client_secrets_path="x", token_storage_path="./tokens")
    mgr = auth_manager.AuthManager(cfg)

    class FakeYoutube:
        def channels(self):
            class L:
                def list(self, **k):
                    class E:
                        def execute(self):
                            raise RuntimeError("api down")
                    return E()
            return L()

    creds = auth_manager.YouTubeCredentials(
        account_name="a",
        token="t",
        client_id="cid",
        client_secret="c",
        scopes=["s"],
    )

    async def fake_get(client_creds):
        return FakeYoutube()

    monkeypatch.setattr(mgr, "get_youtube_client_from_credentials", lambda c: fake_get(c))

    ok = await mgr._validate_credentials(creds)
    assert ok is False


def test_init_encryption_key_fallback_when_keyring_fails(monkeypatch):
    # Simulate keyring throwing when attempting to get encryption key
    monkeypatch.setattr(auth_manager.keyring, "get_password", lambda s, n: (_ for _ in ()).throw(RuntimeError("boom")))

    # Use fake Fernet to make generate_key deterministic
    class FakeF:
        @classmethod
        def generate_key(cls):
            return b"k123"

    monkeypatch.setattr(auth_manager, "Fernet", FakeF)

    cfg = auth_manager.AuthConfig(client_secrets_path="x", token_storage_path="./toksf")
    mgr = auth_manager.AuthManager(cfg)

    assert mgr._encryption_key == FakeF.generate_key()
