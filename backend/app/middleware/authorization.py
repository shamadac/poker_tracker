"""
Authorization middleware for RBAC enforcement.
"""
from typing import Callable, Optional, List, Union
from functools import wraps

from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.rbac_service import RBACService


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class RequirePermission:
    """Decorator class for requiring specific permissions."""
    
    def __init__(
        self,
        permission: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        allow_owner: bool = True,
        owner_field: str = "user_id"
    ):
        """
        Initialize permission requirement.
        
        Args:
            permission: Specific permission name to check
            resource: Resource type (e.g., 'poker_hands', 'users')
            action: Action type (e.g., 'read', 'write', 'delete')
            allow_owner: Whether to allow resource owners to access their own data
            owner_field: Field name that contains the owner ID in the resource
        """
        self.permission = permission
        self.resource = resource
        self.action = action
        self.allow_owner = allow_owner
        self.owner_field = owner_field
    
    def __call__(self, func: Callable) -> Callable:
        """Apply permission check to the decorated function."""
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from function signature
            db: AsyncSession = None
            current_user: User = None
            
            # Look for db and current_user in kwargs (from Depends)
            for key, value in kwargs.items():
                if isinstance(value, AsyncSession):
                    db = value
                elif isinstance(value, User):
                    current_user = value
            
            if not db or not current_user:
                raise AuthorizationError("Missing required dependencies for authorization")
            
            # Check permission
            await self._check_permission(db, current_user, kwargs)
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    
    async def _check_permission(
        self,
        db: AsyncSession,
        user: User,
        kwargs: dict
    ) -> None:
        """Check if user has required permission."""
        
        # Superusers bypass all checks
        if user.is_superuser:
            return
        
        # Check specific permission if provided
        if self.permission:
            has_perm = await RBACService.user_has_permission(db, str(user.id), self.permission)
            if not has_perm:
                raise AuthorizationError(f"Permission '{self.permission}' required")
            return
        
        # Check resource/action permission
        if self.resource and self.action:
            # Try to determine resource owner ID
            resource_owner_id = None
            
            if self.allow_owner:
                # Look for owner ID in various places
                resource_owner_id = self._extract_owner_id(kwargs)
            
            has_access = await RBACService.check_resource_access(
                db, str(user.id), self.resource, self.action, resource_owner_id
            )
            
            if not has_access:
                raise AuthorizationError(
                    f"Access denied for {self.action} on {self.resource}"
                )
            return
        
        # If no specific checks, just verify user is active
        if not user.is_active:
            raise AuthorizationError("Account is inactive")
    
    def _extract_owner_id(self, kwargs: dict) -> Optional[str]:
        """Extract owner ID from function arguments."""
        
        # Direct owner field in kwargs
        if self.owner_field in kwargs:
            return str(kwargs[self.owner_field])
        
        # Look for common ID patterns
        for key in ['user_id', 'id', 'owner_id']:
            if key in kwargs:
                return str(kwargs[key])
        
        # Look in path parameters (for FastAPI)
        for key, value in kwargs.items():
            if key.endswith('_id') and isinstance(value, (str, int)):
                return str(value)
        
        return None


def require_permission(
    permission: Optional[str] = None,
    resource: Optional[str] = None,
    action: Optional[str] = None,
    allow_owner: bool = True,
    owner_field: str = "user_id"
):
    """
    Decorator for requiring specific permissions.
    
    Usage:
        @require_permission(permission="read_all_users")
        @require_permission(resource="poker_hands", action="read")
        @require_permission(resource="users", action="write", allow_owner=True)
    """
    return RequirePermission(permission, resource, action, allow_owner, owner_field)


def require_role(role_name: str):
    """
    Decorator for requiring a specific role.
    
    Usage:
        @require_role("admin")
        @require_role("superuser")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user: User = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise AuthorizationError("Missing user context for role check")
            
            if not current_user.has_role(role_name) and not current_user.is_superuser:
                raise AuthorizationError(f"Role '{role_name}' required")
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_superuser(func: Callable) -> Callable:
    """
    Decorator for requiring superuser privileges.
    
    Usage:
        @require_superuser
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract current_user from kwargs
        current_user: User = None
        for key, value in kwargs.items():
            if isinstance(value, User):
                current_user = value
                break
        
        if not current_user:
            raise AuthorizationError("Missing user context for superuser check")
        
        if not current_user.is_superuser:
            raise AuthorizationError("Superuser privileges required")
        
        return await func(*args, **kwargs)
    
    return wrapper


class ResourceOwnershipChecker:
    """Helper class for checking resource ownership."""
    
    @staticmethod
    async def check_poker_hand_ownership(
        db: AsyncSession,
        user_id: str,
        hand_id: str
    ) -> bool:
        """Check if user owns a specific poker hand."""
        from app.models.hand import PokerHand
        from sqlalchemy import select
        
        result = await db.execute(
            select(PokerHand.user_id).where(PokerHand.id == hand_id)
        )
        owner_id = result.scalar_one_or_none()
        return owner_id and str(owner_id) == str(user_id)
    
    @staticmethod
    async def check_analysis_ownership(
        db: AsyncSession,
        user_id: str,
        analysis_id: str
    ) -> bool:
        """Check if user owns a specific analysis result."""
        from app.models.analysis import AnalysisResult
        from app.models.hand import PokerHand
        from sqlalchemy import select
        
        result = await db.execute(
            select(PokerHand.user_id)
            .join(AnalysisResult)
            .where(AnalysisResult.id == analysis_id)
        )
        owner_id = result.scalar_one_or_none()
        return owner_id and str(owner_id) == str(user_id)
    
    @staticmethod
    async def check_statistics_ownership(
        db: AsyncSession,
        user_id: str,
        stats_id: str
    ) -> bool:
        """Check if user owns specific statistics cache."""
        from app.models.statistics import StatisticsCache
        from sqlalchemy import select
        
        result = await db.execute(
            select(StatisticsCache.user_id).where(StatisticsCache.id == stats_id)
        )
        owner_id = result.scalar_one_or_none()
        return owner_id and str(owner_id) == str(user_id)


# Dependency functions for FastAPI
async def require_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is active."""
    if not current_user.is_active:
        raise AuthorizationError("Account is inactive")
    return current_user


async def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user has admin role."""
    if not current_user.has_role("admin") and not current_user.is_superuser:
        raise AuthorizationError("Admin privileges required")
    return current_user


async def require_superuser_dependency(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is superuser."""
    if not current_user.is_superuser:
        raise AuthorizationError("Superuser privileges required")
    return current_user


def create_ownership_dependency(resource_type: str):
    """
    Create a dependency that checks resource ownership.
    
    Args:
        resource_type: Type of resource ('poker_hands', 'analysis', 'statistics')
    
    Returns:
        Dependency function that checks ownership
    """
    async def check_ownership(
        resource_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # Superusers and admins bypass ownership checks
        if current_user.is_superuser or current_user.has_role("admin"):
            return current_user
        
        # Check ownership based on resource type
        if resource_type == "poker_hands":
            owns_resource = await ResourceOwnershipChecker.check_poker_hand_ownership(
                db, str(current_user.id), resource_id
            )
        elif resource_type == "analysis":
            owns_resource = await ResourceOwnershipChecker.check_analysis_ownership(
                db, str(current_user.id), resource_id
            )
        elif resource_type == "statistics":
            owns_resource = await ResourceOwnershipChecker.check_statistics_ownership(
                db, str(current_user.id), resource_id
            )
        else:
            raise AuthorizationError(f"Unknown resource type: {resource_type}")
        
        if not owns_resource:
            raise AuthorizationError("Access denied: You don't own this resource")
        
        return current_user
    
    return check_ownership