#!/usr/bin/env python3
"""
Property-based test for API request validation.

Feature: professional-poker-analyzer-rebuild
Property 7: API Request Validation

This test validates that for any API request with invalid data, the system should
reject the request with proper validation errors and detailed feedback about what
needs to be corrected according to Requirement 3.4.
"""

import pytest
import asyncio
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from datetime import datetime, timezone
import json
import uuid

from hypothesis import given, strategies as st, settings, assume, HealthCheck
from pydantic import ValidationError
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Import schemas to test
from app.schemas.hand import (
    HandCreate, HandUpdate, HandFilters, HandBatchDeleteRequest,
    DetailedAction, HandResult, TournamentInfo, CashGameInfo,
    PlayerStack, TimebankInfo
)
from app.schemas.common import (
    PaginationParams, ErrorResponse, ExportRequest, DateRangeFilter,
    PlatformFilter, GameTypeFilter, PositionFilter
)
from app.schemas.user import UserCreate, UserUpdate, UserPreferencesUpdate
from app.schemas.analysis import HandAnalysisRequest, SessionAnalysisRequest
from app.schemas.statistics import StatisticsFilters, StatisticsExportRequest


# Hypothesis strategies for generating invalid data
@st.composite
def invalid_string_data(draw):
    """Generate invalid string data."""
    return draw(st.one_of(
        st.none(),  # None when string required
        st.integers(),  # Wrong type
        st.lists(st.text()),  # Wrong type
        st.text(min_size=0, max_size=0),  # Empty string when not allowed
        st.text(min_size=10000),  # Too long string
        st.binary(),  # Binary data
    ))

@st.composite
def invalid_decimal_data(draw):
    """Generate invalid decimal/numeric data."""
    return draw(st.one_of(
        st.text(),  # String when number expected
        st.floats(min_value=-1000, max_value=-0.01),  # Negative when positive required
        st.floats(min_value=float('inf'), max_value=float('inf')),  # Infinity
        st.floats().filter(lambda x: x != x),  # NaN
        st.lists(st.integers()),  # Wrong type
        st.none(),  # None when number required
    ))

@st.composite
def invalid_integer_data(draw):
    """Generate invalid integer data."""
    return draw(st.one_of(
        st.text(),  # String when integer expected
        st.floats(),  # Float when integer expected
        st.integers(max_value=-1),  # Negative when positive required
        st.integers(min_value=1000000),  # Too large
        st.none(),  # None when integer required
        st.lists(st.integers()),  # Wrong type
    ))

@st.composite
def invalid_datetime_data(draw):
    """Generate invalid datetime data."""
    return draw(st.one_of(
        st.text(),  # String when datetime expected
        st.integers(),  # Integer when datetime expected
        st.none(),  # None when datetime required
        st.lists(st.datetimes()),  # Wrong type
    ))

@st.composite
def invalid_boolean_data(draw):
    """Generate invalid boolean data."""
    return draw(st.one_of(
        st.text(),  # String when boolean expected
        st.integers(min_value=2),  # Integer > 1 when boolean expected
        st.floats(),  # Float when boolean expected
        st.none(),  # None when boolean required
        st.lists(st.booleans()),  # Wrong type
    ))

@st.composite
def invalid_list_data(draw):
    """Generate invalid list data."""
    return draw(st.one_of(
        st.text(),  # String when list expected
        st.integers(),  # Integer when list expected
        st.none(),  # None when list required
        st.dictionaries(st.text(), st.text()),  # Dict when list expected
    ))

@st.composite
def invalid_enum_data(draw, valid_values: List[str]):
    """Generate invalid enum data."""
    return draw(st.one_of(
        st.text().filter(lambda x: x not in valid_values),  # Invalid enum value
        st.integers(),  # Wrong type
        st.none(),  # None when enum required
        st.lists(st.sampled_from(valid_values)),  # List when single value expected
    ))

@st.composite
def invalid_email_data(draw):
    """Generate invalid email data."""
    return draw(st.one_of(
        st.text().filter(lambda x: '@' not in x),  # No @ symbol
        st.text(min_size=1, max_size=5),  # Too short
        st.text(alphabet='@'),  # Only @ symbols
        st.integers(),  # Wrong type
        st.none(),  # None when email required
    ))

@st.composite
def invalid_uuid_data(draw):
    """Generate invalid UUID data."""
    return draw(st.one_of(
        st.text().filter(lambda x: len(x) != 36),  # Wrong length
        st.text(alphabet='xyz'),  # Invalid characters
        st.integers(),  # Wrong type
        st.none(),  # None when UUID required
    ))


class TestAPIValidationProperty:
    """Test API request validation using property-based testing."""

    @given(invalid_data=invalid_string_data())
    @settings(max_examples=50, deadline=None)
    def test_hand_create_invalid_hand_id(self, invalid_data):
        """
        Property 7: API Request Validation - Hand ID validation
        
        For any invalid hand_id data, the HandCreate schema should reject
        the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        with pytest.raises(ValidationError) as exc_info:
            HandCreate(
                hand_id=invalid_data,
                platform="pokerstars"
            )
        
        # Verify validation error contains useful information
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Check that error provides field information
        field_errors = [e for e in error.errors() if 'hand_id' in str(e.get('loc', []))]
        assert len(field_errors) > 0, "Should have validation error for hand_id field"
        
        # Verify error message is descriptive
        for field_error in field_errors:
            assert 'msg' in field_error, "Error should contain descriptive message"
            assert field_error['msg'] is not None, "Error message should not be None"

    @given(invalid_platform=invalid_enum_data(['pokerstars', 'ggpoker']))
    @settings(max_examples=50, deadline=None)
    def test_hand_create_invalid_platform(self, invalid_platform):
        """
        Property 7: API Request Validation - Platform enum validation
        
        For any invalid platform data, the HandCreate schema should reject
        the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        with pytest.raises(ValidationError) as exc_info:
            HandCreate(
                hand_id="TEST123",
                platform=invalid_platform
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Check for platform-specific validation error
        platform_errors = [e for e in error.errors() if 'platform' in str(e.get('loc', []))]
        assert len(platform_errors) > 0, "Should have validation error for platform field"

    @given(invalid_amount=invalid_decimal_data())
    @settings(max_examples=50, deadline=None)
    def test_detailed_action_invalid_amount(self, invalid_amount):
        """
        Property 7: API Request Validation - Decimal amount validation
        
        For any invalid amount data, the DetailedAction schema should reject
        the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        with pytest.raises(ValidationError) as exc_info:
            DetailedAction(
                player="TestPlayer",
                action="bet",
                amount=invalid_amount,
                street="flop",
                position="BTN",
                stack_after=Decimal("100.00")
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Check for amount-specific validation error
        amount_errors = [e for e in error.errors() if 'amount' in str(e.get('loc', []))]
        assert len(amount_errors) > 0, "Should have validation error for amount field"

    @given(invalid_action=invalid_enum_data(['fold', 'check', 'call', 'bet', 'raise', 'all-in']))
    @settings(max_examples=50, deadline=None)
    def test_detailed_action_invalid_action_type(self, invalid_action):
        """
        Property 7: API Request Validation - Action enum validation
        
        For any invalid action type, the DetailedAction schema should reject
        the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        with pytest.raises(ValidationError) as exc_info:
            DetailedAction(
                player="TestPlayer",
                action=invalid_action,
                street="flop",
                position="BTN",
                stack_after=Decimal("100.00")
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0

    @given(invalid_email=invalid_email_data())
    @settings(max_examples=50, deadline=None)
    def test_user_create_invalid_email(self, invalid_email):
        """
        Property 7: API Request Validation - Email validation
        
        For any invalid email data, the UserCreate schema should reject
        the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email=invalid_email,
                password="validpassword123"
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Check for email-specific validation error
        email_errors = [e for e in error.errors() if 'email' in str(e.get('loc', []))]
        assert len(email_errors) > 0, "Should have validation error for email field"

    @given(
        skip=invalid_integer_data(),
        limit=invalid_integer_data()
    )
    @settings(max_examples=50, deadline=None)
    def test_pagination_params_invalid_integers(self, skip, limit):
        """
        Property 7: API Request Validation - Pagination parameter validation
        
        For any invalid pagination parameters, the PaginationParams schema
        should reject the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(skip=skip, limit=limit)
        
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Should have errors for invalid integer fields
        field_errors = [e for e in error.errors() if e.get('loc') and (
            'skip' in str(e['loc']) or 'limit' in str(e['loc'])
        )]
        assert len(field_errors) > 0, "Should have validation errors for pagination fields"

    @given(invalid_format=invalid_enum_data(['csv', 'pdf', 'json']))
    @settings(max_examples=50, deadline=None)
    def test_export_request_invalid_format(self, invalid_format):
        """
        Property 7: API Request Validation - Export format validation
        
        For any invalid export format, the ExportRequest schema should reject
        the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        with pytest.raises(ValidationError) as exc_info:
            ExportRequest(format=invalid_format)
        
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Check for format-specific validation error
        format_errors = [e for e in error.errors() if 'format' in str(e.get('loc', []))]
        assert len(format_errors) > 0, "Should have validation error for format field"

    @given(
        start_date=st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31)),
        end_date=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2023, 12, 31))
    )
    @settings(max_examples=50, deadline=None)
    def test_date_range_filter_invalid_range(self, start_date, end_date):
        """
        Property 7: API Request Validation - Date range validation
        
        For any date range where end_date < start_date, the DateRangeFilter
        schema should reject the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        # Ensure end_date is before start_date
        assume(end_date < start_date)
        
        with pytest.raises(ValidationError) as exc_info:
            DateRangeFilter(start_date=start_date, end_date=end_date)
        
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Should have model-level validation error about date range
        error_messages = [e['msg'] for e in error.errors()]
        date_range_error = any('date' in msg.lower() for msg in error_messages)
        assert date_range_error, "Should have validation error about invalid date range"

    @given(invalid_hand_ids=st.one_of(
        st.lists(st.text(), min_size=0, max_size=0),  # Empty list
        st.lists(st.text(), min_size=1001),  # Too many items
        invalid_list_data(),  # Wrong type entirely
    ))
    @settings(max_examples=50, deadline=None)
    def test_batch_delete_invalid_hand_ids(self, invalid_hand_ids):
        """
        Property 7: API Request Validation - Batch operation validation
        
        For any invalid hand_ids list, the HandBatchDeleteRequest schema
        should reject the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        with pytest.raises(ValidationError) as exc_info:
            HandBatchDeleteRequest(
                hand_ids=invalid_hand_ids,
                confirm_deletion=True
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0

    @given(invalid_confirmation=invalid_boolean_data())
    @settings(max_examples=50, deadline=None)
    def test_batch_delete_invalid_confirmation(self, invalid_confirmation):
        """
        Property 7: API Request Validation - Boolean confirmation validation
        
        For any invalid confirmation data, the HandBatchDeleteRequest schema
        should reject the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        with pytest.raises(ValidationError) as exc_info:
            HandBatchDeleteRequest(
                hand_ids=["HAND123"],
                confirm_deletion=invalid_confirmation
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0

    def test_validation_error_structure_consistency(self):
        """
        Property 7: API Request Validation - Error structure consistency
        
        All validation errors should have consistent structure with
        location, message, and type information.
        
        **Validates: Requirements 3.4**
        """
        # Test multiple different validation failures
        test_cases = [
            (lambda: HandCreate(hand_id=None, platform="pokerstars"), "hand_id"),
            (lambda: HandCreate(hand_id="TEST", platform="invalid"), "platform"),
            (lambda: PaginationParams(skip=-1, limit=0), "skip"),
            (lambda: ExportRequest(format="invalid"), "format"),
        ]
        
        for test_func, expected_field in test_cases:
            with pytest.raises(ValidationError) as exc_info:
                test_func()
            
            error = exc_info.value
            assert len(error.errors()) > 0, f"Should have validation errors for {expected_field}"
            
            # Check error structure consistency
            for error_detail in error.errors():
                # Each error should have these required fields
                assert 'loc' in error_detail, "Error should have location information"
                assert 'msg' in error_detail, "Error should have message"
                assert 'type' in error_detail, "Error should have type information"
                
                # Location should be a tuple/list
                assert isinstance(error_detail['loc'], (tuple, list)), "Location should be tuple or list"
                
                # Message should be non-empty string
                assert isinstance(error_detail['msg'], str), "Message should be string"
                assert len(error_detail['msg']) > 0, "Message should not be empty"
                
                # Type should be non-empty string
                assert isinstance(error_detail['type'], str), "Type should be string"
                assert len(error_detail['type']) > 0, "Type should not be empty"

    @given(
        pot_min=st.decimals(min_value=100, max_value=1000),
        pot_max=st.decimals(min_value=1, max_value=99)
    )
    @settings(max_examples=50, deadline=None)
    def test_hand_filters_invalid_pot_range(self, pot_min, pot_max):
        """
        Property 7: API Request Validation - Range validation
        
        For any pot size range where max < min, the HandFilters schema
        should reject the request with proper validation errors.
        
        **Validates: Requirements 3.4**
        """
        # Ensure max is less than min
        assume(pot_max < pot_min)
        
        with pytest.raises(ValidationError) as exc_info:
            HandFilters(
                min_pot_size=pot_min,
                max_pot_size=pot_max
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Should have model-level validation error about pot size range
        error_messages = [e['msg'] for e in error.errors()]
        pot_range_error = any('pot' in msg.lower() for msg in error_messages)
        assert pot_range_error, "Should have validation error about invalid pot size range"

    def test_nested_validation_propagation(self):
        """
        Property 7: API Request Validation - Nested validation
        
        Validation errors in nested objects should be properly propagated
        with clear field paths.
        
        **Validates: Requirements 3.4**
        """
        # Test nested validation with invalid DetailedAction in HandCreate
        with pytest.raises(ValidationError) as exc_info:
            HandCreate(
                hand_id="TEST123",
                platform="pokerstars",
                actions=[
                    DetailedAction(
                        player="TestPlayer",
                        action="invalid_action",  # Invalid enum
                        street="flop",
                        position="BTN",
                        stack_after=Decimal("100.00")
                    )
                ]
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        
        # Check that nested field path is properly reported
        nested_errors = [e for e in error.errors() if len(e.get('loc', [])) > 1]
        assert len(nested_errors) > 0, "Should have nested validation errors"
        
        # Verify nested path includes both parent and child field
        for nested_error in nested_errors:
            loc = nested_error['loc']
            assert 'actions' in str(loc), "Nested error should reference parent field"

    def test_validation_error_serialization(self):
        """
        Property 7: API Request Validation - Error serialization
        
        Validation errors should be serializable to JSON for API responses.
        
        **Validates: Requirements 3.4**
        """
        try:
            HandCreate(hand_id=None, platform="invalid")
        except ValidationError as e:
            # Should be able to serialize error to JSON
            error_dict = e.errors()
            json_str = json.dumps(error_dict, default=str)
            
            # Should be able to deserialize back
            deserialized = json.loads(json_str)
            assert isinstance(deserialized, list), "Errors should deserialize to list"
            assert len(deserialized) > 0, "Should have error entries"
            
            # Each error should have required fields after serialization
            for error_item in deserialized:
                assert 'loc' in error_item, "Serialized error should have location"
                assert 'msg' in error_item, "Serialized error should have message"
                assert 'type' in error_item, "Serialized error should have type"


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])