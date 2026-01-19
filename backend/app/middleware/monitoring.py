"""
Middleware for request monitoring and logging.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import (
    get_logger, 
    performance_logger, 
    security_logger,
    set_request_context, 
    clear_request_context,
    generate_request_id
)
from app.core.monitoring import metrics_collector

logger = get_logger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for request monitoring and performance tracking."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with monitoring and logging."""
        # Generate request ID and set context
        request_id = generate_request_id()
        set_request_context(request_id)
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=client_ip,
            user_agent=user_agent,
            request_id=request_id
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            metrics_collector.record_metric("response_time", duration * 1000)  # Convert to ms
            metrics_collector.record_metric("requests_total", 1, {
                "method": request.method,
                "status": str(response.status_code),
                "path": request.url.path
            })
            
            # Log request completion
            performance_logger.log_request_performance(
                method=request.method,
                path=request.url.path,
                duration=duration,
                status_code=response.status_code
            )
            
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration * 1000,
                request_id=request_id
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration = time.time() - start_time
            
            # Record error metrics
            metrics_collector.record_metric("errors_total", 1, {
                "method": request.method,
                "path": request.url.path,
                "error_type": type(e).__name__
            })
            
            # Log error
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration * 1000,
                error=str(e),
                error_type=type(e).__name__,
                request_id=request_id
            )
            
            # Re-raise the exception
            raise
            
        finally:
            # Clear request context
            clear_request_context()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security monitoring and logging."""
    
    def __init__(self, app, rate_limit_per_minute: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.request_counts = {}  # Simple in-memory rate limiting
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with security monitoring."""
        client_ip = request.client.host if request.client else "unknown"
        
        # Simple rate limiting check
        current_time = time.time()
        minute_window = int(current_time // 60)
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}
        
        if minute_window not in self.request_counts[client_ip]:
            self.request_counts[client_ip][minute_window] = 0
        
        self.request_counts[client_ip][minute_window] += 1
        
        # Check rate limit
        if self.request_counts[client_ip][minute_window] > self.rate_limit:
            security_logger.log_rate_limit_exceeded(
                ip_address=client_ip,
                endpoint=request.url.path,
                limit=self.rate_limit
            )
            
            # Return rate limit error
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Clean up old entries (keep only last 2 minutes)
        cutoff_window = minute_window - 2
        for ip in list(self.request_counts.keys()):
            for window in list(self.request_counts[ip].keys()):
                if window < cutoff_window:
                    del self.request_counts[ip][window]
            if not self.request_counts[ip]:
                del self.request_counts[ip]
        
        # Process request normally
        return await call_next(request)