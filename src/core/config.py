"""
Application Configuration

Handles all application configuration from environment variables.
Secrets are managed through SecretManager for enhanced security.

Design:
- Non-secret config (debug, log level, environment) from environment
- Secrets (API keys, database passwords) from SecretManager
- Validation on startup to catch missing required configuration
- Safe defaults for non-critical settings
"""

import os
import logging
from typing import Optional, List
from dataclasses import dataclass

from src.core.secrets import (
    get_secret_manager,
    SecretBackend,
    initialize_secrets,
)

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load database config from environment."""
        secrets = get_secret_manager()

        url = secrets.get_required("DATABASE_URL")

        echo = int(os.getenv("DB_ECHO", "0")) == 1
        pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))

        return cls(
            url=url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
        )


@dataclass
class RedisConfig:
    """Redis configuration."""

    url: str
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Load Redis config from environment."""
        secrets = get_secret_manager()

        url = secrets.get_required("REDIS_URL")
        socket_timeout = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
        socket_connect_timeout = int(
            os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5")
        )

        return cls(
            url=url,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
        )


@dataclass
class MongoDBConfig:
    """MongoDB configuration."""

    uri: str
    database: str = "faceless_youtube"

    @classmethod
    def from_env(cls) -> "MongoDBConfig":
        """Load MongoDB config from environment."""
        secrets = get_secret_manager()

        uri = secrets.get_required("MONGODB_URI")
        database = os.getenv("MONGODB_DATABASE", "faceless_youtube")

        return cls(uri=uri, database=database)


@dataclass
class APIConfig:
    """API configuration."""

    title: str = "Faceless YouTube API"
    description: str = "REST API for automated content creation"
    version: str = "2.0.0"
    debug: bool = False
    cors_origins: Optional[List[str]] = None
    allowed_hosts: Optional[List[str]] = None
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load API config from environment."""
        debug = os.getenv("DEBUG", "false").lower() == "true"
        log_level = os.getenv("LOG_LEVEL", "INFO")

        cors_origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,"
            "http://127.0.0.1:3000",
        ).split(",")

        allowed_hosts = os.getenv(
            "ALLOWED_HOSTS",
            "localhost,127.0.0.1,*.localhost",
        ).split(",")

        return cls(
            debug=debug,
            log_level=log_level,
            cors_origins=[h.strip() for h in cors_origins],
            allowed_hosts=[h.strip() for h in allowed_hosts],
        )


@dataclass
class AuthConfig:
    """Authentication configuration."""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Load auth config from environment."""
        secrets = get_secret_manager()

        secret_key = secrets.get_required("SECRET_KEY")
        algorithm = os.getenv("AUTH_ALGORITHM", "HS256")
        access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )

        return cls(
            secret_key=secret_key,
            algorithm=algorithm,
            access_token_expire_minutes=access_token_expire_minutes,
        )


@dataclass
class AIConfig:
    """AI/ML configuration."""

    claude_api_key: str
    openai_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    @classmethod
    def from_env(cls) -> "AIConfig":
        """Load AI config from environment."""
        secrets = get_secret_manager()

        claude_api_key = secrets.get_required("ANTHROPIC_API_KEY")
        openai_api_key = secrets.get_optional("OPENAI_API_KEY")
        anthropic_model = os.getenv(
            "ANTHROPIC_MODEL",
            "claude-3-5-sonnet-20241022",
        )

        return cls(
            claude_api_key=claude_api_key,
            openai_api_key=openai_api_key,
            anthropic_model=anthropic_model,
        )


class Config:
    """
    Central configuration management.

    Loads all configuration from environment and secrets.
    Validates required configuration on initialization.
    """

    def __init__(self):
        """Initialize configuration."""
        # Initialize secret manager first
        self.secrets = get_secret_manager()

        # Load all sub-configs
        self.database = DatabaseConfig.from_env()
        self.redis = RedisConfig.from_env()
        self.mongodb = MongoDBConfig.from_env()
        self.api = APIConfig.from_env()
        self.auth = AuthConfig.from_env()
        self.ai = AIConfig.from_env()

        # Environment info
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = self.api.debug
        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

        logger.info(
            f"Configuration loaded for environment: {self.environment}"
        )

    def validate(self) -> bool:
        """
        Validate all required configuration is present.

        Returns:
            True if all configuration is valid

        Raises:
            ValueError: If required configuration is missing
        """
        required_secrets = [
            "DATABASE_URL",
            "REDIS_URL",
            "MONGODB_URI",
            "SECRET_KEY",
            "ANTHROPIC_API_KEY",
        ]

        try:
            self.secrets.validate_required_secrets(required_secrets)
            logger.info("Configuration validation passed")
            return True
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def health_check(self) -> dict:
        """
        Perform configuration health check.

        Returns:
            Health status dictionary
        """
        return {
            "secrets": self.secrets.health_check(),
            "environment": self.environment,
            "debug": self.debug,
            "test_mode": self.test_mode,
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance

    Raises:
        RuntimeError: If configuration not initialized
    """
    global _config

    if _config is None:
        raise RuntimeError(
            "Configuration not initialized. Call initialize_config() first."
        )

    return _config


def initialize_config(
    secret_backends: Optional[List[SecretBackend]] = None,
) -> Config:
    """
    Initialize the global configuration.

    Args:
        secret_backends: List of secret backends to use

    Returns:
        Initialized Config instance

    Raises:
        ValueError: If required configuration is missing
    """
    global _config

    # Initialize secrets first
    if secret_backends:
        initialize_secrets(backends=secret_backends)

    # Create config instance
    _config = Config()

    # Validate configuration
    _config.validate()

    return _config


# Re-export for convenience
__all__ = [
    "Config",
    "DatabaseConfig",
    "RedisConfig",
    "MongoDBConfig",
    "APIConfig",
    "AuthConfig",
    "AIConfig",
    "get_config",
    "initialize_config",
]
