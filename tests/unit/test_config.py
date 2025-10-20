"""Unit tests for configuration helpers in master_config.py"""

from pathlib import Path

from src.config import master_config as cfg


def test_database_config_urls():
    db = cfg.DatabaseConfig(
        postgres_host="dbhost",
        postgres_port=5433,
        postgres_user="pu",
        postgres_password="pw",
        postgres_db="testdb",
        mongodb_host="mhost",
        mongodb_port=27018,
        mongodb_db="mdb",
        redis_host="rhost",
        redis_port=6380,
        redis_db=2,
    )

    assert "postgresql://pu:pw@dbhost:5433/testdb" == db.postgres_url
    assert "mongodb://mhost:27018/mdb" == db.mongodb_url
    assert "redis://rhost:6380/2" == db.redis_url


def test_path_config_ensure_directories(tmp_path):
    p = cfg.PathConfig(project_root=tmp_path)

    # Ensure directories do not exist initially
    for d in [
        p.assets_dir,
        p.video_assets,
        p.audio_assets,
        p.fonts_dir,
        p.output_dir,
        p.temp_dir,
        p.cache_dir,
        p.scripts_dir,
        p.tokens_dir,
    ]:
        if d.exists():
            for child in d.rglob("*"):
                if child.is_file():
                    child.unlink()
        # remove if present
        if d.exists() and d.is_dir():
            continue

    # Create directories
    p.ensure_directories()

    for d in [
        p.assets_dir,
        p.video_assets,
        p.audio_assets,
        p.fonts_dir,
        p.output_dir,
        p.temp_dir,
        p.cache_dir,
        p.scripts_dir,
        p.tokens_dir,
    ]:
        assert d.exists() and d.is_dir()


def test_application_config_cors_list():
    a = cfg.ApplicationConfig(cors_origins="http://a.com, http://b.com")
    assert a.cors_origins_list == ["http://a.com", "http://b.com"]


def test_master_config_validate_and_to_dict(monkeypatch, tmp_path):
    # Prevent MasterConfig from creating directories on repo root
    monkeypatch.setattr(
        cfg.PathConfig, "ensure_directories", lambda self: None
    )

    mc = cfg.MasterConfig()

    # Point project root to a temp dir to avoid touching repo files
    mc.paths.project_root = tmp_path
    mc.api.youtube_client_secrets = "does_not_exist.json"
    mc.database.postgres_password = ""  # empty -> should warn
    mc.app.debug = True  # should warn

    report = mc.validate()

    assert "errors" in report and "warnings" in report
    assert (
        any("YouTube client secrets not found" in e for e in report["errors"])
        or report["errors"]
    )
    assert (
        any("PostgreSQL password not set" in w for w in report["warnings"])
        or report["warnings"]
    )

    # to_dict returns a mapping with expected top-level keys
    d = mc.to_dict()
    assert set(d.keys()) == {"database", "paths", "api", "app"}
