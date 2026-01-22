"""
Pydantic schemas for session management.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class SessionCreate(BaseModel):
    """Schema for creating a new session."""
    timezone: str = Field(..., description="User's timezone (e.g., 'America/New_York')")
    device_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Device information")
    ip_address: Optional[str] = Field(None, description="Client IP address")


class SessionUpdate(BaseModel):
    """Schema for updating session activity."""
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")


class SessionEnd(BaseModel):
    """Schema for ending a session."""
    logout_reason: str = Field(default="logout", description="Reason for ending session")


class SessionResponse(BaseModel):
    """Schema for session response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    start_time: datetime = Field(..., description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    last_activity: datetime = Field(..., description="Last activity time")
    timezone: str = Field(..., description="User's timezone")
    timezone_offset: int = Field(..., description="Timezone offset in minutes from UTC")
    device_info: Dict[str, Any] = Field(default_factory=dict, description="Device information")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    is_active: bool = Field(..., description="Whether session is active")
    session_token: Optional[str] = Field(None, description="Session token")
    logout_reason: Optional[str] = Field(None, description="Logout reason")
    created_at: datetime = Field(..., description="Session creation time")
    updated_at: datetime = Field(..., description="Session last update time")
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate session duration in minutes."""
        if not self.end_time:
            # Session is still active, calculate from current time
            duration = datetime.utcnow() - self.start_time
        else:
            duration = self.end_time - self.start_time
        
        return int(duration.total_seconds() / 60)


class SessionListResponse(BaseModel):
    """Schema for session list response."""
    sessions: List[SessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    active_count: int = Field(..., description="Number of active sessions")


class SessionStatistics(BaseModel):
    """Schema for session statistics."""
    total_sessions: int = Field(..., description="Total number of sessions")
    active_sessions: int = Field(..., description="Number of active sessions")
    total_duration_minutes: int = Field(..., description="Total duration in minutes")
    average_duration_minutes: int = Field(..., description="Average duration in minutes")
    unique_devices: int = Field(..., description="Number of unique devices")
    unique_timezones: int = Field(..., description="Number of unique timezones")
    most_common_timezone: Optional[str] = Field(None, description="Most commonly used timezone")


class DateBoundaries(BaseModel):
    """Schema for date boundaries in user's timezone."""
    start_of_day_utc: datetime = Field(..., description="Start of day in UTC")
    end_of_day_utc: datetime = Field(..., description="End of day in UTC")
    timezone: str = Field(..., description="User's timezone")
    date: str = Field(..., description="Date in YYYY-MM-DD format")


class TimezoneInfo(BaseModel):
    """Schema for timezone information."""
    timezone: str = Field(..., description="Timezone name")
    offset_minutes: int = Field(..., description="Offset from UTC in minutes")
    display_name: str = Field(..., description="Human-readable timezone name")
    is_dst: bool = Field(..., description="Whether daylight saving time is active")


class SessionCleanupResult(BaseModel):
    """Schema for session cleanup results."""
    cleaned_sessions: int = Field(..., description="Number of sessions cleaned up")
    total_active_before: int = Field(..., description="Total active sessions before cleanup")
    total_active_after: int = Field(..., description="Total active sessions after cleanup")
    cleanup_timestamp: datetime = Field(..., description="When cleanup was performed")