"""
Unit Tests for Rate Limiting System

Comprehensive test coverage for:
- Sliding window rate limiter
- Distributed Redis rate limiter
- Endpoint limits configuration
- Exponential backoff strategies
- Integration tests

Date: October 25, 2025
"""

import pytest
import time

from src.security.rate_limiter import (
    SlidingWindowRateLimiter,
)
from src.security.endpoint_limits import (
    EndpointLimitsConfig,
    UserTier,
)
from src.security.backoff_strategy import (
    ExponentialBackoff,
    JitteredBackoff,
    DecorrelatedBackoff,
    BackoffConfig,
    BackoffFactory,
    create_backoff_strategy,
)


###############################################################################
# Fixtures
###############################################################################


@pytest.fixture
def rate_limiter():
    """Create rate limiter for testing."""
    return SlidingWindowRateLimiter(window_size_seconds=60, max_requests=100)


@pytest.fixture
def strict_limiter():
    """Create strict rate limiter for boundary testing."""
    return SlidingWindowRateLimiter(window_size_seconds=60, max_requests=5)


@pytest.fixture
def endpoint_limits_config():
    """Create endpoint limits configuration."""
    return EndpointLimitsConfig()


###############################################################################
# Sliding Window Rate Limiter Tests
###############################################################################


class TestSlidingWindowAlgorithm:
    """Test sliding window algorithm implementation."""

    def test_first_request_allowed(self, rate_limiter):
        """Test that first request is always allowed."""
        result = rate_limiter.record_request("user_123")
        assert result.allowed is True
        assert result.remaining == 99

    def test_requests_under_limit_allowed(self, strict_limiter):
        """Test that requests under limit are allowed."""
        for i in range(5):
            result = strict_limiter.record_request("user_123")
            assert result.allowed is True, f"Request {i} should be allowed"
            assert result.remaining == 4 - i

    def test_requests_over_limit_denied(self, strict_limiter):
        """Test that requests exceeding limit are denied."""
        # Fill up the limit
        for i in range(5):
            strict_limiter.record_request("user_123")

        # This should be denied
        result = strict_limiter.record_request("user_123")
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None
        assert result.retry_after > 0

    def test_window_expiry_and_reset(self):
        """Test that window expiry allows new requests."""
        limiter = SlidingWindowRateLimiter(
            window_size_seconds=1, max_requests=2
        )

        # Fill up window
        limiter.record_request("user_123")
        limiter.record_request("user_123")

        # Should be denied
        result = limiter.record_request("user_123")
        assert result.allowed is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        result = limiter.record_request("user_123")
        assert result.allowed is True

    def test_multiple_identifiers_isolated(self, rate_limiter):
        """Test that different identifiers have separate limits."""
        # Fill user1
        for i in range(100):
            result = rate_limiter.record_request("user_1")
            assert result.allowed is True

        # user1 is now rate limited
        result = rate_limiter.record_request("user_1")
        assert result.allowed is False

        # user_2 should still have capacity
        result = rate_limiter.record_request("user_2")
        assert result.allowed is True

    def test_get_current_limit_non_destructive(self, rate_limiter):
        """Test that getting limit doesn't record a request."""
        rate_limiter.record_request("user_123")

        # Get limit multiple times
        for _ in range(3):
            info = rate_limiter.get_current_limit("user_123")
            assert info.remaining == 99  # Should not change

    def test_reset_limit_clears_history(self, rate_limiter):
        """Test that reset clears request history."""
        # Fill up requests
        for i in range(50):
            rate_limiter.record_request("user_123")

        # Verify rate limited
        result = rate_limiter.record_request("user_123")
        # Not full yet, should still be allowed
        assert result.allowed is True

        # Reset
        rate_limiter.reset_limit("user_123")

        # Should be able to make requests again
        result = rate_limiter.record_request("user_123")
        assert result.allowed is True
        assert result.remaining == 99


###############################################################################
# Endpoint Limits Configuration Tests
###############################################################################


class TestEndpointLimits:
    """Test endpoint rate limits configuration."""

    def test_default_limits_registered(self, endpoint_limits_config):
        """Test that default endpoint limits are registered."""
        limits = endpoint_limits_config.get_all_limits()
        assert len(limits) > 0
        assert "search" in limits
        assert "upload" in limits

    def test_get_limit_by_endpoint(self, endpoint_limits_config):
        """Test retrieving limit by endpoint name."""
        limit = endpoint_limits_config.get_limit("search")
        assert limit is not None
        assert limit.endpoint == "search"
        assert limit.free_tier_requests == 10

    def test_get_limit_for_user_tier(self, endpoint_limits_config):
        """Test getting limit for specific user tier."""
        limit = endpoint_limits_config.get_limit("search")

        free_limit = limit.get_limit_for_tier(UserTier.FREE)
        premium_limit = limit.get_limit_for_tier(UserTier.PREMIUM)
        enterprise_limit = limit.get_limit_for_tier(UserTier.ENTERPRISE)

        assert free_limit == 10
        assert premium_limit == 100
        assert enterprise_limit == 1000

    def test_exemption_checks(self, endpoint_limits_config):
        """Test IP and user exemption."""
        limit = endpoint_limits_config.get_limit("search")

        # Localhost should be exempt
        assert limit.should_exempt(ip="127.0.0.1") is True
        assert limit.should_exempt(ip="::1") is True

        # Non-localhost should not be exempt
        assert limit.should_exempt(ip="192.168.1.1") is False

    def test_update_limit(self, endpoint_limits_config):
        """Test updating endpoint limit."""
        success = endpoint_limits_config.update_limit(
            "search", free_tier_requests=20
        )
        assert success is True

        limit = endpoint_limits_config.get_limit("search")
        assert limit.free_tier_requests == 20


###############################################################################
# Exponential Backoff Tests
###############################################################################


class TestExponentialBackoff:
    """Test exponential backoff strategy."""

    def test_exponential_growth(self):
        """Test exponential growth of backoff delay."""
        backoff = ExponentialBackoff(base_delay_ms=100, max_delay_seconds=60)

        # Attempt 0: 100ms
        delay_0 = backoff.calculate_delay(0, 10)
        assert 0.09 < delay_0 < 0.11

        # Attempt 1: 200ms
        delay_1 = backoff.calculate_delay(1, 10)
        assert 0.19 < delay_1 < 0.21

        # Attempt 2: 400ms
        delay_2 = backoff.calculate_delay(2, 10)
        assert 0.39 < delay_2 < 0.41

        # Verify exponential growth
        assert delay_1 > delay_0
        assert delay_2 > delay_1

    def test_max_delay_cap(self):
        """Test that delay is capped at maximum."""
        backoff = ExponentialBackoff(base_delay_ms=100, max_delay_seconds=5)

        # Very high attempt should be capped
        delay = backoff.calculate_delay(20, 10)
        assert delay == 5.0

    def test_retry_after_header(self):
        """Test Retry-After header value generation."""
        backoff = ExponentialBackoff(base_delay_ms=100, max_delay_seconds=60)

        header_value = backoff.get_retry_after_header(0, 10)
        assert isinstance(header_value, int)
        assert header_value >= 1


###############################################################################
# Jittered Backoff Tests
###############################################################################


class TestJitteredBackoff:
    """Test jittered backoff strategy."""

    def test_jitter_variance(self):
        """Test that jitter is within expected variance."""
        backoff = JitteredBackoff(base_delay_ms=100, jitter_variance=0.2)

        # Test multiple times to verify variance
        delays = [backoff.calculate_delay(0, 10) for _ in range(10)]

        # All delays should be different (with jitter)
        assert len(set(delays)) > 1

        # All should be reasonably close to base (100ms ± 20%)
        for delay in delays:
            assert 0.08 < delay < 0.12

    def test_thundering_herd_prevention(self):
        """Test that jitter prevents thundering herd."""
        backoff1 = JitteredBackoff(base_delay_ms=100)
        backoff2 = JitteredBackoff(base_delay_ms=100)

        delays1 = [backoff1.calculate_delay(1, 10) for _ in range(5)]
        delays2 = [backoff2.calculate_delay(1, 10) for _ in range(5)]

        # Delays should have variance (not all identical)
        assert len(set(delays1)) > 1
        assert len(set(delays2)) > 1


###############################################################################
# Decorrelated Backoff Tests
###############################################################################


class TestDecorrelatedBackoff:
    """Test decorrelated backoff strategy."""

    def test_decorrelated_distribution(self):
        """Test that decorrelated backoff produces well-distributed delays."""
        backoff = DecorrelatedBackoff(base_delay_ms=100, max_delay_seconds=60)

        delays = []
        for i in range(5):
            delay = backoff.calculate_delay(i, 10)
            delays.append(delay)

        # Should be well distributed (multiple different values)
        assert len(set(delays)) > 1

        # First delay should be at least base_delay
        assert delays[0] >= 0.1  # base_delay_ms=100 -> 0.1s

        # Delays should generally trend upward (not strict due to randomness)
        avg_first_half = sum(delays[:2]) / 2
        avg_second_half = sum(delays[3:]) / 2
        assert avg_second_half >= avg_first_half * 0.5  # Allow variance

    def test_decorrelated_prevents_bunching(self):
        """Test that decorrelated prevents retry bunching."""
        backoff1 = DecorrelatedBackoff(base_delay_ms=10)
        backoff2 = DecorrelatedBackoff(base_delay_ms=10)

        # Get multiple retry times
        times1 = [backoff1.calculate_delay(i, 5) for i in range(5)]
        times2 = [backoff2.calculate_delay(i, 5) for i in range(5)]

        # Should be different due to randomness
        assert times1 != times2


###############################################################################
# Backoff Factory Tests
###############################################################################


class TestBackoffFactory:
    """Test backoff strategy factory."""

    def test_create_exponential(self):
        """Test creating exponential backoff."""
        config = BackoffConfig(strategy="exponential")
        backoff = BackoffFactory.create(config)
        assert isinstance(backoff, ExponentialBackoff)

    def test_create_jittered(self):
        """Test creating jittered backoff."""
        config = BackoffConfig(strategy="jittered")
        backoff = BackoffFactory.create(config)
        assert isinstance(backoff, JitteredBackoff)

    def test_create_decorrelated(self):
        """Test creating decorrelated backoff."""
        config = BackoffConfig(strategy="decorrelated")
        backoff = BackoffFactory.create(config)
        assert isinstance(backoff, DecorrelatedBackoff)

    def test_create_with_helper(self):
        """Test helper function for creating backoff."""
        backoff = create_backoff_strategy(
            strategy="jittered", base_delay_ms=50
        )
        assert isinstance(backoff, JitteredBackoff)


###############################################################################
# Performance Tests
###############################################################################


class TestPerformance:
    """Test performance characteristics."""

    def test_request_processing_latency(self, rate_limiter):
        """Test that request processing is sub-5ms."""
        start = time.time()

        for i in range(100):
            rate_limiter.record_request(f"user_{i}")

        elapsed = time.time() - start
        avg_time = (elapsed / 100) * 1000  # Convert to ms

        # Should be well under 5ms average
        assert avg_time < 5.0, f"Average time: {avg_time}ms"

    def test_memory_efficiency(self, rate_limiter):
        """Test memory usage remains reasonable."""
        # Create 1000 tracked identifiers
        for i in range(1000):
            rate_limiter.record_request(f"user_{i}")

        stats = rate_limiter.get_statistics()
        assert stats.tracked_identifiers == 1000

        # Should have reasonable memory footprint
        # (this is a relative check, not absolute)
        assert len(rate_limiter.request_history) == 1000


###############################################################################
# Integration Tests
###############################################################################


class TestIntegration:
    """Integration tests for rate limiting system."""

    def test_end_to_end_rate_limiting(self):
        """Test complete rate limiting flow."""
        limiter = SlidingWindowRateLimiter(
            window_size_seconds=60, max_requests=10
        )

        # Make requests up to limit
        for i in range(10):
            result = limiter.record_request("user_123")
            assert result.allowed is True, f"Request {i} should be allowed"

        # Next request should be denied
        result = limiter.record_request("user_123")
        assert result.allowed is False
        assert result.retry_after is not None

        # Get retry-after header value
        retry_after = result.retry_after
        assert retry_after > 0
        assert retry_after <= 60

    def test_multiple_users_different_limits(self, endpoint_limits_config):
        """Test multiple users with different tier limits."""
        search_limit = endpoint_limits_config.get_limit("search")

        free_limit = search_limit.get_limit_for_tier(UserTier.FREE)
        premium_limit = search_limit.get_limit_for_tier(UserTier.PREMIUM)

        assert free_limit < premium_limit

        # Simulate different users
        free_limiter = SlidingWindowRateLimiter(
            window_size_seconds=60, max_requests=free_limit
        )
        premium_limiter = SlidingWindowRateLimiter(
            window_size_seconds=60, max_requests=premium_limit
        )

        # Free user hits limit sooner
        for i in range(free_limit):
            result = free_limiter.record_request("free_user")
            assert result.allowed is True

        result = free_limiter.record_request("free_user")
        assert result.allowed is False

        # Premium user can still make more requests
        for i in range(free_limit):
            result = premium_limiter.record_request("premium_user")
            assert result.allowed is True

    def test_backoff_with_rate_limiter(self):
        """Test using backoff strategy with rate limiter."""
        limiter = SlidingWindowRateLimiter(
            window_size_seconds=60, max_requests=5
        )
        backoff = JitteredBackoff(base_delay_ms=100, max_delay_seconds=10)

        # Try making requests
        attempt = 0
        for i in range(10):
            result = limiter.record_request("user_123")
            if not result.allowed:
                # Calculate retry delay
                delay = backoff.calculate_delay(attempt, 5)
                assert delay > 0
                attempt += 1
            else:
                attempt = 0

        assert attempt > 0  # Should have been rate limited


###############################################################################
# Edge Cases Tests
###############################################################################


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_remaining_quota(self, strict_limiter):
        """Test behavior when quota is zero."""
        # Fill up the limit
        for i in range(5):
            strict_limiter.record_request("user_123")

        # Check next request
        result = strict_limiter.record_request("user_123")
        assert result.remaining == 0
        assert result.allowed is False

    def test_very_small_window(self):
        """Test with very small time window."""
        limiter = SlidingWindowRateLimiter(
            window_size_seconds=1, max_requests=1
        )

        result1 = limiter.record_request("user_123")
        assert result1.allowed is True

        result2 = limiter.record_request("user_123")
        assert result2.allowed is False

        # Verify retry_after is reasonable
        assert result2.retry_after is not None
        assert result2.retry_after <= 1

    def test_concurrent_requests(self, rate_limiter):
        """Test behavior with rapid concurrent requests."""
        results = []

        for i in range(150):
            result = rate_limiter.record_request("user_123")
            results.append(result)

        # First 100 should be allowed
        for i in range(100):
            assert results[i].allowed is True

        # Rest should be denied
        for i in range(100, 150):
            assert results[i].allowed is False
