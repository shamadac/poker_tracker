"""
FastAPI application entry point for Professional Poker Analyzer.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import async_session_maker
from app.core.error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    get_system_health,
    degradation_manager
)
from app.services.file_watcher import FileWatcherService
from app.services.background_processor import BackgroundFileProcessor
from app.middleware.security import (
    RateLimitMiddleware,
    CSRFProtectionMiddleware, 
    SecurityHeadersMiddleware,
    SecurityEventLogger
)

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
file_watcher_service: FileWatcherService = None
background_processor_service: BackgroundFileProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global file_watcher_service, background_processor_service
    
    # Startup
    logger.info("Starting Professional Poker Analyzer API")
    
    # Initialize background processor service
    try:
        background_processor_service = BackgroundFileProcessor(async_session_maker)
        await background_processor_service.start_service()
        logger.info("Background processor service started successfully")
        degradation_manager.mark_service_up("file_monitoring")
    except Exception as e:
        logger.error(f"Failed to start background processor service: {e}")
        degradation_manager.mark_service_down("file_monitoring")
    
    # Initialize file watcher service
    try:
        file_watcher_service = FileWatcherService(async_session_maker)
        await file_watcher_service.start_service()
        logger.info("File watcher service started successfully")
        degradation_manager.mark_service_up("file_monitoring")
    except Exception as e:
        logger.error(f"Failed to start file watcher service: {e}")
        degradation_manager.mark_service_down("file_monitoring")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Professional Poker Analyzer API")
    
    # Stop background processor service
    if background_processor_service:
        try:
            await background_processor_service.stop_service()
            logger.info("Background processor service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping background processor service: {e}")
    
    # Stop file watcher service
    if file_watcher_service:
        try:
            await file_watcher_service.stop_service()
            logger.info("File watcher service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping file watcher service: {e}")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
        # Custom OpenAPI configuration
        openapi_tags=[
            {
                "name": "authentication",
                "description": "User authentication and authorization operations"
            },
            {
                "name": "hand-history", 
                "description": "Poker hand history management and parsing"
            },
            {
                "name": "statistics",
                "description": "Poker statistics calculation and analysis"
            },
            {
                "name": "ai-analysis",
                "description": "AI-powered poker hand and session analysis"
            },
            {
                "name": "user-management",
                "description": "User profile and preferences management"
            },
            {
                "name": "monitoring",
                "description": "System monitoring and health check operations"
            },
            {
                "name": "file-monitoring",
                "description": "Hand history file monitoring and auto-import"
            }
        ]
    )
    
    # Include API router with versioning
    application.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Add comprehensive error handlers
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(Exception, general_exception_handler)
    
    return application


app = create_application()

# Add security middleware (order matters - add in reverse order of execution)
if settings.SECURITY_HEADERS_ENABLED:
    app.add_middleware(SecurityHeadersMiddleware)

# Add CSRF protection middleware
app.add_middleware(CSRFProtectionMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, redis_url=settings.REDIS_URL)

# Add CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    This is a fallback - most errors should be handled by the comprehensive error handlers.
    """
    logger.error(
        "Fallback exception handler triggered: %s (%s) at %s %s",
        str(exc),
        type(exc).__name__,
        request.method,
        request.url.path
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "message": "An unexpected error occurred. Our team has been notified."
            }
        }
    )


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Professional Poker Analyzer API",
        "version": settings.VERSION,
        "status": "healthy",
        "api_docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint with service status."""
    return await get_system_health()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )