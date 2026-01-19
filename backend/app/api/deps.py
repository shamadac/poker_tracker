"""
Dependency injection for FastAPI endpoints.
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_maker
from app.core.security import TokenManager
from app.models.user import User
from app.services.user_service import UserService
from app.services.rbac_service import RBACService

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify and decode token
    payload = TokenManager.verify_token(token, "access")
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await UserService.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    # For now, all users are considered active
    # This can be extended when user status is implemented
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current superuser.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current admin user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current admin user
        
    Raises:
        HTTPException: If user is not an admin or superuser
    """
    if not (current_user.has_role("admin") or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def check_user_permission(
    permission_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Check if current user has a specific permission.
    
    Args:
        permission_name: Name of the permission to check
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User: Current user if they have the permission
        
    Raises:
        HTTPException: If user doesn't have the permission
    """
    if current_user.is_superuser:
        return current_user
    
    has_permission = await RBACService.user_has_permission(
        db, str(current_user.id), permission_name
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission_name}' required"
        )
    
    return current_user


async def check_resource_access(
    resource: str,
    action: str,
    resource_owner_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Check if current user can access a resource.
    
    Args:
        resource: Resource type (e.g., 'poker_hands', 'users')
        action: Action type (e.g., 'read', 'write', 'delete')
        resource_owner_id: ID of the resource owner
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User: Current user if they have access
        
    Raises:
        HTTPException: If user doesn't have access
    """
    has_access = await RBACService.check_resource_access(
        db, str(current_user.id), resource, action, resource_owner_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied for {action} on {resource}"
        )
    
    return current_user


class CommonQueryParams:
    """
    Common query parameters for pagination and filtering.
    """
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ):
        self.skip = skip
        self.limit = limit
        self.search = search


def common_parameters(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> CommonQueryParams:
    """
    Dependency for common query parameters.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search query string
        
    Returns:
        CommonQueryParams: Common query parameters
    """
    return CommonQueryParams(skip=skip, limit=limit, search=search)