"""
Session management service with timezone awareness.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.exc import SQLAlchemyError
import pytz
import logging

from app.models.session import UserSession
from app.models.user import User

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing user sessions with timezone awareness."""
    
    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: str,
        timezone: str,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        """
        Create a new user session with timezone detection.
        
        Args:
            db: Database session
            user_id: User ID
            timezone: User's timezone (e.g., 'America/New_York')
            device_info: Device information dictionary
            ip_address: Client IP address
            
        Returns:
            UserSession: Created session
        """
        try:
            # Calculate timezone offset
            timezone_offset = SessionService._get_timezone_offset(timezone)
            
            # Generate unique session token
            session_token = secrets.token_urlsafe(32)
            
            # Create session
            session = UserSession(
                user_id=user_id,
                start_time=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                timezone=timezone,
                timezone_offset=timezone_offset,
                device_info=device_info or {},
                ip_address=ip_address,
                is_active=True,
                session_token=session_token
            )
            
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            logger.info(f"Created session {session.id} for user {user_id} in timezone {timezone}")
            return session
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise
    
    @staticmethod
    async def get_active_session(
        db: AsyncSession,
        user_id: str,
        session_token: Optional[str] = None
    ) -> Optional[UserSession]:
        """
        Get the active session for a user.
        
        Args:
            db: Database session
            user_id: User ID
            session_token: Optional session token for specific session lookup
            
        Returns:
            UserSession or None: Active session if found
        """
        try:
            query = select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
            
            if session_token:
                query = query.where(UserSession.session_token == session_token)
            else:
                # Get the most recent active session
                query = query.order_by(desc(UserSession.last_activity))
            
            result = await db.execute(query)
            return result.scalars().first()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get active session for user {user_id}: {e}")
            return None
    
    @staticmethod
    async def update_session_activity(
        db: AsyncSession,
        session_id: str
    ) -> Optional[UserSession]:
        """
        Update session activity timestamp.
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            UserSession or None: Updated session if found
        """
        try:
            query = select(UserSession).where(UserSession.id == session_id)
            result = await db.execute(query)
            session = result.scalars().first()
            
            if session and session.is_active:
                session.last_activity = datetime.utcnow()
                await db.commit()
                await db.refresh(session)
                return session
            
            return None
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to update session activity for session {session_id}: {e}")
            return None
    
    @staticmethod
    async def end_session(
        db: AsyncSession,
        session_id: str,
        logout_reason: str = "logout"
    ) -> bool:
        """
        End a user session.
        
        Args:
            db: Database session
            session_id: Session ID
            logout_reason: Reason for ending session
            
        Returns:
            bool: True if session was ended successfully
        """
        try:
            query = select(UserSession).where(UserSession.id == session_id)
            result = await db.execute(query)
            session = result.scalars().first()
            
            if session and session.is_active:
                session.is_active = False
                session.end_time = datetime.utcnow()
                session.logout_reason = logout_reason
                
                await db.commit()
                logger.info(f"Ended session {session_id} with reason: {logout_reason}")
                return True
            
            return False
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to end session {session_id}: {e}")
            return False
    
    @staticmethod
    async def end_user_sessions(
        db: AsyncSession,
        user_id: str,
        logout_reason: str = "logout_all",
        exclude_session_id: Optional[str] = None
    ) -> int:
        """
        End all active sessions for a user.
        
        Args:
            db: Database session
            user_id: User ID
            logout_reason: Reason for ending sessions
            exclude_session_id: Optional session ID to exclude from ending
            
        Returns:
            int: Number of sessions ended
        """
        try:
            query = select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
            
            if exclude_session_id:
                query = query.where(UserSession.id != exclude_session_id)
            
            result = await db.execute(query)
            sessions = result.scalars().all()
            
            ended_count = 0
            for session in sessions:
                session.is_active = False
                session.end_time = datetime.utcnow()
                session.logout_reason = logout_reason
                ended_count += 1
            
            await db.commit()
            logger.info(f"Ended {ended_count} sessions for user {user_id}")
            return ended_count
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to end sessions for user {user_id}: {e}")
            return 0
    
    @staticmethod
    async def cleanup_expired_sessions(
        db: AsyncSession,
        timeout_minutes: int = 1440  # 24 hours
    ) -> int:
        """
        Clean up expired sessions.
        
        Args:
            db: Database session
            timeout_minutes: Session timeout in minutes
            
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            
            query = select(UserSession).where(
                and_(
                    UserSession.is_active == True,
                    UserSession.last_activity < cutoff_time
                )
            )
            
            result = await db.execute(query)
            expired_sessions = result.scalars().all()
            
            cleaned_count = 0
            for session in expired_sessions:
                session.is_active = False
                session.end_time = datetime.utcnow()
                session.logout_reason = "timeout"
                cleaned_count += 1
            
            await db.commit()
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    @staticmethod
    async def get_user_sessions(
        db: AsyncSession,
        user_id: str,
        active_only: bool = False,
        limit: int = 50
    ) -> List[UserSession]:
        """
        Get user sessions.
        
        Args:
            db: Database session
            user_id: User ID
            active_only: Whether to return only active sessions
            limit: Maximum number of sessions to return
            
        Returns:
            List[UserSession]: User sessions
        """
        try:
            query = select(UserSession).where(UserSession.user_id == user_id)
            
            if active_only:
                query = query.where(UserSession.is_active == True)
            
            query = query.order_by(desc(UserSession.start_time)).limit(limit)
            
            result = await db.execute(query)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def calculate_date_boundaries(
        db: AsyncSession,
        user_id: str,
        date: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
        """
        Calculate date boundaries for a user based on their timezone.
        
        Args:
            db: Database session
            user_id: User ID
            date: Date to calculate boundaries for (defaults to today)
            
        Returns:
            Tuple[datetime, datetime]: Start and end of day in UTC
        """
        try:
            # Get user's active session for timezone info
            session = await SessionService.get_active_session(db, user_id)
            
            if not session:
                # Fallback to UTC if no active session
                target_date = (date or datetime.utcnow()).date()
                start_of_day = datetime.combine(target_date, datetime.min.time())
                end_of_day = datetime.combine(target_date, datetime.max.time())
                return start_of_day, end_of_day
            
            # Use session's timezone for accurate boundaries
            target_date = date or datetime.utcnow()
            return session.get_date_boundaries(target_date)
            
        except Exception as e:
            logger.error(f"Failed to calculate date boundaries for user {user_id}: {e}")
            # Fallback to UTC
            target_date = (date or datetime.utcnow()).date()
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            return start_of_day, end_of_day
    
    @staticmethod
    async def get_session_statistics(
        db: AsyncSession,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get session statistics for a user.
        
        Args:
            db: Database session
            user_id: User ID
            days: Number of days to include in statistics
            
        Returns:
            Dict[str, Any]: Session statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get sessions in the specified period
            query = select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.start_time >= cutoff_date
                )
            ).order_by(UserSession.start_time)
            
            result = await db.execute(query)
            sessions = list(result.scalars().all())
            
            if not sessions:
                return {
                    "total_sessions": 0,
                    "active_sessions": 0,
                    "total_duration_minutes": 0,
                    "average_duration_minutes": 0,
                    "unique_devices": 0,
                    "unique_timezones": 0,
                    "most_common_timezone": None
                }
            
            # Calculate statistics
            active_sessions = sum(1 for s in sessions if s.is_active)
            total_duration = sum(s.duration_minutes or 0 for s in sessions)
            unique_devices = len(set(
                s.device_info.get('user_agent', 'unknown') for s in sessions
            ))
            unique_timezones = len(set(s.timezone for s in sessions))
            
            # Find most common timezone
            timezone_counts = {}
            for session in sessions:
                timezone_counts[session.timezone] = timezone_counts.get(session.timezone, 0) + 1
            
            most_common_timezone = max(timezone_counts.items(), key=lambda x: x[1])[0] if timezone_counts else None
            
            return {
                "total_sessions": len(sessions),
                "active_sessions": active_sessions,
                "total_duration_minutes": total_duration,
                "average_duration_minutes": total_duration // len(sessions) if sessions else 0,
                "unique_devices": unique_devices,
                "unique_timezones": unique_timezones,
                "most_common_timezone": most_common_timezone
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get session statistics for user {user_id}: {e}")
            return {}
    
    @staticmethod
    def _get_timezone_offset(timezone: str) -> int:
        """
        Get timezone offset in minutes from UTC.
        
        Args:
            timezone: Timezone string (e.g., 'America/New_York')
            
        Returns:
            int: Offset in minutes from UTC
        """
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            offset = now.utcoffset()
            return int(offset.total_seconds() / 60) if offset else 0
        except Exception:
            return 0  # Default to UTC if timezone is invalid
    
    @staticmethod
    def detect_timezone_from_request(request_headers: Dict[str, str]) -> str:
        """
        Detect timezone from request headers or other client information.
        
        Args:
            request_headers: HTTP request headers
            
        Returns:
            str: Detected timezone or UTC as fallback
        """
        # This is a simplified implementation
        # In a real application, you might use JavaScript to detect timezone
        # and send it in a custom header
        
        timezone_header = request_headers.get('X-Timezone')
        if timezone_header:
            try:
                # Validate timezone
                pytz.timezone(timezone_header)
                return timezone_header
            except Exception:
                pass
        
        # Fallback to UTC
        return 'UTC'