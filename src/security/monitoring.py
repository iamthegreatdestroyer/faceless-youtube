"""
Rate Limiting Monitoring and Metrics

Prometheus metrics and monitoring for rate limiting system.

Metrics:
- rate_limit_requests_total: Total requests (labels: endpoint, tier, allowed)
- rate_limit_remaining: Requests remaining (labels: endpoint, tier)
- rate_limit_violations: Rate limit violations (labels: endpoint, tier)
- rate_limit_latency_ms: Request processing latency (labels: endpoint)
- rate_limit_cache_hits: Redis cache hits (labels: operation)

Dashboard:
- Request rates by endpoint and tier
- Violation trends
- Latency percentiles
- Cache performance

Date: October 25, 2025
"""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        CollectorRegistry,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


logger = logging.getLogger(__name__)


###############################################################################
# Metrics Definition
###############################################################################


@dataclass
class RateLimitMetrics:
    """Container for rate limit metrics."""

    registry: Optional[CollectorRegistry] = None

    # Counters
    requests_total: Optional[Counter] = None
    violations_total: Optional[Counter] = None
    allowed_total: Optional[Counter] = None
    denied_total: Optional[Counter] = None

    # Gauges
    current_tracking: Optional[Gauge] = None
    current_violations: Optional[Gauge] = None

    # Histograms
    request_latency: Optional[Histogram] = None
    violation_latency: Optional[Histogram] = None

    def __post_init__(self):
        """Initialize Prometheus metrics if available."""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available, metrics disabled")
            return

        if not self.registry:
            self.registry = CollectorRegistry()

        # Request counters
        self.requests_total = Counter(
            "rate_limit_requests_total",
            "Total rate limit check requests",
            ["endpoint", "tier", "action"],
            registry=self.registry,
        )

        self.violations_total = Counter(
            "rate_limit_violations_total",
            "Total rate limit violations",
            ["endpoint", "tier"],
            registry=self.registry,
        )

        self.allowed_total = Counter(
            "rate_limit_allowed_total",
            "Total allowed requests",
            ["endpoint", "tier"],
            registry=self.registry,
        )

        self.denied_total = Counter(
            "rate_limit_denied_total",
            "Total denied requests",
            ["endpoint", "tier"],
            registry=self.registry,
        )

        # Current state gauges
        self.current_tracking = Gauge(
            "rate_limit_tracked_identifiers",
            "Currently tracked identifiers",
            ["endpoint"],
            registry=self.registry,
        )

        self.current_violations = Gauge(
            "rate_limit_current_violations",
            "Currently rate limited identifiers",
            ["endpoint"],
            registry=self.registry,
        )

        # Latency histograms
        self.request_latency = Histogram(
            "rate_limit_request_latency_ms",
            "Request processing latency in milliseconds",
            ["endpoint"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry,
        )

        self.violation_latency = Histogram(
            "rate_limit_violation_latency_ms",
            "Violation response latency in milliseconds",
            ["endpoint"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry,
        )


###############################################################################
# Local Metrics Collector
###############################################################################


@dataclass
class LocalMetricsCollector:
    """Collect metrics without Prometheus."""

    endpoint_stats: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: defaultdict(
            lambda: {
                "total_requests": 0,
                "allowed_requests": 0,
                "denied_requests": 0,
                "violations": 0,
                "latencies": [],
                "tiers": defaultdict(int),
            }
        )
    )

    def record_request(
        self,
        endpoint: str,
        allowed: bool,
        latency_ms: float,
        tier: str = "free",
    ):
        """Record a rate limit check."""
        stats = self.endpoint_stats[endpoint]

        stats["total_requests"] += 1
        stats["tiers"][tier] += 1
        stats["latencies"].append(latency_ms)

        if allowed:
            stats["allowed_requests"] += 1
        else:
            stats["denied_requests"] += 1
            stats["violations"] += 1

        # Keep last 1000 latencies for percentiles
        if len(stats["latencies"]) > 1000:
            stats["latencies"] = stats["latencies"][-1000:]

    def record_violation(self, endpoint: str, tier: str = "free"):
        """Record a violation."""
        stats = self.endpoint_stats[endpoint]
        stats["violations"] += 1

    def get_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get collected statistics."""
        if endpoint:
            return self._get_endpoint_stats(endpoint)
        else:
            return self._get_global_stats()

    def _get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for specific endpoint."""
        if endpoint not in self.endpoint_stats:
            return {
                "endpoint": endpoint,
                "total_requests": 0,
                "allowed_requests": 0,
                "denied_requests": 0,
                "violations": 0,
                "avg_latency_ms": 0,
                "p50_latency_ms": 0,
                "p95_latency_ms": 0,
                "p99_latency_ms": 0,
            }

        stats = self.endpoint_stats[endpoint]
        latencies = sorted(stats["latencies"])

        return {
            "endpoint": endpoint,
            "total_requests": stats["total_requests"],
            "allowed_requests": stats["allowed_requests"],
            "denied_requests": stats["denied_requests"],
            "violations": stats["violations"],
            "violation_rate": (
                stats["violations"] / stats["total_requests"] * 100
                if stats["total_requests"] > 0
                else 0
            ),
            "avg_latency_ms": (
                sum(latencies) / len(latencies) if latencies else 0
            ),
            "p50_latency_ms": self._percentile(latencies, 50),
            "p95_latency_ms": self._percentile(latencies, 95),
            "p99_latency_ms": self._percentile(latencies, 99),
            "tier_distribution": dict(stats["tiers"]),
        }

    def _get_global_stats(self) -> Dict[str, Any]:
        """Get global statistics."""
        total_requests = sum(
            s["total_requests"] for s in self.endpoint_stats.values()
        )
        total_violations = sum(
            s["violations"] for s in self.endpoint_stats.values()
        )

        all_latencies = []
        for stats in self.endpoint_stats.values():
            all_latencies.extend(stats["latencies"])

        all_latencies = sorted(all_latencies)

        return {
            "total_requests": total_requests,
            "total_violations": total_violations,
            "violation_rate": (
                total_violations / total_requests * 100
                if total_requests > 0
                else 0
            ),
            "avg_latency_ms": (
                sum(all_latencies) / len(all_latencies)
                if all_latencies
                else 0
            ),
            "p50_latency_ms": self._percentile(all_latencies, 50),
            "p95_latency_ms": self._percentile(all_latencies, 95),
            "p99_latency_ms": self._percentile(all_latencies, 99),
            "endpoints": len(self.endpoint_stats),
        }

    @staticmethod
    def _percentile(data, percentile):
        """Calculate percentile from data."""
        if not data:
            return 0

        index = int(len(data) * percentile / 100)
        return data[min(index, len(data) - 1)]

    def clear(self):
        """Clear all statistics."""
        self.endpoint_stats.clear()


###############################################################################
# Monitoring Aggregator
###############################################################################


class RateLimitMonitor:
    """Monitor and aggregate rate limiting metrics."""

    def __init__(self, enable_prometheus: bool = True):
        """
        Initialize monitor.

        Args:
            enable_prometheus: Whether to use Prometheus (if available)
        """
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.local_collector = LocalMetricsCollector()

        if self.enable_prometheus:
            self.metrics = RateLimitMetrics()
        else:
            self.metrics = None

        self.start_time = datetime.utcnow()

    def record_request(
        self,
        endpoint: str,
        identifier: str,
        allowed: bool,
        latency_ms: float,
        tier: str = "free",
    ):
        """
        Record a rate limit check.

        Args:
            endpoint: Endpoint name
            identifier: Request identifier (user, IP, etc.)
            allowed: Whether request was allowed
            latency_ms: Processing latency in milliseconds
            tier: User tier
        """
        # Local metrics
        self.local_collector.record_request(
            endpoint, allowed, latency_ms, tier
        )

        # Prometheus metrics
        if self.enable_prometheus and self.metrics:
            action = "allowed" if allowed else "denied"
            self.metrics.requests_total.labels(
                endpoint=endpoint, tier=tier, action=action
            ).inc()

            if allowed:
                self.metrics.allowed_total.labels(
                    endpoint=endpoint, tier=tier
                ).inc()
            else:
                self.metrics.denied_total.labels(
                    endpoint=endpoint, tier=tier
                ).inc()

            self.metrics.request_latency.labels(
                endpoint=endpoint
            ).observe(latency_ms)

    def record_violation(self, endpoint: str, identifier: str, tier: str = "free"):
        """
        Record a rate limit violation.

        Args:
            endpoint: Endpoint name
            identifier: Request identifier
            tier: User tier
        """
        self.local_collector.record_violation(endpoint, tier)

        if self.enable_prometheus and self.metrics:
            self.metrics.violations_total.labels(
                endpoint=endpoint, tier=tier
            ).inc()

    def get_metrics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current metrics.

        Args:
            endpoint: Specific endpoint (or all if None)

        Returns:
            Metrics dictionary
        """
        return self.local_collector.get_stats(endpoint)

    def get_prometheus_registry(self):
        """Get Prometheus registry for scraping."""
        if self.metrics:
            return self.metrics.registry
        return None

    def health_check(self) -> Dict[str, Any]:
        """
        Get health check metrics.

        Returns:
            Health status dictionary
        """
        stats = self.get_metrics()
        uptime = datetime.utcnow() - self.start_time

        return {
            "status": "healthy",
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": stats.get("total_requests", 0),
            "total_violations": stats.get("total_violations", 0),
            "violation_rate": stats.get("violation_rate", 0),
            "avg_latency_ms": stats.get("avg_latency_ms", 0),
            "p99_latency_ms": stats.get("p99_latency_ms", 0),
        }


###############################################################################
# Helper Functions
###############################################################################


class MetricRecorder:
    """Context manager for recording latency."""

    def __init__(self, monitor: RateLimitMonitor, endpoint: str, tier: str):
        """Initialize recorder."""
        self.monitor = monitor
        self.endpoint = endpoint
        self.tier = tier
        self.start_time = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Record latency."""
        if self.start_time:
            latency_ms = (time.time() - self.start_time) * 1000
            self.monitor.record_request(
                endpoint=self.endpoint,
                identifier="metric_recorder",
                allowed=True,
                latency_ms=latency_ms,
                tier=self.tier,
            )


def create_grafana_dashboard_json() -> Dict[str, Any]:
    """
    Generate Grafana dashboard JSON for rate limiting.

    Returns:
        Dashboard definition
    """
    return {
        "dashboard": {
            "title": "Rate Limiting Metrics",
            "description": "Rate limiting system monitoring dashboard",
            "tags": ["rate-limiting", "api"],
            "timezone": "utc",
            "panels": [
                {
                    "title": "Requests Per Minute",
                    "targets": [
                        {
                            "expr": "rate(rate_limit_requests_total[1m])",
                            "legendFormat": "{{endpoint}} - {{action}}",
                        }
                    ],
                },
                {
                    "title": "Violation Rate",
                    "targets": [
                        {
                            "expr": (
                                "rate(rate_limit_denied_total[1m]) / "
                                "rate(rate_limit_requests_total[1m])"
                            ),
                            "legendFormat": "{{endpoint}}",
                        }
                    ],
                },
                {
                    "title": "Latency Percentiles",
                    "targets": [
                        {
                            "expr": (
                                "histogram_quantile(0.95, "
                                "rate(rate_limit_request_latency_ms_bucket[5m]))"
                            ),
                            "legendFormat": "p95 - {{endpoint}}",
                        },
                        {
                            "expr": (
                                "histogram_quantile(0.99, "
                                "rate(rate_limit_request_latency_ms_bucket[5m]))"
                            ),
                            "legendFormat": "p99 - {{endpoint}}",
                        },
                    ],
                },
            ],
        }
    }
