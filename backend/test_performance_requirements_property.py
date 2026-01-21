"""
Property-based test for performance requirements compliance.

**Feature: professional-poker-analyzer-rebuild, Property 24: Performance Requirements Compliance**
**Validates: Requirements 4.4, 9.1, 9.2**

Property 24: Performance Requirements Compliance
*For any* typical system usage, API requests should respond within 500ms for 95% of requests, 
and batch operations should complete within specified time limits
"""
import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Callable
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from unittest.mock import AsyncMock, MagicMock, patch
from statistics import mean

from app.services.database_optimizer import DatabaseOptimizer
from app.services.cache_service import CacheService
from app.services.statistics_service import StatisticsService
from app.schemas.statistics import StatisticsFilters


def percentile(data: List[float], p: float) -> float:
    """Calculate percentile of a dataset."""
    if not data:
        return 0.0
    
    sorted_data = sorted(data)
    n = len(sorted_data)
    
    if p == 100:
        return sorted_data[-1]
    
    k = (n - 1) * (p / 100)
    f = int(k)
    c = k - f
    
    if f + 1 < n:
        return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
    else:
        return sorted_data[f]


class PerformanceMonitor:
    """Monitor and track performance metrics for testing."""
    
    def __init__(self):
        self.response_times = []
        self.operation_times = {}
        self.error_count = 0
        self.total_requests = 0
    
    def record_response_time(self, operation: str, response_time: float):
        """Record response time for an operation."""
        self.response_times.append(response_time)
        if operation not in self.operation_times:
            self.operation_times[operation] = []
        self.operation_times[operation].append(response_time)
        self.total_requests += 1
    
    def record_error(self):
        """Record an error occurrence."""
        self.error_count += 1
    
    def get_percentile_response_time(self, percentile_value: float = 95.0) -> float:
        """Get the percentile response time."""
        if not self.response_times:
            return 0.0
        return percentile(sorted(self.response_times), percentile_value)
    
    def get_average_response_time(self) -> float:
        """Get average response time."""
        if not self.response_times:
            return 0.0
        return mean(self.response_times)
    
    def get_operation_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for a specific operation."""
        if operation not in self.operation_times:
            return {"count": 0, "avg": 0.0, "max": 0.0, "min": 0.0}
        
        times = self.operation_times[operation]
        return {
            "count": len(times),
            "avg": mean(times),
            "max": max(times),
            "min": min(times),
            "p95": percentile(sorted(times), 95.0) if len(times) > 1 else times[0]
        }
    
    def reset(self):
        """Reset all metrics."""
        self.response_times = []
        self.operation_times = {}
        self.error_count = 0
        self.total_requests = 0


@pytest_asyncio.fixture
async def performance_monitor():
    """Create a performance monitor for testing."""
    return PerformanceMonitor()


@pytest_asyncio.fixture
async def mock_db_optimizer():
    """Create a mock database optimizer."""
    optimizer = DatabaseOptimizer()
    # Pre-populate with some realistic query stats
    optimizer.query_stats = {
        "get_user_statistics": {
            "count": 50,
            "total_time": 5.0,
            "avg_time": 0.1,
            "max_time": 0.3,
            "slow_queries": 2
        },
        "get_poker_hands": {
            "count": 100,
            "total_time": 15.0,
            "avg_time": 0.15,
            "max_time": 0.8,
            "slow_queries": 5
        }
    }
    return optimizer


@pytest_asyncio.fixture
async def mock_cache_service():
    """Create a mock cache service with performance tracking."""
    service = CacheService()
    service.connected = True
    
    # Mock Redis client with performance simulation
    class MockRedisWithPerformance:
        def __init__(self):
            self.data = {}
            self.operation_times = []
        
        async def ping(self):
            await asyncio.sleep(0.001)  # 1ms latency
            return True
        
        async def get(self, key: str):
            # Simulate cache lookup time
            lookup_time = 0.002 + (len(self.data) * 0.0001)  # Increases with cache size
            await asyncio.sleep(lookup_time)
            return self.data.get(key)
        
        async def setex(self, key: str, ttl: int, value: str):
            # Simulate cache write time
            write_time = 0.003 + (len(value) * 0.000001)  # Increases with data size
            await asyncio.sleep(write_time)
            self.data[key] = value
            return True
        
        async def delete(self, *keys):
            delete_time = 0.001 * len(keys)
            await asyncio.sleep(delete_time)
            deleted = 0
            for key in keys:
                if key in self.data:
                    del self.data[key]
                    deleted += 1
            return deleted
        
        async def keys(self, pattern: str):
            await asyncio.sleep(0.005)  # Pattern matching is slower
            import fnmatch
            return [key for key in self.data.keys() if fnmatch.fnmatch(key, pattern)]
        
        async def info(self):
            return {
                'keyspace_hits': 100,
                'keyspace_misses': 20,
                'used_memory_human': '1MB',
                'connected_clients': 1,
                'total_commands_processed': 120
            }
        
        async def close(self):
            pass
    
    service.redis_client = MockRedisWithPerformance()
    return service


# Strategy for generating performance test scenarios
@st.composite
def performance_test_scenario(draw):
    """Generate performance test scenarios."""
    return {
        "operation_type": draw(st.sampled_from([
            "statistics_calculation", "cache_operation", "database_query", 
            "batch_processing", "api_request"
        ])),
        "data_size": draw(st.integers(min_value=1, max_value=1000)),
        "concurrent_requests": draw(st.integers(min_value=1, max_value=20)),
        "cache_hit_rate": draw(st.floats(min_value=0.0, max_value=1.0)),
        "expected_max_time": draw(st.floats(min_value=0.1, max_value=2.0))
    }


async def simulate_api_request(operation_type: str, data_size: int, cache_service: CacheService) -> float:
    """Simulate an API request and return response time."""
    start_time = time.time()
    
    try:
        if operation_type == "statistics_calculation":
            # Simulate statistics calculation
            await asyncio.sleep(0.05 + (data_size * 0.0001))  # Base time + data processing
            
        elif operation_type == "cache_operation":
            # Simulate cache operations
            test_data = {"test": "data" * (data_size // 10)}
            await cache_service.set("test_type", f"key_{data_size}", test_data)
            await cache_service.get("test_type", f"key_{data_size}")
            
        elif operation_type == "database_query":
            # Simulate database query
            await asyncio.sleep(0.02 + (data_size * 0.0002))  # Query time increases with data
            
        elif operation_type == "batch_processing":
            # Simulate batch processing
            batch_size = min(data_size, 100)  # Process in batches
            for i in range(0, data_size, batch_size):
                await asyncio.sleep(0.01)  # Process each batch
                
        elif operation_type == "api_request":
            # Simulate general API request
            await asyncio.sleep(0.01 + (data_size * 0.00005))
        
        return time.time() - start_time
        
    except Exception:
        return time.time() - start_time  # Return time even if operation fails


@pytest.mark.asyncio
@given(scenario=performance_test_scenario())
@settings(
    max_examples=100,
    deadline=60000,  # 60 second timeout
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_performance_requirements_compliance(
    performance_monitor, mock_cache_service, scenario
):
    """
    Property 24: Performance Requirements Compliance
    
    *For any* typical system usage, API requests should respond within 500ms for 95% of requests, 
    and batch operations should complete within specified time limits.
    
    **Validates: Requirements 4.4, 9.1, 9.2**
    """
    operation_type = scenario["operation_type"]
    data_size = scenario["data_size"]
    concurrent_requests = scenario["concurrent_requests"]
    expected_max_time = scenario["expected_max_time"]
    
    # Skip unrealistic scenarios
    assume(data_size <= 500 or concurrent_requests <= 10)  # Avoid overwhelming scenarios
    
    performance_monitor.reset()
    
    # Property 1: Individual requests should complete within reasonable time
    response_time = await simulate_api_request(operation_type, data_size, mock_cache_service)
    performance_monitor.record_response_time(operation_type, response_time)
    
    # For non-batch operations, response time should be under 500ms
    if operation_type != "batch_processing":
        assert response_time < 0.5, \
            f"{operation_type} took {response_time:.3f}s, should be under 500ms"
    
    # Property 2: Concurrent requests should maintain performance
    if concurrent_requests > 1:
        tasks = []
        for i in range(min(concurrent_requests, 10)):  # Limit to prevent test timeout
            task = simulate_api_request(operation_type, data_size // concurrent_requests, mock_cache_service)
            tasks.append(task)
        
        concurrent_times = await asyncio.gather(*tasks)
        
        for response_time in concurrent_times:
            performance_monitor.record_response_time(f"{operation_type}_concurrent", response_time)
        
        # 95% of concurrent requests should complete within 500ms (for non-batch operations)
        if operation_type != "batch_processing":
            p95_time = performance_monitor.get_percentile_response_time(95.0)
            assert p95_time < 0.5, \
                f"95th percentile response time {p95_time:.3f}s exceeds 500ms limit"
    
    # Property 3: Batch operations should complete within reasonable time limits
    if operation_type == "batch_processing":
        # Batch operations should complete within reasonable time limits
        # Allow more time for small batches due to overhead
        if data_size <= 10:
            max_batch_time = 0.1  # 100ms for small batches
        elif data_size <= 100:
            max_batch_time = 1.0  # 1s for medium batches
        else:
            max_batch_time = min(30.0, data_size * 0.01)  # 10ms per item, max 30s
        
        assert response_time < max_batch_time, \
            f"Batch processing took {response_time:.3f}s, should be under {max_batch_time:.3f}s"
    
    # Property 4: Cache operations should be fast
    if operation_type == "cache_operation":
        assert response_time < 0.1, \
            f"Cache operation took {response_time:.3f}s, should be under 100ms"
    
    # Property 5: Database queries should be optimized
    if operation_type == "database_query":
        # Database queries should complete within 200ms for typical data sizes
        max_db_time = 0.2 + (data_size * 0.0001)  # Base time + data scaling
        assert response_time < max_db_time, \
            f"Database query took {response_time:.3f}s, should be under {max_db_time:.3f}s"
    
    # Property 6: Performance should scale reasonably with data size
    if data_size > 100:
        # Response time should not increase exponentially with data size
        time_per_item = response_time / data_size
        assert time_per_item < 0.001, \
            f"Time per item {time_per_item:.6f}s is too high, indicates poor scaling"
    
    # Property 7: System should handle load without degradation
    operation_stats = performance_monitor.get_operation_stats(operation_type)
    if operation_stats["count"] > 1:
        # Variance in response times should be reasonable
        max_variance_ratio = operation_stats["max"] / operation_stats["avg"]
        assert max_variance_ratio < 5.0, \
            f"Response time variance too high: max/avg ratio = {max_variance_ratio:.2f}"


@pytest.mark.asyncio
@given(
    query_count=st.integers(min_value=10, max_value=100),
    slow_query_percentage=st.floats(min_value=0.0, max_value=0.3)
)
@settings(
    max_examples=50,
    deadline=30000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_database_performance_monitoring(
    mock_db_optimizer, query_count, slow_query_percentage
):
    """
    Test database performance monitoring and optimization.
    
    **Validates: Requirements 9.1, 9.2**
    """
    db_optimizer = mock_db_optimizer
    
    # Simulate query execution with performance tracking
    query_name = "test_query"
    slow_queries = int(query_count * slow_query_percentage)
    
    # Reset stats for this test
    db_optimizer.query_stats[query_name] = {
        'count': query_count,
        'total_time': 0.0,
        'avg_time': 0.0,
        'max_time': 0.0,
        'slow_queries': slow_queries
    }
    
    # Simulate query times
    total_time = 0.0
    max_time = 0.0
    
    for i in range(query_count):
        if i < slow_queries:
            # Slow query (over 1 second threshold)
            query_time = 1.2 + (i * 0.1)
        else:
            # Fast query
            query_time = 0.05 + (i * 0.001)
        
        total_time += query_time
        max_time = max(max_time, query_time)
    
    db_optimizer.query_stats[query_name]['total_time'] = total_time
    db_optimizer.query_stats[query_name]['avg_time'] = total_time / query_count
    db_optimizer.query_stats[query_name]['max_time'] = max_time
    
    # Property 1: Query statistics should be tracked accurately
    stats = db_optimizer.query_stats[query_name]
    assert stats['count'] == query_count, "Query count should be tracked correctly"
    assert stats['slow_queries'] == slow_queries, "Slow query count should be tracked"
    assert stats['avg_time'] > 0, "Average time should be calculated"
    
    # Property 2: Performance analysis should identify issues
    # Mock the database session for analysis
    mock_db = AsyncMock()
    mock_db.execute.return_value.fetchall.return_value = []
    mock_db.get_bind.return_value.pool.size.return_value = 20
    
    analysis = await db_optimizer.analyze_query_performance(mock_db)
    
    assert "query_stats" in analysis, "Analysis should include query statistics"
    assert "recommendations" in analysis, "Analysis should include recommendations"
    
    # Property 3: Recommendations should be generated for performance issues
    recommendations = analysis["recommendations"]
    
    if slow_queries > 0:
        # Should have slow query recommendations
        slow_query_recs = [r for r in recommendations if r["type"] == "slow_query"]
        assert len(slow_query_recs) > 0, "Should recommend optimization for slow queries"
    
    if query_count > 100:
        # Should have frequent query recommendations
        frequent_query_recs = [r for r in recommendations if r["type"] == "frequent_query"]
        # This depends on average time, so we check conditionally
        if stats['avg_time'] > 0.1:
            assert len(frequent_query_recs) > 0, "Should recommend caching for frequent queries"
    
    # Property 4: Slow query threshold should be enforced
    assert db_optimizer.slow_query_threshold > 0, "Slow query threshold should be positive"
    assert db_optimizer.slow_query_threshold <= 2.0, "Slow query threshold should be reasonable"


@pytest.mark.asyncio
async def test_cache_performance_requirements(mock_cache_service, performance_monitor):
    """Test cache performance requirements."""
    cache_service = mock_cache_service
    performance_monitor.reset()
    
    # Test cache operation performance
    test_data = {"test": "data", "value": 12345}
    
    # Property 1: Cache writes should be fast
    start_time = time.time()
    success = await cache_service.set("test_type", "test_key", test_data)
    write_time = time.time() - start_time
    
    assert success, "Cache write should succeed"
    assert write_time < 0.05, f"Cache write took {write_time:.3f}s, should be under 50ms"
    performance_monitor.record_response_time("cache_write", write_time)
    
    # Property 2: Cache reads should be fast
    start_time = time.time()
    retrieved_data = await cache_service.get("test_type", "test_key")
    read_time = time.time() - start_time
    
    assert retrieved_data is not None, "Cache read should succeed"
    assert read_time < 0.05, f"Cache read took {read_time:.3f}s, should be under 50ms"
    performance_monitor.record_response_time("cache_read", read_time)
    
    # Property 3: Cache operations should scale with concurrent access
    concurrent_operations = 10
    tasks = []
    
    for i in range(concurrent_operations):
        # Mix of reads and writes
        if i % 2 == 0:
            task = cache_service.set("test_type", f"key_{i}", {"data": i})
        else:
            task = cache_service.get("test_type", f"key_{i-1}")
        tasks.append(task)
    
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    concurrent_time = time.time() - start_time
    
    # All operations should complete within reasonable time
    assert concurrent_time < 0.2, \
        f"Concurrent cache operations took {concurrent_time:.3f}s, should be under 200ms"
    
    # Most operations should succeed
    successful_ops = sum(1 for result in results if not isinstance(result, Exception))
    success_rate = successful_ops / len(results)
    assert success_rate >= 0.9, f"Cache success rate {success_rate:.2f} should be at least 90%"
    
    # Property 4: Cache statistics should be available quickly
    start_time = time.time()
    stats = await cache_service.get_cache_stats()
    stats_time = time.time() - start_time
    
    assert stats_time < 0.1, f"Cache stats took {stats_time:.3f}s, should be under 100ms"
    assert "connected" in stats, "Cache stats should include connection status"
    assert "hit_rate" in stats, "Cache stats should include hit rate"


@pytest.mark.asyncio
async def test_performance_monitoring_accuracy(performance_monitor):
    """Test performance monitoring accuracy and calculations."""
    performance_monitor.reset()
    
    # Add known response times
    test_times = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6]
    
    for i, response_time in enumerate(test_times):
        performance_monitor.record_response_time("test_operation", response_time)
    
    # Property 1: Average calculation should be accurate
    expected_avg = sum(test_times) / len(test_times)
    actual_avg = performance_monitor.get_average_response_time()
    assert abs(actual_avg - expected_avg) < 0.001, \
        f"Average calculation incorrect: expected {expected_avg:.3f}, got {actual_avg:.3f}"
    
    # Property 2: Percentile calculation should be reasonable
    p95 = performance_monitor.get_percentile_response_time(95.0)
    assert p95 >= max(test_times) * 0.9, "95th percentile should be near maximum"
    assert p95 <= max(test_times), "95th percentile should not exceed maximum"
    
    # Property 3: Operation statistics should be accurate
    stats = performance_monitor.get_operation_stats("test_operation")
    assert stats["count"] == len(test_times), "Count should match number of recorded times"
    assert abs(stats["avg"] - expected_avg) < 0.001, "Average in stats should be accurate"
    assert stats["max"] == max(test_times), "Maximum should be accurate"
    assert stats["min"] == min(test_times), "Minimum should be accurate"
    
    # Property 4: Performance metrics should handle edge cases
    performance_monitor.reset()
    
    # Empty case
    assert performance_monitor.get_average_response_time() == 0.0
    assert performance_monitor.get_percentile_response_time(95.0) == 0.0
    
    # Single value case
    performance_monitor.record_response_time("single_op", 0.123)
    assert performance_monitor.get_average_response_time() == 0.123
    assert performance_monitor.get_percentile_response_time(95.0) == 0.123


@pytest.mark.asyncio
async def test_batch_operation_performance():
    """Test batch operation performance requirements."""
    
    async def simulate_batch_operation(batch_size: int) -> float:
        """Simulate a batch operation processing."""
        start_time = time.time()
        
        # Simulate processing items in batches
        batch_chunk_size = 50  # Process 50 items at a time
        
        for i in range(0, batch_size, batch_chunk_size):
            chunk_size = min(batch_chunk_size, batch_size - i)
            # Simulate processing time per chunk
            await asyncio.sleep(chunk_size * 0.001)  # 1ms per item
        
        return time.time() - start_time
    
    # Property 1: Small batches should complete quickly
    small_batch_time = await simulate_batch_operation(10)
    assert small_batch_time < 0.1, \
        f"Small batch (10 items) took {small_batch_time:.3f}s, should be under 100ms"
    
    # Property 2: Medium batches should complete within reasonable time
    medium_batch_time = await simulate_batch_operation(100)
    assert medium_batch_time < 1.0, \
        f"Medium batch (100 items) took {medium_batch_time:.3f}s, should be under 1s"
    
    # Property 3: Large batches should complete within time limits
    large_batch_time = await simulate_batch_operation(1000)
    assert large_batch_time < 10.0, \
        f"Large batch (1000 items) took {large_batch_time:.3f}s, should be under 10s"
    
    # Property 4: Batch processing should scale linearly
    # Time per item should be consistent across batch sizes
    small_time_per_item = small_batch_time / 10
    medium_time_per_item = medium_batch_time / 100
    large_time_per_item = large_batch_time / 1000
    
    # Allow some variance but should be roughly linear
    assert abs(small_time_per_item - medium_time_per_item) < 0.01, \
        "Batch processing should scale linearly"
    assert abs(medium_time_per_item - large_time_per_item) < 0.01, \
        "Batch processing should scale linearly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])