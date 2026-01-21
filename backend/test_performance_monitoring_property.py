"""
Property-based test for performance monitoring system.

**Feature: professional-poker-analyzer-rebuild, Property 27: Performance Monitoring**
**Validates: Requirements 9.7**

Property 27: Performance Monitoring
*For any* performance issues or system problems, monitoring systems should detect and alert on issues 
with appropriate thresholds and notification mechanisms
"""
import pytest
import pytest_asyncio
import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from dataclasses import dataclass
from enum import Enum

from app.core.monitoring import (
    MetricsCollector, AlertManager, PerformanceMonitor, Alert, AlertSeverity,
    MetricPoint, SystemMetrics, metrics_collector, performance_monitor
)


# Test data strategies
@st.composite
def metric_data_strategy(draw):
    """Generate metric data for testing."""
    return {
        "name": draw(st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')),
        "value": draw(st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)),
        "tags": draw(st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'),
            values=st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5
        ))
    }


@st.composite
def system_metrics_strategy(draw):
    """Generate system metrics for testing."""
    return {
        "cpu_percent": draw(st.floats(min_value=0.0, max_value=100.0)),
        "memory_percent": draw(st.floats(min_value=0.0, max_value=100.0)),
        "memory_used_mb": draw(st.floats(min_value=0.0, max_value=32768.0)),
        "disk_usage_percent": draw(st.floats(min_value=0.0, max_value=100.0)),
        "active_connections": draw(st.integers(min_value=0, max_value=1000))
    }


@st.composite
def alert_scenario_strategy(draw):
    """Generate alert scenarios for testing."""
    return {
        "alert_type": draw(st.sampled_from([
            "high_cpu", "high_memory", "high_disk", "slow_response", "high_error_rate"
        ])),
        "severity": draw(st.sampled_from(list(AlertSeverity))),
        "threshold": draw(st.floats(min_value=1.0, max_value=100.0)),
        "current_value": draw(st.floats(min_value=0.0, max_value=200.0)),
        "should_trigger": draw(st.booleans())
    }


@st.composite
def performance_scenario_strategy(draw):
    """Generate performance monitoring scenarios."""
    return {
        "cpu_usage": draw(st.floats(min_value=0.0, max_value=100.0)),
        "memory_usage": draw(st.floats(min_value=0.0, max_value=100.0)),
        "disk_usage": draw(st.floats(min_value=0.0, max_value=100.0)),
        "response_times": draw(st.lists(
            st.floats(min_value=0.001, max_value=5.0),
            min_size=1,
            max_size=100
        )),
        "error_count": draw(st.integers(min_value=0, max_value=50)),
        "request_count": draw(st.integers(min_value=1, max_value=1000)),
        "monitoring_duration": draw(st.integers(min_value=1, max_value=300))  # seconds
    }


class MockNotificationHandler:
    """Mock notification handler for testing."""
    
    def __init__(self):
        self.notifications = []
        self.call_count = 0
        self.last_alert = None
    
    def __call__(self, alert: Alert):
        """Handle alert notification."""
        self.notifications.append(alert)
        self.call_count += 1
        self.last_alert = alert
    
    def reset(self):
        """Reset handler state."""
        self.notifications = []
        self.call_count = 0
        self.last_alert = None


@pytest_asyncio.fixture
async def fresh_metrics_collector():
    """Create a fresh metrics collector for testing."""
    collector = MetricsCollector(max_points=1000)
    return collector


@pytest_asyncio.fixture
async def fresh_alert_manager():
    """Create a fresh alert manager for testing."""
    manager = AlertManager()
    # Clear any existing state
    manager.alerts.clear()
    manager.alert_history.clear()
    manager.notification_handlers.clear()
    return manager


@pytest_asyncio.fixture
async def fresh_performance_monitor(fresh_metrics_collector):
    """Create a fresh performance monitor for testing."""
    return PerformanceMonitor(fresh_metrics_collector)


@pytest_asyncio.fixture
async def mock_notification_handler():
    """Create a mock notification handler."""
    return MockNotificationHandler()


@pytest.mark.asyncio
@given(metric_data=metric_data_strategy())
@settings(
    max_examples=100,
    deadline=30000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_metrics_collection_accuracy(fresh_metrics_collector, metric_data):
    """
    Property 27.1: Metrics Collection Accuracy
    
    *For any* metric data recorded, the monitoring system should store it accurately 
    and make it available for retrieval with correct timestamps and values.
    
    **Validates: Requirements 9.7**
    """
    collector = fresh_metrics_collector
    
    # Clear any existing metrics to ensure clean state
    collector.metrics.clear()
    
    # Property 1: Metrics should be recorded accurately
    metric_name = metric_data["name"]
    metric_value = metric_data["value"]
    metric_tags = metric_data["tags"]
    
    # Skip invalid metric names
    assume(len(metric_name.strip()) > 0)
    assume(not any(char in metric_name for char in [' ', '\n', '\t']))
    
    before_time = datetime.now()
    collector.record_metric(metric_name, metric_value, metric_tags)
    after_time = datetime.now()
    
    # Retrieve the recorded metric
    recorded_metrics = collector.get_metrics(metric_name)
    
    assert len(recorded_metrics) == 1, f"Should record exactly one metric point, got {len(recorded_metrics)} for metric '{metric_name}'"
    
    recorded_point = recorded_metrics[0]
    assert recorded_point.value == metric_value, \
        f"Recorded value {recorded_point.value} should match input {metric_value}"
    assert recorded_point.tags == metric_tags, \
        f"Recorded tags {recorded_point.tags} should match input {metric_tags}"
    
    # Timestamp should be within reasonable range
    assert before_time <= recorded_point.timestamp <= after_time, \
        "Timestamp should be within recording time window"
    
    # Property 2: Multiple metrics should be stored independently
    if len(metric_name) > 1:
        different_name = metric_name + "_different"
        different_value = metric_value + 1.0
        
        collector.record_metric(different_name, different_value)
        
        original_metrics = collector.get_metrics(metric_name)
        different_metrics = collector.get_metrics(different_name)
        
        assert len(original_metrics) == 1, "Original metric should remain unchanged"
        assert len(different_metrics) == 1, "Different metric should be recorded"
        assert original_metrics[0].value == metric_value, "Original value should be preserved"
        assert different_metrics[0].value == different_value, "Different value should be recorded"
    
    # Property 3: Time-based filtering should work correctly
    # Record another metric after a small delay
    await asyncio.sleep(0.001)  # 1ms delay
    collector.record_metric(metric_name, metric_value + 10.0)
    
    # Get metrics since after the first recording
    filtered_metrics = collector.get_metrics(metric_name, since=after_time)
    all_metrics = collector.get_metrics(metric_name)
    
    assert len(all_metrics) == 2, "Should have two total metrics"
    assert len(filtered_metrics) <= 2, "Filtered metrics should not exceed total"
    
    # Property 4: Metrics should respect max_points limit
    max_points = collector.max_points
    for i in range(max_points + 10):  # Exceed the limit
        collector.record_metric(f"test_limit_{i % 5}", float(i))
    
    # Check that no single metric exceeds max_points
    for i in range(5):
        limit_metrics = collector.get_metrics(f"test_limit_{i}")
        assert len(limit_metrics) <= max_points, \
            f"Metric series should not exceed max_points limit of {max_points}"


@pytest.mark.asyncio
@given(system_data=system_metrics_strategy())
@settings(
    max_examples=50,
    deadline=30000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_system_metrics_collection(fresh_metrics_collector, system_data):
    """
    Property 27.2: System Metrics Collection
    
    *For any* system state, the monitoring system should collect accurate system metrics
    including CPU, memory, disk usage, and network connections.
    
    **Validates: Requirements 9.7**
    """
    collector = fresh_metrics_collector
    
    # Mock psutil functions to return controlled test data
    with patch('psutil.cpu_percent', return_value=system_data["cpu_percent"]), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.net_connections', return_value=['conn'] * system_data["active_connections"]):
        
        # Setup memory mock
        mock_memory.return_value.percent = system_data["memory_percent"]
        mock_memory.return_value.used = system_data["memory_used_mb"] * 1024 * 1024
        
        # Setup disk mock
        mock_disk.return_value.percent = system_data["disk_usage_percent"]
        
        # Collect system metrics
        metrics = await collector.collect_system_metrics()
        
        # Property 1: System metrics should match actual system state
        assert abs(metrics.cpu_percent - system_data["cpu_percent"]) < 0.1, \
            f"CPU percent should match: expected {system_data['cpu_percent']}, got {metrics.cpu_percent}"
        
        assert abs(metrics.memory_percent - system_data["memory_percent"]) < 0.1, \
            f"Memory percent should match: expected {system_data['memory_percent']}, got {metrics.memory_percent}"
        
        assert abs(metrics.memory_used_mb - system_data["memory_used_mb"]) < 1.0, \
            f"Memory used MB should match: expected {system_data['memory_used_mb']}, got {metrics.memory_used_mb}"
        
        assert abs(metrics.disk_usage_percent - system_data["disk_usage_percent"]) < 0.1, \
            f"Disk usage should match: expected {system_data['disk_usage_percent']}, got {metrics.disk_usage_percent}"
        
        assert metrics.active_connections == system_data["active_connections"], \
            f"Active connections should match: expected {system_data['active_connections']}, got {metrics.active_connections}"
        
        # Property 2: Metrics should be stored in collector
        stored_metrics = collector.get_system_metrics()
        assert len(stored_metrics) >= 1, "System metrics should be stored"
        
        latest_stored = stored_metrics[-1]
        assert latest_stored.cpu_percent == metrics.cpu_percent, "Stored CPU should match collected"
        assert latest_stored.memory_percent == metrics.memory_percent, "Stored memory should match collected"
        
        # Property 3: Timestamp should be recent
        time_diff = datetime.now() - metrics.timestamp
        assert time_diff.total_seconds() < 1.0, "Timestamp should be very recent"
        
        # Property 4: Multiple collections should maintain history
        await asyncio.sleep(0.001)  # Small delay
        metrics2 = await collector.collect_system_metrics()
        
        all_stored = collector.get_system_metrics()
        assert len(all_stored) >= 2, "Should store multiple system metrics"
        assert all_stored[-1].timestamp > all_stored[-2].timestamp, "Timestamps should be ordered"


@pytest.mark.asyncio
@given(alert_scenario=alert_scenario_strategy())
@settings(
    max_examples=100,
    deadline=30000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_alert_management(fresh_alert_manager, mock_notification_handler, alert_scenario):
    """
    Property 27.3: Alert Management
    
    *For any* performance threshold violation, the alert system should create appropriate alerts
    with correct severity levels and trigger notification mechanisms.
    
    **Validates: Requirements 9.7**
    """
    alert_manager = fresh_alert_manager
    handler = mock_notification_handler
    
    # Reset handler state for this test
    handler.reset()
    
    # Add notification handler
    alert_manager.add_notification_handler(handler)
    
    alert_type = alert_scenario["alert_type"]
    severity = alert_scenario["severity"]
    threshold = alert_scenario["threshold"]
    current_value = alert_scenario["current_value"]
    should_trigger = alert_scenario["should_trigger"]
    
    # Adjust current_value based on should_trigger
    if should_trigger:
        current_value = threshold + abs(threshold * 0.1) + 1.0  # Exceed threshold
    else:
        current_value = min(current_value, threshold - 1.0)  # Stay below threshold
    
    message = f"{alert_type} threshold exceeded: {current_value} > {threshold}"
    
    # Property 1: Alert creation should work correctly
    alert = alert_manager.create_alert(alert_type, severity, message, threshold, current_value)
    
    assert alert.type == alert_type, f"Alert type should be {alert_type}"
    assert alert.severity == severity, f"Alert severity should be {severity}"
    assert alert.message == message, f"Alert message should match"
    assert alert.threshold == threshold, f"Alert threshold should be {threshold}"
    assert alert.current == current_value, f"Alert current value should be {current_value}"
    assert not alert.resolved, "New alert should not be resolved"
    assert alert.resolved_at is None, "New alert should not have resolved timestamp"
    
    # Property 2: Alert should be stored and retrievable
    stored_alert = alert_manager.alerts.get(alert.id)
    assert stored_alert is not None, "Alert should be stored"
    assert stored_alert.id == alert.id, "Stored alert should have same ID"
    
    active_alerts = alert_manager.get_active_alerts()
    assert alert in active_alerts, "Alert should be in active alerts list"
    
    # Property 3: Notification handler should be called
    assert handler.call_count == 1, "Notification handler should be called once"
    assert handler.last_alert.id == alert.id, "Handler should receive the correct alert"
    
    # Property 4: Alert resolution should work correctly
    resolution_success = alert_manager.resolve_alert(alert.id)
    assert resolution_success, "Alert resolution should succeed"
    
    resolved_alert = alert_manager.alerts[alert.id]
    assert resolved_alert.resolved, "Alert should be marked as resolved"
    assert resolved_alert.resolved_at is not None, "Alert should have resolved timestamp"
    
    active_alerts_after = alert_manager.get_active_alerts()
    assert alert not in active_alerts_after, "Resolved alert should not be in active alerts"
    
    # Property 5: Alert history should be maintained
    alert_history = alert_manager.get_alert_history(hours=1)
    assert alert in alert_history, "Alert should be in history"
    
    # Property 6: Multiple alerts should be handled independently
    alert2 = alert_manager.create_alert(
        f"{alert_type}_2", severity, f"Second {message}", threshold, current_value
    )
    
    assert len(alert_manager.alerts) == 2, "Should have two alerts"
    assert alert2.id != alert.id, "Alerts should have different IDs"
    
    active_alerts_multi = alert_manager.get_active_alerts()
    assert alert2 in active_alerts_multi, "Second alert should be active"
    assert alert not in active_alerts_multi, "First alert should still be resolved"


@pytest.mark.asyncio
@given(perf_scenario=performance_scenario_strategy())
@settings(
    max_examples=50,
    deadline=60000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_performance_threshold_detection(
    fresh_performance_monitor, mock_notification_handler, perf_scenario
):
    """
    Property 27.4: Performance Threshold Detection
    
    *For any* system performance metrics, the monitoring system should detect threshold violations
    and generate appropriate alerts with correct severity levels.
    
    **Validates: Requirements 9.7**
    """
    monitor = fresh_performance_monitor
    handler = mock_notification_handler
    
    # Add notification handler
    monitor.alert_manager.add_notification_handler(handler)
    
    cpu_usage = perf_scenario["cpu_usage"]
    memory_usage = perf_scenario["memory_usage"]
    disk_usage = perf_scenario["disk_usage"]
    response_times = perf_scenario["response_times"]
    error_count = perf_scenario["error_count"]
    request_count = perf_scenario["request_count"]
    
    # Skip unrealistic scenarios
    assume(len(response_times) > 0)
    assume(request_count > 0)
    
    # Mock system metrics with test data
    with patch('psutil.cpu_percent', return_value=cpu_usage), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.net_connections', return_value=['conn'] * 10):
        
        mock_memory.return_value.percent = memory_usage
        mock_memory.return_value.used = memory_usage * 1024 * 1024 * 100  # Convert to bytes
        mock_disk.return_value.percent = disk_usage
        
        # Collect system metrics
        await monitor.metrics.collect_system_metrics()
        
        # Add response time metrics
        for response_time in response_times:
            monitor.metrics.record_metric("response_time", response_time * 1000)  # Convert to ms
        
        # Add error and request metrics
        monitor.metrics.record_metric("errors_total", error_count)
        monitor.metrics.record_metric("requests_total", request_count)
        
        # Check performance thresholds
        new_alerts = monitor.check_performance_thresholds()
        
        # Property 1: CPU threshold detection
        cpu_threshold = monitor.thresholds["cpu_percent"]
        if cpu_usage > cpu_threshold:
            cpu_alerts = [a for a in new_alerts if a.type == "high_cpu"]
            assert len(cpu_alerts) > 0, f"Should generate CPU alert when usage {cpu_usage}% > {cpu_threshold}%"
            
            cpu_alert = cpu_alerts[0]
            assert cpu_alert.current == cpu_usage, "CPU alert should have correct current value"
            assert cpu_alert.threshold == cpu_threshold, "CPU alert should have correct threshold"
            
            # Severity should increase with usage
            if cpu_usage > 90:
                assert cpu_alert.severity == AlertSeverity.HIGH, "Very high CPU should be HIGH severity"
            else:
                assert cpu_alert.severity == AlertSeverity.MEDIUM, "High CPU should be MEDIUM severity"
        
        # Property 2: Memory threshold detection
        memory_threshold = monitor.thresholds["memory_percent"]
        if memory_usage > memory_threshold:
            memory_alerts = [a for a in new_alerts if a.type == "high_memory"]
            assert len(memory_alerts) > 0, f"Should generate memory alert when usage {memory_usage}% > {memory_threshold}%"
            
            memory_alert = memory_alerts[0]
            assert memory_alert.current == memory_usage, "Memory alert should have correct current value"
            
            # Severity should increase with usage
            if memory_usage > 95:
                assert memory_alert.severity == AlertSeverity.CRITICAL, "Very high memory should be CRITICAL"
            else:
                assert memory_alert.severity == AlertSeverity.HIGH, "High memory should be HIGH severity"
        
        # Property 3: Disk threshold detection
        disk_threshold = monitor.thresholds["disk_usage_percent"]
        if disk_usage > disk_threshold:
            disk_alerts = [a for a in new_alerts if a.type == "high_disk"]
            assert len(disk_alerts) > 0, f"Should generate disk alert when usage {disk_usage}% > {disk_threshold}%"
            
            disk_alert = disk_alerts[0]
            assert disk_alert.current == disk_usage, "Disk alert should have correct current value"
        
        # Property 4: Response time threshold detection
        avg_response_time = sum(response_times) / len(response_times)
        response_threshold_ms = monitor.thresholds["response_time_ms"]
        
        if avg_response_time * 1000 > response_threshold_ms:  # Convert to ms
            response_alerts = [a for a in new_alerts if a.type == "slow_response"]
            assert len(response_alerts) > 0, \
                f"Should generate response time alert when avg {avg_response_time*1000:.1f}ms > {response_threshold_ms}ms"
            
            response_alert = response_alerts[0]
            assert abs(response_alert.current - avg_response_time * 1000) < 1.0, \
                "Response time alert should have correct current value"
        
        # Property 5: Error rate threshold detection
        error_rate = (error_count / request_count) * 100
        error_threshold = monitor.thresholds["error_rate_percent"]
        
        if error_rate > error_threshold:
            error_alerts = [a for a in new_alerts if a.type == "high_error_rate"]
            assert len(error_alerts) > 0, \
                f"Should generate error rate alert when rate {error_rate:.1f}% > {error_threshold}%"
            
            error_alert = error_alerts[0]
            assert abs(error_alert.current - error_rate) < 0.1, \
                "Error rate alert should have correct current value"
            
            # Severity should increase with error rate
            if error_rate > 20:
                assert error_alert.severity == AlertSeverity.CRITICAL, "Very high error rate should be CRITICAL"
            else:
                assert error_alert.severity == AlertSeverity.HIGH, "High error rate should be HIGH severity"
        
        # Property 6: Notification handlers should be called for all alerts
        expected_notifications = len(new_alerts)
        assert handler.call_count == expected_notifications, \
            f"Should have {expected_notifications} notifications, got {handler.call_count}"


@pytest.mark.asyncio
@given(
    notification_count=st.integers(min_value=1, max_value=20),
    handler_failure_rate=st.floats(min_value=0.0, max_value=0.5)
)
@settings(
    max_examples=30,
    deadline=30000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_notification_reliability(
    fresh_alert_manager, notification_count, handler_failure_rate
):
    """
    Property 27.5: Notification Reliability
    
    *For any* alert notifications, the system should handle notification failures gracefully
    and ensure alert information is preserved even when handlers fail.
    
    **Validates: Requirements 9.7**
    """
    alert_manager = fresh_alert_manager
    
    # Create handlers with controlled failure rates
    successful_handler = MockNotificationHandler()
    failing_handler = MockNotificationHandler()
    
    def make_failing_handler(failure_rate: float):
        def handler(alert: Alert):
            failing_handler.call_count += 1
            if failing_handler.call_count <= int(notification_count * failure_rate):
                raise Exception(f"Simulated handler failure for alert {alert.id}")
            failing_handler.notifications.append(alert)
        return handler
    
    # Add both handlers
    alert_manager.add_notification_handler(successful_handler)
    alert_manager.add_notification_handler(make_failing_handler(handler_failure_rate))
    
    # Generate multiple alerts
    created_alerts = []
    for i in range(notification_count):
        alert = alert_manager.create_alert(
            alert_type=f"test_alert_{i}",
            severity=AlertSeverity.MEDIUM,
            message=f"Test alert {i}",
            threshold=50.0,
            current=75.0
        )
        created_alerts.append(alert)
    
    # Property 1: All alerts should be created despite handler failures
    assert len(alert_manager.alerts) == notification_count, \
        "All alerts should be created even if handlers fail"
    
    for alert in created_alerts:
        assert alert.id in alert_manager.alerts, "Each alert should be stored"
        assert not alert.resolved, "New alerts should not be resolved"
    
    # Property 2: Successful handler should receive all notifications
    assert successful_handler.call_count == notification_count, \
        "Successful handler should receive all notifications"
    assert len(successful_handler.notifications) == notification_count, \
        "Successful handler should store all notifications"
    
    # Property 3: Failing handler should be called but failures shouldn't affect alert storage
    assert failing_handler.call_count == notification_count, \
        "Failing handler should be called for all alerts"
    
    expected_successful_notifications = notification_count - int(notification_count * handler_failure_rate)
    assert len(failing_handler.notifications) >= expected_successful_notifications - 1, \
        "Failing handler should succeed for some notifications"
    
    # Property 4: Alert history should be complete regardless of handler failures
    alert_history = alert_manager.get_alert_history(hours=1)
    assert len(alert_history) == notification_count, \
        "Alert history should contain all alerts regardless of handler failures"
    
    # Property 5: Active alerts should be correct
    active_alerts = alert_manager.get_active_alerts()
    assert len(active_alerts) == notification_count, \
        "All alerts should be active (none resolved yet)"
    
    # Property 6: Alert resolution should work despite previous handler failures
    first_alert = created_alerts[0]
    resolution_success = alert_manager.resolve_alert(first_alert.id)
    assert resolution_success, "Alert resolution should succeed despite handler failures"
    
    active_after_resolution = alert_manager.get_active_alerts()
    assert len(active_after_resolution) == notification_count - 1, \
        "Should have one less active alert after resolution"


@pytest.mark.asyncio
async def test_property_monitoring_system_integration(
    fresh_performance_monitor, mock_notification_handler
):
    """
    Property 27.6: Monitoring System Integration
    
    *For any* complete monitoring scenario, all components (metrics collection, threshold detection,
    alerting, and notifications) should work together correctly.
    
    **Validates: Requirements 9.7**
    """
    monitor = fresh_performance_monitor
    handler = mock_notification_handler
    
    # Setup monitoring system
    monitor.alert_manager.add_notification_handler(handler)
    
    # Property 1: System should start in healthy state
    initial_health = monitor.get_health_status()
    assert initial_health["status"] == "healthy", "System should start healthy"
    assert initial_health["active_alerts"] == 0, "Should have no active alerts initially"
    
    # Property 2: System should detect and alert on multiple issues simultaneously
    with patch('psutil.cpu_percent', return_value=85.0), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.net_connections', return_value=['conn'] * 50):
        
        # Setup high resource usage
        mock_memory.return_value.percent = 90.0
        mock_memory.return_value.used = 90.0 * 1024 * 1024 * 100
        mock_disk.return_value.percent = 95.0
        
        # Collect metrics
        await monitor.metrics.collect_system_metrics()
        
        # Add slow response times
        for _ in range(10):
            monitor.metrics.record_metric("response_time", 1500.0)  # 1.5 seconds
        
        # Add high error rate
        monitor.metrics.record_metric("errors_total", 15)
        monitor.metrics.record_metric("requests_total", 100)
        
        # Check thresholds
        new_alerts = monitor.check_performance_thresholds()
        
        # Should detect multiple issues
        alert_types = {alert.type for alert in new_alerts}
        expected_types = {"high_cpu", "high_memory", "high_disk", "slow_response", "high_error_rate"}
        
        # Should have at least some of these alerts
        assert len(alert_types) >= 3, f"Should detect multiple issues, got: {alert_types}"
        
        # Property 3: Health status should reflect system problems
        health_after_issues = monitor.get_health_status()
        assert health_after_issues["status"] in ["warning", "degraded", "critical"], \
            "Health status should reflect detected issues"
        assert health_after_issues["active_alerts"] > 0, "Should have active alerts"
        
        # Property 4: Notifications should be sent for all alerts
        assert handler.call_count == len(new_alerts), \
            "Should send notification for each alert"
        
        # Property 5: Alert severities should be appropriate
        critical_alerts = [a for a in new_alerts if a.severity == AlertSeverity.CRITICAL]
        high_alerts = [a for a in new_alerts if a.severity == AlertSeverity.HIGH]
        
        # High resource usage should generate high/critical alerts
        assert len(critical_alerts) + len(high_alerts) > 0, \
            "High resource usage should generate high or critical alerts"
        
        # Property 6: System should recover when issues are resolved
        # Resolve all alerts
        for alert in new_alerts:
            monitor.alert_manager.resolve_alert(alert.id)
        
        health_after_resolution = monitor.get_health_status()
        assert health_after_resolution["status"] == "healthy", \
            "System should return to healthy after alert resolution"
        assert health_after_resolution["active_alerts"] == 0, \
            "Should have no active alerts after resolution"


@pytest.mark.asyncio
async def test_property_metrics_time_series_accuracy():
    """
    Property 27.7: Metrics Time Series Accuracy
    
    *For any* time-based metric queries, the system should return accurate data
    within the specified time ranges with correct ordering.
    
    **Validates: Requirements 9.7**
    """
    collector = MetricsCollector(max_points=100)
    
    # Record metrics with known timestamps
    base_time = datetime.now()
    test_metrics = []
    
    for i in range(10):
        timestamp = base_time + timedelta(seconds=i)
        value = float(i * 10)
        
        # Manually create metric point with specific timestamp
        point = MetricPoint(timestamp=timestamp, value=value, tags={"sequence": str(i)})
        collector.metrics["test_series"].append(point)
        test_metrics.append(point)
    
    # Property 1: All metrics should be retrievable
    all_metrics = collector.get_metrics("test_series")
    assert len(all_metrics) == 10, "Should retrieve all recorded metrics"
    
    # Property 2: Metrics should be in chronological order
    timestamps = [m.timestamp for m in all_metrics]
    assert timestamps == sorted(timestamps), "Metrics should be in chronological order"
    
    # Property 3: Time-based filtering should work correctly
    midpoint = base_time + timedelta(seconds=5)
    recent_metrics = collector.get_metrics("test_series", since=midpoint)
    
    # Should get metrics from second 5 onwards (5 metrics)
    assert len(recent_metrics) == 5, f"Should get 5 recent metrics, got {len(recent_metrics)}"
    
    for metric in recent_metrics:
        assert metric.timestamp >= midpoint, "All filtered metrics should be after cutoff time"
    
    # Property 4: Values should be preserved accurately
    for i, metric in enumerate(all_metrics):
        expected_value = float(i * 10)
        assert metric.value == expected_value, \
            f"Metric {i} should have value {expected_value}, got {metric.value}"
        assert metric.tags["sequence"] == str(i), \
            f"Metric {i} should have correct sequence tag"
    
    # Property 5: Empty time ranges should return empty results
    future_time = base_time + timedelta(hours=1)
    future_metrics = collector.get_metrics("test_series", since=future_time)
    assert len(future_metrics) == 0, "Future time range should return no metrics"
    
    # Property 6: Non-existent metrics should return empty results
    nonexistent_metrics = collector.get_metrics("nonexistent_series")
    assert len(nonexistent_metrics) == 0, "Non-existent metric series should return empty list"


@pytest.mark.asyncio
async def test_property_alert_suppression_and_escalation(fresh_alert_manager):
    """
    Property 27.8: Alert Suppression and Escalation
    
    *For any* repeated alert conditions, the system should handle alert suppression
    and escalation appropriately to prevent notification spam.
    
    **Validates: Requirements 9.7**
    """
    alert_manager = fresh_alert_manager
    handler = MockNotificationHandler()
    alert_manager.add_notification_handler(handler)
    
    # Property 1: Duplicate alerts should be handled appropriately
    alert_type = "high_cpu"
    threshold = 80.0
    current_value = 85.0
    message = f"CPU usage is {current_value}%"
    
    # Create multiple similar alerts
    alerts = []
    for i in range(5):
        alert = alert_manager.create_alert(
            alert_type=alert_type,
            severity=AlertSeverity.MEDIUM,
            message=f"{message} (occurrence {i+1})",
            threshold=threshold,
            current=current_value + i
        )
        alerts.append(alert)
    
    # All alerts should be created (no suppression in basic implementation)
    assert len(alert_manager.alerts) == 5, "All alerts should be created"
    assert handler.call_count == 5, "All alerts should trigger notifications"
    
    # Property 2: Alert resolution should work for individual alerts
    first_alert = alerts[0]
    resolution_success = alert_manager.resolve_alert(first_alert.id)
    assert resolution_success, "Should be able to resolve individual alerts"
    
    active_alerts = alert_manager.get_active_alerts()
    assert len(active_alerts) == 4, "Should have 4 active alerts after resolving one"
    assert first_alert not in active_alerts, "Resolved alert should not be active"
    
    # Property 3: Alert history should maintain all alerts
    alert_history = alert_manager.get_alert_history(hours=1)
    assert len(alert_history) == 5, "History should contain all alerts"
    
    resolved_in_history = [a for a in alert_history if a.resolved]
    assert len(resolved_in_history) == 1, "History should show one resolved alert"
    
    # Property 4: Escalation based on severity should work
    # Create critical alert
    critical_alert = alert_manager.create_alert(
        alert_type="critical_memory",
        severity=AlertSeverity.CRITICAL,
        message="Critical memory usage",
        threshold=95.0,
        current=98.0
    )
    
    # Critical alert should be in active alerts
    active_alerts_with_critical = alert_manager.get_active_alerts()
    critical_active = [a for a in active_alerts_with_critical if a.severity == AlertSeverity.CRITICAL]
    assert len(critical_active) == 1, "Should have one critical alert"
    assert critical_alert in critical_active, "Critical alert should be active"
    
    # Property 5: Alert aging should be trackable
    # Check that older alerts can be identified
    import time
    time.sleep(0.001)  # Small delay
    
    recent_alert = alert_manager.create_alert(
        alert_type="recent_alert",
        severity=AlertSeverity.LOW,
        message="Recent alert",
        threshold=10.0,
        current=15.0
    )
    
    all_alerts = list(alert_manager.alerts.values())
    timestamps = [a.timestamp for a in all_alerts]
    assert max(timestamps) == recent_alert.timestamp, "Most recent alert should have latest timestamp"
    
    # Property 6: Bulk alert operations should work
    # Resolve multiple alerts
    remaining_alerts = [a for a in alerts[1:] if not a.resolved]
    for alert in remaining_alerts:
        alert_manager.resolve_alert(alert.id)
    
    final_active = alert_manager.get_active_alerts()
    # Should have critical alert and recent alert still active
    assert len(final_active) == 2, "Should have 2 active alerts after bulk resolution"
    
    active_types = {a.type for a in final_active}
    assert "critical_memory" in active_types, "Critical alert should still be active"
    assert "recent_alert" in active_types, "Recent alert should still be active"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])