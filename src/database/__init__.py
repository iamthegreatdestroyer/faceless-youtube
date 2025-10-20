"""
Compatibility shim for legacy imports under `src.database`.

Tests and older modules import helpers from `src.database.*` (e.g.
`src.database.postgres`, `src.database.mongodb`, `src.database.models`).
The codebase now keeps canonical implementations under `src.core.*` but
we provide a thin adapter layer so tests and other modules keep working
without changing many imports.

This package exposes:
- postgres.get_db (async session generator)
- mongodb.get_mongo (motor client factory)
- models (re-export of model classes)
"""

from . import postgres  # re-export module
from . import mongodb
from . import models

__all__ = ["postgres", "mongodb", "models"]
