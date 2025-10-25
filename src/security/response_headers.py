"""
Rate Limit Response Headers

Utilities for generating standard rate limit response headers.

Headers:
- RateLimit-Limit: Maximum requests in window
- RateLimit-Remaining: Requests remaining in current window
- RateLimit-Reset: Unix timestamp when limit resets
- Retry-After: Seconds to wait before retrying (for 429 responses)

Standards:
- RFC 6585 (HTTP 429)
- IETF Draft: RateLimit Header Fields for HTTP

Date: October 25, 2025
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class RateLimitHeaders:
    """Rate limit headers for response."""

    limit: int
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert to response headers dict."""
        headers = {
            "RateLimit-Limit": str(self.limit),
            "RateLimit-Remaining": str(max(0, self.remaining)),
            "RateLimit-Reset": str(int(self.reset_at.timestamp())),
        }

        if self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)

        return headers


class HeaderGenerator:
    """Generate rate limit response headers."""

    @staticmethod
    def from_rate_limit_info(
        rate_limit_info, tier_name: str = "standard"
    ) -> RateLimitHeaders:
        """
        Create headers from rate limit info.

        Args:
            rate_limit_info: RateLimitInfo from limiter
            tier_name: User tier name for logging

        Returns:
            RateLimitHeaders with all fields populated
        """
        # Calculate retry-after if rate limited
        retry_after = None
        if not rate_limit_info.allowed:
            retry_after = HeaderGenerator._calculate_retry_after(
                rate_limit_info.reset_at, tier_name
            )

        return RateLimitHeaders(
            limit=rate_limit_info.limit,
            remaining=rate_limit_info.remaining,
            reset_at=rate_limit_info.reset_at,
            retry_after=retry_after,
        )

    @staticmethod
    def _calculate_retry_after(reset_at: datetime, tier: str) -> int:
        """
        Calculate seconds to wait before retry.

        Args:
            reset_at: When rate limit resets
            tier: User tier (affects base delay)

        Returns:
            Seconds to wait (minimum 1 second)
        """
        if not reset_at:
            reset_at = datetime.utcnow() + timedelta(seconds=60)

        now = datetime.utcnow()
        diff = (reset_at - now).total_seconds()

        # Tier-based minimum delays
        tier_delays = {
            "free": 60,
            "premium": 30,
            "enterprise": 10,
            "standard": 60,
        }

        base_delay = tier_delays.get(tier.lower(), 60)

        # Return maximum of calculated or tier minimum
        return max(1, int(diff) + base_delay)

    @staticmethod
    def generate_for_429(
        limit: int,
        retry_after: int,
        reset_at: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """
        Generate headers for 429 Too Many Requests response.

        Args:
            limit: Rate limit quota
            retry_after: Seconds to wait before retry
            reset_at: When limit resets (optional)

        Returns:
            Headers dict for 429 response

        Example:
            headers = HeaderGenerator.generate_for_429(
                limit=100,
                retry_after=60,
                reset_at=datetime.utcnow() + timedelta(seconds=60)
            )
        """
        if not reset_at:
            reset_at = datetime.utcnow() + timedelta(seconds=retry_after)

        return {
            "RateLimit-Limit": str(limit),
            "RateLimit-Remaining": "0",
            "RateLimit-Reset": str(int(reset_at.timestamp())),
            "Retry-After": str(retry_after),
            "Content-Type": "application/json",
        }

    @staticmethod
    def generate_for_success(
        limit: int,
        remaining: int,
        reset_at: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """
        Generate headers for successful (non-rate-limited) response.

        Args:
            limit: Rate limit quota
            remaining: Requests remaining
            reset_at: When limit resets (optional)

        Returns:
            Headers dict for normal response

        Example:
            headers = HeaderGenerator.generate_for_success(
                limit=100,
                remaining=95
            )
        """
        if not reset_at:
            reset_at = datetime.utcnow() + timedelta(seconds=60)

        return {
            "RateLimit-Limit": str(limit),
            "RateLimit-Remaining": str(max(0, remaining)),
            "RateLimit-Reset": str(int(reset_at.timestamp())),
        }


class RetryAfterCalculator:
    """Calculate optimal Retry-After values."""

    @staticmethod
    def calculate_with_jitter(
        base_seconds: int, jitter_percentage: float = 0.1
    ) -> int:
        """
        Calculate Retry-After with jitter.

        Args:
            base_seconds: Base retry delay
            jitter_percentage: Jitter as percentage (0.1 = 10%)

        Returns:
            Jittered delay in seconds
        """
        import random

        jitter_amount = int(base_seconds * jitter_percentage)
        jitter = random.randint(-jitter_amount, jitter_amount)
        return max(1, base_seconds + jitter)

    @staticmethod
    def calculate_from_reset_time(
        reset_at: datetime, minimum_seconds: int = 1
    ) -> int:
        """
        Calculate Retry-After from reset timestamp.

        Args:
            reset_at: When rate limit resets
            minimum_seconds: Minimum retry delay

        Returns:
            Seconds to wait (at least minimum_seconds)
        """
        now = datetime.utcnow()
        diff = (reset_at - now).total_seconds()
        return max(minimum_seconds, int(diff))

    @staticmethod
    def calculate_backoff(
        attempt: int, base_delay: int = 1, max_delay: int = 60
    ) -> int:
        """
        Calculate exponential backoff Retry-After.

        Args:
            attempt: Retry attempt number
            base_delay: Base delay for first attempt
            max_delay: Maximum delay cap

        Returns:
            Retry-After delay in seconds

        Example:
            >>> calc = RetryAfterCalculator()
            >>> calc.calculate_backoff(0)  # First retry
            1
            >>> calc.calculate_backoff(1)  # Second retry
            2
            >>> calc.calculate_backoff(2)  # Third retry
            4
        """
        delay = base_delay * (2 ** attempt)
        return min(max_delay, delay)


class RateLimitResponseBuilder:
    """Build complete 429 response with headers and body."""

    @staticmethod
    def build_429_response(
        limit: int,
        retry_after: int,
        reset_at: Optional[datetime] = None,
        message: str = "Too Many Requests",
        error_code: str = "rate_limited",
        details: Optional[Dict] = None,
    ) -> tuple[Dict, Dict[str, str]]:
        """
        Build complete 429 response.

        Args:
            limit: Rate limit quota
            retry_after: Seconds to wait
            reset_at: When limit resets
            message: Error message
            error_code: Error code
            details: Additional details

        Returns:
            Tuple of (response_body, headers)

        Example:
            body, headers = RateLimitResponseBuilder.build_429_response(
                limit=100,
                retry_after=60
            )
            return JSONResponse(
                status_code=429,
                content=body,
                headers=headers
            )
        """
        if not reset_at:
            reset_at = datetime.utcnow() + timedelta(seconds=retry_after)

        headers = HeaderGenerator.generate_for_429(
            limit=limit, retry_after=retry_after, reset_at=reset_at
        )

        body = {
            "error": error_code,
            "detail": message,
            "limit": limit,
            "remaining": 0,
            "reset_at": reset_at.isoformat(),
            "retry_after": retry_after,
        }

        if details:
            body.update(details)

        return body, headers

    @staticmethod
    def build_success_response(
        limit: int,
        remaining: int,
        reset_at: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """
        Build headers for successful response.

        Args:
            limit: Rate limit quota
            remaining: Requests remaining
            reset_at: When limit resets

        Returns:
            Headers dict

        Example:
            headers = RateLimitResponseBuilder.build_success_response(
                limit=100,
                remaining=95
            )
        """
        return HeaderGenerator.generate_for_success(
            limit=limit, remaining=remaining, reset_at=reset_at
        )


###############################################################################
# Standard Rate Limit Response Templates
###############################################################################


def get_429_template(identifier: str) -> tuple[Dict, Dict[str, str]]:
    """
    Get standard 429 response template.

    Args:
        identifier: Request identifier (user, IP, etc.)

    Returns:
        Tuple of (body, headers) for 429 response
    """
    return RateLimitResponseBuilder.build_429_response(
        limit=100,
        retry_after=60,
        message="Too Many Requests - Rate limit exceeded",
        details={"identifier": identifier},
    )


def get_rate_limit_headers(
    limit: int, remaining: int, reset_timestamp: int
) -> Dict[str, str]:
    """
    Get standard rate limit headers for successful response.

    Args:
        limit: Rate limit quota
        remaining: Requests remaining
        reset_timestamp: Unix timestamp when limit resets

    Returns:
        Headers dict
    """
    return {
        "RateLimit-Limit": str(limit),
        "RateLimit-Remaining": str(max(0, remaining)),
        "RateLimit-Reset": str(reset_timestamp),
    }
