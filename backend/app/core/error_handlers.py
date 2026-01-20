"""
Comprehensive error handling system for graceful degradation and proper error messaging.
"""
import logging
import traceback
from typing import Dict, Any, Optional, Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
import asyncio

from app.core.logging import get_logger, security_logger
from app.services.exceptions import (
    HandParsingError,
    UnsupportedPlatformError,
    ValidationError,
    DuplicateHandError,
    FileMonitoringError,
    NotFoundError
)

logger = get_logger(__name__)


class ErrorResponse:
    """Standardized error response format."""
    
    def __init__(
        self,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
        user_message: Optional[str] = None
    ):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        self.user_message = user_message or self._get_user_friendly_message()
    
    def _get_user_friendly_message(self) -> str:
        """Generate user-friendly error messages."""
        user_messages = {
            "validation_error": "Please check your input and try again.",
            "authentication_error": "Please log in to continue.",
            "authorization_error": "You don't have permission to perform this action.",
            "not_found": "The requested resource was not found.",
            "rate_limit_exceeded": "Too many requests. Please try again later.",
            "database_error": "We're experiencing technical difficulties. Please try again.",
            "external_service_error": "External service is temporarily unavailable.",
            "file_processing_error": "There was an issue processing your file.",
            "parsing_error": "Unable to parse the hand history file.",
            "internal_error": "An unexpected error occurred. Our team has been notified."
        }
        return user_messages.get(self.error_type, self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "error": {
                "type": self.error_type,
                "message": self.user_message,
                "details": self.details
            }
        }


class ServiceDegradationManager:
    """Manages graceful service degradation when dependencies fail."""
    
    def __init__(self):
        self.service_status = {
            "database": True,
            "redis": True,
            "ai_providers": {"gemini": True, "groq": True},
            "file_monitoring": True
        }
        self.degraded_features = set()
    
    def mark_service_down(self, service: str, feature: Optional[str] = None):
        """Mark a service as down and enable degraded mode."""
        if service in self.service_status:
            if isinstance(self.service_status[service], dict) and feature:
                self.service_status[service][feature] = False
            else:
                self.service_status[service] = False
        
        # Add degraded features
        degraded_features_map = {
            "database": ["statistics", "hand_history", "user_data"],
            "redis": ["caching", "real_time_updates"],
            "ai_providers": ["hand_analysis", "session_analysis"],
            "file_monitoring": ["auto_import", "real_time_processing"]
        }
        
        if service in degraded_features_map:
            self.degraded_features.update(degraded_features_map[service])
        
        logger.warning(f"Service degradation: {service} marked as down")
    
    def mark_service_up(self, service: str, feature: Optional[str] = None):
        """Mark a service as up and restore functionality."""
        if service in self.service_status:
            if isinstance(self.service_status[service], dict) and feature:
                self.service_status[service][feature] = True
            else:
                self.service_status[service] = True
        
        logger.info(f"Service restored: {service} marked as up")
    
    def is_service_available(self, service: str, feature: Optional[str] = None) -> bool:
        """Check if a service is available."""
        if service not in self.service_status:
            return True  # Unknown services are assumed available
        
        if isinstance(self.service_status[service], dict) and feature:
            return self.service_status[service].get(feature, False)
        
        return self.service_status[service]
    
    def get_degraded_features(self) -> set:
        """Get list of currently degraded features."""
        return self.degraded_features.copy()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            "services": self.service_status.copy(),
            "degraded_features": list(self.degraded_features),
            "overall_health": "degraded" if self.degraded_features else "healthy"
        }


# Global service degradation manager
degradation_manager = ServiceDegradationManager()


class DatabaseErrorHandler:
    """Handle database-related errors with graceful degradation."""
    
    @staticmethod
    async def handle_database_error(error: SQLAlchemyError, operation: str) -> ErrorResponse:
        """Handle database errors with appropriate responses."""
        logger.error(f"Database error during {operation}: {str(error)}")
        
        if isinstance(error, OperationalError):
            # Database connection issues
            degradation_manager.mark_service_down("database")
            return ErrorResponse(
                error_type="database_connection_error",
                message="Database connection failed",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                user_message="We're experiencing database connectivity issues. Please try again in a few moments."
            )
        
        elif isinstance(error, IntegrityError):
            # Data integrity violations
            return ErrorResponse(
                error_type="data_integrity_error",
                message="Data integrity constraint violated",
                status_code=status.HTTP_409_CONFLICT,
                user_message="This operation conflicts with existing data. Please check your input."
            )
        
        else:
            # Generic database error
            return ErrorResponse(
                error_type="database_error",
                message="Database operation failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExternalServiceErrorHandler:
    """Handle external service errors (Redis, AI providers)."""
    
    @staticmethod
    async def handle_redis_error(error: RedisError, operation: str) -> ErrorResponse:
        """Handle Redis errors with graceful degradation."""
        logger.error(f"Redis error during {operation}: {str(error)}")
        
        if isinstance(error, RedisConnectionError):
            degradation_manager.mark_service_down("redis")
            return ErrorResponse(
                error_type="cache_unavailable",
                message="Cache service unavailable",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                user_message="Caching is temporarily unavailable. The system will continue to work but may be slower."
            )
        
        return ErrorResponse(
            error_type="cache_error",
            message="Cache operation failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    async def handle_ai_provider_error(error: Exception, provider: str, operation: str) -> ErrorResponse:
        """Handle AI provider errors."""
        logger.error(f"AI provider {provider} error during {operation}: {str(error)}")
        
        degradation_manager.mark_service_down("ai_providers", provider)
        
        return ErrorResponse(
            error_type="ai_service_error",
            message=f"AI provider {provider} unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            user_message=f"The {provider} AI service is temporarily unavailable. Please try again later or use a different provider."
        )


class ApplicationErrorHandler:
    """Handle application-specific errors."""
    
    @staticmethod
    async def handle_parsing_error(error: HandParsingError) -> ErrorResponse:
        """Handle hand parsing errors."""
        logger.error(f"Hand parsing error: {str(error)}")
        
        if isinstance(error, UnsupportedPlatformError):
            return ErrorResponse(
                error_type="unsupported_platform",
                message="Unsupported poker platform",
                status_code=status.HTTP_400_BAD_REQUEST,
                user_message="This poker platform is not supported. Please use PokerStars or GGPoker hand histories."
            )
        
        elif isinstance(error, ValidationError):
            return ErrorResponse(
                error_type="validation_error",
                message="Hand validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                user_message="The hand history data appears to be corrupted or invalid."
            )
        
        elif isinstance(error, DuplicateHandError):
            return ErrorResponse(
                error_type="duplicate_hand",
                message="Duplicate hand detected",
                status_code=status.HTTP_409_CONFLICT,
                user_message="This hand has already been processed."
            )
        
        return ErrorResponse(
            error_type="parsing_error",
            message="Hand parsing failed",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    async def handle_file_monitoring_error(error: FileMonitoringError) -> ErrorResponse:
        """Handle file monitoring errors."""
        logger.error(f"File monitoring error: {str(error)}")
        
        degradation_manager.mark_service_down("file_monitoring")
        
        return ErrorResponse(
            error_type="file_monitoring_error",
            message="File monitoring failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            user_message="Automatic file monitoring is temporarily unavailable. You can still upload files manually."
        )


async def create_error_response(error: Exception, request: Request) -> JSONResponse:
    """Create standardized error response."""
    error_response = None
    
    # Handle specific error types
    if isinstance(error, HTTPException):
        error_response = ErrorResponse(
            error_type="http_error",
            message=error.detail,
            status_code=error.status_code
        )
    
    elif isinstance(error, RequestValidationError):
        error_response = ErrorResponse(
            error_type="validation_error",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": error.errors()}
        )
    
    elif isinstance(error, SQLAlchemyError):
        error_response = await DatabaseErrorHandler.handle_database_error(error, "unknown")
    
    elif isinstance(error, RedisError):
        error_response = await ExternalServiceErrorHandler.handle_redis_error(error, "unknown")
    
    elif isinstance(error, HandParsingError):
        error_response = await ApplicationErrorHandler.handle_parsing_error(error)
    
    elif isinstance(error, FileMonitoringError):
        error_response = await ApplicationErrorHandler.handle_file_monitoring_error(error)
    
    elif isinstance(error, NotFoundError):
        error_response = ErrorResponse(
            error_type="not_found",
            message="Resource not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    else:
        # Generic error handling
        logger.error(f"Unhandled error: {str(error)}\n{traceback.format_exc()}")
        error_response = ErrorResponse(
            error_type="internal_error",
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Log security events for suspicious errors
    if error_response.status_code in [400, 401, 403, 422]:
        security_logger.log_suspicious_activity(
            "error_response",
            {
                "client_ip": request.client.host if request.client else "unknown",
                "path": str(request.url.path),
                "method": request.method,
                "error_type": error_response.error_type,
                "status_code": error_response.status_code
            }
        )
    
    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict()
    )


# Exception handlers for FastAPI
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return await create_error_response(exc, request)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation exceptions."""
    return await create_error_response(exc, request)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    return await create_error_response(exc, request)


# Health check with service status
async def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health status."""
    health_status = {
        "status": "healthy",
        "timestamp": logger.logger.handlers[0].formatter.formatTime(logger.logger.makeRecord(
            "health", logging.INFO, "", 0, "", (), None
        )),
        "services": degradation_manager.get_service_status(),
        "version": "1.0.0"
    }
    
    # Determine overall status
    if degradation_manager.get_degraded_features():
        health_status["status"] = "degraded"
    
    return health_status


# Circuit breaker pattern for external services
class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True
        
        import time
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """Handle failed call."""
        import time
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"