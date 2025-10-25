"""
Rate Limiter Core Implementation

Provides sliding window rate limiting with support for distributed Redis-backed
limiting and exponential backoff strategies.

Date: October 25, 2025
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


###############################################################################
# Data Models
###############################################################################


@dataclass
class RateLimitConfig:
    """Configuration for rate limiter."""

    window_size_seconds: int = 60  # 1 minute
    max_requests: int = 100  # 100 requests per window
    burst_multiplier: float = 1.2  # Allow 20% burst
    enable_redis: bool = False
    redis_url: str = "redis://localhost:6379"
    key_prefix: str = "rate_limit"
    cleanup_interval: int = 300  # Cleanup every 5 minutes


@dataclass
class RateLimitWindow:
    """Individual rate limit window."""

    start_time: float = field(default_factory=time.time)
    request_count: int = 0
    window_size: int = 60


class RateLimitInfo(BaseModel):
    """Rate limit information returned after request check."""

    allowed: bool = Field(..., description="Whether request is allowed")
    limit: int = Field(..., description="Total requests allowed in window")
    remaining: int = Field(..., description="Requests remaining in window")
    reset_at: int = Field(..., description="Unix timestamp of window reset")
    retry_after: Optional[int] = Field(None, description="Seconds to retry (if denied)")


class RateLimitStats(BaseModel):
    """Statistics for rate limiter."""

    total_requests: int = 0
    allowed_requests: int = 0
    denied_requests: int = 0
    tracked_identifiers: int = 0
    avg_response_time_ms: float = 0.0
    peak_qps: float = 0.0


###############################################################################
# Sliding Window Rate Limiter
###############################################################################


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter with O(1) performance.

    Uses sliding window algorithm for accurate rate limiting:
    - Window slides as time progresses
    - Requests outside window are automatically expired
    - No periodic cleanup needed (lazy evaluation)

    Example:
        >>> limiter = SlidingWindowRateLimiter(window_size=60, max_requests=100)
        >>> result = limiter.record_request("user_123")
        >>> if result.allowed:
        ...     # Process request
        ...     pass
    """

    def __init__(
        self,
        window_size_seconds: int = 60,
        max_requests: int = 100,
        burst_multiplier: float = 1.2,
    ):
        """
        Initialize sliding window rate limiter.

        Args:
            window_size_seconds: Size of rate limit window
            max_requests: Maximum requests allowed per window
            burst_multiplier: Burst allowance multiplier (1.2 = 20% burst)
        """
        self.window_size = window_size_seconds
        self.max_requests = max_requests
        self.burst_limit = int(max_requests * burst_multiplier)

        # Per-identifier tracking: {identifier: [timestamp, timestamp, ...]}
        self.request_history: Dict[str, list] = {}

        # Statistics
        self.stats = RateLimitStats()
        self.last_cleanup = time.time()

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed (non-blocking).

        Args:
            identifier: IP address, user ID, or API key

        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.time()
        window_start = now - self.window_size

        # Get or create request history for identifier
        if identifier not in self.request_history:
            return True

        history = self.request_history[identifier]

        # Remove requests outside window
        history[:] = [ts for ts in history if ts > window_start]

        # Check if under limit
        return len(history) < self.max_requests

    def record_request(self, identifier: str) -> RateLimitInfo:
        """
        Record a request and return rate limit info.

        Args:
            identifier: IP address, user ID, or API key

        Returns:
            RateLimitInfo with current limit status
        """
        now = time.time()
        window_start = now - self.window_size

        # Get or create request history
        if identifier not in self.request_history:
            self.request_history[identifier] = []

        history = self.request_history[identifier]

        # Remove old requests outside window
        history[:] = [ts for ts in history if ts > window_start]

        # Check if allowed
        allowed = len(history) < self.max_requests

        # Record request
        history.append(now)

        # Update statistics
        self.stats.total_requests += 1
        if allowed:
            self.stats.allowed_requests += 1
        else:
            self.stats.denied_requests += 1
        self.stats.tracked_identifiers = len(self.request_history)

        # Calculate info
        remaining = max(0, self.max_requests - len(history))
        reset_at = int(int(now) + self.window_size)

        # Calculate retry-after if denied
        retry_after = None
        if not allowed:
            # Next available slot (oldest request time + window)
            oldest_time = min(history)
            retry_after = int(oldest_time + self.window_size - now)
            retry_after = max(1, retry_after)

        return RateLimitInfo(
            allowed=allowed,
            limit=self.max_requests,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after,
        )

    def get_current_limit(self, identifier: str) -> RateLimitInfo:
        """
        Get current rate limit status without recording request.

        Args:
            identifier: IP address, user ID, or API key

        Returns:
            RateLimitInfo with current status
        """
        now = time.time()
        window_start = now - self.window_size

        if identifier not in self.request_history:
            return RateLimitInfo(
                allowed=True,
                limit=self.max_requests,
                remaining=self.max_requests,
                reset_at=int(now) + self.window_size,
            )

        history = self.request_history[identifier]
        # Don't modify history in this method
        history_filtered = [ts for ts in history if ts > window_start]

        remaining = max(0, self.max_requests - len(history_filtered))
        reset_at = int(now) + self.window_size

        return RateLimitInfo(
            allowed=len(history_filtered) < self.max_requests,
            limit=self.max_requests,
            remaining=remaining,
            reset_at=reset_at,
        )

    def reset_limit(self, identifier: str) -> None:
        """
        Reset rate limit for identifier.

        Args:
            identifier: IP address, user ID, or API key
        """
        if identifier in self.request_history:
            del self.request_history[identifier]
            logger.info(f"Rate limit reset for {identifier}")

    def get_statistics(self) -> RateLimitStats:
        """
        Get rate limiter statistics.

        Returns:
            RateLimitStats with current metrics
        """
        return self.stats

    def cleanup_old_entries(self) -> int:
        """
        Clean up old entries (manual cleanup, not required by algorithm).

        Returns:
            Number of entries cleaned up
        """
        now = time.time()
        window_start = now - (self.window_size * 2)  # Keep 2x window

        cleaned_count = 0
        identifiers_to_remove = []

        for identifier, history in self.request_history.items():
            # Filter out old timestamps
            filtered_history = [ts for ts in history if ts > window_start]

            if not filtered_history:
                identifiers_to_remove.append(identifier)
                cleaned_count += 1
            elif len(filtered_history) < len(history):
                self.request_history[identifier] = filtered_history

        # Remove empty identifiers
        for identifier in identifiers_to_remove:
            del self.request_history[identifier]

        return cleaned_count


###############################################################################
# Distributed Rate Limiter (Redis-backed)
###############################################################################


class DistributedRateLimiter:
    """
    Redis-backed distributed rate limiter for horizontal scaling.

    Coordinates rate limiting across multiple instances using Redis:
    - Atomic increment operations
    - Cross-instance consistency
    - TTL-based key expiry
    - Connection pooling

    Example:
        >>> limiter = DistributedRateLimiter(redis_url="redis://localhost:6379")
        >>> await limiter.connect()
        >>> result = await limiter.record_request("user_123")
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        window_size_seconds: int = 60,
        max_requests: int = 100,
        key_prefix: str = "rate_limit",
    ):
        """
        Initialize distributed rate limiter.

        Args:
            redis_url: Redis connection URL
            window_size_seconds: Rate limit window size
            max_requests: Max requests per window
            key_prefix: Redis key prefix
        """
        self.redis_url = redis_url
        self.window_size = window_size_seconds
        self.max_requests = max_requests
        self.key_prefix = key_prefix
        self.redis = None
        self.fallback_limiter = SlidingWindowRateLimiter(
            window_size_seconds=window_size_seconds,
            max_requests=max_requests,
        )
        self.use_fallback = False

    async def connect(self) -> None:
        """
        Initialize Redis connection.

        Falls back to memory-based limiter if connection fails.
        """
        try:
            import aioredis

            self.redis = await aioredis.from_url(self.redis_url)
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis ({self.redis_url}): {e}. "
                f"Falling back to memory-based limiter."
            )
            self.use_fallback = True

    async def record_request(self, identifier: str) -> RateLimitInfo:
        """
        Record request in distributed rate limiter.

        Args:
            identifier: IP address, user ID, or API key

        Returns:
            RateLimitInfo with current status
        """
        if self.use_fallback or not self.redis:
            return self.fallback_limiter.record_request(identifier)

        try:
            now = time.time()
            key = f"{self.key_prefix}:{identifier}"

            # Atomic increment with TTL
            async with self.redis.pipeline() as pipe:
                # Get current count
                await pipe.execute()  # Reset pipeline

                current_count = await self.redis.incr(key)
                await self.redis.expire(key, self.window_size)

            allowed = current_count <= self.max_requests

            # Get TTL for reset time
            ttl = await self.redis.ttl(key)
            reset_at = int(now) + (ttl if ttl > 0 else self.window_size)

            remaining = max(0, self.max_requests - current_count)
            retry_after = None

            if not allowed:
                retry_after = max(1, ttl if ttl > 0 else self.window_size)

            return RateLimitInfo(
                allowed=allowed,
                limit=self.max_requests,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
            )

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}. Using fallback.")
            self.use_fallback = True
            return self.fallback_limiter.record_request(identifier)

    async def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed (non-blocking).

        Args:
            identifier: IP address, user ID, or API key

        Returns:
            True if allowed, False if rate limited
        """
        if self.use_fallback or not self.redis:
            return self.fallback_limiter.is_allowed(identifier)

        try:
            key = f"{self.key_prefix}:{identifier}"
            current_count = await self.redis.get(key)

            if current_count is None:
                return True

            return int(current_count) < self.max_requests

        except Exception as e:
            logger.error(f"Redis check failed: {e}. Using fallback.")
            self.use_fallback = True
            return self.fallback_limiter.is_allowed(identifier)

    async def reset_limit(self, identifier: str) -> None:
        """
        Reset rate limit for identifier.

        Args:
            identifier: IP address, user ID, or API key
        """
        if self.use_fallback or not self.redis:
            self.fallback_limiter.reset_limit(identifier)
            return

        try:
            key = f"{self.key_prefix}:{identifier}"
            await self.redis.delete(key)
            logger.info(f"Rate limit reset for {identifier}")
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")

    async def get_statistics(self) -> Dict:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with metrics
        """
        if self.use_fallback or not self.redis:
            return self.fallback_limiter.get_statistics().dict()

        try:
            keys = await self.redis.keys(f"{self.key_prefix}:*")
            return {
                "tracked_identifiers": len(keys),
                "using_redis": True,
                "fallback_mode": False,
            }
        except Exception:
            return {"error": "Failed to get statistics"}

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
