"""Async PostgreSQL helpers for tests and integration.

Provides an async context manager `get_db()` that yields an
`AsyncSession` compatible object for use with `async with` in tests.

This module is intentionally lightweight: it converts a sync
`DATABASE_URL` to an async url (using asyncpg) when needed so code that
passes `postgresql+psycopg2://...` continues to work in tests.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
from sqlalchemy import text

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

DEFAULT_DB = "postgresql+asyncpg://test_user:test_password@test-postgres:5432/faceless_test"


def _normalize_to_async_url(url: str) -> str:
    """Ensure the URL uses an async driver (asyncpg) for SQLAlchemy async engine.

    If the incoming URL already contains `+asyncpg` it's left unchanged.
    If it contains `+psycopg2` it's replaced with `+asyncpg`.
    If it is a bare `postgresql://...` it will be rewritten to
    `postgresql+asyncpg://...`.
    """
    if not url:
        return DEFAULT_DB

    if "+asyncpg" in url:
        return url

    if "+psycopg2" in url:
        return url.replace("+psycopg2", "+asyncpg")

    # If it's a plain postgresql:// prefix, inject +asyncpg
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Best effort fallback
    return url


DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB)
ASYNC_DATABASE_URL = _normalize_to_async_url(DATABASE_URL)


# Note: avoid creating the async engine/sessionmaker at module import
# time because that can create event-loop-bound resources which cause
# "Future attached to a different loop" errors in pytest-asyncio
# environments. Instead, the engine/sessionmaker are created lazily
# inside `get_db()` so they are bound to the currently running loop.


class _AsyncSessionProxy:
    """Proxy around AsyncSession to provide lenient execute() handling.

    Several tests pass raw SQL strings to `execute()` (e.g. "SELECT 1").
    SQLAlchemy 2.0 requires explicit `text()` for textual SQL; wrap
    string arguments so tests continue to work without modifying them.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def execute(self, statement: Any, *args, **kwargs):
        if isinstance(statement, str):
            statement = text(statement)
        return await self._session.execute(statement, *args, **kwargs)

    def __getattr__(self, name: str):
        # Delegate all other attributes to the underlying session
        return getattr(self._session, name)


@asynccontextmanager
async def get_db() -> AsyncGenerator[_AsyncSessionProxy, None]:
    """Yield an AsyncSession proxy created in the current event loop.

    Creating the async engine/sessionmaker inside the active event loop
    prevents cross-loop futures/tasks that lead to 'Future attached to
    a different loop' runtime errors observed in async test runs.
    """
    # Create a per-call engine/sessionmaker so they are bound to the
    # current event loop. This is slightly less efficient but robust
    # for test environments and one-off scripts.
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        future=True,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )

    SessionLocal = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )

    async with SessionLocal() as session:
        proxy = _AsyncSessionProxy(session)
        try:
            yield proxy
        finally:
            # Dispose the engine to clean up pooled connections
            await engine.dispose()


# Convenience alias - only export get_db for test usage
__all__ = ["get_db"]
