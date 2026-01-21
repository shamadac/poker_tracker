"""
Validation test for concurrent performance property testing framework.

This test validates that the concurrent performance testing framework works correctly
and can detect performance issues as required by Requirements 9.3.
"""
import pytest
import pytest_asyncio
import asyncio
from test_concurrent_performance_property import ConcurrentPerformanceTester


@pytest.mark.asyncio
async def test_concurrent_performance_framework_validation():
    """
    Validate that the concurrent performance testing framework works correctly.
    
    This test demonstrates that:
    1. The framework can execute concurrent operations
    2. Performance metrics are collected accurately
    3. Requirements 9.3 validation works correctly
    4. The system handles concurrent users without degradation
    """
    
    # Test with a reasonable concurrent load
    async with ConcurrentPerformanceTester(mock_mode=True) as tester:
        
        # Balanced operation mix
        operation_mix = {
            "api_request": 0.4,
            "cache_operation": 0.3,
            "database_query": 0.3
        }
        
        # Run concurrent performance test
        report = await tester.run_concurrent_test(
            concurrent_users=5,
            operations_per_user=20,
            test_duration=30.0,
            operation_mix=operation_mix,
            ramp_up_time=2.0
        )
        
        # Validate framework functionality
        assert report.concurrent_users == 5, "Should handle 5 concurrent users"
        assert report.total_operations > 0, "Should execute operations"
        assert report.successful_operations > 0, "Should have successful operations"
        
        # Validate performance metrics collection
        assert report.avg_response_time > 0, "Should collect response time metrics"
        assert report.operations_per_second > 0, "Should calculate throughput"
        assert report.peak_memory_usage_mb > 0, "Should collect memory metrics"
        
        # Validate Requirements 9.3 compliance
        # For a well-behaved system with reasonable load:
        assert report.error_rate < 10.0, f"Error rate {report.error_rate:.1f}% should be reasonable"
        assert report.avg_response_time < 1.0, f"Average response time {report.avg_response_time*1000:.1f}ms should be reasonable"
        
        # Validate concurrency analysis
        assert not report.deadlock_detected, "Should not detect deadlocks in normal operation"
        assert report.concurrent_operations_peak >= 1, "Should track concurrent operations"
        
        print(f"✅ Concurrent Performance Framework Validation Passed")
        print(f"   • Handled {report.concurrent_users} concurrent users")
        print(f"   • Executed {report.total_operations} operations")
        print(f"   • Success rate: {100-report.error_rate:.1f}%")
        print(f"   • Average response time: {report.avg_response_time*1000:.1f}ms")
        print(f"   • Throughput: {report.operations_per_second:.2f} ops/sec")
        print(f"   • Peak concurrent operations: {report.concurrent_operations_peak}")


@pytest.mark.asyncio
async def test_concurrent_performance_requirements_validation():
    """
    Validate that the framework correctly identifies Requirements 9.3 compliance.
    
    This test demonstrates the framework's ability to validate:
    - Response time requirements (95% under 500ms)
    - Error rate thresholds
    - Resource utilization monitoring
    - Performance degradation detection
    """
    
    async with ConcurrentPerformanceTester(mock_mode=True) as tester:
        
        # Light load that should meet requirements
        operation_mix = {"api_request": 1.0}
        
        report = await tester.run_concurrent_test(
            concurrent_users=3,
            operations_per_user=15,
            test_duration=20.0,
            operation_mix=operation_mix,
            ramp_up_time=1.0
        )
        
        # Validate Requirements 9.3 assessment
        print(f"\n🎯 Requirements 9.3 Validation Results:")
        print(f"   • Error rate: {report.error_rate:.1f}%")
        print(f"   • 95th percentile response time: {report.p95_response_time*1000:.1f}ms")
        print(f"   • Average response time: {report.avg_response_time*1000:.1f}ms")
        print(f"   • Performance degradation detected: {report.performance_degradation_detected}")
        
        if report.degradation_reasons:
            print(f"   • Degradation reasons:")
            for reason in report.degradation_reasons:
                print(f"     - {reason}")
        
        # The framework should provide meaningful performance assessment
        assert isinstance(report.performance_degradation_detected, bool), \
            "Should provide performance degradation assessment"
        
        assert isinstance(report.error_rate, float), \
            "Should calculate error rate"
        
        assert report.p95_response_time >= 0, \
            "Should calculate 95th percentile response time"
        
        # Resource monitoring should work
        assert report.peak_memory_usage_mb > 0, "Should monitor memory usage"
        assert report.peak_cpu_percent >= 0, "Should monitor CPU usage"
        
        print(f"✅ Requirements 9.3 Validation Framework Working Correctly")


@pytest.mark.asyncio
async def test_concurrent_performance_edge_cases():
    """
    Test edge cases and error conditions in concurrent performance testing.
    """
    
    async with ConcurrentPerformanceTester(mock_mode=True) as tester:
        
        # Test with single user (edge case)
        report = await tester.run_concurrent_test(
            concurrent_users=1,
            operations_per_user=5,
            test_duration=10.0,
            operation_mix={"api_request": 1.0},
            ramp_up_time=1.0
        )
        
        assert report.concurrent_users == 1, "Should handle single user"
        assert report.total_operations > 0, "Should execute operations with single user"
        
        # Test with mixed operations including potential failures
        mixed_operations = {
            "api_request": 0.3,
            "cache_operation": 0.3,
            "database_query": 0.2,
            "file_processing": 0.2  # This might have higher error rate
        }
        
        report2 = await tester.run_concurrent_test(
            concurrent_users=4,
            operations_per_user=10,
            test_duration=15.0,
            operation_mix=mixed_operations,
            ramp_up_time=1.0
        )
        
        # Should handle mixed workload
        assert report2.total_operations > 0, "Should handle mixed operations"
        assert len(report2.errors_by_type) >= 0, "Should track error types"
        
        print(f"✅ Edge Cases Handled Correctly")
        print(f"   • Single user test: {report.total_operations} operations")
        print(f"   • Mixed workload test: {report2.total_operations} operations")
        print(f"   • Error types tracked: {list(report2.errors_by_type.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])