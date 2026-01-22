"""
Session model for user session tracking with timezone awareness.
"""
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import String, Text, Boolean, JSON, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class UserSession(Base, UUIDMixin, TimestampMixin):
    """User session model for tracking login sessions with timezone awareness."""
    
    __tablename__ = "user_sessions"
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Session timing information
    start_time: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
        comment="Session start timestamp in UTC"
    )
    
    end_time: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Session end timestamp in UTC (null if active)"
    )
    
    last_activity: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
        comment="Last activity timestamp in UTC"
    )
    
    # Timezone information
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="User's timezone (e.g., 'America/New_York')"
    )
    
    timezone_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Timezone offset in minutes from UTC"
    )
    
    # Device and connection information
    device_info: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Device information (user agent, platform, etc.)"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 compatible
        nullable=True,
        comment="Client IP address"
    )
    
    # Session status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the session is currently active"
    )
    
    # Session metadata
    session_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Unique session token for tracking"
    )
    
    logout_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Reason for session end (logout, timeout, expired, etc.)"
    )
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, timezone={self.timezone}, active={self.is_active})>"
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate session duration in minutes."""
        if not self.end_time:
            # Session is still active, calculate from current time
            current_time = datetime.utcnow()
            # Ensure both times are timezone-naive for comparison
            start_time = self.start_time.replace(tzinfo=None) if self.start_time.tzinfo else self.start_time
            duration = current_time - start_time
        else:
            # Both times should be from database, ensure they're timezone-naive
            start_time = self.start_time.replace(tzinfo=None) if self.start_time.tzinfo else self.start_time
            end_time = self.end_time.replace(tzinfo=None) if self.end_time.tzinfo else self.end_time
            duration = end_time - start_time
        
        return int(duration.total_seconds() / 60)
    
    def is_expired(self, timeout_minutes: int = 1440) -> bool:  # 24 hours default
        """Check if session is expired based on last activity."""
        if not self.is_active:
            return True
        
        current_time = datetime.utcnow()
        # Ensure both times are timezone-naive for comparison
        last_activity = self.last_activity.replace(tzinfo=None) if self.last_activity.tzinfo else self.last_activity
        time_since_activity = current_time - last_activity
        return time_since_activity.total_seconds() > (timeout_minutes * 60)
    
    def get_local_time(self, utc_time: datetime) -> datetime:
        """Convert UTC time to user's local timezone."""
        import pytz
        
        try:
            user_tz = pytz.timezone(self.timezone)
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
            return utc_time.astimezone(user_tz)
        except Exception:
            # Fallback to UTC if timezone conversion fails
            return utc_time
    
    def get_date_boundaries(self, date: datetime) -> tuple[datetime, datetime]:
        """
        Get the start and end of a day in the user's timezone.
        
        Args:
            date: Date to get boundaries for (in any timezone)
            
        Returns:
            Tuple of (start_of_day_utc, end_of_day_utc)
        """
        import pytz
        
        try:
            user_tz = pytz.timezone(self.timezone)
            
            # Convert to user's timezone and get date
            if date.tzinfo is None:
                date = pytz.UTC.localize(date)
            
            local_date = date.astimezone(user_tz).date()
            
            # Create start and end of day in user's timezone
            start_of_day = user_tz.localize(
                datetime.combine(local_date, datetime.min.time())
            )
            end_of_day = user_tz.localize(
                datetime.combine(local_date, datetime.max.time())
            )
            
            # Convert back to UTC
            start_of_day_utc = start_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
            end_of_day_utc = end_of_day.astimezone(pytz.UTC).replace(tzinfo=None)
            
            return start_of_day_utc, end_of_day_utc
            
        except Exception:
            # Fallback to UTC boundaries if timezone conversion fails
            utc_date = date.date() if hasattr(date, 'date') else date
            start_of_day = datetime.combine(utc_date, datetime.min.time())
            end_of_day = datetime.combine(utc_date, datetime.max.time())
            return start_of_day, end_of_day