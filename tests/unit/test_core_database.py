"""Unit tests for core database utilities.

These tests monkeypatch the module-level engine and SessionLocal to use
an in-memory SQLite engine so we can safely exercise init_db,
get_table_row_counts and check_db_connection without external services.
"""

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

import src.core.database as db_mod
from src.core import models


def _setup_inmemory(monkeypatch):
    # Create in-memory SQLite engine and session factory
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Monkeypatch module-level engine and SessionLocal
    monkeypatch.setattr(db_mod, "engine", engine)
    monkeypatch.setattr(db_mod, "SessionLocal", SessionLocal)

    # Ensure metadata is created on the test engine for models
    models.Base.metadata.create_all(bind=engine)

    return engine, SessionLocal


def test_init_db_creates_tables(monkeypatch):
    engine, _ = _setup_inmemory(monkeypatch)

    # Re-create via init_db (should not raise and should create tables)
    db_mod.init_db(drop_all=True)

    insp = inspect(engine)
    # Minimal smoke checks: core tables exist
    assert insp.has_table("users")
    assert insp.has_table("videos")
    assert insp.has_table("jobs")


def test_get_table_row_counts_and_inserts(monkeypatch):
    engine, SessionLocal = _setup_inmemory(monkeypatch)

    # Insert a Job row using a direct session
    session = SessionLocal()
    job = models.Job(topic="unittest", status="queued")
    session.add(job)
    session.commit()
    session.close()

    counts = db_mod.get_table_row_counts()
    assert isinstance(counts, dict)
    assert counts.get("jobs", 0) == 1


def test_check_db_connection_returns_true(monkeypatch):
    _setup_inmemory(monkeypatch)
    assert db_mod.check_db_connection() is True
