"""
Per-Endpoint Rate Limiting Configuration

Defines rate limits for specific API endpoints with tier-based customization.

Date: October 25, 2025
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)


###############################################################################
# Enums
###############################################################################


class UserTier(str, Enum):
    """User tier levels."""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    INTERNAL = "internal"  # Internal services, unlimited


class LimitScope(str, Enum):
    """Rate limit scope."""

    GLOBAL = "global"  # All requests combined
    PER_USER = "per_user"  # Per authenticated user
    PER_IP = "per_ip"  # Per IP address
    HYBRID = "hybrid"  # Per user if auth, else per IP


###############################################################################
# Configuration Models
###############################################################################


@dataclass
class EndpointLimit:
    """Rate limit configuration for an endpoint."""

    endpoint: str
    path_pattern: str  # FastAPI path pattern (e.g., "/api/search")
    methods: list = None  # HTTP methods (GET, POST, etc.)

    # Request limits (requests per window)
    free_tier_requests: int = 10
    premium_tier_requests: int = 100
    enterprise_tier_requests: int = 1000

    # Window size
    window_size_seconds: int = 60  # Default 1 minute

    # Burst allowance (multiplier, e.g., 1.2 = 20% burst)
    burst_multiplier: float = 1.2

    # Scope
    scope: LimitScope = LimitScope.PER_IP

    # Exemptions
    exempt_ips: Set[str] = None  # IPs to bypass limit
    exempt_users: Set[str] = None  # User IDs to bypass
    exempt_tokens: Set[str] = None  # API tokens to bypass

    def __post_init__(self):
        """Initialize default values."""
        if self.methods is None:
            self.methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if self.exempt_ips is None:
            self.exempt_ips = {"127.0.0.1", "::1"}  # Localhost
        if self.exempt_users is None:
            self.exempt_users = set()
        if self.exempt_tokens is None:
            self.exempt_tokens = set()

    def get_limit_for_tier(self, tier: UserTier) -> int:
        """Get request limit for user tier."""
        if tier == UserTier.FREE:
            return self.free_tier_requests
        elif tier == UserTier.PREMIUM:
            return self.premium_tier_requests
        elif tier == UserTier.ENTERPRISE:
            return self.enterprise_tier_requests
        else:  # INTERNAL
            return int(1e9)  # Essentially unlimited

    def should_exempt(self, ip: Optional[str] = None, user_id: Optional[str] = None) -> bool:
        """Check if request should be exempted."""
        if ip and ip in self.exempt_ips:
            return True
        if user_id and user_id in self.exempt_users:
            return True
        return False


###############################################################################
# Endpoint Configuration Registry
###############################################################################


class EndpointLimitsConfig:
    """Central registry for all endpoint rate limits."""

    def __init__(self):
        """Initialize endpoint limits."""
        self.limits: Dict[str, EndpointLimit] = {}
        self._setup_default_limits()

    def _setup_default_limits(self) -> None:
        """Set up default limits for all endpoints."""
        limits = [
            # Search endpoint - moderate traffic
            EndpointLimit(
                endpoint="search",
                path_pattern="/api/v1/search",
                methods=["GET", "POST"],
                free_tier_requests=10,
                premium_tier_requests=100,
                enterprise_tier_requests=1000,
                window_size_seconds=60,
                scope=LimitScope.PER_IP,
            ),
            # Upload endpoint - strict limit (expensive operation)
            EndpointLimit(
                endpoint="upload",
                path_pattern="/api/v1/upload",
                methods=["POST"],
                free_tier_requests=5,
                premium_tier_requests=10,
                enterprise_tier_requests=100,
                window_size_seconds=3600,  # 1 hour
                scope=LimitScope.PER_USER,
            ),
            # Export endpoint - moderate limit
            EndpointLimit(
                endpoint="export",
                path_pattern="/api/v1/export",
                methods=["GET", "POST"],
                free_tier_requests=20,
                premium_tier_requests=50,
                enterprise_tier_requests=500,
                window_size_seconds=3600,  # 1 hour
                scope=LimitScope.PER_USER,
            ),
            # User API endpoint - high volume
            EndpointLimit(
                endpoint="users",
                path_pattern="/api/v1/users",
                methods=["GET", "POST", "PUT", "DELETE"],
                free_tier_requests=50,
                premium_tier_requests=200,
                enterprise_tier_requests=2000,
                window_size_seconds=60,
                scope=LimitScope.PER_IP,
            ),
            # Project API endpoint - high volume
            EndpointLimit(
                endpoint="projects",
                path_pattern="/api/v1/projects",
                methods=["GET", "POST", "PUT", "DELETE"],
                free_tier_requests=30,
                premium_tier_requests=150,
                enterprise_tier_requests=1500,
                window_size_seconds=60,
                scope=LimitScope.PER_IP,
            ),
            # Admin API endpoint - internal only, very high limit
            EndpointLimit(
                endpoint="admin",
                path_pattern="/api/v1/admin",
                methods=["GET", "POST", "PUT", "DELETE"],
                free_tier_requests=500,
                premium_tier_requests=5000,
                enterprise_tier_requests=50000,
                window_size_seconds=60,
                scope=LimitScope.GLOBAL,
                exempt_ips={"127.0.0.1", "::1", "localhost"},
            ),
            # Health check endpoint - exempt
            EndpointLimit(
                endpoint="health",
                path_pattern="/health",
                methods=["GET"],
                free_tier_requests=int(1e6),  # Essentially unlimited
                premium_tier_requests=int(1e6),
                enterprise_tier_requests=int(1e6),
                window_size_seconds=1,
                scope=LimitScope.GLOBAL,
                exempt_ips={"0.0.0.0/0"},  # All IPs exempt
            ),
            # Metrics endpoint - exempt
            EndpointLimit(
                endpoint="metrics",
                path_pattern="/metrics",
                methods=["GET"],
                free_tier_requests=int(1e6),
                premium_tier_requests=int(1e6),
                enterprise_tier_requests=int(1e6),
                window_size_seconds=1,
                scope=LimitScope.GLOBAL,
                exempt_ips={"127.0.0.1", "::1"},
            ),
        ]

        for limit in limits:
            self.register_limit(limit)

        logger.info(f"Registered {len(limits)} endpoint rate limits")

    def register_limit(self, limit: EndpointLimit) -> None:
        """
        Register endpoint rate limit.

        Args:
            limit: EndpointLimit configuration
        """
        self.limits[limit.endpoint] = limit
        logger.debug(f"Registered rate limit for {limit.endpoint}: {limit.path_pattern}")

    def get_limit(self, endpoint: str) -> Optional[EndpointLimit]:
        """
        Get rate limit for endpoint.

        Args:
            endpoint: Endpoint name

        Returns:
            EndpointLimit or None if not found
        """
        return self.limits.get(endpoint)

    def get_limit_by_path(self, path: str) -> Optional[Tuple[str, EndpointLimit]]:
        """
        Get rate limit for request path.

        Args:
            path: Request path (e.g., "/api/v1/search")

        Returns:
            Tuple of (endpoint_name, EndpointLimit) or None
        """
        # Simple path matching (can be enhanced with regex if needed)
        for endpoint, limit in self.limits.items():
            if path.startswith(limit.path_pattern):
                return endpoint, limit

        return None

    def get_all_limits(self) -> Dict[str, EndpointLimit]:
        """
        Get all registered limits.

        Returns:
            Dictionary of all limits
        """
        return self.limits.copy()

    def update_limit(self, endpoint: str, **kwargs) -> bool:
        """
        Update endpoint rate limit.

        Args:
            endpoint: Endpoint name
            **kwargs: Fields to update

        Returns:
            True if updated, False if not found
        """
        if endpoint not in self.limits:
            return False

        limit = self.limits[endpoint]
        for key, value in kwargs.items():
            if hasattr(limit, key):
                setattr(limit, key, value)
                logger.info(f"Updated {endpoint}.{key} = {value}")
            else:
                logger.warning(f"Unknown field: {key}")

        return True


# Global configuration instance
ENDPOINT_LIMITS = EndpointLimitsConfig()


# Helper functions
def get_endpoint_limit(endpoint: str) -> Optional[EndpointLimit]:
    """Get limit for endpoint."""
    return ENDPOINT_LIMITS.get_limit(endpoint)


def get_limit_by_path(path: str) -> Optional[EndpointLimit]:
    """Get limit for request path."""
    result = ENDPOINT_LIMITS.get_limit_by_path(path)
    return result[1] if result else None
