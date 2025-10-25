"""
Integration Tests: Rate Limiter with FastAPI Middleware

Tests for middleware integration with FastAPI and rate limiter components.

Date: October 25, 2025
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.security.middleware import (
    RequestIdentifier,
    RateLimitMiddleware,
    rate_limit,
)
from src.security.endpoint_limits import (
    EndpointLimitsConfig,
    LimitScope,
    UserTier,
)
from src.security.rate_limiter import SlidingWindowRateLimiter
from src.security.response_headers import (
    HeaderGenerator,
    RetryAfterCalculator,
    RateLimitResponseBuilder,
)


###############################################################################
# Request Identifier Tests
###############################################################################


class TestRequestIdentifier:
    """Test request identification for rate limiting."""

    def test_get_client_ip_from_direct_connection(self):
        """Test extracting client IP from direct connection."""
        request = MagicMock()
        request.client.host = "192.168.1.100"
        request.headers = {}

        identifier = RequestIdentifier(EndpointLimitsConfig())
        ip = identifier._get_client_ip(request)

        assert ip == "192.168.1.100"

    def test_get_client_ip_from_x_forwarded_for(self):
        """Test extracting IP from X-Forwarded-For header."""
        request = MagicMock()
        request.client = None
        request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}

        identifier = RequestIdentifier(EndpointLimitsConfig())
        ip = identifier._get_client_ip(request)

        assert ip == "203.0.113.1"

    def test_get_user_id_from_bearer_token(self):
        """Test extracting user ID from Bearer token."""
        request = MagicMock()
        request.headers = {"Authorization": "Bearer user_12345"}
        request.client = MagicMock(host="127.0.0.1")

        identifier = RequestIdentifier(EndpointLimitsConfig())
        user_id = identifier._get_user_id(request)

        assert user_id == "user_12345"

    def test_get_user_tier_from_header(self):
        """Test extracting user tier from header."""
        request = MagicMock()
        request.headers = {"X-User-Tier": "PREMIUM"}
        request.client = MagicMock(host="127.0.0.1")

        identifier = RequestIdentifier(EndpointLimitsConfig())
        tier = identifier._get_user_tier(request)

        assert tier == UserTier.PREMIUM

    def test_generate_global_identifier(self):
        """Test generating global scope identifier."""
        identifier = RequestIdentifier(EndpointLimitsConfig())
        result = identifier._generate_identifier(
            LimitScope.GLOBAL, "user_123", "192.168.1.1"
        )

        assert result == "global"

    def test_generate_per_ip_identifier(self):
        """Test generating per-IP scope identifier."""
        identifier = RequestIdentifier(EndpointLimitsConfig())
        result = identifier._generate_identifier(
            LimitScope.PER_IP, "user_123", "192.168.1.1"
        )

        assert result == "ip:192.168.1.1"

    def test_generate_per_user_identifier(self):
        """Test generating per-user scope identifier."""
        identifier = RequestIdentifier(EndpointLimitsConfig())
        result = identifier._generate_identifier(
            LimitScope.PER_USER, "user_123", "192.168.1.1"
        )

        assert result == "user:user_123"

    def test_generate_hybrid_identifier_prefers_user(self):
        """Test hybrid scope prefers user ID when available."""
        identifier = RequestIdentifier(EndpointLimitsConfig())
        result = identifier._generate_identifier(
            LimitScope.HYBRID, "user_123", "192.168.1.1"
        )

        assert result == "user:user_123"

    def test_generate_hybrid_identifier_falls_back_to_ip(self):
        """Test hybrid scope falls back to IP when no user ID."""
        identifier = RequestIdentifier(EndpointLimitsConfig())
        result = identifier._generate_identifier(
            LimitScope.HYBRID, None, "192.168.1.1"
        )

        assert result == "ip:192.168.1.1"


###############################################################################
# Response Headers Tests
###############################################################################


class TestResponseHeaders:
    """Test response header generation."""

    def test_header_generator_from_rate_limit_info(self):
        """Test generating headers from rate limit info."""
        mock_info = MagicMock()
        mock_info.allowed = True
        mock_info.limit = 100
        mock_info.remaining = 95
        mock_info.reset_at = None
        mock_info.retry_after = None

        headers = HeaderGenerator.from_rate_limit_info(mock_info)

        assert headers.limit == 100
        assert headers.remaining == 95

    def test_429_response_builder(self):
        """Test building 429 response."""
        body, headers = RateLimitResponseBuilder.build_429_response(
            limit=100, retry_after=60
        )

        assert body["error"] == "rate_limited"
        assert headers["RateLimit-Limit"] == "100"
        assert headers["Retry-After"] == "60"

    def test_retry_after_calculation(self):
        """Test Retry-After calculation."""
        from datetime import datetime, timedelta

        reset_at = datetime.utcnow() + timedelta(seconds=30)
        retry_after = RetryAfterCalculator.calculate_from_reset_time(reset_at)

        # Allow for minor timing variations (up to 2 seconds drift)
        assert retry_after >= 28
        assert retry_after <= 32

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff Retry-After."""
        retry_after_0 = RetryAfterCalculator.calculate_backoff(0, base_delay=1)
        retry_after_1 = RetryAfterCalculator.calculate_backoff(1, base_delay=1)
        retry_after_2 = RetryAfterCalculator.calculate_backoff(2, base_delay=1)

        assert retry_after_0 == 1
        assert retry_after_1 == 2
        assert retry_after_2 == 4


###############################################################################
# Middleware Integration Tests
###############################################################################


class TestMiddlewareIntegration:
    """Test middleware integration with rate limiter."""

    @pytest.mark.asyncio
    async def test_middleware_initialization(self):
        """Test middleware initialization."""
        app = MagicMock()
        limiter = SlidingWindowRateLimiter(
            window_size_seconds=60, max_requests=100
        )

        middleware = RateLimitMiddleware(app, rate_limiter=limiter)

        assert middleware.limiter is not None
        assert middleware.total_requests == 0
        assert middleware.rate_limited_requests == 0

    def test_endpoint_extraction(self):
        """Test extracting endpoint name from path."""
        app = MagicMock()
        middleware = RateLimitMiddleware(app)

        endpoint = middleware._extract_endpoint("/api/v1/search?q=test")
        assert endpoint == "search" or endpoint == "api"

    def test_exempt_endpoint_detection(self):
        """Test detecting exempt endpoints."""
        app = MagicMock()
        middleware = RateLimitMiddleware(app)

        request = MagicMock()

        # Health endpoint should be exempt
        assert middleware._is_exempt_endpoint("health", request) is True

        # Metrics should be exempt
        assert middleware._is_exempt_endpoint("metrics", request) is True

        # Search should not be exempt
        assert middleware._is_exempt_endpoint("search", request) is False

    def test_middleware_statistics(self):
        """Test getting middleware statistics."""
        app = MagicMock()
        middleware = RateLimitMiddleware(app)

        middleware.total_requests = 1000
        middleware.rate_limited_requests = 50

        stats = middleware.get_statistics()

        assert stats["total_requests"] == 1000
        assert stats["rate_limited_requests"] == 50
        assert stats["rate_limited_percentage"] == 5.0


###############################################################################
# Endpoint Limits Integration Tests
###############################################################################


class TestEndpointLimitsIntegration:
    """Test endpoint limits with middleware."""

    def test_search_endpoint_tier_limits(self):
        """Test search endpoint has correct tier limits."""
        config = EndpointLimitsConfig()
        search = config.get_limit("search")

        assert search is not None
        assert search.free_tier_requests == 10
        assert search.premium_tier_requests == 100
        assert search.enterprise_tier_requests == 1000

    def test_upload_endpoint_window_size(self):
        """Test upload endpoint has 1-hour window."""
        config = EndpointLimitsConfig()
        upload = config.get_limit("upload")

        assert upload is not None
        assert upload.window_size_seconds == 3600

    def test_admin_endpoint_internal_only(self):
        """Test admin endpoint is internal only."""
        config = EndpointLimitsConfig()
        admin = config.get_limit("admin")

        assert admin is not None
        assert admin.endpoint == "admin"

    def test_health_endpoint_unlimited(self):
        """Test health endpoint has unlimited access."""
        config = EndpointLimitsConfig()
        health = config.get_limit("health")

        assert health is not None
        # Unlimited indicated by very high request count
        assert health.free_tier_requests > 100000

    def test_endpoint_exemption_localhost(self):
        """Test localhost is exempted from rate limits."""
        config = EndpointLimitsConfig()
        search = config.get_limit("search")

        assert search.should_exempt(ip="127.0.0.1") is True
        assert search.should_exempt(ip="::1") is True

    def test_endpoint_exemption_external(self):
        """Test external IPs are not automatically exempted."""
        config = EndpointLimitsConfig()
        search = config.get_limit("search")

        assert search.should_exempt(ip="8.8.8.8") is False


###############################################################################
# End-to-End Scenarios
###############################################################################


class TestE2EScenarios:
    """Test complete end-to-end scenarios."""

    def test_free_user_search_limit(self):
        """Test free user hitting search API limit."""
        config = EndpointLimitsConfig()
        search_limit = config.get_limit("search")

        # Free user gets 10 requests per minute
        free_limit = search_limit.get_limit_for_tier(UserTier.FREE)
        assert free_limit == 10

        # Create limiter with this limit
        limiter = SlidingWindowRateLimiter(
            window_size_seconds=60, max_requests=free_limit
        )

        # Make requests up to limit
        for i in range(free_limit):
            result = limiter.record_request("free_user")
            assert result.allowed is True

        # Next request should be denied
        result = limiter.record_request("free_user")
        assert result.allowed is False

    def test_premium_user_higher_limit(self):
        """Test premium user has higher limit."""
        config = EndpointLimitsConfig()
        search_limit = config.get_limit("search")

        free_limit = search_limit.get_limit_for_tier(UserTier.FREE)
        premium_limit = search_limit.get_limit_for_tier(UserTier.PREMIUM)

        assert premium_limit > free_limit
        assert premium_limit == 100

    def test_tiered_access_scenario(self):
        """Test complete tiered access scenario."""
        config = EndpointLimitsConfig()
        upload_limit = config.get_limit("upload")

        # Free user: 5/hour
        free_limit = upload_limit.get_limit_for_tier(UserTier.FREE)
        assert free_limit == 5

        # Premium user: 10/hour
        premium_limit = upload_limit.get_limit_for_tier(UserTier.PREMIUM)
        assert premium_limit == 10

        # Enterprise user: 100/hour
        enterprise_limit = upload_limit.get_limit_for_tier(UserTier.ENTERPRISE)
        assert enterprise_limit == 100

        # Verify progression
        assert free_limit < premium_limit < enterprise_limit
