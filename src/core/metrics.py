"""
Prometheus Metrics Configuration

Provides Prometheus metrics integration for FastAPI.
Collects metrics for requests, errors, latency, and business operations.

Design:
- Counter: Request count, errors, by endpoint, status code
- Histogram: Request duration, response size
- Gauge: Active connections, queue depth
- Summary: Percentiles for request duration

Integration:
- FastAPI: Middleware for automatic request/response metrics
- Endpoints: GET /metrics for Prometheus scraping
- Dashboard: Metrics exported to Prometheus for visualization

Metrics Collected:
- http_requests_total{method, endpoint, status}
- http_request_duration_seconds{method, endpoint}
- http_response_size_bytes{method, endpoint}
- http_connections_active
- database_query_duration_seconds{operation}
- database_connections_active
- redis_operations_total{operation, status}
"""

import time
from typing import Callable, Optional
from functools import wraps

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    REGISTRY,
    CONTENT_TYPE_LATEST,
)


# Prometheus metrics registry
registry = REGISTRY

# HTTP Request Metrics
http_requests_total = Counter(
    name="http_requests_total",
    documentation="Total HTTP requests",
    labelnames=["method", "endpoint", "status"],
    registry=registry
)

http_request_duration_seconds = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP request duration in seconds",
    labelnames=["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=registry
)

http_response_size_bytes = Histogram(
    name="http_response_size_bytes",
    documentation="HTTP response size in bytes",
    labelnames=["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=registry
)

http_connections_active = Gauge(
    name="http_connections_active",
    documentation="Active HTTP connections",
    labelnames=["endpoint"],
    registry=registry
)

# Error Metrics
http_errors_total = Counter(
    name="http_errors_total",
    documentation="Total HTTP errors by type",
    labelnames=["error_type", "endpoint"],
    registry=registry
)

http_exceptions_total = Counter(
    name="http_exceptions_total",
    documentation="Total unhandled exceptions",
    labelnames=["exception_type", "endpoint"],
    registry=registry
)

# Database Metrics
database_query_duration_seconds = Histogram(
    name="database_query_duration_seconds",
    documentation="Database query duration in seconds",
    labelnames=["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=registry
)

database_connections_active = Gauge(
    name="database_connections_active",
    documentation="Active database connections",
    registry=registry
)

database_queries_total = Counter(
    name="database_queries_total",
    documentation="Total database queries",
    labelnames=["operation", "status"],
    registry=registry
)

# Redis Metrics
redis_operations_total = Counter(
    name="redis_operations_total",
    documentation="Total Redis operations",
    labelnames=["operation", "status"],
    registry=registry
)

redis_operation_duration_seconds = Histogram(
    name="redis_operation_duration_seconds",
    documentation="Redis operation duration in seconds",
    labelnames=["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5),
    registry=registry
)

redis_cache_hit_ratio = Gauge(
    name="redis_cache_hit_ratio",
    documentation="Redis cache hit ratio (0-1)",
    registry=registry
)

# Business Metrics
videos_processed_total = Counter(
    name="videos_processed_total",
    documentation="Total videos processed",
    labelnames=["status", "source"],
    registry=registry
)

videos_processing_duration_seconds = Histogram(
    name="videos_processing_duration_seconds",
    documentation="Video processing duration in seconds",
    labelnames=["source"],
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600),
    registry=registry
)

api_requests_in_progress = Gauge(
    name="api_requests_in_progress",
    documentation="API requests currently in progress",
    labelnames=["method", "endpoint"],
    registry=registry
)


def add_metrics_middleware(app: FastAPI) -> None:
    """
    Add Prometheus metrics middleware to FastAPI application.
    
    Collects:
    - Request count (by method, endpoint, status)
    - Request duration
    - Response size
    - Active connections
    - Error rates
    
    Args:
        app: FastAPI application instance
    
    Example:
        >>> app = FastAPI()
        >>> add_metrics_middleware(app)
    """

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next) -> Response:
        """
        Middleware to collect HTTP metrics.
        
        Args:
            request: FastAPI Request
            call_next: Next middleware/handler
            
        Returns:
            Response from handler
        """
        # Extract endpoint
        endpoint = request.url.path or "/"
        method = request.method
        
        # Increment active connections
        api_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # Start timing
        start_time = time.time()
        
        try:
            # Call the endpoint
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            status_code = response.status_code
            
            # Record request count and duration
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Record response size if available
            if "content-length" in response.headers:
                try:
                    size = int(response.headers["content-length"])
                    http_response_size_bytes.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(size)
                except ValueError:
                    pass
            
            return response
            
        except Exception as exc:
            # Record error
            http_errors_total.labels(
                error_type=type(exc).__name__,
                endpoint=endpoint
            ).inc()
            
            http_exceptions_total.labels(
                exception_type=type(exc).__name__,
                endpoint=endpoint
            ).inc()
            
            raise
            
        finally:
            # Decrement active connections
            api_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()

    @app.get("/metrics", tags=["monitoring"])
    async def metrics() -> Response:
        """
        Prometheus metrics endpoint.
        
        Returns:
            Prometheus-formatted metrics
        """
        return Response(
            content=generate_latest(registry),
            media_type=CONTENT_TYPE_LATEST
        )


def track_db_operation(operation: str, table: str = "unknown") -> Callable:
    """
    Decorator to track database operation metrics.
    
    Records:
    - Operation count (success/failure)
    - Operation duration
    
    Args:
        operation: Operation type (SELECT, INSERT, UPDATE, DELETE)
        table: Table name (optional)
    
    Returns:
        Decorated function
    
    Example:
        >>> @track_db_operation("SELECT", "users")
        >>> def get_user(user_id: int):
        ...     return db.query(User).get(user_id)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                database_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
                
                database_queries_total.labels(
                    operation=operation,
                    status="success"
                ).inc()
                
                return result
                
            except Exception as exc:
                duration = time.time() - start_time
                
                database_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
                
                database_queries_total.labels(
                    operation=operation,
                    status="error"
                ).inc()
                
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                database_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
                
                database_queries_total.labels(
                    operation=operation,
                    status="success"
                ).inc()
                
                return result
                
            except Exception as exc:
                duration = time.time() - start_time
                
                database_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
                
                database_queries_total.labels(
                    operation=operation,
                    status="error"
                ).inc()
                
                raise

        # Return async wrapper if original is async, otherwise sync
        if hasattr(func, '__await__'):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_redis_operation(operation: str) -> Callable:
    """
    Decorator to track Redis operation metrics.
    
    Records:
    - Operation count (success/failure)
    - Operation duration
    
    Args:
        operation: Operation type (GET, SET, DEL, etc.)
    
    Returns:
        Decorated function
    
    Example:
        >>> @track_redis_operation("GET")
        >>> def get_cache(key: str):
        ...     return redis.get(key)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                redis_operation_duration_seconds.labels(
                    operation=operation
                ).observe(duration)
                
                redis_operations_total.labels(
                    operation=operation,
                    status="success"
                ).inc()
                
                return result
                
            except Exception:
                duration = time.time() - start_time
                
                redis_operation_duration_seconds.labels(
                    operation=operation
                ).observe(duration)
                
                redis_operations_total.labels(
                    operation=operation,
                    status="error"
                ).inc()
                
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                redis_operation_duration_seconds.labels(
                    operation=operation
                ).observe(duration)
                
                redis_operations_total.labels(
                    operation=operation,
                    status="success"
                ).inc()
                
                return result
                
            except Exception:
                duration = time.time() - start_time
                
                redis_operation_duration_seconds.labels(
                    operation=operation
                ).observe(duration)
                
                redis_operations_total.labels(
                    operation=operation,
                    status="error"
                ).inc()
                
                raise

        if hasattr(func, '__await__'):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def set_database_connections(count: int) -> None:
    """Set active database connections gauge."""
    database_connections_active.set(count)


def set_redis_cache_hit_ratio(ratio: float) -> None:
    """
    Set Redis cache hit ratio.
    
    Args:
        ratio: Hit ratio as float (0-1)
    """
    redis_cache_hit_ratio.set(max(0, min(1, ratio)))


def record_video_processing(
    source: str,
    status: str = "success",
    duration: Optional[float] = None
) -> None:
    """
    Record video processing metrics.
    
    Args:
        source: Video source (youtube, local, etc.)
        status: Processing status (success, failed, etc.)
        duration: Processing duration in seconds (optional)
    """
    videos_processed_total.labels(status=status, source=source).inc()
    
    if duration is not None:
        videos_processing_duration_seconds.labels(source=source).observe(duration)
