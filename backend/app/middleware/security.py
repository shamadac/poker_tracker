"""
Security middleware for rate limiting, CSRF protection, and security event logging.
"""
import time
import secrets
import hashlib
from typing import Dict, Optional, Set
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
import logging
from datetime import datetime, timedelta, timezone

from app.core.config import settings

# Security event logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Create security log handler if not exists
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


class SecurityEventLogger:
    """Centralized security event logging system."""
    
    @staticmethod
    def log_authentication_attempt(
        request: Request, 
        user_id: Optional[str] = None, 
        success: bool = False,
        failure_reason: Optional[str] = None
    ):
        """Log authentication attempts."""
        client_ip = SecurityEventLogger._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")
        
        event_data = {
            "event_type": "authentication_attempt",
            "client_ip": client_ip,
            "user_agent": user_agent,
            "user_id": user_id,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
            "method": request.method
        }
        
        if not success and failure_reason:
            event_data["failure_reason"] = failure_reason
        
        if success:
            security_logger.info(f"Authentication successful: {event_data}")
        else:
            security_logger.warning(f"Authentication failed: {event_data}")
    
    @staticmethod
    def log_rate_limit_exceeded(request: Request, limit_type: str):
        """Log rate limit violations."""
        client_ip = SecurityEventLogger._get_client_ip(request)
        
        event_data = {
            "event_type": "rate_limit_exceeded",
            "client_ip": client_ip,
            "limit_type": limit_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
            "method": request.method,
            "user_agent": request.headers.get("user-agent", "Unknown")
        }
        
        security_logger.warning(f"Rate limit exceeded: {event_data}")
    
    @staticmethod
    def log_csrf_violation(request: Request):
        """Log CSRF token violations."""
        client_ip = SecurityEventLogger._get_client_ip(request)
        
        event_data = {
            "event_type": "csrf_violation",
            "client_ip": client_ip,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
            "method": request.method,
            "user_agent": request.headers.get("user-agent", "Unknown"),
            "referer": request.headers.get("referer", "Unknown")
        }
        
        security_logger.warning(f"CSRF violation detected: {event_data}")
    
    @staticmethod
    def log_suspicious_activity(
        request: Request, 
        activity_type: str, 
        details: Optional[Dict] = None
    ):
        """Log suspicious activities."""
        client_ip = SecurityEventLogger._get_client_ip(request)
        
        event_data = {
            "event_type": "suspicious_activity",
            "activity_type": activity_type,
            "client_ip": client_ip,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
            "method": request.method,
            "user_agent": request.headers.get("user-agent", "Unknown")
        }
        
        if details:
            event_data.update(details)
        
        security_logger.warning(f"Suspicious activity detected: {event_data}")
    
    @staticmethod
    def log_data_access(
        request: Request, 
        user_id: str, 
        resource_type: str, 
        resource_id: Optional[str] = None
    ):
        """Log sensitive data access."""
        client_ip = SecurityEventLogger._get_client_ip(request)
        
        event_data = {
            "event_type": "data_access",
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "client_ip": client_ip,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
            "method": request.method
        }
        
        security_logger.info(f"Data access: {event_data}")
    
    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for reverse proxy setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis for distributed rate limiting."""
    
    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        
        # Rate limit configurations
        self.rate_limits = {
            "global": {"requests": 100, "window": 60},  # 100 requests per minute globally
            "auth": {"requests": 10, "window": 60},     # 10 auth requests per minute
            "api": {"requests": 60, "window": 60},      # 60 API requests per minute
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Initialize Redis connection if needed
        if not self.redis_client:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
            except Exception as e:
                security_logger.error(f"Failed to connect to Redis for rate limiting: {e}")
                # Continue without rate limiting if Redis is unavailable
                return await call_next(request)
        
        # Determine rate limit type based on path
        limit_type = self._get_limit_type(request.url.path)
        
        # Check rate limit
        if await self._is_rate_limited(request, limit_type):
            SecurityEventLogger.log_rate_limit_exceeded(request, limit_type)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "type": "rate_limit_exceeded"
                }
            )
        
        # Process request
        response = await call_next(request)
        return response
    
    def _get_limit_type(self, path: str) -> str:
        """Determine rate limit type based on request path."""
        if "/auth/" in path:
            return "auth"
        elif "/api/" in path:
            return "api"
        else:
            return "global"
    
    async def _is_rate_limited(self, request: Request, limit_type: str) -> bool:
        """Check if request should be rate limited."""
        if not self.redis_client:
            return False
        
        client_ip = SecurityEventLogger._get_client_ip(request)
        limit_config = self.rate_limits.get(limit_type, self.rate_limits["global"])
        
        # Create rate limit key
        key = f"rate_limit:{limit_type}:{client_ip}"
        
        try:
            # Get current count
            current = await self.redis_client.get(key)
            
            if current is None:
                # First request in window
                await self.redis_client.setex(key, limit_config["window"], 1)
                return False
            
            current_count = int(current)
            if current_count >= limit_config["requests"]:
                return True
            
            # Increment counter
            await self.redis_client.incr(key)
            return False
            
        except Exception as e:
            security_logger.error(f"Rate limiting error: {e}")
            # Allow request if rate limiting fails
            return False


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for state-changing operations."""
    
    def __init__(self, app):
        super().__init__(app)
        self.csrf_tokens: Dict[str, float] = {}  # In-memory token store for development
        self.token_expiry = 3600  # 1 hour
        
        # Methods that require CSRF protection
        self.protected_methods = {"POST", "PUT", "PATCH", "DELETE"}
        
        # Paths that are exempt from CSRF protection
        self.exempt_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register", 
            "/api/v1/auth/refresh",
            "/health",
            "/"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with CSRF protection."""
        # Skip CSRF protection for safe methods and exempt paths
        if (request.method not in self.protected_methods or 
            request.url.path in self.exempt_paths):
            return await call_next(request)
        
        # Check for CSRF token
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            SecurityEventLogger.log_csrf_violation(request)
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "CSRF token missing",
                    "type": "csrf_token_missing"
                }
            )
        
        # Validate CSRF token
        if not self._validate_csrf_token(csrf_token):
            SecurityEventLogger.log_csrf_violation(request)
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Invalid CSRF token",
                    "type": "csrf_token_invalid"
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add new CSRF token to response for next request
        new_token = self._generate_csrf_token()
        response.headers["X-CSRF-Token"] = new_token
        
        return response
    
    def _generate_csrf_token(self) -> str:
        """Generate a new CSRF token."""
        token = secrets.token_urlsafe(32)
        self.csrf_tokens[token] = time.time()
        
        # Clean up expired tokens
        self._cleanup_expired_tokens()
        
        return token
    
    def _validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token."""
        if token not in self.csrf_tokens:
            return False
        
        # Check if token is expired
        token_time = self.csrf_tokens[token]
        if time.time() - token_time > self.token_expiry:
            del self.csrf_tokens[token]
            return False
        
        return True
    
    def _cleanup_expired_tokens(self):
        """Remove expired CSRF tokens."""
        current_time = time.time()
        expired_tokens = [
            token for token, token_time in self.csrf_tokens.items()
            if current_time - token_time > self.token_expiry
        ]
        
        for token in expired_tokens:
            del self.csrf_tokens[token]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # HSTS (only in production)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response