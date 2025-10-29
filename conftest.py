"""Pytest configuration and fixtures."""

import sys
import os
from pathlib import Path

# Add project root to sys.path so 'src' module can be imported
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest


@pytest.fixture
def project_root_path():
    """Return the project root path."""
    return project_root


@pytest.fixture
def dotenv_loaded():
    """Ensure .env is loaded."""
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
    return True
