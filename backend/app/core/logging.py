"""
Centralized logging configuration and utilities.
"""
import logging
import logging.config
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
from pathlib import Path

# Context variables for request tracking
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def set_request_context(request_id: str) -> None:
    """Set the request ID in context."""
    request_id_context.set(request_id)


def clear_request_context() -> None:
    """Clear the request context."""
    request_id_context.set(None)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return request_id_context.get()


class ContextualFormatter(logging.Formatter):
    """Custom formatter that includes request context."""
    
    def format(self, record):
        # Add request ID to log record if available
        request_id = get_request_id()
        if request_id:
            record.request_id = request_id
        else:
            record.request_id = "no-request"
        
        return super().format(record)


class StructuredLogger:
    """Structured logger for consistent log formatting."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, **kwargs) -> None:
        """Log with structured data."""
        extra = {
            'timestamp': datetime.now().isoformat(),
            'request_id': get_request_id(),
            **kwargs
        }
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)


class PerformanceLogger:
    """Logger specifically for performance metrics."""
    
    def __init__(self):
        self.logger = StructuredLogger("performance")
    
    def log_request_performance(self, method: str, path: str, duration: float, status_code: int) -> None:
        """Log request performance metrics."""
        self.logger.info(
            "request_performance",
            method=method,
            path=path,
            duration_seconds=duration,
            duration_ms=duration * 1000,
            status_code=status_code
        )
    
    def log_database_query(self, query_type: str, duration: float, table: str = None) -> None:
        """Log database query performance."""
        self.logger.info(
            "database_query",
            query_type=query_type,
            duration_seconds=duration,
            duration_ms=duration * 1000,
            table=table
        )
    
    def log_cache_operation(self, operation: str, key: str, hit: bool, duration: float = None) -> None:
        """Log cache operation performance."""
        self.logger.info(
            "cache_operation",
            operation=operation,
            cache_key=key,
            cache_hit=hit,
            duration_ms=duration * 1000 if duration else None
        )


class SecurityLogger:
    """Logger specifically for security events."""
    
    def __init__(self):
        self.logger = StructuredLogger("security")
    
    def log_authentication_attempt(self, user_id: str, success: bool, ip_address: str) -> None:
        """Log authentication attempts."""
        self.logger.info(
            "authentication_attempt",
            user_id=user_id,
            success=success,
            ip_address=ip_address
        )
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str) -> None:
        """Log authorization failures."""
        self.logger.warning(
            "authorization_failure",
            user_id=user_id,
            resource=resource,
            action=action
        )
    
    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str, limit: int) -> None:
        """Log rate limit violations."""
        self.logger.warning(
            "rate_limit_exceeded",
            ip_address=ip_address,
            endpoint=endpoint,
            limit=limit
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any]) -> None:
        """Log suspicious activities."""
        self.logger.warning(
            "suspicious_activity",
            activity_type=activity_type,
            **details
        )


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup application logging configuration."""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "()": ContextualFormatter,
                "format": "%(asctime)s [%(levelname)s] %(name)s [%(request_id)s]: %(message)s"
            },
            "detailed": {
                "()": ContextualFormatter,
                "format": "%(asctime)s [%(levelname)s] %(name)s [%(request_id)s] %(filename)s:%(lineno)d: %(message)s"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(request_id)s %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": log_level,
                "propagate": False
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "performance": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "security": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            }
        }
    }
    
    # Add file handler if log file is specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "detailed",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        
        # Add file handler to all loggers
        for logger_name in config["loggers"]:
            if "handlers" in config["loggers"][logger_name]:
                config["loggers"][logger_name]["handlers"].append("file")
    
    # Apply configuration
    logging.config.dictConfig(config)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


# Global logger instances
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()