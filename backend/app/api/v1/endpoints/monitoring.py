"""
Monitoring and health check endpoints.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.monitoring import metrics_collector, performance_monitor, startup_monitoring, shutdown_monitoring
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    environment: str
    monitoring: Dict[str, Any]
    timestamp: datetime


class MetricsResponse(BaseModel):
    """Metrics response model."""
    total_metrics: int
    metric_names: List[str]
    system_metrics_count: int
    collection_running: bool
    latest_system_metrics: Dict[str, Any] = None


class AlertResponse(BaseModel):
    """Alert response model."""
    type: str
    message: str
    threshold: float
    current: float
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Get system health status.
    
    Returns comprehensive health information including:
    - Overall system status
    - Monitoring metrics
    - Recent alerts
    """
    try:
        health_status = performance_monitor.get_health_status()
        
        from app.core.config import settings
        
        return HealthResponse(
            status=health_status["status"],
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            monitoring={
                "metrics_collected": len(metrics_collector.metrics),
                "system_metrics_count": len(metrics_collector.system_metrics),
                "recent_alerts": health_status["recent_alerts"],
                "collection_running": metrics_collector._running,
                "thresholds": health_status["thresholds"]
            },
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get application metrics summary.
    
    Returns:
    - Total number of metrics collected
    - Available metric names
    - System metrics count
    - Latest system metrics
    """
    try:
        summary = metrics_collector.get_summary()
        
        return MetricsResponse(
            total_metrics=summary["total_metrics"],
            metric_names=summary["metric_names"],
            system_metrics_count=summary["system_metrics_count"],
            collection_running=summary["collection_running"],
            latest_system_metrics=summary.get("latest_system_metrics")
        )
        
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/metrics/{metric_name}")
async def get_metric_details(
    metric_name: str,
    hours: int = Query(default=1, ge=1, le=24, description="Hours of data to retrieve")
):
    """
    Get detailed data for a specific metric.
    
    Args:
        metric_name: Name of the metric to retrieve
        hours: Number of hours of historical data to include
    
    Returns:
        Detailed metric data points
    """
    try:
        since = datetime.now() - timedelta(hours=hours)
        points = metrics_collector.get_metrics(metric_name, since=since)
        
        if not points:
            raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")
        
        return {
            "metric_name": metric_name,
            "data_points": len(points),
            "time_range_hours": hours,
            "data": [
                {
                    "timestamp": point.timestamp.isoformat(),
                    "value": point.value,
                    "tags": point.tags
                }
                for point in points
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get metric details", metric_name=metric_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metric details")


@router.get("/system-metrics")
async def get_system_metrics(
    hours: int = Query(default=1, ge=1, le=24, description="Hours of data to retrieve")
):
    """
    Get system resource metrics.
    
    Args:
        hours: Number of hours of historical data to include
    
    Returns:
        System metrics including CPU, memory, disk usage
    """
    try:
        since = datetime.now() - timedelta(hours=hours)
        system_metrics = metrics_collector.get_system_metrics(since=since)
        
        return {
            "data_points": len(system_metrics),
            "time_range_hours": hours,
            "data": [
                {
                    "timestamp": metrics.timestamp.isoformat(),
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                    "memory_used_mb": metrics.memory_used_mb,
                    "disk_usage_percent": metrics.disk_usage_percent,
                    "active_connections": metrics.active_connections
                }
                for metrics in system_metrics
            ]
        }
        
    except Exception as e:
        logger.error("Failed to get system metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts():
    """
    Get current performance alerts.
    
    Returns:
        List of active performance alerts
    """
    try:
        alerts = performance_monitor.check_performance_thresholds()
        
        return [
            AlertResponse(
                type=alert["type"],
                message=alert["message"],
                threshold=alert["threshold"],
                current=alert["current"],
                timestamp=alert["timestamp"]
            )
            for alert in alerts
        ]
        
    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/collect-metrics")
async def trigger_metrics_collection():
    """
    Manually trigger system metrics collection.
    
    Useful for testing or immediate metrics gathering.
    """
    try:
        metrics = await metrics_collector.collect_system_metrics()
        
        return {
            "message": "Metrics collected successfully",
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "memory_used_mb": metrics.memory_used_mb,
            "disk_usage_percent": metrics.disk_usage_percent,
            "active_connections": metrics.active_connections
        }
        
    except Exception as e:
        logger.error("Failed to collect metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to collect metrics")