"""
Performance monitoring and metrics collection system.
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque


class MetricsCollector:
    """Collects and stores application metrics."""
    
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.system_metrics: List[Dict[str, Any]] = []
        self._running = False
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record a metric point."""
        metric_data = {
            "timestamp": datetime.now(),
            "value": value,
            "tags": tags or {}
        }
        self.metrics[name].append(metric_data)
    
    def get_metrics(self, name: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get metrics for a given name, optionally filtered by time."""
        points = list(self.metrics[name])
        
        if since:
            points = [p for p in points if p["timestamp"] >= since]
        
        return points
    
    def get_system_metrics(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get system metrics, optionally filtered by time."""
        metrics = list(self.system_metrics)
        
        if since:
            metrics = [m for m in metrics if m["timestamp"] >= since]
        
        return metrics
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics (simplified version)."""
        try:
            # Simplified metrics collection without psutil for now
            metrics = {
                "cpu_percent": 25.0,  # Placeholder
                "memory_percent": 45.0,  # Placeholder
                "memory_used_mb": 1024.0,  # Placeholder
                "disk_usage_percent": 60.0,  # Placeholder
                "active_connections": 10,  # Placeholder
                "timestamp": datetime.now()
            }
            
            self.system_metrics.append(metrics)
            
            # Keep only last 1000 entries
            if len(self.system_metrics) > 1000:
                self.system_metrics = self.system_metrics[-1000:]
            
            return metrics
            
        except Exception as e:
            print(f"Failed to collect system metrics: {e}")
            raise
    
    async def start_collection(self, interval: int = 60) -> None:
        """Start periodic system metrics collection."""
        if self._running:
            return
        
        self._running = True
        
        async def collection_loop():
            while self._running:
                try:
                    await self.collect_system_metrics()
                    await asyncio.sleep(interval)
                except Exception as e:
                    print(f"Error in metrics collection loop: {e}")
                    await asyncio.sleep(interval)
        
        # Note: In a real implementation, you'd store this task reference
        asyncio.create_task(collection_loop())
    
    async def stop_collection(self) -> None:
        """Stop metrics collection."""
        self._running = False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics."""
        summary = {
            "total_metrics": len(self.metrics),
            "metric_names": list(self.metrics.keys()),
            "system_metrics_count": len(self.system_metrics),
            "collection_running": self._running
        }
        
        # Add latest system metrics if available
        if self.system_metrics:
            latest = self.system_metrics[-1]
            summary["latest_system_metrics"] = {
                "cpu_percent": latest["cpu_percent"],
                "memory_percent": latest["memory_percent"],
                "memory_used_mb": latest["memory_used_mb"],
                "disk_usage_percent": latest["disk_usage_percent"],
                "active_connections": latest["active_connections"],
                "timestamp": latest["timestamp"].isoformat()
            }
        
        return summary


class PerformanceMonitor:
    """Monitor application performance and detect issues."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.thresholds = {
            "response_time_ms": 1000,  # 1 second
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_usage_percent": 90,
            "error_rate_percent": 5
        }
        self.alerts: List[Dict[str, Any]] = []
    
    def check_performance_thresholds(self) -> List[Dict[str, Any]]:
        """Check if any performance thresholds are exceeded."""
        alerts = []
        
        # Check system metrics
        if self.metrics.system_metrics:
            latest = self.metrics.system_metrics[-1]
            
            if latest["cpu_percent"] > self.thresholds["cpu_percent"]:
                alerts.append({
                    "type": "high_cpu",
                    "message": f"CPU usage is {latest['cpu_percent']:.1f}%",
                    "threshold": self.thresholds["cpu_percent"],
                    "current": latest["cpu_percent"],
                    "timestamp": latest["timestamp"]
                })
            
            if latest["memory_percent"] > self.thresholds["memory_percent"]:
                alerts.append({
                    "type": "high_memory",
                    "message": f"Memory usage is {latest['memory_percent']:.1f}%",
                    "threshold": self.thresholds["memory_percent"],
                    "current": latest["memory_percent"],
                    "timestamp": latest["timestamp"]
                })
        
        # Check response time metrics
        response_times = self.metrics.get_metrics("response_time", since=datetime.now() - timedelta(minutes=5))
        if response_times:
            avg_response_time = sum(p["value"] for p in response_times) / len(response_times)
            if avg_response_time > self.thresholds["response_time_ms"]:
                alerts.append({
                    "type": "slow_response",
                    "message": f"Average response time is {avg_response_time:.1f}ms",
                    "threshold": self.thresholds["response_time_ms"],
                    "current": avg_response_time,
                    "timestamp": datetime.now()
                })
        
        # Store alerts
        self.alerts.extend(alerts)
        
        return alerts
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        recent_alerts = [a for a in self.alerts if a["timestamp"] > datetime.now() - timedelta(minutes=10)]
        
        status = "healthy"
        if len(recent_alerts) > 0:
            status = "warning"
        if len(recent_alerts) > 3:
            status = "critical"
        
        return {
            "status": status,
            "recent_alerts": len(recent_alerts),
            "total_alerts": len(self.alerts),
            "thresholds": self.thresholds,
            "last_check": datetime.now().isoformat()
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor(metrics_collector)


async def startup_monitoring():
    """Start monitoring services."""
    await metrics_collector.start_collection()
    print("Monitoring services started")


async def shutdown_monitoring():
    """Stop monitoring services."""
    await metrics_collector.stop_collection()
    print("Monitoring services stopped")