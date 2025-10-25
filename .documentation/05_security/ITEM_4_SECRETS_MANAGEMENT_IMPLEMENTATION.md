# Item 4: Secrets Management - Implementation Guide

**Priority:** CRITICAL  
**Estimated Effort:** 4-6 hours  
**Status:** ⏳ READY FOR IMPLEMENTATION  
**Target:** Oct 24, 14:00 UTC - 20:00 UTC (after Items 2-3)

---

## Overview

This guide implements centralized secrets management and prepares the application for production-grade secret handling via HashiCorp Vault (deployment in Phase 2).

**Current State:**

- Secrets in `.env` files (development pattern)
- Environment variables injected via docker-compose
- Works for development, not production-ready

**Target State:**

- Centralized secret management
- Secrets abstracted from application code
- Vault-ready architecture
- Safe credential handling

---

## Current Secrets in Codebase

**Identified Secrets:**

```
1. Database Credentials
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - DATABASE_URL

2. API Keys
   - YOUTUBE_API_KEY
   - OPENAI_API_KEY (if used)
   - ANTHROPIC_API_KEY (Claude)

3. OAuth Credentials
   - GOOGLE_CLIENT_ID
   - GOOGLE_CLIENT_SECRET
   - OAUTH_REDIRECT_URI

4. Application Secrets
   - SECRET_KEY (for JWT)
   - ENCRYPTION_KEY
   - REDIS_PASSWORD

5. Service Credentials
   - MONGODB_URI
   - SENDGRID_API_KEY (if used)

6. Configuration
   - ENVIRONMENT (dev/staging/prod)
   - DEBUG_MODE
   - LOG_LEVEL
```

---

## Implementation Approach

### Phase 1: Create Secret Manager Abstraction

**Purpose:** Decouple secret access from source

**Create:** `src/core/secrets.py`

**Benefits:**

- Secrets accessed through single interface
- Easy to swap backends (env vars → Vault)
- Centralized secret validation
- Audit logging of secret access

### Phase 2: Refactor Config Loading

**Purpose:** Update `src/core/config.py` to use SecretManager

**Impact:**

- No changes to application logic
- Secrets transparently loaded from right source
- Backward compatible with env vars

### Phase 3: Update Environment Templates

**Files:**

- `.env.example` - Template without sensitive values
- `.env.production.example` - Production template

### Phase 4: Document Vault Integration

**Purpose:** Enable Phase 2 deployment

**Content:**

- Vault setup instructions
- Integration code examples
- Credential rotation procedures

### Phase 5: Testing & Validation

**Verification:**

- Application starts without errors
- All secrets properly loaded
- No breaking changes
- Performance maintained

---

## Implementation Steps

### STEP 1: Create Secret Manager Class

**Location:** `src/core/secrets.py`

**File Content:**

```python
"""
Centralized secret management for the application.

This module provides a unified interface for accessing secrets, supporting
multiple backends (environment variables, Vault, etc.).

Backend Priority:
1. HashiCorp Vault (production) - Phase 2
2. Environment variables (staging/development)
3. .env files (local development fallback)
"""

import os
import logging
from typing import Optional, Dict, Any
from enum import Enum
from functools import lru_cache

logger = logging.getLogger(__name__)


class SecretNotFoundError(Exception):
    """Raised when a required secret cannot be found."""
    pass


class SecretSource(Enum):
    """Supported secret sources."""
    ENVIRONMENT = "environment"
    VAULT = "vault"
    FILE = "file"


class SecretManager:
    """
    Centralized secret manager with support for multiple backends.

    Usage:
        secrets = SecretManager()
        api_key = secrets.get_secret("youtube_api_key")

    Vault Integration (Phase 2):
        secrets = SecretManager(source="vault", vault_addr="https://vault.example.com")
        api_key = secrets.get_secret("youtube_api_key")
    """

    # Secret definitions with metadata
    SECRETS_MANIFEST = {
        # Database Credentials
        "database_url": {
            "required": True,
            "description": "PostgreSQL connection URL",
            "patterns": ["DATABASE_URL", "SQLALCHEMY_DATABASE_URI"],
            "sensitive": True,
        },
        "postgres_user": {
            "required": True,
            "description": "PostgreSQL username",
            "patterns": ["POSTGRES_USER"],
            "sensitive": True,
        },
        "postgres_password": {
            "required": True,
            "description": "PostgreSQL password",
            "patterns": ["POSTGRES_PASSWORD"],
            "sensitive": True,
        },

        # API Keys
        "youtube_api_key": {
            "required": False,
            "description": "YouTube Data API key",
            "patterns": ["YOUTUBE_API_KEY"],
            "sensitive": True,
        },
        "anthropic_api_key": {
            "required": False,
            "description": "Anthropic Claude API key",
            "patterns": ["ANTHROPIC_API_KEY"],
            "sensitive": True,
        },

        # OAuth Credentials
        "google_client_id": {
            "required": False,
            "description": "Google OAuth client ID",
            "patterns": ["GOOGLE_CLIENT_ID"],
            "sensitive": True,
        },
        "google_client_secret": {
            "required": False,
            "description": "Google OAuth client secret",
            "patterns": ["GOOGLE_CLIENT_SECRET"],
            "sensitive": True,
        },

        # Application Secrets
        "secret_key": {
            "required": True,
            "description": "Secret key for JWT and sessions",
            "patterns": ["SECRET_KEY", "APP_SECRET_KEY"],
            "sensitive": True,
        },
        "encryption_key": {
            "required": False,
            "description": "Master encryption key for sensitive data",
            "patterns": ["ENCRYPTION_KEY"],
            "sensitive": True,
        },

        # Redis
        "redis_password": {
            "required": False,
            "description": "Redis password",
            "patterns": ["REDIS_PASSWORD"],
            "sensitive": True,
        },

        # MongoDB
        "mongodb_uri": {
            "required": False,
            "description": "MongoDB connection URI",
            "patterns": ["MONGODB_URI"],
            "sensitive": True,
        },

        # Configuration (non-sensitive)
        "environment": {
            "required": True,
            "description": "Deployment environment (dev/staging/prod)",
            "patterns": ["ENVIRONMENT", "ENV"],
            "sensitive": False,
        },
        "debug_mode": {
            "required": False,
            "description": "Debug mode enabled",
            "patterns": ["DEBUG"],
            "sensitive": False,
        },
        "log_level": {
            "required": False,
            "description": "Logging level",
            "patterns": ["LOG_LEVEL"],
            "sensitive": False,
        },
    }

    def __init__(self, source: str = "environment", **kwargs):
        """
        Initialize SecretManager.

        Args:
            source: Secret source ("environment" or "vault")
            **kwargs: Backend-specific configuration
        """
        self.source = SecretSource(source)
        self.vault_config = kwargs if source == "vault" else {}
        self._secret_cache: Dict[str, Any] = {}

        if source == "vault":
            self._init_vault_client(**kwargs)

        logger.info(f"SecretManager initialized with source: {source}")

    def _init_vault_client(self, **config):
        """
        Initialize Vault client.

        Configuration:
            vault_addr: Vault server address (default: http://localhost:8200)
            vault_token: Authentication token (from environment)
            vault_namespace: Vault namespace (if using Enterprise)
        """
        try:
            import hvac

            vault_addr = config.get("vault_addr", os.getenv("VAULT_ADDR", "http://localhost:8200"))
            vault_token = os.getenv("VAULT_TOKEN")

            if not vault_token:
                raise ValueError("VAULT_TOKEN environment variable not set")

            self.vault_client = hvac.Client(
                url=vault_addr,
                token=vault_token,
                namespace=config.get("vault_namespace"),
            )

            # Verify Vault connection
            if not self.vault_client.is_authenticated():
                raise ValueError("Failed to authenticate with Vault")

            logger.info(f"Vault client initialized: {vault_addr}")

        except ImportError:
            logger.warning("hvac library not installed. Vault support disabled.")
            self.vault_client = None

    @lru_cache(maxsize=128)
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from configured source.

        Args:
            key: Secret key (lowercase with underscores)
            default: Default value if secret not found

        Returns:
            Secret value or default

        Raises:
            SecretNotFoundError: If required secret not found
        """
        # Check cache first
        if key in self._secret_cache:
            return self._secret_cache[key]

        # Get from source based on configuration
        secret = None

        if self.source == SecretSource.VAULT:
            secret = self._get_from_vault(key)
        elif self.source == SecretSource.ENVIRONMENT:
            secret = self._get_from_environment(key)

        # Handle not found
        if secret is None:
            manifest = self.SECRETS_MANIFEST.get(key, {})
            if manifest.get("required"):
                raise SecretNotFoundError(
                    f"Required secret '{key}' not found. "
                    f"Description: {manifest.get('description')}"
                )
            secret = default

        # Cache the result
        if secret is not None:
            self._secret_cache[key] = secret

        return secret

    def _get_from_environment(self, key: str) -> Optional[str]:
        """Get secret from environment variables."""
        manifest = self.SECRETS_MANIFEST.get(key, {})
        patterns = manifest.get("patterns", [key.upper()])

        for pattern in patterns:
            value = os.getenv(pattern)
            if value:
                if manifest.get("sensitive"):
                    logger.debug(f"Secret loaded from environment: {pattern}")
                else:
                    logger.debug(f"Configuration loaded from environment: {pattern}")
                return value

        return None

    def _get_from_vault(self, key: str) -> Optional[str]:
        """Get secret from HashiCorp Vault."""
        if not self.vault_client:
            logger.warning("Vault client not initialized, falling back to environment")
            return self._get_from_environment(key)

        try:
            # Vault path: secret/data/{environment}/{key}
            environment = os.getenv("ENVIRONMENT", "development")
            path = f"secret/data/{environment}/{key}"

            response = self.vault_client.secrets.kv.v2.read_secret_version(path)
            secret = response["data"]["data"].get("value")

            if secret:
                logger.debug(f"Secret loaded from Vault: {path}")
                return secret

        except Exception as e:
            logger.warning(f"Failed to read secret from Vault: {e}")
            # Fall back to environment variables
            return self._get_from_environment(key)

        return None

    def list_secrets(self) -> Dict[str, Any]:
        """
        List all configured secrets (for debugging).

        Returns:
            Dictionary of secret metadata (without values)
        """
        return {
            key: {
                "source": self.source.value,
                "required": manifest.get("required"),
                "sensitive": manifest.get("sensitive"),
                "description": manifest.get("description"),
            }
            for key, manifest in self.SECRETS_MANIFEST.items()
        }

    def validate_secrets(self) -> Dict[str, bool]:
        """
        Validate that all required secrets are available.

        Returns:
            Dictionary of secret names and validation status
        """
        validation_results = {}

        for key, manifest in self.SECRETS_MANIFEST.items():
            if manifest.get("required"):
                try:
                    secret = self.get_secret(key)
                    validation_results[key] = secret is not None
                except SecretNotFoundError:
                    validation_results[key] = False
                    logger.error(f"Required secret missing: {key}")

        return validation_results

    def clear_cache(self):
        """Clear secret cache (use after rotation)."""
        self._secret_cache.clear()
        logger.info("Secret cache cleared")


# Singleton instance for application
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """Get or create the global SecretManager instance."""
    global _secret_manager

    if _secret_manager is None:
        source = os.getenv("SECRET_SOURCE", "environment")
        _secret_manager = SecretManager(source=source)

    return _secret_manager


# Convenience function
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a secret.

    Usage:
        from src.core.secrets import get_secret
        api_key = get_secret("youtube_api_key")
    """
    return get_secret_manager().get_secret(key, default=default)
```

### STEP 2: Update Config Module

**Location:** `src/core/config.py` (modify existing)

**Changes to make:**

```python
"""
Configuration module with centralized secret management.

This module loads configuration from environment variables and secrets manager.
All sensitive values are sourced through SecretManager for production readiness.
"""

import os
from typing import Optional
from functools import lru_cache

from src.core.secrets import get_secret_manager, SecretNotFoundError

logger = None  # Will be set in __init__


class Settings:
    """
    Application settings loaded from environment and secrets.

    Priority:
    1. Environment variables (override)
    2. Secrets manager (Vault or env vars)
    3. Default values
    """

    def __init__(self):
        """Initialize settings with secrets."""
        self.secrets = get_secret_manager()

        # Database
        self.database_url: str = self.secrets.get_secret(
            "database_url",
            default=os.getenv("DATABASE_URL", "postgresql://user:password@localhost/db")
        )

        # API Keys
        self.youtube_api_key: Optional[str] = self.secrets.get_secret(
            "youtube_api_key",
            default=None
        )

        self.anthropic_api_key: Optional[str] = self.secrets.get_secret(
            "anthropic_api_key",
            default=os.getenv("ANTHROPIC_API_KEY")
        )

        # OAuth
        self.google_client_id: Optional[str] = self.secrets.get_secret(
            "google_client_id",
            default=None
        )

        self.google_client_secret: Optional[str] = self.secrets.get_secret(
            "google_client_secret",
            default=None
        )

        # Application Secrets
        self.secret_key: str = self.secrets.get_secret(
            "secret_key",
            default=os.getenv("SECRET_KEY", "change-me-in-production")
        )

        self.encryption_key: Optional[str] = self.secrets.get_secret(
            "encryption_key",
            default=None
        )

        # Redis
        self.redis_password: Optional[str] = self.secrets.get_secret(
            "redis_password",
            default=None
        )

        # MongoDB
        self.mongodb_uri: Optional[str] = self.secrets.get_secret(
            "mongodb_uri",
            default=None
        )

        # Environment
        self.environment: str = self.secrets.get_secret(
            "environment",
            default=os.getenv("ENVIRONMENT", "development")
        )

        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def validate(self) -> bool:
        """
        Validate all required settings are available.

        Returns:
            True if all required settings are available

        Raises:
            ValueError: If required settings are missing
        """
        required_keys = ["database_url", "secret_key", "environment"]

        validation_results = self.secrets.validate_secrets()

        missing = [key for key, valid in validation_results.items() if not valid]

        if missing:
            raise ValueError(
                f"Missing required secrets: {', '.join(missing)}. "
                f"Ensure these are set in environment or Vault."
            )

        return True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Usage:
        from src.core.config import get_settings
        settings = get_settings()
        db_url = settings.database_url
    """
    settings = Settings()
    settings.validate()
    return settings
```

### STEP 3: Update `.env.example`

**Location:** `.env.example` (modify existing)

**Content:**

```bash
# Faceless YouTube Automation - Configuration Template
# Copy this to .env and fill in your values
# DO NOT commit actual .env file with secrets!

# ENVIRONMENT CONFIGURATION
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO

# SECRET SOURCE
# Options: environment (default), vault
SECRET_SOURCE=environment

# DATABASE CONFIGURATION
DATABASE_URL=postgresql://postgres:password@postgres:5432/faceless_youtube
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password

# API KEYS
# Get from YouTube Data API console
YOUTUBE_API_KEY=your-youtube-api-key-here

# Get from Anthropic console
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# OAuth CREDENTIALS
# Get from Google Cloud Console
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# APPLICATION SECRETS
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-generated-secret-key-here
ENCRYPTION_KEY=your-generated-encryption-key-here

# REDIS CONFIGURATION
REDIS_PASSWORD=your-redis-password

# MONGODB CONFIGURATION
MONGODB_URI=mongodb://admin:password@mongodb:27017/faceless_youtube

# VAULT CONFIGURATION (For Phase 2 - production deployment)
# VAULT_ADDR=https://vault.example.com
# VAULT_TOKEN=s.xxxxxxxxxxxxx
# VAULT_NAMESPACE=faceless-youtube

# LOGGING
LOG_LEVEL=INFO
LOG_FORMAT=json

# WORKER CONFIGURATION
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API CONFIGURATION
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# CORS CONFIGURATION
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# FEATURES
ENABLE_TRANSCRIPTION=true
ENABLE_ANALYSIS=true
ENABLE_SCHEDULING=true
```

### STEP 4: Create Production `.env.example`

**Location:** `.env.production.example`

**Content:**

```bash
# Faceless YouTube Automation - Production Configuration
# This template includes all production-specific settings
# Use with Vault for secret management

ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# PRODUCTION SECRETS - MANAGED BY VAULT
# Set SECRET_SOURCE=vault in deployment environment
SECRET_SOURCE=vault

# Database (example - actual URL from Vault)
DATABASE_URL=postgresql://prod_user:***VAULT***@prod-db.rds.amazonaws.com/faceless_youtube

# All other secrets sourced from Vault in production
# Environment variables not needed when using Vault

# LOGGING
LOG_LEVEL=WARNING
LOG_FORMAT=json

# API CONFIGURATION
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=8

# CORS CONFIGURATION (Production domain)
CORS_ORIGINS=https://app.faceless-youtube.com

# VAULT CONFIGURATION
VAULT_ADDR=https://vault.faceless-youtube.com
# VAULT_TOKEN set via secret in deployment
# VAULT_NAMESPACE=faceless-youtube
```

### STEP 5: Update Main Application Initialization

**Location:** `src/api/main.py` - Update imports and startup

**Changes:**

```python
# Add to imports section (line ~30):
from src.core.secrets import get_secret_manager
from src.core.config import get_settings

# Add to startup event (after other startup code):
@app.on_event("startup")
async def startup_secrets():
    """Validate secrets on application startup."""
    try:
        secrets = get_secret_manager()
        settings = get_settings()

        # Validate required secrets
        validation = secrets.validate_secrets()
        failed_secrets = [k for k, v in validation.items() if not v]

        if failed_secrets:
            logger.error(f"Missing required secrets: {failed_secrets}")
            raise ValueError(f"Cannot start without required secrets: {failed_secrets}")

        logger.info(f"✓ All required secrets validated ({len(validation)} total)")
        logger.info(f"✓ Environment: {settings.environment}")
        logger.info(f"✓ Debug mode: {settings.debug}")

    except Exception as e:
        logger.error(f"✗ Secrets validation failed: {e}")
        raise
```

### STEP 6: Create Secrets Validation Tests

**Location:** `tests/unit/test_secrets.py`

**Content:**

```python
"""
Unit tests for secret management.
"""

import os
import pytest
from src.core.secrets import (
    SecretManager,
    SecretNotFoundError,
    get_secret,
    get_secret_manager,
)


class TestSecretManager:
    """Test SecretManager functionality."""

    def test_secret_manager_creation(self):
        """Test that SecretManager initializes correctly."""
        manager = SecretManager(source="environment")
        assert manager is not None
        assert manager.source.value == "environment"

    def test_get_secret_from_environment(self, monkeypatch):
        """Test getting secret from environment variables."""
        monkeypatch.setenv("TEST_SECRET", "test_value")

        manager = SecretManager(source="environment")
        # Register test secret
        manager.SECRETS_MANIFEST["test_secret"] = {
            "required": False,
            "patterns": ["TEST_SECRET"],
            "sensitive": True,
        }

        secret = manager.get_secret("test_secret")
        assert secret == "test_value"

    def test_required_secret_not_found(self):
        """Test that SecretNotFoundError raised for missing required secret."""
        manager = SecretManager(source="environment")

        with pytest.raises(SecretNotFoundError):
            manager.get_secret("nonexistent_required_secret")

    def test_secret_caching(self, monkeypatch):
        """Test that secrets are cached."""
        monkeypatch.setenv("CACHED_SECRET", "cached_value")

        manager = SecretManager(source="environment")
        manager.SECRETS_MANIFEST["cached_secret"] = {
            "required": False,
            "patterns": ["CACHED_SECRET"],
            "sensitive": True,
        }

        # First access
        secret1 = manager.get_secret("cached_secret")

        # Change environment value
        monkeypatch.setenv("CACHED_SECRET", "new_value")

        # Second access should return cached value
        secret2 = manager.get_secret("cached_secret")

        assert secret1 == secret2 == "cached_value"

    def test_cache_clear(self, monkeypatch):
        """Test clearing secret cache."""
        monkeypatch.setenv("CLEAR_TEST_SECRET", "initial_value")

        manager = SecretManager(source="environment")
        manager.SECRETS_MANIFEST["clear_test_secret"] = {
            "required": False,
            "patterns": ["CLEAR_TEST_SECRET"],
            "sensitive": True,
        }

        secret1 = manager.get_secret("clear_test_secret")
        manager.clear_cache()

        monkeypatch.setenv("CLEAR_TEST_SECRET", "updated_value")
        secret2 = manager.get_secret("clear_test_secret")

        assert secret1 == "initial_value"
        assert secret2 == "updated_value"

    def test_list_secrets(self):
        """Test listing available secrets."""
        manager = SecretManager(source="environment")
        secrets_list = manager.list_secrets()

        assert isinstance(secrets_list, dict)
        assert len(secrets_list) > 0
        assert "database_url" in secrets_list
```

---

## Verification & Testing

### Test 1: Verify Secret Manager Loads

```bash
# Test importing and initializing SecretManager
python -c "
from src.core.secrets import get_secret_manager
manager = get_secret_manager()
print(f'✓ SecretManager initialized: {manager.source.value}')
"
```

### Test 2: Test Environment Variable Loading

```bash
# Set test environment variable
export TEST_API_KEY="test-key-123"

# Test loading
python -c "
from src.core.secrets import get_secret
secret = get_secret('youtube_api_key', default='fallback')
print(f'✓ Secret loaded: {secret}')
"
```

### Test 3: Validate Config Loading

```bash
# Test configuration initialization
python -c "
from src.core.config import get_settings
settings = get_settings()
print(f'✓ Environment: {settings.environment}')
print(f'✓ Debug: {settings.debug}')
"
```

### Test 4: Run Secret Management Tests

```bash
# Run unit tests for secrets
pytest tests/unit/test_secrets.py -v

# Expected output:
# test_secret_manager_creation PASSED
# test_get_secret_from_environment PASSED
# test_required_secret_not_found PASSED
# test_secret_caching PASSED
# test_cache_clear PASSED
# test_list_secrets PASSED
```

### Test 5: Application Startup with Secrets

```bash
# Start application and verify secrets validation
docker-compose -f docker-compose.staging.yml up api

# Expected log output:
# INFO: ✓ All required secrets validated (15 total)
# INFO: ✓ Environment: staging
# INFO: ✓ Debug mode: False
# INFO: Application started successfully
```

### Test 6: .env.example Validation

```bash
# Verify .env.example doesn't contain actual secrets
grep -E "api.key|password|token|secret" .env.example || echo "✓ No secrets in .env.example"

# Expected: Returns only placeholder text like "your-api-key-here"
```

---

## Migration Guide

### For Existing Code

**Before (directly accessing os.environ):**

```python
api_key = os.getenv("YOUTUBE_API_KEY")
db_url = os.getenv("DATABASE_URL")
```

**After (using SecretManager):**

```python
from src.core.secrets import get_secret

api_key = get_secret("youtube_api_key")
db_url = get_secret("database_url")
```

**Or using Config:**

```python
from src.core.config import get_settings

settings = get_settings()
api_key = settings.youtube_api_key
db_url = settings.database_url
```

---

## Verification Checklist

### Before Commit

- [ ] `src/core/secrets.py` created with SecretManager class
- [ ] `src/core/config.py` updated to use SecretManager
- [ ] `.env.example` created without sensitive data
- [ ] `.env.production.example` created
- [ ] `tests/unit/test_secrets.py` created
- [ ] `src/api/main.py` updated with secrets validation on startup
- [ ] All secret manager tests pass
- [ ] Application starts successfully
- [ ] All existing tests still pass

### After Deployment

- [ ] Application initializes without errors
- [ ] Secrets loaded correctly from environment
- [ ] Config object has all values
- [ ] Database connection works
- [ ] API endpoints respond correctly
- [ ] No secrets exposed in logs
- [ ] Cache clears properly after rotation
- [ ] Performance maintained

---

## Production Vault Setup (Phase 2)

### Environment variables for Vault:

```bash
# Set before application startup
export SECRET_SOURCE=vault
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=s.xxxxxxxxxxxxx
export VAULT_NAMESPACE=faceless-youtube
```

### Vault paths structure:

```
secret/data/development/
  ├── database_url
  ├── youtube_api_key
  ├── anthropic_api_key
  ├── google_client_id
  ├── google_client_secret
  ├── secret_key
  └── encryption_key

secret/data/staging/
  ├── [same structure]

secret/data/production/
  ├── [same structure with production values]
```

---

## File Summary

### New Files Created

1. `src/core/secrets.py` - SecretManager class (300+ lines)
2. `tests/unit/test_secrets.py` - Secrets tests
3. `.env.production.example` - Production config template

### Modified Files

1. `src/core/config.py` - Updated to use SecretManager
2. `src/api/main.py` - Add secrets validation on startup
3. `.env.example` - Remove sensitive data

### No Changes Required

- `src/` other modules - Transparent refactoring
- `requirements.txt` - No new dependencies (hvac optional for Vault)

---

## Rollback Plan

If issues occur:

```bash
# Revert changes
git checkout HEAD -- src/core/secrets.py src/core/config.py src/api/main.py

# Or roll back specific commit
git revert <commit-hash>

# Restart containers
docker-compose -f docker-compose.staging.yml restart api
```

---

## Next Steps After Secrets Management

1. ✅ Create SecretManager class
2. ✅ Update config module
3. ✅ Create environment templates
4. ✅ Update application initialization
5. ✅ Create tests
6. ✅ Verify all functionality
7. ✅ Commit changes to git
8. ⏳ **Phase 1 COMPLETE**: All 4 critical items done
9. ⏳ **Phase 2**: Vault deployment (future)

---

## Timeline

- **SecretManager Creation:** 40 minutes
- **Config Update:** 20 minutes
- **Environment Templates:** 10 minutes
- **Tests Creation:** 20 minutes
- **Application Integration:** 15 minutes
- **Testing & Verification:** 30 minutes
- **Documentation & Commit:** 15 minutes

**Total Expected Time: 150 minutes (2.5 hours)**

---

## References

- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
- [HVAC Python Client](https://hvac.readthedocs.io/)
- [12-Factor App - Config](https://12factor.net/config)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Pydantic Settings](https://docs.pydantic.dev/latest/api/pydantic_settings/)

---

**Status:** Ready for implementation ✅  
**Next Action:** After Items 2 & 3 - Create SecretManager class
