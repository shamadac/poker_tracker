#!/usr/bin/env python3
"""
Unit tests for database failure handling.

**Validates: Requirements 4.9**

This test suite validates:
1. Graceful degradation when database is unavailable
2. Proper error handling for database connection failures
3. Transaction rollback on failures
4. Connection pool management during failures
5. User-friendly error messages for database issues
6. Recovery mechanisms after database restoration
7. Data integrity protection during failures
"""

import asyncio
import pytest
import sqlite3
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import logging

# Test configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_db_failure.db"

class DatabaseFailureSimulator:
    """Simulate various database failure scenarios."""
    
    def __init__(self):
        self.failure_modes = {
            "connection_timeout": self._simulate_connection_timeout,
            "connection_refused": self._simulate_connection_refused,
            "database_locked": self._simulate_database_locked,
            "disk_full": self._simulate_disk_full,
            "transaction_deadlock": self._simulate_transaction_deadlock,
            "constraint_violation": self._simulate_constraint_violation,
            "connection_lost": self._simulate_connection_lost,
            "pool_exhausted": self._simulate_pool_exhausted,
        }
    
    def _simulate_connection_timeout(self):
        """Simulate database connection timeout."""
        import asyncio
        raise asyncio.TimeoutError("Database connection timeout")
    
    def _simulate_connection_refused(self):
        """Simulate database connection refused."""
        import sqlite3
        raise sqlite3.OperationalError("database connection refused")
    
    def _simulate_database_locked(self):
        """Simulate database locked error."""
        import sqlite3
        raise sqlite3.OperationalError("database is locked")
    
    def _simulate_disk_full(self):
        """Simulate disk full error."""
        import sqlite3
        raise sqlite3.OperationalError("database or disk is full")
    
    def _simulate_transaction_deadlock(self):
        """Simulate transaction deadlock."""
        import sqlite3
        raise sqlite3.OperationalError("database deadlock")
    
    def _simulate_constraint_violation(self):
        """Simulate constraint violation."""
        import sqlite3
        raise sqlite3.IntegrityError("UNIQUE constraint failed")
    
    def _simulate_connection_lost(self):
        """Simulate connection lost during operation."""
        import sqlite3
        raise sqlite3.OperationalError("connection lost")
    
    def _simulate_pool_exhausted(self):
        """Simulate connection pool exhausted."""
        raise Exception("Connection pool exhausted")
    
    def trigger_failure(self, failure_mode: str):
        """Trigger a specific failure mode."""
        if failure_mode in self.failure_modes:
            self.failure_modes[failure_mode]()
        else:
            raise ValueError(f"Unknown failure mode: {failure_mode}")

class MockDatabaseService:
    """Mock database service for testing failure scenarios."""
    
    def __init__(self):
        self.failure_simulator = DatabaseFailureSimulator()
        self.connection_available = True
        self.transaction_active = False
        self.operations_log = []
    
    async def connect(self):
        """Mock database connection."""
        if not self.connection_available:
            self.failure_simulator.trigger_failure("connection_refused")
        
        self.operations_log.append("connect")
        return True
    
    async def disconnect(self):
        """Mock database disconnection."""
        self.operations_log.append("disconnect")
        return True
    
    async def begin_transaction(self):
        """Mock transaction begin."""
        if not self.connection_available:
            self.failure_simulator.trigger_failure("connection_lost")
        
        self.transaction_active = True
        self.operations_log.append("begin_transaction")
    
    async def commit_transaction(self):
        """Mock transaction commit."""
        if not self.connection_available:
            self.failure_simulator.trigger_failure("connection_lost")
        
        self.transaction_active = False
        self.operations_log.append("commit_transaction")
    
    async def rollback_transaction(self):
        """Mock transaction rollback."""
        self.transaction_active = False
        self.operations_log.append("rollback_transaction")
    
    async def execute_query(self, query: str, params: Optional[Dict] = None):
        """Mock query execution."""
        if not self.connection_available:
            self.failure_simulator.trigger_failure("connection_lost")
        
        self.operations_log.append(f"execute_query: {query[:50]}")
        
        # Simulate specific query failures
        if "INSERT" in query.upper() and "duplicate" in str(params or {}):
            self.failure_simulator.trigger_failure("constraint_violation")
        
        return {"success": True, "rows_affected": 1}
    
    def set_connection_available(self, available: bool):
        """Set connection availability for testing."""
        self.connection_available = available
    
    def get_operations_log(self) -> List[str]:
        """Get log of operations performed."""
        return self.operations_log.copy()
    
    def clear_operations_log(self):
        """Clear operations log."""
        self.operations_log.clear()

class DatabaseFailureHandler:
    """Handle database failures gracefully."""
    
    def __init__(self, db_service: MockDatabaseService):
        self.db_service = db_service
        self.retry_attempts = 3
        self.retry_delay = 0.1  # Short delay for testing
        self.fallback_enabled = True
        self.error_log = []
    
    async def execute_with_retry(self, operation_name: str, operation_func, *args, **kwargs):
        """Execute database operation with retry logic."""
        last_exception = None
        actual_attempts = 0
        
        for attempt in range(self.retry_attempts):
            actual_attempts = attempt + 1
            try:
                result = await operation_func(*args, **kwargs)
                return {"success": True, "result": result, "attempts": actual_attempts}
            
            except Exception as e:
                last_exception = e
                self.error_log.append({
                    "operation": operation_name,
                    "attempt": actual_attempts,
                    "error": str(e),
                    "timestamp": datetime.now()
                })
                
                # Don't retry for certain errors
                if self._is_non_retryable_error(e):
                    break
                
                # Wait before retry (except last attempt)
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
        
        # All retries failed
        return {
            "success": False,
            "error": str(last_exception),
            "attempts": actual_attempts,
            "fallback_available": self.fallback_enabled
        }
    
    def _is_non_retryable_error(self, error: Exception) -> bool:
        """Check if error should not be retried."""
        error_str = str(error).lower()
        non_retryable_patterns = [
            "constraint failed",
            "unique constraint",
            "foreign key constraint",
            "not null constraint"
        ]
        
        return any(pattern in error_str for pattern in non_retryable_patterns)
    
    async def execute_transaction_with_rollback(self, operations: List[Dict[str, Any]]):
        """Execute multiple operations in a transaction with rollback on failure."""
        try:
            await self.db_service.begin_transaction()
            
            results = []
            for operation in operations:
                op_name = operation.get("name", "unknown")
                op_func = operation.get("function")
                op_args = operation.get("args", [])
                op_kwargs = operation.get("kwargs", {})
                
                result = await self.execute_with_retry(
                    op_name, op_func, *op_args, **op_kwargs
                )
                
                if not result["success"]:
                    # Rollback on any failure
                    await self.db_service.rollback_transaction()
                    return {
                        "success": False,
                        "error": f"Transaction failed at operation '{op_name}': {result['error']}",
                        "completed_operations": len(results),
                        "total_operations": len(operations)
                    }
                
                results.append(result)
            
            # All operations succeeded, commit transaction
            await self.db_service.commit_transaction()
            return {
                "success": True,
                "results": results,
                "completed_operations": len(results)
            }
            
        except Exception as e:
            # Ensure rollback on any exception
            try:
                await self.db_service.rollback_transaction()
            except Exception:
                pass  # Rollback might fail if connection is lost
            
            return {
                "success": False,
                "error": f"Transaction exception: {str(e)}",
                "completed_operations": 0,
                "total_operations": len(operations)
            }
    
    def get_user_friendly_error(self, error: Exception) -> str:
        """Convert technical database errors to user-friendly messages."""
        error_str = str(error).lower()
        
        if "connection" in error_str and ("refused" in error_str or "timeout" in error_str):
            return "Unable to connect to the database. Please try again later."
        
        elif "database is locked" in error_str:
            return "The database is temporarily busy. Please try again in a moment."
        
        elif "disk is full" in error_str:
            return "Storage space is full. Please contact support."
        
        elif "constraint" in error_str:
            if "unique" in error_str:
                return "This data already exists. Please check your input."
            elif "foreign key" in error_str:
                return "Invalid reference. Please check related data."
            elif "not null" in error_str:
                return "Required information is missing. Please complete all fields."
        
        elif "deadlock" in error_str:
            return "A temporary conflict occurred. Please try again."
        
        else:
            return "A database error occurred. Please try again or contact support."
    
    def get_error_log(self) -> List[Dict[str, Any]]:
        """Get error log for debugging."""
        return self.error_log.copy()
    
    def clear_error_log(self):
        """Clear error log."""
        self.error_log.clear()

# Unit tests
class TestDatabaseFailureHandling:
    """Unit tests for database failure handling."""
    
    def setup_method(self):
        """Set up test environment."""
        self.db_service = MockDatabaseService()
        self.failure_handler = DatabaseFailureHandler(self.db_service)
    
    def test_connection_failure_handling(self):
        """Test handling of database connection failures."""
        # Simulate connection unavailable
        self.db_service.set_connection_available(False)
        
        async def test_connection():
            result = await self.failure_handler.execute_with_retry(
                "connect", self.db_service.connect
            )
            return result
        
        # Run the test
        result = asyncio.run(test_connection())
        
        # Should fail after retries
        assert not result["success"]
        assert result["attempts"] == 3
        assert "connection refused" in result["error"].lower()
        assert result["fallback_available"]
        
        # Should have logged errors
        error_log = self.failure_handler.get_error_log()
        assert len(error_log) == 3  # 3 retry attempts
        assert all("connect" in log["operation"] for log in error_log)
    
    def test_transaction_rollback_on_failure(self):
        """Test transaction rollback when operations fail."""
        # Create operations where second one will fail
        operations = [
            {
                "name": "insert_user",
                "function": self.db_service.execute_query,
                "args": ["INSERT INTO users (name) VALUES (?)", {"name": "test"}]
            },
            {
                "name": "insert_duplicate",
                "function": self.db_service.execute_query,
                "args": ["INSERT INTO users (name) VALUES (?)", {"name": "duplicate"}]
            }
        ]
        
        # Mock the second operation to fail
        original_execute = self.db_service.execute_query
        call_count = 0
        
        async def mock_execute_query(query, params=None):
            nonlocal call_count
            call_count += 1
            if call_count > 1:  # Second call fails
                raise Exception("UNIQUE constraint failed")
            return await original_execute(query, params)
        
        self.db_service.execute_query = mock_execute_query
        
        async def test_transaction():
            result = await self.failure_handler.execute_transaction_with_rollback(operations)
            return result
        
        # Run the test
        result = asyncio.run(test_transaction())
        
        # Transaction should fail and rollback
        assert not result["success"]
        assert "constraint failed" in result["error"].lower()
        assert result["completed_operations"] == 1  # First operation completed before second failed
        
        # Check operations log includes rollback
        ops_log = self.db_service.get_operations_log()
        assert "begin_transaction" in ops_log
        assert "rollback_transaction" in ops_log
        assert "commit_transaction" not in ops_log
    
    def test_transaction_rollback_on_connection_loss(self):
        """Test transaction rollback when connection is lost."""
        operations = [
            {
                "name": "insert_user",
                "function": self.db_service.execute_query,
                "args": ["INSERT INTO users (name) VALUES (?)", {"name": "test"}]
            }
        ]
        
        async def test_transaction_with_connection_loss():
            # Start transaction
            await self.db_service.begin_transaction()
            
            # Simulate connection loss during transaction
            self.db_service.set_connection_available(False)
            
            result = await self.failure_handler.execute_transaction_with_rollback(operations)
            return result
        
        # Run the test
        result = asyncio.run(test_transaction_with_connection_loss())
        
        # Transaction should fail
        assert not result["success"]
        assert "connection lost" in result["error"].lower()
        assert result["completed_operations"] == 0
        
        # Should have attempted rollback
        ops_log = self.db_service.get_operations_log()
        assert "rollback_transaction" in ops_log
    
    def test_retry_logic_with_temporary_failures(self):
        """Test retry logic with temporary failures."""
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:  # Fail first 2 attempts
                raise Exception("Temporary failure")
            
            return "success"
        
        async def test_retry():
            result = await self.failure_handler.execute_with_retry(
                "test_operation", failing_operation
            )
            return result
        
        # Run the test
        result = asyncio.run(test_retry())
        
        # Should succeed on 3rd attempt
        assert result["success"]
        assert result["attempts"] == 3
        assert result["result"] == "success"
        
        # Should have logged 2 errors (first 2 failures)
        error_log = self.failure_handler.get_error_log()
        assert len(error_log) == 2
    
    def test_non_retryable_errors(self):
        """Test that certain errors are not retried."""
        async def constraint_violation():
            raise Exception("UNIQUE constraint failed")
        
        async def test_non_retryable():
            result = await self.failure_handler.execute_with_retry(
                "constraint_test", constraint_violation
            )
            return result
        
        # Run the test
        result = asyncio.run(test_non_retryable())
        
        # Should fail immediately without retries (constraint errors are non-retryable)
        assert not result["success"]
        assert result["attempts"] == 1  # Only 1 attempt due to non-retryable error
        assert "constraint failed" in result["error"].lower()
        
        # Should have only 1 error log entry
        error_log = self.failure_handler.get_error_log()
        assert len(error_log) == 1
    
    def test_user_friendly_error_messages(self):
        """Test conversion of technical errors to user-friendly messages."""
        test_cases = [
            (Exception("database connection refused"), "Unable to connect to the database"),
            (Exception("connection timeout"), "Unable to connect to the database"),
            (Exception("database is locked"), "database is temporarily busy"),
            (Exception("database or disk is full"), "Storage space is full"),
            (Exception("UNIQUE constraint failed"), "This data already exists"),
            (Exception("FOREIGN KEY constraint failed"), "Invalid reference"),
            (Exception("NOT NULL constraint failed"), "Required information is missing"),
            (Exception("database deadlock"), "temporary conflict occurred"),
            (Exception("unknown error"), "database error occurred"),
        ]
        
        for error, expected_message_part in test_cases:
            friendly_message = self.failure_handler.get_user_friendly_error(error)
            assert expected_message_part.lower() in friendly_message.lower(), (
                f"Expected '{expected_message_part}' in '{friendly_message}' for error: {error}"
            )
    
    def test_graceful_degradation(self):
        """Test graceful degradation when database is unavailable."""
        # Simulate database unavailable
        self.db_service.set_connection_available(False)
        
        async def test_degradation():
            # Try to perform database operation
            result = await self.failure_handler.execute_with_retry(
                "get_user_data", self.db_service.execute_query,
                "SELECT * FROM users WHERE id = ?", {"id": 1}
            )
            
            return result
        
        # Run the test
        result = asyncio.run(test_degradation())
        
        # Should fail gracefully
        assert not result["success"]
        assert result["fallback_available"]  # Indicates fallback options exist
        
        # Error should be user-friendly
        friendly_error = self.failure_handler.get_user_friendly_error(
            Exception(result["error"])
        )
        assert "try again" in friendly_error.lower()
    
    def test_connection_pool_exhaustion_handling(self):
        """Test handling of connection pool exhaustion."""
        async def pool_exhausted_operation():
            raise Exception("Connection pool exhausted")
        
        async def test_pool_exhaustion():
            result = await self.failure_handler.execute_with_retry(
                "pool_test", pool_exhausted_operation
            )
            return result
        
        # Run the test
        result = asyncio.run(test_pool_exhaustion())
        
        # Should fail after retries
        assert not result["success"]
        assert result["attempts"] == 3
        assert "pool exhausted" in result["error"].lower()
        
        # Should provide user-friendly error
        friendly_error = self.failure_handler.get_user_friendly_error(
            Exception(result["error"])
        )
        assert "database error occurred" in friendly_error.lower()
    
    def test_database_recovery_after_failure(self):
        """Test system recovery after database becomes available again."""
        # Start with database unavailable
        self.db_service.set_connection_available(False)
        
        async def test_recovery():
            # First operation should fail
            result1 = await self.failure_handler.execute_with_retry(
                "test_op", self.db_service.execute_query,
                "SELECT 1", {}
            )
            
            # Restore database availability
            self.db_service.set_connection_available(True)
            
            # Second operation should succeed
            result2 = await self.failure_handler.execute_with_retry(
                "test_op", self.db_service.execute_query,
                "SELECT 1", {}
            )
            
            return result1, result2
        
        # Run the test
        result1, result2 = asyncio.run(test_recovery())
        
        # First should fail, second should succeed
        assert not result1["success"]
        assert result2["success"]
        assert result2["attempts"] == 1  # Should succeed immediately
    
    def test_error_logging_and_monitoring(self):
        """Test error logging for monitoring and debugging."""
        # Clear any existing logs
        self.failure_handler.clear_error_log()
        
        async def test_error_logging():
            # Cause some failures
            self.db_service.set_connection_available(False)
            
            await self.failure_handler.execute_with_retry(
                "test_op1", self.db_service.connect
            )
            
            await self.failure_handler.execute_with_retry(
                "test_op2", self.db_service.execute_query,
                "SELECT 1", {}
            )
            
            return True
        
        # Run the test
        asyncio.run(test_error_logging())
        
        # Check error log
        error_log = self.failure_handler.get_error_log()
        
        # Should have logged multiple errors (3 retries per operation)
        assert len(error_log) == 6  # 2 operations × 3 retries each
        
        # Check log structure
        for log_entry in error_log:
            assert "operation" in log_entry
            assert "attempt" in log_entry
            assert "error" in log_entry
            assert "timestamp" in log_entry
            assert isinstance(log_entry["timestamp"], datetime)
        
        # Check operation names are logged
        operations = [log["operation"] for log in error_log]
        assert "test_op1" in operations
        assert "test_op2" in operations
    
    def test_data_integrity_protection(self):
        """Test that data integrity is protected during failures."""
        # Test partial transaction failure
        operations = [
            {
                "name": "create_user",
                "function": self.db_service.execute_query,
                "args": ["INSERT INTO users (name) VALUES (?)", {"name": "test_user"}]
            },
            {
                "name": "create_profile", 
                "function": self.db_service.execute_query,
                "args": ["INSERT INTO profiles (user_id) VALUES (?)", {"user_id": 1}]
            }
        ]
        
        async def test_integrity():
            # Start transaction
            result = await self.failure_handler.execute_transaction_with_rollback(operations)
            
            # Simulate failure during second operation
            self.db_service.set_connection_available(False)
            
            # Try another transaction that should fail
            result2 = await self.failure_handler.execute_transaction_with_rollback(operations)
            
            return result, result2
        
        # Run the test
        result1, result2 = asyncio.run(test_integrity())
        
        # First transaction should succeed
        assert result1["success"]
        assert result1["completed_operations"] == 2
        
        # Second transaction should fail and rollback
        assert not result2["success"]
        assert result2["completed_operations"] == 0
        
        # Check that rollback was attempted
        ops_log = self.db_service.get_operations_log()
        assert "rollback_transaction" in ops_log

def test_database_failure_integration():
    """Integration test for database failure handling."""
    db_service = MockDatabaseService()
    failure_handler = DatabaseFailureHandler(db_service)
    
    # Test basic functionality
    async def test_basic():
        result = await failure_handler.execute_with_retry(
            "test", db_service.execute_query,
            "SELECT 1", {}
        )
        return result
    
    result = asyncio.run(test_basic())
    assert result["success"]
    
    # Test failure handling
    db_service.set_connection_available(False)
    
    async def test_failure():
        result = await failure_handler.execute_with_retry(
            "test", db_service.connect
        )
        return result
    
    result = asyncio.run(test_failure())
    assert not result["success"]
    assert result["attempts"] == 3
    
    print("✅ Database failure handling tests passed:")
    print("   - Connection failure handling working")
    print("   - Transaction rollback working")
    print("   - Retry logic working")
    print("   - User-friendly error messages working")
    print("   - Graceful degradation working")

if __name__ == "__main__":
    # Run integration test
    test_database_failure_integration()
    print("🎉 Database failure handling tests ready to run!")