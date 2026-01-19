#!/usr/bin/env python3
"""
Performance monitoring and cache management API endpoints.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.cache_service import get_cache_service, get_stats_cache, CacheService
from app.services.database_optimizer import get_db_optimizer, DatabaseOptimizer
from app.middleware.authorization import require_permission

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/cache/stats")
async def get_cache_statistics(
    cache_service: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get Redis cache statistics and performance metrics.
    
    Returns cache hit rates, memory usage, and connection info.
    """
    try:
        cache_stats = await cache_service.get_cache_stats()
        
        return {
            "status": "success",
            "data": {
                "cache_stats": cache_stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ttl_config": cache_service.ttl_config,
                "connected": cache_service.connected
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@router.post("/cache/invalidate/user/{user_id}")
async def invalidate_user_cache(
    user_id: str,
    cache_service: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invalidate all cache entries for a specific user.
    
    Requires admin permission or user must be invalidating their own cache.
    """
    # Check permissions - user can invalidate their own cache or admin can invalidate any
    if str(current_user.id) != user_id:
        await require_permission(db, current_user.id, "admin", "cache_management")
    
    try:
        deleted_count = await cache_service.invalidate_user_cache(user_id)
        
        return {
            "status": "success",
            "message": f"Invalidated {deleted_count} cache entries for user {user_id}",
            "data": {
                "user_id": user_id,
                "deleted_entries": deleted_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error invalidating user cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate user cache: {str(e)}"
        )


@router.post("/cache/invalidate/pattern")
async def invalidate_cache_pattern(
    pattern: str,
    cache_service: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invalidate cache entries matching a specific pattern.
    
    Requires admin permission.
    """
    await require_permission(db, current_user.id, "admin", "cache_management")
    
    try:
        deleted_count = await cache_service.invalidate_pattern(pattern)
        
        return {
            "status": "success",
            "message": f"Invalidated {deleted_count} cache entries matching pattern '{pattern}'",
            "data": {
                "pattern": pattern,
                "deleted_entries": deleted_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache pattern: {str(e)}"
        )


@router.get("/database/performance")
async def get_database_performance(
    db_optimizer: DatabaseOptimizer = Depends(get_db_optimizer),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get database performance analysis and recommendations.
    
    Requires admin permission.
    """
    await require_permission(db, current_user.id, "admin", "performance_monitoring")
    
    try:
        performance_analysis = await db_optimizer.analyze_query_performance(db)
        
        return {
            "status": "success",
            "data": {
                "performance_analysis": performance_analysis,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting database performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve database performance: {str(e)}"
        )


@router.post("/database/optimize/indexes")
async def optimize_database_indexes(
    db_optimizer: DatabaseOptimizer = Depends(get_db_optimizer),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Optimize database indexes for better query performance.
    
    Creates recommended indexes for common query patterns.
    Requires admin permission.
    """
    await require_permission(db, current_user.id, "admin", "database_optimization")
    
    try:
        optimization_results = await db_optimizer.optimize_statistics_queries(db)
        
        return {
            "status": "success",
            "message": f"Index optimization completed. Created {len(optimization_results['indexes_created'])} indexes.",
            "data": {
                "optimization_results": optimization_results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error optimizing database indexes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize database indexes: {str(e)}"
        )


@router.post("/database/vacuum")
async def vacuum_analyze_database(
    db_optimizer: DatabaseOptimizer = Depends(get_db_optimizer),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run VACUUM ANALYZE on important tables for performance optimization.
    
    This helps maintain database performance by updating statistics
    and reclaiming space. Requires admin permission.
    """
    await require_permission(db, current_user.id, "admin", "database_maintenance")
    
    try:
        vacuum_results = await db_optimizer.vacuum_analyze_tables(db)
        
        return {
            "status": "success",
            "message": f"VACUUM ANALYZE completed on {len(vacuum_results['tables_processed'])} tables in {vacuum_results['total_time']}s",
            "data": {
                "vacuum_results": vacuum_results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error running VACUUM ANALYZE: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run VACUUM ANALYZE: {str(e)}"
        )


@router.get("/performance/summary")
async def get_performance_summary(
    cache_service: CacheService = Depends(get_cache_service),
    db_optimizer: DatabaseOptimizer = Depends(get_db_optimizer),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive performance summary including cache and database metrics.
    
    Provides overview of system performance for monitoring dashboards.
    """
    try:
        # Get cache statistics
        cache_stats = await cache_service.get_cache_stats()
        
        # Get basic database performance info (without requiring admin permissions)
        query_stats = db_optimizer.query_stats.copy()
        
        # Calculate summary metrics
        total_queries = sum(stats['count'] for stats in query_stats.values())
        total_slow_queries = sum(stats['slow_queries'] for stats in query_stats.values())
        avg_query_time = (
            sum(stats['avg_time'] * stats['count'] for stats in query_stats.values()) / total_queries
            if total_queries > 0 else 0
        )
        
        performance_summary = {
            "cache": {
                "connected": cache_stats.get("connected", False),
                "hit_rate": cache_stats.get("hit_rate", 0),
                "used_memory": cache_stats.get("used_memory", "N/A")
            },
            "database": {
                "total_queries": total_queries,
                "slow_queries": total_slow_queries,
                "slow_query_percentage": (total_slow_queries / total_queries * 100) if total_queries > 0 else 0,
                "average_query_time": round(avg_query_time, 4)
            },
            "recommendations": []
        }
        
        # Add basic recommendations
        if cache_stats.get("hit_rate", 0) < 80:
            performance_summary["recommendations"].append({
                "type": "cache_performance",
                "message": "Cache hit rate is below 80%. Consider reviewing cache TTL settings."
            })
        
        if total_slow_queries > 0:
            performance_summary["recommendations"].append({
                "type": "query_performance", 
                "message": f"{total_slow_queries} slow queries detected. Consider database optimization."
            })
        
        return {
            "status": "success",
            "data": {
                "performance_summary": performance_summary,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance summary: {str(e)}"
        )


@router.get("/health/detailed")
async def get_detailed_health_check(
    cache_service: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Detailed health check including cache and database connectivity.
    
    Public endpoint for monitoring systems.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }
    
    # Check database connectivity
    try:
        await db.execute("SELECT 1")
        health_status["services"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "degraded"
    
    # Check Redis connectivity
    try:
        if not cache_service.connected:
            await cache_service.connect()
        
        if cache_service.connected:
            health_status["services"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        else:
            health_status["services"]["redis"] = {
                "status": "unhealthy", 
                "message": "Redis connection failed"
            }
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection error: {str(e)}"
        }
        health_status["status"] = "degraded"
    
    return health_status