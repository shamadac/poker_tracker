"""
Session management API endpoints.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.session_service import SessionService
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionListResponse,
    SessionStatistics,
    DateBoundaries,
    SessionCleanupResult,
    SessionEnd
)

router = APIRouter()


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user session with timezone awareness.
    """
    # Extract device info from request
    device_info = {
        "user_agent": request.headers.get("user-agent", ""),
        "accept_language": request.headers.get("accept-language", ""),
        "platform": session_data.device_info.get("platform", "unknown"),
        "browser": session_data.device_info.get("browser", "unknown"),
        "screen_resolution": session_data.device_info.get("screen_resolution", "unknown")
    }
    
    # Get client IP
    ip_address = session_data.ip_address or request.client.host if request.client else None
    
    session = await SessionService.create_session(
        db=db,
        user_id=str(current_user.id),
        timezone=session_data.timezone,
        device_info=device_info,
        ip_address=ip_address
    )
    
    return SessionResponse.model_validate(session)


@router.get("/current", response_model=Optional[SessionResponse])
async def get_current_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current active session for the authenticated user.
    """
    session = await SessionService.get_active_session(db, str(current_user.id))
    
    if not session:
        return None
    
    return SessionResponse.model_validate(session)


@router.put("/{session_id}/activity", response_model=SessionResponse)
async def update_session_activity(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update session activity timestamp.
    """
    session = await SessionService.update_session_activity(db, session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or inactive"
        )
    
    # Verify session belongs to current user
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/end", response_model=dict)
async def end_session(
    session_id: str,
    session_end: SessionEnd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    End a specific session.
    """
    # First verify the session belongs to the current user
    session = await SessionService.get_active_session(db, str(current_user.id))
    if not session or session.id != session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    success = await SessionService.end_session(
        db, session_id, session_end.logout_reason
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already ended"
        )
    
    return {"message": "Session ended successfully"}


@router.post("/end-all", response_model=dict)
async def end_all_sessions(
    session_end: SessionEnd,
    exclude_current: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    End all active sessions for the current user.
    """
    current_session = None
    if exclude_current:
        current_session = await SessionService.get_active_session(db, str(current_user.id))
    
    ended_count = await SessionService.end_user_sessions(
        db=db,
        user_id=str(current_user.id),
        logout_reason=session_end.logout_reason,
        exclude_session_id=current_session.id if current_session else None
    )
    
    return {
        "message": f"Ended {ended_count} sessions",
        "ended_count": ended_count
    }


@router.get("/", response_model=SessionListResponse)
async def get_user_sessions(
    active_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sessions for the current user.
    """
    sessions = await SessionService.get_user_sessions(
        db=db,
        user_id=str(current_user.id),
        active_only=active_only,
        limit=limit
    )
    
    session_responses = [SessionResponse.model_validate(s) for s in sessions]
    active_count = sum(1 for s in session_responses if s.is_active)
    
    return SessionListResponse(
        sessions=session_responses,
        total=len(session_responses),
        active_count=active_count
    )


@router.get("/statistics", response_model=SessionStatistics)
async def get_session_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get session statistics for the current user.
    """
    stats = await SessionService.get_session_statistics(
        db=db,
        user_id=str(current_user.id),
        days=days
    )
    
    return SessionStatistics(**stats)


@router.get("/date-boundaries", response_model=DateBoundaries)
async def get_date_boundaries(
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get date boundaries for the current user based on their timezone.
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
    """
    target_date = None
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    start_utc, end_utc = await SessionService.calculate_date_boundaries(
        db=db,
        user_id=str(current_user.id),
        date=target_date
    )
    
    # Get user's timezone from active session
    session = await SessionService.get_active_session(db, str(current_user.id))
    timezone = session.timezone if session else "UTC"
    
    return DateBoundaries(
        start_of_day_utc=start_utc,
        end_of_day_utc=end_utc,
        timezone=timezone,
        date=(target_date or datetime.utcnow()).strftime("%Y-%m-%d")
    )


@router.post("/cleanup", response_model=SessionCleanupResult)
async def cleanup_expired_sessions(
    timeout_minutes: int = 1440,  # 24 hours
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clean up expired sessions (admin only for now, but could be extended).
    """
    # For now, only allow users to clean up their own expired sessions
    # In the future, this could be restricted to admin users for global cleanup
    
    # Get count before cleanup
    sessions_before = await SessionService.get_user_sessions(
        db=db,
        user_id=str(current_user.id),
        active_only=True
    )
    total_active_before = len(sessions_before)
    
    # Cleanup expired sessions for this user only
    # Note: This is a simplified version - in production you might want global cleanup
    cleaned_count = 0
    for session in sessions_before:
        if session.is_expired(timeout_minutes):
            await SessionService.end_session(
                db, session.id, "timeout"
            )
            cleaned_count += 1
    
    # Get count after cleanup
    sessions_after = await SessionService.get_user_sessions(
        db=db,
        user_id=str(current_user.id),
        active_only=True
    )
    total_active_after = len(sessions_after)
    
    return SessionCleanupResult(
        cleaned_sessions=cleaned_count,
        total_active_before=total_active_before,
        total_active_after=total_active_after,
        cleanup_timestamp=datetime.utcnow()
    )