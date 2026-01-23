"""
Property-based test for session tracking accuracy.

**Feature: poker-app-fixes-and-cleanup, Property 13: Session Tracking Accuracy**
**Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5**

Property 13: Session Tracking Accuracy
*For any* user login session, the system should create session records with proper timezone 
information, use session data for accurate date boundary calculations, record session end times 
properly, handle concurrent multi-device sessions consistently, and provide accurate time-based 
filtering for reports.
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, delete
from sqlalchemy.exc import SQLAlchemyError
import pytz
import secrets

from app.models.user import User
from app.models.session import UserSession
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate, SessionResponse


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine and session
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# Create a minimal metadata that only includes the tables we need
test_metadata = MetaData()
User.__table__.to_metadata(test_metadata)
UserSession.__table__.to_metadata(test_metadata)


# Hypothesis strategies for generating test data
def valid_timezones():
    """Generate valid timezone strings."""
    common_timezones = [
        'UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London',
        'Europe/Paris', 'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney',
        'America/Chicago', 'America/Denver', 'Europe/Berlin', 'Asia/Kolkata'
    ]
    return st.sampled_from(common_timezones)


def device_info_data():
    """Generate device information dictionaries."""
    return st.fixed_dictionaries({
        'platform': st.sampled_from(['Windows', 'macOS', 'Linux', 'iOS', 'Android']),
        'browser': st.sampled_from(['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']),
        'user_agent': st.text(min_size=10, max_size=200),
        'screen_resolution': st.sampled_from(['1920x1080', '1366x768', '1440x900', '2560x1440'])
    })


def ip_addresses():
    """Generate valid IP addresses."""
    return st.one_of(
        st.ip_addresses(v=4).map(str),
        st.ip_addresses(v=6).map(str)
    )


def session_create_data():
    """Generate SessionCreate data."""
    return st.builds(
        SessionCreate,
        timezone=valid_timezones(),
        device_info=device_info_data(),
        ip_address=st.one_of(st.none(), ip_addresses())
    )


def logout_reasons():
    """Generate logout reasons."""
    return st.sampled_from(['logout', 'timeout', 'expired', 'logout_all', 'admin_logout'])


class TestSessionTrackingAccuracy:
    """Property-based tests for session tracking accuracy."""
    
    @given(session_create_data())
    @settings(max_examples=50, deadline=5000)
    def test_property_session_creation_with_timezone_info(self, session_data):
        """
        Property: Session creation should always include proper timezone information.
        
        **Validates: Requirement 13.1**
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                import uuid
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"test-{user_id}@example.com",
                    password_hash="hashed_password",
                    is_active=True,
                    is_superuser=False
                )
                session.add(user)
                await session.commit()
                
                # Create session using the service
                created_session = await SessionService.create_session(
                    db=session,
                    user_id=user_id,
                    timezone=session_data.timezone,
                    device_info=session_data.device_info,
                    ip_address=session_data.ip_address
                )
                
                # Verify session was created with proper timezone information
                assert created_session is not None
                assert created_session.user_id == user_id
                assert created_session.timezone == session_data.timezone
                assert created_session.timezone_offset is not None
                assert isinstance(created_session.timezone_offset, int)
                assert created_session.start_time is not None
                assert created_session.last_activity is not None
                assert created_session.is_active is True
                assert created_session.session_token is not None
                assert len(created_session.session_token) > 0
                
                # Verify timezone offset is reasonable (-12 to +14 hours)
                assert -12*60 <= created_session.timezone_offset <= 14*60
                
                # Verify device info is preserved
                if session_data.device_info:
                    for key, value in session_data.device_info.items():
                        assert created_session.device_info.get(key) == value
                
                # Verify IP address is preserved
                assert created_session.ip_address == session_data.ip_address
        
        asyncio.run(run_test())
    
    @given(valid_timezones(), st.dates(min_value=datetime(2020, 1, 1).date(), max_value=datetime(2030, 12, 31).date()))
    @settings(max_examples=30, deadline=5000)
    def test_property_date_boundary_calculations(self, timezone_str, test_date):
        """
        Property: Date boundary calculations should be accurate for any timezone and date.
        
        **Validates: Requirement 13.2**
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                import uuid
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"test-{user_id}@example.com",
                    password_hash="hashed_password",
                    is_active=True,
                    is_superuser=False
                )
                session.add(user)
                await session.commit()
                
                # Create a session with the specified timezone
                created_session = await SessionService.create_session(
                    db=session,
                    user_id=user_id,
                    timezone=timezone_str,
                    device_info={'platform': 'test'},
                    ip_address='127.0.0.1'
                )
                
                # Calculate date boundaries
                test_datetime = datetime.combine(test_date, datetime.min.time())
                start_utc, end_utc = await SessionService.calculate_date_boundaries(
                    db=session,
                    user_id=user_id,
                    date=test_datetime
                )
                
                # Verify boundaries are valid
                assert start_utc is not None
                assert end_utc is not None
                assert isinstance(start_utc, datetime)
                assert isinstance(end_utc, datetime)
                assert start_utc < end_utc
                
                # Verify the boundaries span exactly 24 hours
                duration = end_utc - start_utc
                # Allow for small differences due to DST transitions
                assert 23*3600 <= duration.total_seconds() <= 25*3600
                
                # Verify boundaries are in UTC (no timezone info)
                assert start_utc.tzinfo is None
                assert end_utc.tzinfo is None
                
                # Verify the date boundaries make sense for the timezone
                user_tz = pytz.timezone(timezone_str)
                start_local = pytz.UTC.localize(start_utc).astimezone(user_tz)
                end_local = pytz.UTC.localize(end_utc).astimezone(user_tz)
                
                # Start should be at or near midnight
                assert start_local.hour == 0
                assert start_local.minute == 0
                assert start_local.second == 0
                
                # End should be at or near end of day
                assert end_local.hour == 23
                assert end_local.minute == 59
                assert end_local.second == 59
        
        asyncio.run(run_test())
    
    @given(logout_reasons())
    @settings(max_examples=20, deadline=5000)
    def test_property_session_end_recording(self, logout_reason):
        """
        Property: Session end should be properly recorded with timestamps and reasons.
        
        **Validates: Requirement 13.3**
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                import uuid
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"test-{user_id}@example.com",
                    password_hash="hashed_password",
                    is_active=True,
                    is_superuser=False
                )
                session.add(user)
                await session.commit()
                
                # Create a session
                created_session = await SessionService.create_session(
                    db=session,
                    user_id=user_id,
                    timezone='UTC',
                    device_info={'platform': 'test'},
                    ip_address='127.0.0.1'
                )
                
                original_start_time = created_session.start_time
                
                # Wait a small amount to ensure end_time > start_time
                await asyncio.sleep(0.01)
                
                # End the session
                success = await SessionService.end_session(
                    db=session,
                    session_id=created_session.id,
                    logout_reason=logout_reason
                )
                
                # Verify session was ended successfully
                assert success is True
                
                # Refresh session to get updated data
                await session.refresh(created_session)
                
                # Verify session end was recorded properly
                assert created_session.is_active is False
                assert created_session.end_time is not None
                assert created_session.logout_reason == logout_reason
                
                # Verify end_time is after start_time
                assert created_session.end_time > original_start_time
                
                # Verify end_time is reasonable (not too far in the future)
                now = datetime.utcnow()
                assert created_session.end_time <= now + timedelta(seconds=1)  # Allow small clock differences
        
        asyncio.run(run_test())
    
    @given(st.integers(min_value=2, max_value=5), valid_timezones())
    @settings(max_examples=15, deadline=8000)
    def test_property_concurrent_multi_device_sessions(self, num_devices, timezone_str):
        """
        Property: Multiple concurrent sessions should be tracked consistently.
        
        **Validates: Requirement 13.4**
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                import uuid
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"test-{user_id}@example.com",
                    password_hash="hashed_password",
                    is_active=True,
                    is_superuser=False
                )
                session.add(user)
                await session.commit()
                
                sessions = []
                
                # Create multiple concurrent sessions for the same user
                for i in range(num_devices):
                    device_info = {
                        'platform': f'Device_{i}',
                        'browser': f'Browser_{i}',
                        'device_id': f'device_{i}'
                    }
                    
                    created_session = await SessionService.create_session(
                        db=session,
                        user_id=user_id,
                        timezone=timezone_str,
                        device_info=device_info,
                        ip_address=f'192.168.1.{i+1}'
                    )
                    sessions.append(created_session)
                
                # Verify all sessions were created
                assert len(sessions) == num_devices
                
                # Verify all sessions are active and belong to the same user
                for created_session in sessions:
                    assert created_session.is_active is True
                    assert created_session.user_id == user_id
                    assert created_session.timezone == timezone_str
                
                # Verify sessions have unique tokens
                tokens = [s.session_token for s in sessions]
                assert len(set(tokens)) == len(tokens)  # All tokens should be unique
                
                # Verify sessions have different device info
                device_platforms = [s.device_info.get('platform') for s in sessions]
                assert len(set(device_platforms)) == len(device_platforms)  # All platforms should be unique
                
                # Get user sessions and verify count
                user_sessions = await SessionService.get_user_sessions(
                    db=session,
                    user_id=user_id,
                    active_only=True
                )
                assert len(user_sessions) == num_devices
                
                # Test timezone consistency across all sessions
                for created_session in sessions:
                    start_utc, end_utc = created_session.get_date_boundaries(datetime.utcnow())
                    assert start_utc is not None
                    assert end_utc is not None
                    assert start_utc < end_utc
                
                # End some sessions and verify counts
                sessions_to_end = sessions[:num_devices//2]
                for created_session in sessions_to_end:
                    success = await SessionService.end_session(
                        db=session,
                        session_id=created_session.id,
                        logout_reason='test_logout'
                    )
                    assert success is True
                
                # Verify active session count decreased
                remaining_active = await SessionService.get_user_sessions(
                    db=session,
                    user_id=user_id,
                    active_only=True
                )
                expected_active = num_devices - len(sessions_to_end)
                assert len(remaining_active) == expected_active
        
        asyncio.run(run_test())
    
    @given(st.integers(min_value=1, max_value=30), valid_timezones())
    @settings(max_examples=20, deadline=6000)
    def test_property_time_based_filtering_accuracy(self, days_back, timezone_str):
        """
        Property: Time-based filtering should provide accurate results for any time range.
        
        **Validates: Requirement 13.5**
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                import uuid
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"test-{user_id}@example.com",
                    password_hash="hashed_password",
                    is_active=True,
                    is_superuser=False
                )
                session.add(user)
                await session.commit()
                
                # Create a session for the user
                created_session = await SessionService.create_session(
                    db=session,
                    user_id=user_id,
                    timezone=timezone_str,
                    device_info={'platform': 'test'},
                    ip_address='127.0.0.1'
                )
                
                # Get session statistics for the specified period
                stats = await SessionService.get_session_statistics(
                    db=session,
                    user_id=user_id,
                    days=days_back
                )
                
                # Verify statistics structure
                assert isinstance(stats, dict)
                required_keys = [
                    'total_sessions', 'active_sessions', 'total_duration_minutes',
                    'average_duration_minutes', 'unique_devices', 'unique_timezones',
                    'most_common_timezone'
                ]
                for key in required_keys:
                    assert key in stats
                
                # Verify statistics values are reasonable
                assert stats['total_sessions'] >= 1  # At least the session we created
                assert stats['active_sessions'] >= 1  # At least the session we created
                assert stats['total_duration_minutes'] >= 0
                assert stats['average_duration_minutes'] >= 0
                assert stats['unique_devices'] >= 1
                assert stats['unique_timezones'] >= 1
                assert stats['most_common_timezone'] == timezone_str
                
                # Verify numeric consistency
                if stats['total_sessions'] > 0:
                    assert stats['average_duration_minutes'] == stats['total_duration_minutes'] // stats['total_sessions']
                
                # Verify active sessions don't exceed total sessions
                assert stats['active_sessions'] <= stats['total_sessions']
                
                # Test date boundary calculations for filtering
                now = datetime.utcnow()
                start_utc, end_utc = await SessionService.calculate_date_boundaries(
                    db=session,
                    user_id=user_id,
                    date=now
                )
                
                # Verify the session falls within today's boundaries
                assert start_utc <= created_session.start_time <= end_utc
                
                # Test cleanup of expired sessions
                timeout_minutes = 1  # Very short timeout for testing
                cleaned_count = await SessionService.cleanup_expired_sessions(
                    db=session,
                    timeout_minutes=timeout_minutes
                )
                
                # Since we just created the session, it shouldn't be cleaned up yet
                assert cleaned_count == 0
                
                # Verify session is still active
                active_session = await SessionService.get_active_session(
                    db=session,
                    user_id=user_id
                )
                assert active_session is not None
                assert active_session.id == created_session.id
        
        asyncio.run(run_test())
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=10, deadline=8000)
    def test_property_session_activity_updates(self, num_updates):
        """
        Property: Session activity updates should maintain accurate timestamps.
        
        **Validates: Requirements 13.1, 13.3**
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                import uuid
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"test-{user_id}@example.com",
                    password_hash="hashed_password",
                    is_active=True,
                    is_superuser=False
                )
                session.add(user)
                await session.commit()
                
                # Create a session
                created_session = await SessionService.create_session(
                    db=session,
                    user_id=user_id,
                    timezone='UTC',
                    device_info={'platform': 'test'},
                    ip_address='127.0.0.1'
                )
                
                original_activity = created_session.last_activity
                
                # Perform multiple activity updates
                for i in range(num_updates):
                    await asyncio.sleep(0.01)  # Small delay to ensure timestamp changes
                    
                    updated_session = await SessionService.update_session_activity(
                        db=session,
                        session_id=created_session.id
                    )
                    
                    # Verify update was successful
                    assert updated_session is not None
                    assert updated_session.id == created_session.id
                    assert updated_session.is_active is True
                    
                    # Verify last_activity was updated
                    assert updated_session.last_activity > original_activity
                    original_activity = updated_session.last_activity
                
                # Verify final state
                final_session = await SessionService.get_active_session(
                    db=session,
                    user_id=user_id
                )
                assert final_session is not None
                assert final_session.last_activity == original_activity
        
        asyncio.run(run_test())
    
    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=10, deadline=6000)
    def test_property_session_expiration_detection(self, timeout_minutes):
        """
        Property: Session expiration should be detected accurately based on timeout.
        
        **Validates: Requirement 13.3**
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                import uuid
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"test-{user_id}@example.com",
                    password_hash="hashed_password",
                    is_active=True,
                    is_superuser=False
                )
                session.add(user)
                await session.commit()
                
                # Create a session
                created_session = await SessionService.create_session(
                    db=session,
                    user_id=user_id,
                    timezone='UTC',
                    device_info={'platform': 'test'},
                    ip_address='127.0.0.1'
                )
                
                # Test that session is not expired initially
                assert not created_session.is_expired(timeout_minutes)
                
                # Manually set last_activity to simulate an old session
                old_time = datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
                created_session.last_activity = old_time
                await session.commit()
                
                # Test that session is now expired
                await session.refresh(created_session)
                assert created_session.is_expired(timeout_minutes)
                
                # Test cleanup of expired sessions
                cleaned_count = await SessionService.cleanup_expired_sessions(
                    db=session,
                    timeout_minutes=timeout_minutes
                )
                
                # Should have cleaned up our expired session
                assert cleaned_count >= 1
                
                # Verify session is no longer active
                await session.refresh(created_session)
                assert created_session.is_active is False
                assert created_session.logout_reason == 'timeout'
        
        asyncio.run(run_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
