"""
API v1 router configuration.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, hands, stats, analysis, users, monitoring, rbac, file_monitoring, file_processing, performance

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(hands.router, prefix="/hands", tags=["hand-history"])
api_router.include_router(stats.router, prefix="/stats", tags=["statistics"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["ai-analysis"])
api_router.include_router(users.router, prefix="/users", tags=["user-management"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(file_monitoring.router, prefix="/file-monitoring", tags=["file-monitoring"])
api_router.include_router(file_processing.router, prefix="/file-processing", tags=["file-processing"])
api_router.include_router(rbac.router, prefix="/rbac", tags=["role-based-access-control"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance-optimization"])