"""
Error handling validation tests.
Tests comprehensive error handling and graceful degradation.
Requirements: 4.9
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, IntegrityError
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.error_handlers import (
    ErrorResponse,
    ServiceDegradationManager,
    DatabaseErrorHandler,
    ExternalServiceErrorHandler,
    ApplicationErrorHandler,
    create_error_response,
    degradation_manager
)
from app.services.exceptions import (
    HandParsingError,
    UnsupportedPlatformError,
    ValidationError,
    DuplicateHandError,
    FileMonitoringError,
    NotFoundError
)


class TestErrorResponse:
    """Test error response formatting."""
    
    def test_error_response_creation(self):
        """Test creating error responses with proper formatting."""
        error = ErrorResponse(
            error_type="validation_error",
            message="Test validation error",
            status_code=400,
            details={"field": "test_field"}
        )
        
        assert error.error_type == "validation_error"
        assert error.status_code == 400
        assert error.details["field"] == "test_field"
        assert "check your input" in error.user_message.lower()
    
    def test_user_friendly_messages(self):
        """Test user-friendly error message generation."""
        test_cases = [
            ("authentication_error", "log in"),
            ("authorization_error", "permission"),
            ("not_found", "not found"),
            ("rate_limit_exceeded", "try again later"),
            ("database_error", "technical difficulties"),
            ("internal_error", "unexpected error")
        ]
        
        for error_type, expected_phrase in test_cases:
            error = ErrorResponse(error_type=error_type, message="Test")
            assert expected_phrase.lower() in error.user_message.lower()
    
    def test_error_response_serialization(self):
        """Test error response serialization to dictionary."""
        error = ErrorResponse(
            error_type="test_error",
            message="Test message",
            details={"key": "value"}
        )
        
        result = error.to_dict()
        
        assert "error" in result
        assert result["error"]["type"] == "test_error"
        assert result["error"]["message"] == error.user_message
        assert result["error"]["details"]["key"] == "value"


class TestServiceDegradationManager:
    """Test service degradation management."""
    
    def setup_method(self):
        """Reset degradation manager before each test."""
        self.manager = ServiceDegradationManager()
    
    def test_service_status_tracking(self):
        """Test tracking service status changes."""
        # Initially all services should be up
        assert self.manager.is_service_available("database")
        assert self.manager.is_service_available("redis")
        
        # Mark database as down
        self.manager.mark_service_down("database")
        assert not self.manager.is_service_available("database")
        assert self.manager.is_service_available("redis")
        
        # Restore database
        self.manager.mark_service_up("database")
        assert self.manager.is_service_available("database")
    
    def test_ai_provider_specific_status(self):
        """Test AI provider specific status tracking."""
        # Mark specific AI provider as down
        self.manager.mark_service_down("ai_providers", "gemini")
        
        assert not self.manager.is_service_available("ai_providers", "gemini")
        assert self.manager.is_service_available("ai_providers", "groq")
        
        # Restore specific provider
        self.manager.mark_service_up("ai_providers", "gemini")
        assert self.manager.is_service_available("ai_providers", "gemini")
    
    def test_degraded_features_tracking(self):
        """Test degraded features are tracked correctly."""
        # Initially no degraded features
        assert len(self.manager.get_degraded_features()) == 0
        
        # Mark database as down - should add degraded features
        self.manager.mark_service_down("database")
        degraded = self.manager.get_degraded_features()
        
        assert "statistics" in degraded
        assert "hand_history" in degraded
        assert "user_data" in degraded
    
    def test_service_status_summary(self):
        """Test comprehensive service status summary."""
        # Mark some services as down
        self.manager.mark_service_down("redis")
        self.manager.mark_service_down("ai_providers", "gemini")
        
        status = self.manager.get_service_status()
        
        assert status["services"]["redis"] == False
        assert status["services"]["ai_providers"]["gemini"] == False
        assert status["services"]["ai_providers"]["groq"] == True
        assert status["overall_health"] == "degraded"
        assert len(status["degraded_features"]) > 0


class TestDatabaseErrorHandler:
    """Test database error handling."""
    
    @pytest.mark.asyncio
    async def test_operational_error_handling(self):
        """Test handling of database connection errors."""
        error = OperationalError("Connection failed", None, None)
        
        response = await DatabaseErrorHandler.handle_database_error(error, "test_operation")
        
        assert response.error_type == "database_connection_error"
        assert response.status_code == 503
        assert "database connectivity issues" in response.user_message.lower()
    
    @pytest.mark.asyncio
    async def test_integrity_error_handling(self):
        """Test handling of data integrity violations."""
        error = IntegrityError("Constraint violation", None, None)
        
        response = await DatabaseErrorHandler.handle_database_error(error, "test_operation")
        
        assert response.error_type == "data_integrity_error"
        assert response.status_code == 409
        assert "conflicts with existing data" in response.user_message.lower()
    
    @pytest.mark.asyncio
    async def test_generic_database_error(self):
        """Test handling of generic database errors."""
        from sqlalchemy.exc import SQLAlchemyError
        error = SQLAlchemyError("Generic database error")
        
        response = await DatabaseErrorHandler.handle_database_error(error, "test_operation")
        
        assert response.error_type == "database_error"
        assert response.status_code == 500


class TestExternalServiceErrorHandler:
    """Test external service error handling."""
    
    @pytest.mark.asyncio
    async def test_redis_connection_error(self):
        """Test Redis connection error handling."""
        error = RedisConnectionError("Redis connection failed")
        
        response = await ExternalServiceErrorHandler.handle_redis_error(error, "test_operation")
        
        assert response.error_type == "cache_unavailable"
        assert response.status_code == 503
        assert "temporarily unavailable" in response.user_message.lower()
    
    @pytest.mark.asyncio
    async def test_ai_provider_error(self):
        """Test AI provider error handling."""
        error = Exception("AI service timeout")
        
        response = await ExternalServiceErrorHandler.handle_ai_provider_error(
            error, "gemini", "hand_analysis"
        )
        
        assert response.error_type == "ai_service_error"
        assert response.status_code == 503
        assert "gemini" in response.user_message.lower()


class TestApplicationErrorHandler:
    """Test application-specific error handling."""
    
    @pytest.mark.asyncio
    async def test_unsupported_platform_error(self):
        """Test unsupported platform error handling."""
        error = UnsupportedPlatformError("Platform not supported")
        
        response = await ApplicationErrorHandler.handle_parsing_error(error)
        
        assert response.error_type == "unsupported_platform"
        assert response.status_code == 400
        assert "pokerstars or ggpoker" in response.user_message.lower()
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test validation error handling."""
        error = ValidationError("Hand validation failed")
        
        response = await ApplicationErrorHandler.handle_parsing_error(error)
        
        assert response.error_type == "validation_error"
        assert response.status_code == 400
        assert "corrupted or invalid" in response.user_message.lower()
    
    @pytest.mark.asyncio
    async def test_duplicate_hand_error(self):
        """Test duplicate hand error handling."""
        error = DuplicateHandError("Hand already processed")
        
        response = await ApplicationErrorHandler.handle_parsing_error(error)
        
        assert response.error_type == "duplicate_hand"
        assert response.status_code == 409
        assert "already been processed" in response.user_message.lower()
    
    @pytest.mark.asyncio
    async def test_file_monitoring_error(self):
        """Test file monitoring error handling."""
        error = FileMonitoringError("File monitoring failed")
        
        response = await ApplicationErrorHandler.handle_file_monitoring_error(error)
        
        assert response.error_type == "file_monitoring_error"
        assert response.status_code == 500
        assert "upload files manually" in response.user_message.lower()


class TestComprehensiveErrorHandling:
    """Test comprehensive error handling integration."""
    
    @pytest.mark.asyncio
    async def test_create_error_response_http_exception(self):
        """Test creating error response from HTTP exception."""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        
        http_error = HTTPException(status_code=404, detail="Not found")
        
        response = await create_error_response(http_error, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_create_error_response_database_error(self):
        """Test creating error response from database error."""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        
        db_error = OperationalError("Database connection failed", None, None)
        
        response = await create_error_response(db_error, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 503
    
    @pytest.mark.asyncio
    async def test_create_error_response_parsing_error(self):
        """Test creating error response from parsing error."""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        
        parsing_error = UnsupportedPlatformError("Platform not supported")
        
        response = await create_error_response(parsing_error, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_create_error_response_generic_error(self):
        """Test creating error response from generic error."""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        
        generic_error = Exception("Something went wrong")
        
        response = await create_error_response(generic_error, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestGracefulDegradation:
    """Test graceful degradation scenarios."""
    
    def test_database_unavailable_degradation(self):
        """Test system behavior when database is unavailable."""
        # Mark database as down
        degradation_manager.mark_service_down("database")
        
        # Check that appropriate features are marked as degraded
        degraded_features = degradation_manager.get_degraded_features()
        
        assert "statistics" in degraded_features
        assert "hand_history" in degraded_features
        assert "user_data" in degraded_features
        
        # System should still report degraded status
        status = degradation_manager.get_service_status()
        assert status["overall_health"] == "degraded"
        
        # Restore database
        degradation_manager.mark_service_up("database")
    
    def test_cache_unavailable_degradation(self):
        """Test system behavior when cache is unavailable."""
        # Mark Redis as down
        degradation_manager.mark_service_down("redis")
        
        # Check that caching features are marked as degraded
        degraded_features = degradation_manager.get_degraded_features()
        
        assert "caching" in degraded_features
        assert "real_time_updates" in degraded_features
        
        # Restore Redis
        degradation_manager.mark_service_up("redis")
    
    def test_ai_provider_partial_degradation(self):
        """Test system behavior when some AI providers are unavailable."""
        # Mark one AI provider as down
        degradation_manager.mark_service_down("ai_providers", "gemini")
        
        # System should still be partially functional
        assert not degradation_manager.is_service_available("ai_providers", "gemini")
        assert degradation_manager.is_service_available("ai_providers", "groq")
        
        # Check degraded features
        degraded_features = degradation_manager.get_degraded_features()
        assert "hand_analysis" in degraded_features
        
        # Restore AI provider
        degradation_manager.mark_service_up("ai_providers", "gemini")
    
    def test_multiple_service_failures(self):
        """Test system behavior with multiple service failures."""
        # Mark multiple services as down
        degradation_manager.mark_service_down("database")
        degradation_manager.mark_service_down("redis")
        degradation_manager.mark_service_down("file_monitoring")
        
        # Check overall system health
        status = degradation_manager.get_service_status()
        assert status["overall_health"] == "degraded"
        
        # Check that many features are degraded
        degraded_features = degradation_manager.get_degraded_features()
        assert len(degraded_features) > 5  # Multiple features should be affected
        
        # Restore all services
        degradation_manager.mark_service_up("database")
        degradation_manager.mark_service_up("redis")
        degradation_manager.mark_service_up("file_monitoring")


class TestErrorRecovery:
    """Test error recovery mechanisms."""
    
    def test_service_recovery_tracking(self):
        """Test that services can recover from failures."""
        # Get initial state
        initial_degraded_features = degradation_manager.get_degraded_features()
        
        # Mark service as down
        degradation_manager.mark_service_down("database")
        assert not degradation_manager.is_service_available("database")
        
        # Check that more features are degraded
        degraded_after_failure = degradation_manager.get_degraded_features()
        assert len(degraded_after_failure) >= len(initial_degraded_features)
        
        # Restore service
        degradation_manager.mark_service_up("database")
        assert degradation_manager.is_service_available("database")
        
        # Check that degraded features are reduced after recovery
        degraded_after_recovery = degradation_manager.get_degraded_features()
        # Should have same or fewer degraded features after recovery
        assert len(degraded_after_recovery) <= len(degraded_after_failure)
    
    def test_partial_recovery(self):
        """Test partial service recovery."""
        # Mark multiple AI providers as down
        degradation_manager.mark_service_down("ai_providers", "gemini")
        degradation_manager.mark_service_down("ai_providers", "groq")
        
        # Restore one provider
        degradation_manager.mark_service_up("ai_providers", "gemini")
        
        # Check partial recovery
        assert degradation_manager.is_service_available("ai_providers", "gemini")
        assert not degradation_manager.is_service_available("ai_providers", "groq")
        
        # Restore remaining provider
        degradation_manager.mark_service_up("ai_providers", "groq")
        assert degradation_manager.is_service_available("ai_providers", "groq")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])