"""
Secrets Management Module

Handles secure storage and retrieval of sensitive configuration data.
Provides a pluggable architecture for multiple backend implementations:

- Environment variables (current, simple)
- HashiCorp Vault (production-ready)
- AWS Secrets Manager (AWS deployments)
- Azure Key Vault (Azure deployments)
- Encrypted file storage (fallback)

Design principles:
1. Never log sensitive data
2. Validate all inputs
3. Support hot reloading of secrets
4. Provide clear audit trails
5. Fail secure (reject on error)
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecretBackend(Enum):
    """Available secret storage backends."""

    ENVIRONMENT = "environment"
    VAULT = "vault"
    AWS_SECRETS = "aws_secrets"
    AZURE_KEYVAULT = "azure_keyvault"
    FILE = "file"


@dataclass
class Secret:
    """Represents a secret value with metadata."""

    key: str
    value: str
    backend: SecretBackend
    expires_at: Optional[str] = None
    last_accessed: Optional[str] = None
    access_count: int = 0

    def __repr__(self) -> str:
        """Safe representation without exposing secret value."""
        return f"Secret(key='{self.key}', backend={self.backend.value})"


class SecretBackendBase(ABC):
    """Abstract base class for secret backends."""

    def __init__(self):
        self.backend_type = "unknown"
        self.available = False

    @abstractmethod
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value."""
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> bool:
        """Set a secret value."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a secret."""
        pass

    @abstractmethod
    def list_keys(self) -> List[str]:
        """List all secret keys (without values)."""
        pass


class EnvironmentSecretBackend(SecretBackendBase):
    """Backend using environment variables."""

    def __init__(self):
        super().__init__()
        self.backend_type = "environment"
        self.available = True
        logger.debug("EnvironmentSecretBackend initialized")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from environment variable."""
        value = os.getenv(key, default)
        if value is not None:
            logger.debug(f"Secret retrieved from environment: {key}")
        return value

    def set(self, key: str, value: str) -> bool:
        """Set secret in environment (runtime only, not persistent)."""
        try:
            os.environ[key] = value
            logger.debug(f"Secret set in environment: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret in environment: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete secret from environment."""
        try:
            if key in os.environ:
                del os.environ[key]
                logger.debug(f"Secret deleted from environment: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from environment: {e}")
            return False

    def list_keys(self) -> List[str]:
        """List all environment variable keys (not recommended for production)."""
        # Only list keys that look like secrets (start with known prefixes)
        secret_prefixes = ("API_", "DB_", "SECRET_", "TOKEN_", "KEY_")
        keys = [
            k
            for k in os.environ.keys()
            if any(k.startswith(prefix) for prefix in secret_prefixes)
        ]
        logger.debug(f"Listed {len(keys)} secret keys from environment")
        return keys


class VaultSecretBackend(SecretBackendBase):
    """Backend using HashiCorp Vault (production-ready)."""

    def __init__(self, vault_addr: str = "http://localhost:8200", token: Optional[str] = None):
        super().__init__()
        self.backend_type = "vault"
        self.vault_addr = vault_addr
        self.token = token
        self.available = False

        try:
            import hvac

            self.client = hvac.Client(url=vault_addr, token=token)
            if self.client.is_authenticated():
                self.available = True
                logger.info(f"VaultSecretBackend connected to {vault_addr}")
            else:
                logger.warning("VaultSecretBackend authentication failed")
        except ImportError:
            logger.warning("hvac library not installed - VaultSecretBackend unavailable")
        except Exception as e:
            logger.warning(f"VaultSecretBackend initialization failed: {e}")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from Vault."""
        if not self.available:
            logger.warning("VaultSecretBackend not available")
            return default

        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=key)
            value = response["data"]["data"]["value"]
            logger.debug(f"Secret retrieved from Vault: {key}")
            return value
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault: {e}")
            return default

    def set(self, key: str, value: str) -> bool:
        """Set secret in Vault."""
        if not self.available:
            logger.warning("VaultSecretBackend not available")
            return False

        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=key, secret_data={"value": value}
            )
            logger.debug(f"Secret stored in Vault: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret in Vault: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete secret from Vault."""
        if not self.available:
            logger.warning("VaultSecretBackend not available")
            return False

        try:
            self.client.secrets.kv.v2.delete_secret_version(path=key)
            logger.debug(f"Secret deleted from Vault: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from Vault: {e}")
            return False

    def list_keys(self) -> List[str]:
        """List secret keys in Vault."""
        if not self.available:
            return []

        try:
            response = self.client.secrets.kv.v2.list_secrets(path="")
            keys = response.get("data", {}).get("keys", [])
            logger.debug(f"Listed {len(keys)} secret keys from Vault")
            return keys
        except Exception as e:
            logger.error(f"Failed to list secrets in Vault: {e}")
            return []


class SecretManager:
    """
    High-level secrets management interface.

    Provides:
    - Pluggable backend system
    - Fallback chain for availability
    - Validation of secret requirements
    - Audit logging
    - Type-safe retrieval

    Usage:
        manager = SecretManager()
        api_key = manager.get_required("API_KEY")
        optional_value = manager.get_optional("OPTIONAL_VAR", default="default")
    """

    def __init__(self, backends: Optional[List[SecretBackend]] = None):
        """
        Initialize SecretManager with specified backends.

        Args:
            backends: List of backends to use (in priority order).
                     Defaults to [ENVIRONMENT, VAULT]
        """
        self.backends: List[SecretBackendBase] = []
        self.backend_instances: Dict[SecretBackend, SecretBackendBase] = {}

        # Default to environment backend (always available)
        if backends is None:
            backends = [SecretBackend.ENVIRONMENT, SecretBackend.VAULT]

        # Initialize backends in order
        for backend_type in backends:
            backend = self._create_backend(backend_type)
            if backend and backend.available:
                self.backends.append(backend)
                self.backend_instances[backend_type] = backend
                logger.info(f"Initialized backend: {backend_type.value}")
            else:
                logger.warning(f"Backend not available: {backend_type.value}")

        if not self.backends:
            raise RuntimeError("No secret backends available - cannot initialize SecretManager")

        logger.info(f"SecretManager initialized with {len(self.backends)} backend(s)")

    @staticmethod
    def _create_backend(backend_type: SecretBackend) -> Optional[SecretBackendBase]:
        """Factory method to create backend instances."""
        try:
            if backend_type == SecretBackend.ENVIRONMENT:
                return EnvironmentSecretBackend()
            elif backend_type == SecretBackend.VAULT:
                vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
                vault_token = os.getenv("VAULT_TOKEN")
                return VaultSecretBackend(vault_addr=vault_addr, token=vault_token)
            else:
                logger.warning(f"Backend not implemented: {backend_type.value}")
                return None
        except Exception as e:
            logger.error(f"Failed to create backend {backend_type.value}: {e}")
            return None

    def get_required(self, key: str) -> str:
        """
        Get a required secret. Raises ValueError if not found.

        Args:
            key: Secret key name

        Returns:
            Secret value

        Raises:
            ValueError: If secret not found in any backend
        """
        for backend in self.backends:
            value = backend.get(key)
            if value is not None:
                logger.debug(f"Retrieved required secret: {key}")
                return value

        error_msg = f"Required secret not found: {key}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    def get_optional(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an optional secret. Returns default if not found.

        Args:
            key: Secret key name
            default: Default value if not found

        Returns:
            Secret value or default
        """
        for backend in self.backends:
            value = backend.get(key)
            if value is not None:
                logger.debug(f"Retrieved optional secret: {key}")
                return value

        logger.debug(f"Optional secret not found, using default: {key}")
        return default

    def set_secret(self, key: str, value: str) -> bool:
        """
        Set a secret in the first available backend.

        Args:
            key: Secret key name
            value: Secret value

        Returns:
            True if successful, False otherwise
        """
        if not self.backends:
            logger.error("No backends available for setting secrets")
            return False

        backend = self.backends[0]  # Use first (primary) backend
        result = backend.set(key, value)
        if result:
            logger.info(f"Secret stored in {backend.backend_type} backend: {key}")
        else:
            logger.error(f"Failed to store secret in {backend.backend_type} backend: {key}")
        return result

    def delete_secret(self, key: str) -> bool:
        """
        Delete a secret from all backends.

        Args:
            key: Secret key name

        Returns:
            True if deleted from at least one backend
        """
        deleted = False
        for backend in self.backends:
            if backend.delete(key):
                deleted = True

        if deleted:
            logger.info(f"Secret deleted: {key}")
        else:
            logger.warning(f"Secret not found for deletion: {key}")

        return deleted

    def validate_required_secrets(self, required_keys: List[str]) -> bool:
        """
        Validate that all required secrets are available.

        Args:
            required_keys: List of required secret keys

        Returns:
            True if all secrets are available

        Raises:
            ValueError: If any required secret is missing
        """
        missing = []

        for key in required_keys:
            try:
                self.get_required(key)
            except ValueError:
                missing.append(key)

        if missing:
            error_msg = f"Missing required secrets: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"All {len(required_keys)} required secrets validated")
        return True

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all backends.

        Returns:
            Dictionary with health status for each backend
        """
        health = {
            "status": "healthy" if self.backends else "unhealthy",
            "backends": {},
        }

        for backend in self.backends:
            try:
                # Try to list keys as a health check
                keys = backend.list_keys()
                health["backends"][backend.backend_type] = {
                    "available": True,
                    "accessible_keys": len(keys),
                }
            except Exception as e:
                health["backends"][backend.backend_type] = {
                    "available": False,
                    "error": str(e),
                }

        return health


# Global singleton instance
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """
    Get or create the global SecretManager singleton.

    Returns:
        SecretManager instance
    """
    global _secret_manager

    if _secret_manager is None:
        _secret_manager = SecretManager()

    return _secret_manager


def initialize_secrets(backends: Optional[List[SecretBackend]] = None) -> SecretManager:
    """
    Initialize the global SecretManager with custom backends.

    Args:
        backends: List of backends to use

    Returns:
        Initialized SecretManager instance
    """
    global _secret_manager

    _secret_manager = SecretManager(backends=backends)
    return _secret_manager
