"""
Property-based test for system event logging.

Feature: professional-poker-analyzer-rebuild
Property 8: System Event Logging

This test validates that for any significant system operation (authentication, 
data processing, errors), appropriate log entries are generated with proper 
detail levels and structured format according to Requirement 3.8.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from contextlib import contextmanager

# Import the logging components to test
from app.core.logging import (
    StructuredLogger, 
    PerformanceLogger, 
    SecurityLogger,
    setup_logging,
    get_logger,
    set_request_context,
    clear_request_context,
    get_request_id,
    generate_request_id,
    ContextualFormatter
)


class LogCapture:
    """Helper class to capture log messages for testing."""
    
    def __init__(self):
        self.records: List[logging.LogRecord] = []
        self.handler = logging.Handler()
        self.handler.emit = self._emit
    
    def _emit(self, record: logging.LogRecord):
        """Capture log record."""
        self.records.append(record)
    
    def clear(self):
        """Clear captured records."""
        self.records.clear()
    
    def get_messages(self, level: Optional[int] = None) -> List[str]:
        """Get formatted log messages, optionally filtered by level."""
        messages = []
        for record in self.records:
            if level is None or record.levelno >= level:
                messages.append(record.getMessage())
        return messages
    
    def get_records(self, level: Optional[int] = None) -> List[logging.LogRecord]:
        """Get log records, optionally filtered by level."""
        if level is None:
            return self.records.copy()
        return [r for r in self.records if r.levelno >= level]


class TestSystemLoggingProperty:
    """Property-based tests for system event logging."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create log capture
        self.log_capture = LogCapture()
        
        # Store original handlers
        self.original_handlers = {}
        
        # Clear any existing request context
        clear_request_context()
    
    def teardown_method(self):
        """Clean up test environment."""
        # Restore original handlers
        for logger_name, handlers in self.original_handlers.items():
            logger = logging.getLogger(logger_name)
            logger.handlers = handlers
        
        # Clear request context
        clear_request_context()
        
        # Clear log capture
        self.log_capture.clear()
    
    @contextmanager
    def capture_logs(self, logger_names: List[str]):
        """Context manager to capture logs from specified loggers."""
        loggers = []
        
        try:
            # Set up log capture for each logger
            for logger_name in logger_names:
                logger = logging.getLogger(logger_name)
                # Store original handlers
                self.original_handlers[logger_name] = logger.handlers.copy()
                # Add our capture handler
                logger.addHandler(self.log_capture.handler)
                logger.setLevel(logging.DEBUG)
                loggers.append(logger)
            
            yield self.log_capture
            
        finally:
            # Remove capture handler from all loggers
            for logger in loggers:
                if self.log_capture.handler in logger.handlers:
                    logger.removeHandler(self.log_capture.handler)
    
    @given(
        message=st.text(min_size=1, max_size=200),
        level=st.sampled_from([logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]),
        extra_data=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))).filter(
                lambda x: x not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 
                                   'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 
                                   'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info', 
                                   'exc_text', 'stack_info', 'timestamp', 'request_id']
            ),
            st.one_of(
                st.text(max_size=50),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans()
            ),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_structured_logging_property(self, message: str, level: int, extra_data: Dict[str, Any]):
        """
        Property: For any log message with structured data, the StructuredLogger
        should generate log entries with proper structure and include all provided data.
        
        Validates: Requirements 3.8 - comprehensive logging with structured format
        """
        logger_name = "test_structured"
        
        with self.capture_logs([logger_name]):
            # Create structured logger
            structured_logger = StructuredLogger(logger_name)
            
            # Log message with extra data
            if level == logging.DEBUG:
                structured_logger.debug(message, **extra_data)
            elif level == logging.INFO:
                structured_logger.info(message, **extra_data)
            elif level == logging.WARNING:
                structured_logger.warning(message, **extra_data)
            elif level == logging.ERROR:
                structured_logger.error(message, **extra_data)
            elif level == logging.CRITICAL:
                structured_logger.critical(message, **extra_data)
            
            # Verify log was captured
            records = self.log_capture.get_records(level)
            assert len(records) >= 1
            
            record = records[-1]  # Get the most recent record
            
            # Verify basic log properties
            assert record.levelno == level
            assert record.getMessage() == message
            assert record.name == logger_name
            
            # Verify structured data is present
            assert hasattr(record, 'timestamp')
            assert hasattr(record, 'request_id')
            
            # Verify extra data is included
            for key, value in extra_data.items():
                assert hasattr(record, key)
                assert getattr(record, key) == value
            
            # Verify timestamp format
            timestamp = getattr(record, 'timestamp')
            assert isinstance(timestamp, str)
            # Should be ISO format
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    @given(
        request_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
        message=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50, deadline=None)
    def test_request_context_tracking_property(self, request_id: str, message: str):
        """
        Property: For any request ID set in context, all log messages should
        include that request ID for proper request tracking.
        
        Validates: Requirements 3.8 - comprehensive logging with request correlation
        """
        logger_name = "test_context"
        
        with self.capture_logs([logger_name]):
            # Set request context
            set_request_context(request_id)
            
            # Verify context is set
            assert get_request_id() == request_id
            
            # Create logger and log message
            structured_logger = StructuredLogger(logger_name)
            structured_logger.info(message)
            
            # Verify log includes request ID
            records = self.log_capture.get_records(logging.INFO)
            assert len(records) >= 1
            
            record = records[-1]
            assert hasattr(record, 'request_id')
            assert getattr(record, 'request_id') == request_id
            
            # Clear context and verify it changes
            clear_request_context()
            assert get_request_id() is None
            
            # Log another message
            structured_logger.info(message + "_after_clear")
            
            # Verify new log has no request ID or default value
            records = self.log_capture.get_records(logging.INFO)
            assert len(records) >= 2
            
            record = records[-1]
            request_id_value = getattr(record, 'request_id', None)
            assert request_id_value is None or request_id_value == "no-request"
    
    @given(
        method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
        path=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd', 'Ps'))).map(lambda x: f"/{x}"),
        duration=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False),
        status_code=st.integers(min_value=200, max_value=599)
    )
    @settings(max_examples=100, deadline=None)
    def test_performance_logging_property(self, method: str, path: str, duration: float, status_code: int):
        """
        Property: For any request performance data, the PerformanceLogger should
        log structured performance metrics with all required fields.
        
        Validates: Requirements 3.8 - comprehensive logging for performance monitoring
        """
        with self.capture_logs(["performance"]):
            # Create performance logger
            perf_logger = PerformanceLogger()
            
            # Log request performance
            perf_logger.log_request_performance(method, path, duration, status_code)
            
            # Verify log was captured
            records = self.log_capture.get_records(logging.INFO)
            assert len(records) >= 1
            
            record = records[-1]
            
            # Verify performance data is logged
            assert record.getMessage() == "request_performance"
            assert hasattr(record, 'method')
            assert hasattr(record, 'path')
            assert hasattr(record, 'duration_seconds')
            assert hasattr(record, 'duration_ms')
            assert hasattr(record, 'status_code')
            
            # Verify values
            assert getattr(record, 'method') == method
            assert getattr(record, 'path') == path
            assert getattr(record, 'duration_seconds') == duration
            assert abs(getattr(record, 'duration_ms') - (duration * 1000)) < 0.001
            assert getattr(record, 'status_code') == status_code
    
    @given(
        query_type=st.sampled_from(['SELECT', 'INSERT', 'UPDATE', 'DELETE']),
        duration=st.floats(min_value=0.001, max_value=5.0, allow_nan=False, allow_infinity=False),
        table=st.one_of(
            st.none(),
            st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_database_performance_logging_property(self, query_type: str, duration: float, table: Optional[str]):
        """
        Property: For any database query performance data, the PerformanceLogger
        should log structured database metrics with proper timing information.
        
        Validates: Requirements 3.8 - comprehensive logging for data processing operations
        """
        with self.capture_logs(["performance"]):
            # Create performance logger
            perf_logger = PerformanceLogger()
            
            # Log database query performance
            perf_logger.log_database_query(query_type, duration, table)
            
            # Verify log was captured
            records = self.log_capture.get_records(logging.INFO)
            assert len(records) >= 1
            
            record = records[-1]
            
            # Verify database performance data is logged
            assert record.getMessage() == "database_query"
            assert hasattr(record, 'query_type')
            assert hasattr(record, 'duration_seconds')
            assert hasattr(record, 'duration_ms')
            assert hasattr(record, 'table')
            
            # Verify values
            assert getattr(record, 'query_type') == query_type
            assert getattr(record, 'duration_seconds') == duration
            assert abs(getattr(record, 'duration_ms') - (duration * 1000)) < 0.001
            assert getattr(record, 'table') == table
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
        success=st.booleans(),
        ip_address=st.one_of(
            st.just("127.0.0.1"),
            st.just("192.168.1.1"),
            st.just("10.0.0.1"),
            st.text(min_size=7, max_size=15).filter(lambda x: '.' in x and len(x.split('.')) == 4)
        )
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_authentication_logging_property(self, user_id: str, success: bool, ip_address: str):
        """
        Property: For any authentication attempt, the SecurityLogger should
        log structured authentication events with user, success status, and IP.
        
        Validates: Requirements 3.8 - comprehensive logging for authentication operations
        """
        with self.capture_logs(["security"]):
            # Create security logger
            sec_logger = SecurityLogger()
            
            # Log authentication attempt
            sec_logger.log_authentication_attempt(user_id, success, ip_address)
            
            # Verify log was captured
            records = self.log_capture.get_records(logging.INFO)
            assert len(records) >= 1
            
            record = records[-1]
            
            # Verify authentication data is logged
            assert record.getMessage() == "authentication_attempt"
            assert hasattr(record, 'user_id')
            assert hasattr(record, 'success')
            assert hasattr(record, 'ip_address')
            
            # Verify values
            assert getattr(record, 'user_id') == user_id
            assert getattr(record, 'success') == success
            assert getattr(record, 'ip_address') == ip_address
    
    @given(
        user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
        resource=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        action=st.sampled_from(['read', 'write', 'delete', 'update', 'create'])
    )
    @settings(max_examples=100, deadline=None)
    def test_authorization_failure_logging_property(self, user_id: str, resource: str, action: str):
        """
        Property: For any authorization failure, the SecurityLogger should
        log structured security events with user, resource, and action details.
        
        Validates: Requirements 3.8 - comprehensive logging for security events
        """
        with self.capture_logs(["security"]):
            # Create security logger
            sec_logger = SecurityLogger()
            
            # Log authorization failure
            sec_logger.log_authorization_failure(user_id, resource, action)
            
            # Verify log was captured
            records = self.log_capture.get_records(logging.WARNING)
            assert len(records) >= 1
            
            record = records[-1]
            
            # Verify authorization failure data is logged
            assert record.getMessage() == "authorization_failure"
            assert hasattr(record, 'user_id')
            assert hasattr(record, 'resource')
            assert hasattr(record, 'action')
            
            # Verify values
            assert getattr(record, 'user_id') == user_id
            assert getattr(record, 'resource') == resource
            assert getattr(record, 'action') == action
    
    @given(
        ip_address=st.one_of(
            st.just("127.0.0.1"),
            st.just("192.168.1.1"),
            st.just("10.0.0.1"),
            st.text(min_size=7, max_size=15).filter(lambda x: '.' in x and len(x.split('.')) == 4)
        ),
        endpoint=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd', 'Ps'))).map(lambda x: f"/{x}"),
        limit=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_rate_limit_logging_property(self, ip_address: str, endpoint: str, limit: int):
        """
        Property: For any rate limit violation, the SecurityLogger should
        log structured security events with IP, endpoint, and limit details.
        
        Validates: Requirements 3.8 - comprehensive logging for security protection
        """
        with self.capture_logs(["security"]):
            # Create security logger
            sec_logger = SecurityLogger()
            
            # Log rate limit exceeded
            sec_logger.log_rate_limit_exceeded(ip_address, endpoint, limit)
            
            # Verify log was captured
            records = self.log_capture.get_records(logging.WARNING)
            assert len(records) >= 1
            
            record = records[-1]
            
            # Verify rate limit data is logged
            assert record.getMessage() == "rate_limit_exceeded"
            assert hasattr(record, 'ip_address')
            assert hasattr(record, 'endpoint')
            assert hasattr(record, 'limit')
            
            # Verify values
            assert getattr(record, 'ip_address') == ip_address
            assert getattr(record, 'endpoint') == endpoint
            assert getattr(record, 'limit') == limit
    
    @given(
        activity_type=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        details=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            st.one_of(st.text(max_size=50), st.integers(), st.booleans()),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_suspicious_activity_logging_property(self, activity_type: str, details: Dict[str, Any]):
        """
        Property: For any suspicious activity, the SecurityLogger should
        log structured security events with activity type and detailed information.
        
        Validates: Requirements 3.8 - comprehensive logging for security monitoring
        """
        with self.capture_logs(["security"]):
            # Create security logger
            sec_logger = SecurityLogger()
            
            # Log suspicious activity
            sec_logger.log_suspicious_activity(activity_type, details)
            
            # Verify log was captured
            records = self.log_capture.get_records(logging.WARNING)
            assert len(records) >= 1
            
            record = records[-1]
            
            # Verify suspicious activity data is logged
            assert record.getMessage() == "suspicious_activity"
            assert hasattr(record, 'activity_type')
            
            # Verify activity type
            assert getattr(record, 'activity_type') == activity_type
            
            # Verify all details are included
            for key, value in details.items():
                assert hasattr(record, key)
                assert getattr(record, key) == value
    
    def test_request_id_generation_property(self):
        """
        Property: Generated request IDs should be unique and properly formatted.
        
        Validates: Requirements 3.8 - proper request correlation tracking
        """
        # Generate multiple request IDs
        request_ids = set()
        for _ in range(100):
            request_id = generate_request_id()
            
            # Verify format (should be UUID-like)
            assert isinstance(request_id, str)
            assert len(request_id) > 10  # UUIDs are much longer
            assert request_id not in request_ids  # Should be unique
            
            request_ids.add(request_id)
            
            # Verify it can be used as UUID
            try:
                uuid.UUID(request_id)
            except ValueError:
                pytest.fail(f"Generated request ID '{request_id}' is not a valid UUID")
    
    @given(
        log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
        log_file=st.one_of(
            st.none(),
            st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))).map(lambda x: f"/tmp/{x}.log")
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_logging_setup_property(self, log_level: str, log_file: Optional[str]):
        """
        Property: For any valid logging configuration, setup_logging should
        configure the logging system with appropriate handlers and formatters.
        
        Validates: Requirements 3.8 - comprehensive logging configuration
        """
        # Store original root logger state
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers.copy()
        original_level = root_logger.level
        
        try:
            # Clear existing handlers
            root_logger.handlers.clear()
            
            # Mock the JSON formatter to avoid dependency issues
            with patch('app.core.logging.logging.config.dictConfig') as mock_dict_config:
                # Setup logging with test parameters
                setup_logging(log_level=log_level, log_file=log_file)
                
                # Verify dictConfig was called
                assert mock_dict_config.called
                
                # Get the config that was passed
                config = mock_dict_config.call_args[0][0]
                
                # Verify basic configuration structure
                assert 'version' in config
                assert config['version'] == 1
                assert 'formatters' in config
                assert 'handlers' in config
                assert 'loggers' in config
                
                # Verify formatters are configured
                assert 'standard' in config['formatters']
                assert 'detailed' in config['formatters']
                
                # Verify handlers are configured
                assert 'console' in config['handlers']
                assert config['handlers']['console']['level'] == log_level
                
                # If log file specified, verify file handler is configured
                if log_file:
                    assert 'file' in config['handlers']
                    assert config['handlers']['file']['filename'] == log_file
                
                # Verify specific loggers are configured
                assert '' in config['loggers']  # Root logger
                assert 'performance' in config['loggers']
                assert 'security' in config['loggers']
                
                # Verify logger levels
                assert config['loggers']['']['level'] == log_level
                assert config['loggers']['performance']['level'] == 'INFO'
                assert config['loggers']['security']['level'] == 'INFO'
            
        finally:
            # Restore original logger state
            root_logger.handlers = original_handlers
            root_logger.level = original_level
    
    @given(
        cache_operation=st.sampled_from(['get', 'set', 'delete', 'clear']),
        cache_key=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'))),
        cache_hit=st.booleans(),
        duration=st.one_of(
            st.none(),
            st.floats(min_value=0.001, max_value=1.0, allow_nan=False, allow_infinity=False)
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_cache_operation_logging_property(self, cache_operation: str, cache_key: str, cache_hit: bool, duration: Optional[float]):
        """
        Property: For any cache operation, the PerformanceLogger should
        log structured cache metrics with operation details and timing.
        
        Validates: Requirements 3.8 - comprehensive logging for data processing operations
        """
        with self.capture_logs(["performance"]):
            # Create performance logger
            perf_logger = PerformanceLogger()
            
            # Log cache operation
            perf_logger.log_cache_operation(cache_operation, cache_key, cache_hit, duration)
            
            # Verify log was captured
            records = self.log_capture.get_records(logging.INFO)
            assert len(records) >= 1
            
            record = records[-1]
            
            # Verify cache operation data is logged
            assert record.getMessage() == "cache_operation"
            assert hasattr(record, 'operation')
            assert hasattr(record, 'cache_key')
            assert hasattr(record, 'cache_hit')
            assert hasattr(record, 'duration_ms')
            
            # Verify values
            assert getattr(record, 'operation') == cache_operation
            assert getattr(record, 'cache_key') == cache_key
            assert getattr(record, 'cache_hit') == cache_hit
            
            # Verify duration handling
            duration_ms = getattr(record, 'duration_ms')
            if duration is not None:
                assert abs(duration_ms - (duration * 1000)) < 0.001
            else:
                assert duration_ms is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])