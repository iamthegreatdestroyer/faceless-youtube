"""
End-to-End Test Fixtures

Shared fixtures for E2E tests using actual PostgreSQL database.
These tests use the real database environment (PostgreSQL 18 on port 5433).
"""

import pytest
import os
from typing import Generator
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.core.database import Base, get_db
from src.core.models import User, Video, Asset, Script

# Load environment variables
load_dotenv()


# ============================================
# DATABASE FIXTURES (E2E - Real PostgreSQL)
# ============================================

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create database session for E2E testing using real PostgreSQL.
    
    Uses the actual PostgreSQL 18 database on port 5433.
    Each test gets a fresh session with automatic rollback.
    """
    # Get database URL from environment
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:FacelessYT2025!@localhost:5433/faceless_youtube"
    )
    
    # Create engine for testing
    engine = create_engine(db_url, pool_pre_ping=True)
    
    # Create sessionmaker
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    # Create session
    session = TestingSessionLocal()
    
    # Begin transaction
    connection = engine.connect()
    transaction = connection.begin()
    
    # Bind session to transaction
    session.bind = connection
    
    yield session
    
    # Rollback transaction (cleanup)
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_user(db: Session):
    """
    Create test user for E2E tests.
    
    Creates a user in the database and returns it for use in tests.
    The user is automatically cleaned up after the test.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == "youtube_test_user").first()
    if existing_user:
        return existing_user
    
    user = User(
        username="youtube_test_user",
        email="youtube@test.com",
        password_hash="$2b$12$test_hash_for_e2e_testing"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    yield user
    
    # Cleanup handled by db fixture rollback


@pytest.fixture(scope="function")
def cleanup_test_files():
    """
    Cleanup fixture to remove test files after E2E tests.
    
    Automatically removes any test videos, audio, or assets created during testing.
    """
    test_files = []
    
    def _register_file(filepath: str):
        """Register a file for cleanup."""
        test_files.append(filepath)
    
    yield _register_file
    
    # Cleanup registered files
    import os
    for filepath in test_files:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Warning: Failed to cleanup {filepath}: {e}")


# ============================================
# API FIXTURES (for E2E testing)
# ============================================

@pytest.fixture(scope="function")
def api_headers():
    """
    Create authentication headers for API E2E tests.
    
    Returns headers dict with test authentication token.
    """
    return {
        "Authorization": "Bearer test_token_for_e2e",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="function")
def auth_config():
    """
    Create AuthConfig for YouTube authentication tests.
    
    Returns AuthConfig with test settings.
    """
    from src.services.youtube_uploader.auth_manager import AuthConfig
    from dataclasses import field
    
    return AuthConfig(
        client_secrets_path="client_secrets.json",
        token_storage_path="test_youtube_tokens",
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
        ],
        redirect_port=8080,
        encrypt_tokens=False,  # Disable encryption for testing
        auto_refresh=True
    )


# ============================================
# MOCK FIXTURES (for external services)
# ============================================

@pytest.fixture(scope="function")
def mock_youtube_service():
    """
    Mock YouTube service for E2E tests.
    
    Returns a mock YouTube client to avoid actual API calls during testing.
    """
    from unittest.mock import Mock, MagicMock
    
    mock_service = Mock()
    mock_service.videos.return_value.insert.return_value.execute.return_value = {
        "id": "test_video_id_123",
        "snippet": {
            "title": "Test Video",
            "description": "Test Description"
        }
    }
    
    return mock_service


@pytest.fixture(scope="function")
def mock_ai_services():
    """
    Mock AI services (Claude, Gemini, Grok) for E2E tests.
    
    Returns dict of mock AI clients to avoid actual API calls and costs.
    """
    from unittest.mock import AsyncMock
    
    return {
        "claude": AsyncMock(
            generate=AsyncMock(return_value="Mock Claude response")
        ),
        "gemini": AsyncMock(
            generate=AsyncMock(return_value="Mock Gemini response")
        ),
        "grok": AsyncMock(
            generate=AsyncMock(return_value="Mock Grok response")
        )
    }
