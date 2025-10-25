"""
Structured Logging Configuration

Provides JSON-formatted structured logging for FastAPI, compatible with Loki.
All logs include context (request_id, endpoint, method, etc.) for easy correlation.

Design:
- JSON log format for machine parsing
- Request correlation IDs for tracing
- Performance metrics in logs (duration, status)
- Error context and stack traces
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Integration:
- FastAPI: Middleware for request/response logging
- FastAPI: Exception handler for error logging
- Gunicorn: ASGI server logging
- Application: Direct logger usage throughout code
"""

import json
import logging
import time
import traceback
import uuid
from typing import Optional, Any, Dict
from datetime import datetime

from pythonjsonlogger import jsonlogger
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError


class StructuredJSONFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds context information to logs.
    
    Adds:
    - timestamp (ISO format)
    - request_id (correlation ID)
    - environment (staging/production)
    - application (faceless-youtube)
    """

    def add_fields(
        self, log_record: Dict, record: logging.LogRecord, message_dict: Dict
    ) -> None:
        """
        Add custom fields to log record.
        
        Args:
            log_record: Dictionary to populate with log data
            record: LogRecord from Python logging
            message_dict: Message dictionary from formatter
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add application metadata
        log_record["application"] = "faceless-youtube"
        log_record["environment"] = "staging"
        
        # Add logger metadata
        log_record["logger_name"] = record.name
        log_record["file"] = record.filename
        log_record["line"] = record.lineno
        
        # Add error context if present
        if record.exc_info:
            log_record["exception"] = traceback.format_exception(*record.exc_info)
        
        # Add request context if available in record
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "endpoint"):
            log_record["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_record["method"] = record.method
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms


def configure_structured_logging(
    level: str = "INFO",
    log_file: Optional[str] = "/var/log/fastapi/app.log"
) -> None:
    """
    Configure structured JSON logging for the entire application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file, or None for stdout only
    
    Example:
        >>> configure_structured_logging(level="INFO")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = StructuredJSONFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if path provided)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_formatter = StructuredJSONFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            console_logger = logging.getLogger(__name__)
            console_logger.warning(
                f"Could not configure file logging to {log_file}: {e}"
            )
    
    # Configure popular libraries to use structured logging
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("sqlalchemy").setLevel(level)
    logging.getLogger("asyncio").setLevel(level)


class RequestContextLogFilter(logging.Filter):
    """
    Logging filter that injects request context into all log records.
    
    Allows logs to include request_id, endpoint, method, etc.
    """

    def __init__(self):
        """Initialize filter."""
        super().__init__()
        self.request_context: Dict[str, Any] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request context to log record.
        
        Args:
            record: LogRecord to enrich
            
        Returns:
            True to log the record
        """
        for key, value in self.request_context.items():
            setattr(record, key, value)
        return True

    def set_context(self, **kwargs: Any) -> None:
        """Set context for subsequent logs."""
        self.request_context = kwargs

    def clear_context(self) -> None:
        """Clear context."""
        self.request_context = {}


# Global filter instance
_request_filter = RequestContextLogFilter()


def add_request_filter(logger: logging.Logger) -> None:
    """
    Add request context filter to a logger.
    
    Args:
        logger: Logger to add filter to
    """
    logger.addFilter(_request_filter)


def set_request_context(**kwargs: Any) -> None:
    """
    Set request context for all subsequent logs.
    
    Args:
        **kwargs: Context fields (request_id, endpoint, method, etc.)
    
    Example:
        >>> set_request_context(request_id="abc-123", endpoint="/api/health")
    """
    _request_filter.set_context(**kwargs)


def clear_request_context() -> None:
    """Clear request context."""
    _request_filter.clear_context()


def add_logging_middleware(app: FastAPI) -> None:
    """
    Add request/response logging middleware to FastAPI app.
    
    Logs:
    - Request: method, path, query params, client IP
    - Response: status code, response time, response size
    - Errors: exception type and message
    
    Args:
        app: FastAPI application instance
    
    Example:
        >>> app = FastAPI()
        >>> add_logging_middleware(app)
    """
    logger = logging.getLogger(__name__)
    add_request_filter(logger)

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next) -> Response:
        """
        Middleware to log HTTP requests and responses.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/endpoint
            
        Returns:
            Response from endpoint
        """
        # Generate or use existing request ID
        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4())
        )
        
        # Extract request information
        method = request.method
        path = request.url.path
        query_string = request.url.query
        client_ip = request.client.host if request.client else "unknown"
        
        # Set context for all logs in this request
        set_request_context(
            request_id=request_id,
            endpoint=path,
            method=method,
            client_ip=client_ip,
            query_string=query_string
        )
        
        # Time the request
        start_time = time.time()
        
        try:
            # Call the endpoint
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the request
            logger.info(
                f"{method} {path}",
                extra={
                    "request_id": request_id,
                    "endpoint": path,
                    "method": method,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # Log the error with context
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Error processing {method} {path}: {exc}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "endpoint": path,
                    "method": method,
                    "error": str(exc),
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                }
            )
            raise
        
        finally:
            # Always clear request context
            clear_request_context()

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        Handle exceptions and log them with full context.
        
        Args:
            request: Request that caused the error
            exc: Exception that was raised
            
        Returns:
            JSON error response
        """
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={
                "endpoint": request.url.path,
                "method": request.method,
                "error": str(exc),
            }
        )
        
        return {
            "error": "Internal server error",
            "request_id": request.headers.get("X-Request-ID")
        }

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ):
        """
        Handle validation errors and log them.
        
        Args:
            request: Request with validation error
            exc: Validation error
            
        Returns:
            JSON error response
        """
        logger.warning(
            f"Validation error on {request.method} {request.url.path}",
            extra={
                "endpoint": request.url.path,
                "method": request.method,
                "validation_errors": exc.errors(),
            }
        )
        
        return {
            "error": "Validation error",
            "details": exc.errors(),
            "request_id": request.headers.get("X-Request-ID")
        }
