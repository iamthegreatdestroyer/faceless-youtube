"""
FastAPI Middleware for Rate Limiting

Provides middleware for integrating rate limiting into FastAPI applications.
Handles:
- Request identification (IP, user ID, API token)
- Rate limit checking and enforcement
- Response headers (RateLimit-Limit, RateLimit-Remaining, Retry-After)
- 429 Too Many Requests responses
- Monitoring and logging

Date: October 25, 2025
"""

import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.security.rate_limiter import (
    SlidingWindowRateLimiter,
    DistributedRateLimiter,
)
from src.security.endpoint_limits import (
    EndpointLimitsConfig,
    UserTier,
    LimitScope,
)
from src.security.backoff_strategy import BackoffFactory, BackoffConfig


logger = logging.getLogger(__name__)


###############################################################################
# Request Identifier
###############################################################################


class RequestIdentifier:
    """Extract and identify request source for rate limiting."""

    def __init__(self, endpoint_limits_config: EndpointLimitsConfig):
        """Initialize identifier with config."""
        self.config = endpoint_limits_config

    def get_identifier(
        self, request: Request, endpoint: str
    ) -> tuple[str, UserTier]:
        """
        Extract identifier and tier from request.

        Args:
            request: FastAPI Request object
            endpoint: Endpoint name (e.g., "search")

        Returns:
            Tuple of (identifier, user_tier)
            Identifier format depends on LimitScope:
            - GLOBAL: "global"
            - PER_IP: "ip:192.168.1.1"
            - PER_USER: "user:123" (if authenticated)
            - HYBRID: "user:123" or "ip:192.168.1.1"

        Example:
            >>> identifier, tier = get_identifier(request, "search")
            >>> print(identifier)
            'user:12345'
            >>> print(tier)
            <UserTier.PREMIUM: 'premium'>
        """
        # Get endpoint limit
        limit = self.config.get_limit(endpoint)
        if not limit:
            # Default to global limit if not found
            return "global", UserTier.FREE

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Get user info from request (if available)
        user_id = self._get_user_id(request)
        user_tier = self._get_user_tier(request)

        # Generate identifier based on scope
        identifier = self._generate_identifier(
            limit.scope, user_id, client_ip
        )

        return identifier, user_tier

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For (for proxies)
        if "X-Forwarded-For" in request.headers:
            return request.headers["X-Forwarded-For"].split(",")[0].strip()

        # Check X-Real-IP
        if "X-Real-IP" in request.headers:
            return request.headers["X-Real-IP"]

        # Fall back to client connection
        if request.client:
            return request.client.host

        return "0.0.0.0"

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        # Check authorization header
        if "Authorization" in request.headers:
            auth = request.headers["Authorization"]
            if auth.startswith("Bearer "):
                return auth[7:]  # Extract token

        # Check user_id in scope (if set by auth middleware)
        if hasattr(request.state, "user_id"):
            return str(request.state.user_id)

        return None

    def _get_user_tier(self, request: Request) -> UserTier:
        """Extract user tier from request."""
        # Check user tier in scope (if set by auth middleware)
        if hasattr(request.state, "user_tier"):
            tier_str = str(request.state.user_tier).lower()
            try:
                return UserTier[tier_str.upper()]
            except KeyError:
                pass

        # Check for premium status header
        if "X-User-Tier" in request.headers:
            tier_str = request.headers["X-User-Tier"].upper()
            try:
                return UserTier[tier_str]
            except KeyError:
                pass

        return UserTier.FREE

    def _generate_identifier(
        self, scope: LimitScope, user_id: Optional[str], ip: str
    ) -> str:
        """Generate identifier based on scope."""
        if scope == LimitScope.GLOBAL:
            return "global"
        elif scope == LimitScope.PER_USER:
            return f"user:{user_id}" if user_id else f"ip:{ip}"
        elif scope == LimitScope.PER_IP:
            return f"ip:{ip}"
        elif scope == LimitScope.HYBRID:
            # Use user ID if available, fall back to IP
            if user_id:
                return f"user:{user_id}"
            else:
                return f"ip:{ip}"
        else:
            return "global"


###############################################################################
# Rate Limit Middleware
###############################################################################


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Integrates rate limiting into request processing pipeline.
    - Checks rate limits before processing request
    - Adds rate limit headers to response
    - Returns 429 if rate limited
    - Logs rate limit violations
    """

    def __init__(
        self,
        app,
        rate_limiter: Optional[SlidingWindowRateLimiter] = None,
        distributed_limiter: Optional[DistributedRateLimiter] = None,
        endpoint_limits: Optional[EndpointLimitsConfig] = None,
        backoff_config: Optional[BackoffConfig] = None,
        enabled: bool = True,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            rate_limiter: SlidingWindowRateLimiter instance
            distributed_limiter: DistributedRateLimiter for distributed setup
            endpoint_limits: EndpointLimitsConfig with endpoint definitions
            backoff_config: BackoffConfig for Retry-After calculation
            enabled: Whether middleware is enabled (default: True)
        """
        super().__init__(app)

        self.enabled = enabled
        self.endpoint_limits = endpoint_limits or EndpointLimitsConfig()

        # Use distributed limiter if available, else memory-based
        if distributed_limiter:
            self.limiter = distributed_limiter
        else:
            self.limiter = rate_limiter or SlidingWindowRateLimiter(
                window_size_seconds=60, max_requests=1000
            )

        # Create backoff strategy for Retry-After header
        self.backoff_factory = BackoffFactory()
        self.backoff_config = backoff_config or BackoffConfig()

        # Create request identifier
        self.identifier = RequestIdentifier(self.endpoint_limits)

        # Statistics
        self.total_requests = 0
        self.rate_limited_requests = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response (429 if rate limited, else normal response)
        """
        if not self.enabled:
            return await call_next(request)

        self.total_requests += 1

        # Extract endpoint name from path
        endpoint = self._extract_endpoint(request.url.path)

        # Check if endpoint is exempt
        if self._is_exempt_endpoint(endpoint, request):
            return await call_next(request)

        # Get endpoint limit
        limit = self.endpoint_limits.get_limit(endpoint)
        if not limit:
            return await call_next(request)

        # Get request identifier and user tier
        identifier, user_tier = self.identifier.get_identifier(
            request, endpoint
        )

        # Check exemptions
        client_ip = self.identifier._get_client_ip(request)
        if limit.should_exempt(ip=client_ip):
            return await call_next(request)

        # Get rate limit for user tier
        rate_limit = limit.get_limit_for_tier(user_tier)

        # Check rate limit
        if hasattr(self.limiter, "record_request_async"):
            # Async version
            rate_limit_info = await self.limiter.record_request_async(
                f"{endpoint}:{identifier}", rate_limit
            )
        else:
            # Sync version
            rate_limit_info = self.limiter.record_request(
                f"{endpoint}:{identifier}"
            )

        # Create response with rate limit headers
        response = await call_next(request)

        # Add rate limit headers
        response.headers["RateLimit-Limit"] = str(rate_limit)
        response.headers["RateLimit-Remaining"] = str(
            max(0, rate_limit_info.remaining)
        )
        response.headers["RateLimit-Reset"] = str(
            int(rate_limit_info.reset_at.timestamp())
            if rate_limit_info.reset_at
            else int((datetime.utcnow() + timedelta(seconds=60)).timestamp())
        )

        # Check if rate limited
        if not rate_limit_info.allowed:
            self.rate_limited_requests += 1

            # Get retry-after value
            retry_after = self._get_retry_after(
                user_tier, rate_limit_info
            )
            response.headers["Retry-After"] = str(retry_after)

            # Log violation
            logger.warning(
                f"Rate limit exceeded: {identifier} on {endpoint}, "
                f"tier={user_tier.value}, ip={client_ip}"
            )

            # Return 429 response
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too Many Requests",
                    "error": "rate_limited",
                    "retry_after": retry_after,
                    "limit": rate_limit,
                    "remaining": 0,
                    "reset_at": (
                        rate_limit_info.reset_at.isoformat()
                        if rate_limit_info.reset_at
                        else None
                    ),
                },
                headers={"Retry-After": str(retry_after)},
            )

        return response

    def _extract_endpoint(self, path: str) -> str:
        """Extract endpoint name from request path."""
        # Try to match against configured limits
        for limit in self.endpoint_limits.get_all_limits().values():
            if path.startswith(limit.path_pattern.split(":")[0]):
                return limit.endpoint

        # Fall back to first path segment
        parts = path.strip("/").split("/")
        return parts[0] if parts else "unknown"

    def _is_exempt_endpoint(self, endpoint: str, request: Request) -> bool:
        """Check if endpoint is exempt from rate limiting."""
        exempt = ["health", "metrics", "docs", "openapi"]
        return endpoint in exempt

    def _get_retry_after(self, tier: UserTier, info) -> int:
        """Calculate Retry-After value in seconds."""
        if info.retry_after:
            return int(info.retry_after)

        # Default based on tier
        if tier == UserTier.FREE:
            return 60
        elif tier == UserTier.PREMIUM:
            return 30
        else:
            return 10

    def get_statistics(self) -> Dict[str, Any]:
        """Get middleware statistics."""
        return {
            "total_requests": self.total_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "rate_limited_percentage": (
                (self.rate_limited_requests / self.total_requests * 100)
                if self.total_requests > 0
                else 0
            ),
        }


###############################################################################
# Decorator-based Rate Limiting
###############################################################################


def rate_limit(
    max_requests: int,
    window_seconds: int = 60,
    scope: LimitScope = LimitScope.PER_IP,
):
    """
    Decorator for endpoint-level rate limiting.

    Args:
        max_requests: Maximum requests in window
        window_seconds: Time window in seconds
        scope: How to identify request (PER_IP, PER_USER, etc.)

    Example:
        @app.get("/api/search")
        @rate_limit(max_requests=100, window_seconds=60)
        async def search(q: str):
            return {"query": q}
    """

    def decorator(func: Callable) -> Callable:
        # Create limiter for this endpoint
        limiter = SlidingWindowRateLimiter(
            window_size_seconds=window_seconds, max_requests=max_requests
        )

        async def wrapper(*args, request: Request = None, **kwargs) -> Any:
            if not request:
                # Try to extract from kwargs
                request = kwargs.get("request")

            if not request:
                # Can't rate limit without request
                return await func(*args, **kwargs)

            # Get identifier
            identifier = RequestIdentifier(
                EndpointLimitsConfig()
            )._get_client_ip(request)

            # Check rate limit
            info = limiter.record_request(identifier)

            if not info.allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limited",
                        "retry_after": info.retry_after,
                    },
                )

            # Call function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


###############################################################################
# Utility Functions
###############################################################################


async def setup_rate_limiting(
    app,
    redis_url: Optional[str] = None,
    enabled: bool = True,
) -> RateLimitMiddleware:
    """
    Setup rate limiting middleware for FastAPI app.

    Args:
        app: FastAPI application
        redis_url: Redis connection URL (for distributed mode)
        enabled: Whether to enable rate limiting

    Returns:
        Configured RateLimitMiddleware instance

    Example:
        from fastapi import FastAPI
        app = FastAPI()

        middleware = await setup_rate_limiting(
            app,
            redis_url="redis://localhost:6379",
            enabled=True
        )
    """
    # Create limiter
    if redis_url:
        limiter = DistributedRateLimiter(redis_url=redis_url)
        await limiter.connect()
    else:
        limiter = SlidingWindowRateLimiter()

    # Create middleware
    middleware = RateLimitMiddleware(
        app, rate_limiter=limiter, enabled=enabled
    )

    # Add to app
    app.add_middleware(RateLimitMiddleware, limiter=limiter)

    logger.info("Rate limiting middleware configured and enabled")

    return middleware
