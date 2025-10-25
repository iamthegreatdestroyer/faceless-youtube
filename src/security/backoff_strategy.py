"""
Exponential Backoff Strategies for Rate Limiting

Implements various backoff strategies for optimal retry behavior:
- Standard exponential backoff
- Jittered backoff (prevents thundering herd)
- Decorrelated backoff (better variance)

Date: October 25, 2025
"""

import logging
import random
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


###############################################################################
# Backoff Strategy Base Class
###############################################################################


class BackoffStrategy(ABC):
    """Abstract base class for backoff strategies."""

    @abstractmethod
    def calculate_delay(self, attempt: int, max_retries: int) -> float:
        """
        Calculate backoff delay in seconds.

        Args:
            attempt: Current attempt number (0-indexed)
            max_retries: Maximum retry attempts

        Returns:
            Delay in seconds
        """
        pass

    @abstractmethod
    def calculate_jitter(self, base_delay: float) -> float:
        """
        Calculate jitter to apply to delay.

        Args:
            base_delay: Base delay before jitter

        Returns:
            Jitter amount in seconds
        """
        pass

    def get_retry_after_header(self, attempt: int, max_retries: int) -> int:
        """
        Get Retry-After header value.

        Args:
            attempt: Current attempt number
            max_retries: Maximum retries

        Returns:
            Seconds to wait before retry
        """
        delay = self.calculate_delay(attempt, max_retries)
        return max(1, int(math.ceil(delay)))


###############################################################################
# Exponential Backoff Implementation
###############################################################################


class ExponentialBackoff(BackoffStrategy):
    """
    Standard exponential backoff: delay = base * (2 ^ attempt)

    Grows exponentially with each retry attempt.
    Formula: delay = base_delay * (2 ^ attempt)

    Example:
        Base 100ms, attempt 0: 100ms
        Base 100ms, attempt 1: 200ms
        Base 100ms, attempt 2: 400ms
        Base 100ms, attempt 3: 800ms
    """

    def __init__(
        self,
        base_delay_ms: int = 100,
        max_delay_seconds: int = 60,
    ):
        """
        Initialize exponential backoff.

        Args:
            base_delay_ms: Base delay in milliseconds
            max_delay_seconds: Maximum delay cap in seconds
        """
        self.base_delay = base_delay_ms / 1000.0
        self.max_delay = max_delay_seconds

    def calculate_delay(self, attempt: int, max_retries: int) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Current attempt (0-indexed)
            max_retries: Maximum retries

        Returns:
            Delay in seconds
        """
        if attempt >= max_retries:
            return self.max_delay

        # delay = base * (2 ^ attempt)
        delay = self.base_delay * (2 ** attempt)

        # Cap at maximum
        return min(delay, self.max_delay)

    def calculate_jitter(self, base_delay: float) -> float:
        """
        No jitter for standard backoff (use JitteredBackoff for that).

        Returns:
            0 (no jitter)
        """
        return 0.0


###############################################################################
# Jittered Backoff Implementation
###############################################################################


class JitteredBackoff(BackoffStrategy):
    """
    Exponential backoff with random jitter.

    Prevents thundering herd problem when multiple clients retry simultaneously.
    Formula: delay = base * (2 ^ attempt) + jitter

    Jitter: random value between -20% and +20% of base delay

    Example:
        Base 100ms, attempt 0: ~100ms ± 20ms
        Base 100ms, attempt 1: ~200ms ± 40ms
        Base 100ms, attempt 2: ~400ms ± 80ms
    """

    def __init__(
        self,
        base_delay_ms: int = 100,
        max_delay_seconds: int = 60,
        jitter_variance: float = 0.2,  # ±20%
    ):
        """
        Initialize jittered backoff.

        Args:
            base_delay_ms: Base delay in milliseconds
            max_delay_seconds: Maximum delay cap
            jitter_variance: Jitter variance (0.2 = ±20%)
        """
        self.base_delay = base_delay_ms / 1000.0
        self.max_delay = max_delay_seconds
        self.jitter_variance = jitter_variance

    def calculate_delay(self, attempt: int, max_retries: int) -> float:
        """
        Calculate exponential backoff with jitter.

        Args:
            attempt: Current attempt (0-indexed)
            max_retries: Maximum retries

        Returns:
            Delay in seconds
        """
        if attempt >= max_retries:
            return self.max_delay

        # Base exponential delay
        base_delay = self.base_delay * (2 ** attempt)
        base_delay = min(base_delay, self.max_delay)

        # Add jitter
        jitter = self.calculate_jitter(base_delay)
        final_delay = base_delay + jitter

        return max(0.001, final_delay)  # Minimum 1ms

    def calculate_jitter(self, base_delay: float) -> float:
        """
        Calculate random jitter (±variance of base).

        Args:
            base_delay: Base delay before jitter

        Returns:
            Jitter in seconds (can be negative)
        """
        variance_amount = base_delay * self.jitter_variance
        return random.uniform(-variance_amount, variance_amount)


###############################################################################
# Decorrelated Backoff Implementation
###############################################################################


class DecorrelatedBackoff(BackoffStrategy):
    """
    Decorrelated jitter backoff algorithm.

    Improves upon jittered backoff by decorrelating retries.
    Proposed by AWS for optimal retry behavior.

    Formula:
        temp = base * 3
        delay = random(base, temp)
        temp = min(cap, delay * 3)
        delay = random(base, temp)
        ...

    This prevents bunching of retries better than simple jitter.

    Example:
        Provides well-distributed delays that prevent thundering herd
        while exponentially backing off
    """

    def __init__(
        self,
        base_delay_ms: int = 100,
        max_delay_seconds: int = 60,
    ):
        """
        Initialize decorrelated backoff.

        Args:
            base_delay_ms: Base delay in milliseconds
            max_delay_seconds: Maximum delay cap
        """
        self.base_delay = base_delay_ms / 1000.0
        self.max_delay = max_delay_seconds
        self.last_delay = self.base_delay

    def calculate_delay(self, attempt: int, max_retries: int) -> float:
        """
        Calculate decorrelated backoff delay.

        Args:
            attempt: Current attempt (0-indexed)
            max_retries: Maximum retries

        Returns:
            Delay in seconds
        """
        if attempt >= max_retries:
            return self.max_delay

        if attempt == 0:
            self.last_delay = self.base_delay
            return self.base_delay

        # temp = min(cap, last_delay * 3)
        temp = min(self.max_delay, self.last_delay * 3)

        # delay = random(base, temp)
        delay = random.uniform(self.base_delay, temp)

        self.last_delay = delay
        return delay

    def calculate_jitter(self, base_delay: float) -> float:
        """
        Jitter is built into the algorithm.

        Returns:
            0 (jitter already included)
        """
        return 0.0


###############################################################################
# Backoff Configuration & Factory
###############################################################################


@dataclass
class BackoffConfig:
    """Configuration for backoff behavior."""

    strategy: str = "jittered"  # "exponential", "jittered", "decorrelated"
    base_delay_ms: int = 100
    max_delay_seconds: int = 60
    max_retries: int = 5
    jitter_variance: float = 0.2  # For jittered backoff


class BackoffFactory:
    """Factory for creating backoff strategies."""

    @staticmethod
    def create(config: BackoffConfig) -> BackoffStrategy:
        """
        Create backoff strategy from config.

        Args:
            config: BackoffConfig with strategy details

        Returns:
            BackoffStrategy instance
        """
        if config.strategy == "exponential":
            return ExponentialBackoff(
                base_delay_ms=config.base_delay_ms,
                max_delay_seconds=config.max_delay_seconds,
            )
        elif config.strategy == "jittered":
            return JitteredBackoff(
                base_delay_ms=config.base_delay_ms,
                max_delay_seconds=config.max_delay_seconds,
                jitter_variance=config.jitter_variance,
            )
        elif config.strategy == "decorrelated":
            return DecorrelatedBackoff(
                base_delay_ms=config.base_delay_ms,
                max_delay_seconds=config.max_delay_seconds,
            )
        else:
            logger.warning(f"Unknown backoff strategy: {config.strategy}. Using jittered.")
            return JitteredBackoff(
                base_delay_ms=config.base_delay_ms,
                max_delay_seconds=config.max_delay_seconds,
            )


# Helper function
def create_backoff_strategy(
    strategy: str = "jittered",
    base_delay_ms: int = 100,
    max_delay_seconds: int = 60,
) -> BackoffStrategy:
    """
    Create backoff strategy.

    Args:
        strategy: "exponential", "jittered", or "decorrelated"
        base_delay_ms: Base delay in milliseconds
        max_delay_seconds: Maximum delay cap

    Returns:
        BackoffStrategy instance
    """
    config = BackoffConfig(
        strategy=strategy,
        base_delay_ms=base_delay_ms,
        max_delay_seconds=max_delay_seconds,
    )
    return BackoffFactory.create(config)
