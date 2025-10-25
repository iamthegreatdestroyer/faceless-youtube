"""
Unit tests for secrets management module.

Tests for:
- SecretManager initialization
- Secret retrieval (required/optional)
- Backend operations
- Secret validation
- Error handling
"""

import pytest
import os

from src.core.secrets import (
    SecretManager,
    EnvironmentSecretBackend,
    Secret,
    SecretBackend,
    get_secret_manager,
    initialize_secrets,
)


class TestEnvironmentSecretBackend:
    """Test EnvironmentSecretBackend."""

    def test_backend_init(self):
        """Test backend initialization."""
        backend = EnvironmentSecretBackend()
        assert backend.available is True
        assert backend.backend_type == "environment"

    def test_get_existing_secret(self):
        """Test retrieving existing secret."""
        backend = EnvironmentSecretBackend()
        os.environ["TEST_SECRET"] = "secret_value"

        try:
            value = backend.get("TEST_SECRET")
            assert value == "secret_value"
        finally:
            del os.environ["TEST_SECRET"]

    def test_get_missing_secret_with_default(self):
        """Test retrieving missing secret with default."""
        backend = EnvironmentSecretBackend()
        value = backend.get("NONEXISTENT_SECRET", default="default_value")
        assert value == "default_value"

    def test_get_missing_secret_without_default(self):
        """Test retrieving missing secret without default."""
        backend = EnvironmentSecretBackend()
        value = backend.get("NONEXISTENT_SECRET")
        assert value is None

    def test_set_secret(self):
        """Test setting a secret."""
        backend = EnvironmentSecretBackend()
        result = backend.set("NEW_SECRET", "new_value")

        try:
            assert result is True
            assert os.environ["NEW_SECRET"] == "new_value"
        finally:
            del os.environ["NEW_SECRET"]

    def test_delete_secret(self):
        """Test deleting a secret."""
        backend = EnvironmentSecretBackend()
        os.environ["DELETE_ME"] = "value"

        result = backend.delete("DELETE_ME")
        assert result is True
        assert "DELETE_ME" not in os.environ

    def test_delete_nonexistent_secret(self):
        """Test deleting nonexistent secret (should still return True)."""
        backend = EnvironmentSecretBackend()
        result = backend.delete("NONEXISTENT")
        assert result is True

    def test_list_keys(self):
        """Test listing secret keys."""
        backend = EnvironmentSecretBackend()
        os.environ["API_KEY_1"] = "value1"
        os.environ["SECRET_TOKEN"] = "value2"
        os.environ["REGULAR_VAR"] = "value3"

        try:
            keys = backend.list_keys()
            # Should include our secret keys
            assert "API_KEY_1" in keys
            assert "SECRET_TOKEN" in keys
        finally:
            del os.environ["API_KEY_1"]
            del os.environ["SECRET_TOKEN"]
            del os.environ["REGULAR_VAR"]


class TestSecretManager:
    """Test SecretManager."""

    @pytest.fixture
    def manager(self):
        """Create a SecretManager for testing."""
        return SecretManager(backends=[SecretBackend.ENVIRONMENT])

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert len(manager.backends) >= 1
        assert manager.backends[0].available is True

    def test_get_required_secret_found(self, manager):
        """Test getting required secret that exists."""
        os.environ["REQUIRED_SECRET"] = "secret_value"

        try:
            value = manager.get_required("REQUIRED_SECRET")
            assert value == "secret_value"
        finally:
            del os.environ["REQUIRED_SECRET"]

    def test_get_required_secret_not_found(self, manager):
        """Test getting required secret that doesn't exist."""
        with pytest.raises(ValueError, match="Required secret not found"):
            manager.get_required("NONEXISTENT_REQUIRED_SECRET")

    def test_get_optional_secret_found(self, manager):
        """Test getting optional secret that exists."""
        os.environ["OPTIONAL_SECRET"] = "secret_value"

        try:
            value = manager.get_optional("OPTIONAL_SECRET")
            assert value == "secret_value"
        finally:
            del os.environ["OPTIONAL_SECRET"]

    def test_get_optional_secret_not_found_with_default(self, manager):
        """Test getting optional secret with default."""
        value = manager.get_optional("NONEXISTENT", default="default_value")
        assert value == "default_value"

    def test_get_optional_secret_not_found_without_default(self, manager):
        """Test getting optional secret without default."""
        value = manager.get_optional("NONEXISTENT")
        assert value is None

    def test_set_secret(self, manager):
        """Test setting a secret."""
        result = manager.set_secret("NEW_SECRET", "new_value")

        try:
            assert result is True
            value = manager.get_optional("NEW_SECRET")
            assert value == "new_value"
        finally:
            if "NEW_SECRET" in os.environ:
                del os.environ["NEW_SECRET"]

    def test_delete_secret(self, manager):
        """Test deleting a secret."""
        os.environ["DELETE_ME"] = "value"

        result = manager.delete_secret("DELETE_ME")
        assert result is True

    def test_validate_required_secrets_all_present(self, manager):
        """Test validation when all required secrets present."""
        os.environ["SECRET_1"] = "value1"
        os.environ["SECRET_2"] = "value2"

        try:
            result = manager.validate_required_secrets(
                ["SECRET_1", "SECRET_2"]
            )
            assert result is True
        finally:
            del os.environ["SECRET_1"]
            del os.environ["SECRET_2"]

    def test_validate_required_secrets_missing(self, manager):
        """Test validation when required secrets missing."""
        with pytest.raises(ValueError, match="Missing required secrets"):
            manager.validate_required_secrets(
                ["NONEXISTENT_1", "NONEXISTENT_2"]
            )

    def test_health_check(self, manager):
        """Test health check functionality."""
        health = manager.health_check()

        assert "status" in health
        assert health["status"] in ("healthy", "unhealthy")
        assert "backends" in health
        assert len(health["backends"]) >= 1


class TestSecretModel:
    """Test Secret dataclass."""

    def test_secret_creation(self):
        """Test creating a Secret."""
        secret = Secret(
            key="API_KEY",
            value="secret_value",
            backend=SecretBackend.ENVIRONMENT,
        )

        assert secret.key == "API_KEY"
        assert secret.value == "secret_value"
        assert secret.backend == SecretBackend.ENVIRONMENT

    def test_secret_repr_safe(self):
        """Test that secret repr doesn't expose value."""
        secret = Secret(
            key="API_KEY",
            value="super_secret_value",
            backend=SecretBackend.ENVIRONMENT,
        )

        repr_str = repr(secret)
        assert "API_KEY" in repr_str
        assert "super_secret_value" not in repr_str


@pytest.mark.integration
class TestSecretManagerIntegration:
    """Integration tests for SecretManager."""

    def test_singleton_pattern(self):
        """Test that get_secret_manager returns same instance."""
        manager1 = get_secret_manager()
        manager2 = get_secret_manager()

        assert manager1 is manager2

    def test_initialize_secrets_custom_backends(self):
        """Test initializing with custom backends."""
        manager = initialize_secrets(backends=[SecretBackend.ENVIRONMENT])

        assert len(manager.backends) >= 1
        assert manager.backends[0].available is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
