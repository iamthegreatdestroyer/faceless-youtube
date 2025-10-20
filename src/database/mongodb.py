"""MongoDB helper for tests.

Provides a simple factory `get_mongo()` that returns an
`AsyncIOMotorClient` connected using `MONGODB_URI` environment variable
or using MONGO_HOST / MONGO_PORT / credentials.
"""
from __future__ import annotations

import os
from typing import Optional

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except Exception:  # pragma: no cover - motor may not be installed in some environments
    AsyncIOMotorClient = None  # type: ignore


def _build_uri_from_env() -> str:
    uri = os.getenv("MONGODB_URI")
    if uri:
        return uri

    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    pwd = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

    if user and pwd:
        return f"mongodb://{user}:{pwd}@{host}:{port}/?authSource=admin"
    return f"mongodb://{host}:{port}/"


def get_mongo() -> Optional[AsyncIOMotorClient]:
    """Return an AsyncIOMotorClient instance.

    This function always returns a client (or None if motor is not
    installed). Tests expect to `await mongo.admin.command('ping')` on
    the returned object.
    """
    if AsyncIOMotorClient is None:
        raise RuntimeError("motor (AsyncIOMotorClient) is not installed")

    uri = _build_uri_from_env()
    return AsyncIOMotorClient(uri)


__all__ = ["get_mongo"]
