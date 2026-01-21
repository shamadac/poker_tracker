"""
Performance monitoring and metrics collection system.
"""
import asyncio
import time
import psutil
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Performance alert."""
    id: str
    type: str
    severity: AlertSeverity
    message: str
    threshold: float
    current: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class MetricPoint:
    """A single metric measurement."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """Collects and stores application metrics."""
    
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.system_metrics: deque = deque(maxlen=max_points)
        self._collection_task: Optional[asyncio.Task] = None
        self._running = False
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record a metric point."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags or {}
        )
        self.metrics[name].append(point)
    
    def get_metrics(self, name: str, since: Optional[datetime] = None) -> List[MetricPoint]:
        """Get metrics for a given name, optionally filtered by time."""
        points = list(self.metrics[name])
        
        if since:
            points = [p for p in points if p.timestamp >= since]
        
        return points
    
    def get_system_metrics(self, since: Optional[datetime] = None) -> List[SystemMetrics]:
        """Get system metrics, optionally filtered by time."""
        metrics = list(self.system_metrics)
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            
            # Disk usage (use C: drive on Windows, / on Unix)
            import os
            if os.name == 'nt':  # Windows
                disk = psutil.disk_usage('C:')
            else:  # Unix/Linux/Mac
                disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network connections (approximate active connections)
            connections = len(psutil.net_connections())
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                active_connections=connections
            )
            
            self.system_metrics.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
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
                    logger.error("Error in metrics collection loop", error=str(e))
                    await asyncio.sleep(interval)
        
        self._collection_task = asyncio.create_task(collection_loop())
    
    async def stop_collection(self) -> None:
        """Stop metrics collection."""
        self._running = False
        
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
    
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
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_used_mb": latest.memory_used_mb,
                "disk_usage_percent": latest.disk_usage_percent,
                "active_connections": latest.active_connections,
                "timestamp": latest.timestamp.isoformat()
            }
        
        return summary


class AlertManager:
    """Manages performance alerts and notifications."""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.notification_handlers: List[Callable[[Alert], None]] = []
        self.alert_history: List[Alert] = []
    
    def add_notification_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add a notification handler for alerts."""
        self.notification_handlers.append(handler)
    
    def create_alert(self, alert_type: str, severity: AlertSeverity, message: str, 
                    threshold: float, current: float) -> Alert:
        """Create a new alert."""
        import uuid
        alert = Alert(
            id=str(uuid.uuid4()),
            type=alert_type,
            severity=severity,
            message=message,
            threshold=threshold,
            current=current,
            timestamp=datetime.now()
        )
        
        # Store alert
        self.alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Notify handlers
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error("Failed to send alert notification", 
                           alert_id=alert.id, error=str(e))
        
        logger.warning("Performance alert created", 
                      alert_type=alert_type, 
                      severity=severity.value,
                      message=message,
                      threshold=threshold,
                      current=current)
        
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            logger.info("Performance alert resolved", 
                       alert_id=alert_id, 
                       alert_type=alert.type)
            return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff]


class PerformanceMonitor:
    """Monitor application performance and detect issues."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alert_manager = AlertManager()
        self.thresholds = {
            "response_time_ms": 1000,  # 1 second
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_usage_percent": 90,
            "error_rate_percent": 5
        }
        
        # Setup default notification handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """Setup default alert notification handlers."""
        # Console logging handler (always enabled)
        def console_handler(alert: Alert):
            logger.warning(f"ALERT: {alert.message}", 
                         alert_type=alert.type,
                         severity=alert.severity.value,
                         threshold=alert.threshold,
                         current=alert.current)
        
        self.alert_manager.add_notification_handler(console_handler)
    
    def add_email_alerting(self, smtp_host: str, smtp_port: int, 
                          username: str, password: str, 
                          recipients: List[str]) -> None:
        """Add email alerting for critical alerts."""
        def email_handler(alert: Alert):
            if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                try:
                    self._send_email_alert(alert, smtp_host, smtp_port, 
                                         username, password, recipients)
                except Exception as e:
                    logger.error("Failed to send email alert", 
                               alert_id=alert.id, error=str(e))
        
        self.alert_manager.add_notification_handler(email_handler)
    
    def _send_email_alert(self, alert: Alert, smtp_host: str, smtp_port: int,
                         username: str, password: str, recipients: List[str]) -> None:
        """Send email alert notification."""
        msg = MimeMultipart()
        msg['From'] = username
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = f"Performance Alert: {alert.type} ({alert.severity.value.upper()})"
        
        body = f"""
        Performance Alert Details:
        
        Type: {alert.type}
        Severity: {alert.severity.value.upper()}
        Message: {alert.message}
        Threshold: {alert.threshold}
        Current Value: {alert.current}
        Timestamp: {alert.timestamp}
        
        Please investigate this issue promptly.
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
    
    def check_performance_thresholds(self) -> List[Alert]:
    def check_performance_thresholds(self) -> List[Alert]:
        """Check if any performance thresholds are exceeded."""
        new_alerts = []
        
        # Check system metrics
        if self.metrics.system_metrics:
            latest = self.metrics.system_metrics[-1]
            
            if latest.cpu_percent > self.thresholds["cpu_percent"]:
                severity = AlertSeverity.HIGH if latest.cpu_percent > 90 else AlertSeverity.MEDIUM
                alert = self.alert_manager.create_alert(
                    alert_type="high_cpu",
                    severity=severity,
                    message=f"CPU usage is {latest.cpu_percent:.1f}%",
                    threshold=self.thresholds["cpu_percent"],
                    current=latest.cpu_percent
                )
                new_alerts.append(alert)
            
            if latest.memory_percent > self.thresholds["memory_percent"]:
                severity = AlertSeverity.CRITICAL if latest.memory_percent > 95 else AlertSeverity.HIGH
                alert = self.alert_manager.create_alert(
                    alert_type="high_memory",
                    severity=severity,
                    message=f"Memory usage is {latest.memory_percent:.1f}%",
                    threshold=self.thresholds["memory_percent"],
                    current=latest.memory_percent
                )
                new_alerts.append(alert)
            
            if latest.disk_usage_percent > self.thresholds["disk_usage_percent"]:
                severity = AlertSeverity.CRITICAL if latest.disk_usage_percent > 95 else AlertSeverity.HIGH
                alert = self.alert_manager.create_alert(
                    alert_type="high_disk",
                    severity=severity,
                    message=f"Disk usage is {latest.disk_usage_percent:.1f}%",
                    threshold=self.thresholds["disk_usage_percent"],
                    current=latest.disk_usage_percent
                )
                new_alerts.append(alert)
        
        # Check response time metrics
        response_times = self.metrics.get_metrics("response_time", since=datetime.now() - timedelta(minutes=5))
        if response_times:
            avg_response_time = sum(p.value for p in response_times) / len(response_times)
            if avg_response_time > self.thresholds["response_time_ms"]:
                severity = AlertSeverity.HIGH if avg_response_time > 2000 else AlertSeverity.MEDIUM
                alert = self.alert_manager.create_alert(
                    alert_type="slow_response",
                    severity=severity,
                    message=f"Average response time is {avg_response_time:.1f}ms",
                    threshold=self.thresholds["response_time_ms"],
                    current=avg_response_time
                )
                new_alerts.append(alert)
        
        # Check error rate
        error_metrics = self.metrics.get_metrics("errors_total", since=datetime.now() - timedelta(minutes=5))
        request_metrics = self.metrics.get_metrics("requests_total", since=datetime.now() - timedelta(minutes=5))
        
        if error_metrics and request_metrics:
            error_count = sum(p.value for p in error_metrics)
            request_count = sum(p.value for p in request_metrics)
            
            if request_count > 0:
                error_rate = (error_count / request_count) * 100
                if error_rate > self.thresholds["error_rate_percent"]:
                    severity = AlertSeverity.CRITICAL if error_rate > 20 else AlertSeverity.HIGH
                    alert = self.alert_manager.create_alert(
                        alert_type="high_error_rate",
                        severity=severity,
                        message=f"Error rate is {error_rate:.1f}%",
                        threshold=self.thresholds["error_rate_percent"],
                        current=error_rate
                    )
                    new_alerts.append(alert)
        
        return new_alerts
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        active_alerts = self.alert_manager.get_active_alerts()
        recent_alerts = self.alert_manager.get_alert_history(hours=1)
        
        # Determine status based on alert severity
        status = "healthy"
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        high_alerts = [a for a in active_alerts if a.severity == AlertSeverity.HIGH]
        
        if critical_alerts:
            status = "critical"
        elif high_alerts:
            status = "degraded"
        elif active_alerts:
            status = "warning"
        
        return {
            "status": status,
            "active_alerts": len(active_alerts),
            "recent_alerts": len(recent_alerts),
            "critical_alerts": len(critical_alerts),
            "high_alerts": len(high_alerts),
            "thresholds": self.thresholds,
            "last_check": datetime.now().isoformat()
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor(metrics_collector)


async def startup_monitoring():
    """Start monitoring services."""
    await metrics_collector.start_collection()
    logger.info("Monitoring services started")


async def shutdown_monitoring():
    """Stop monitoring services."""
    await metrics_collector.stop_collection()
    logger.info("Monitoring services stopped")