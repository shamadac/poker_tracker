"""
Role-Based Access Control (RBAC) service.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.rbac import Role, Permission, UserRole
from app.models.user import User


class RBACService:
    """Service for managing roles, permissions, and access control."""
    
    @staticmethod
    async def get_role_by_name(db: AsyncSession, role_name: str) -> Optional[Role]:
        """Get role by name."""
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.name == role_name)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_role_by_id(db: AsyncSession, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_roles(db: AsyncSession) -> List[Role]:
        """Get all roles."""
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .order_by(Role.name)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_permission_by_name(db: AsyncSession, permission_name: str) -> Optional[Permission]:
        """Get permission by name."""
        result = await db.execute(
            select(Permission).where(Permission.name == permission_name)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_permissions_by_resource_action(
        db: AsyncSession, 
        resource: str, 
        action: str
    ) -> List[Permission]:
        """Get permissions by resource and action."""
        result = await db.execute(
            select(Permission).where(
                and_(Permission.resource == resource, Permission.action == action)
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def assign_role_to_user(
        db: AsyncSession,
        user_id: str,
        role_name: str,
        assigned_by_id: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> UserRole:
        """Assign a role to a user."""
        # Get the role
        role = await RBACService.get_role_by_name(db, role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found"
            )
        
        # Check if user already has this role
        existing = await db.execute(
            select(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.role_id == role.id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User already has role '{role_name}'"
            )
        
        # Create user role assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=role.id,
            assigned_by=assigned_by_id,
            expires_at=expires_at
        )
        
        db.add(user_role)
        await db.commit()
        await db.refresh(user_role)
        
        return user_role
    
    @staticmethod
    async def remove_role_from_user(
        db: AsyncSession,
        user_id: str,
        role_name: str
    ) -> bool:
        """Remove a role from a user."""
        # Get the role
        role = await RBACService.get_role_by_name(db, role_name)
        if not role:
            return False
        
        # Find and delete the user role assignment
        result = await db.execute(
            select(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.role_id == role.id)
            )
        )
        user_role = result.scalar_one_or_none()
        
        if user_role:
            await db.delete(user_role)
            await db.commit()
            return True
        
        return False
    
    @staticmethod
    async def get_user_roles(db: AsyncSession, user_id: str) -> List[Role]:
        """Get all active roles for a user."""
        result = await db.execute(
            select(Role)
            .join(UserRole)
            .options(selectinload(Role.permissions))
            .where(
                and_(
                    UserRole.user_id == user_id,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_user_permissions(db: AsyncSession, user_id: str) -> List[Permission]:
        """Get all permissions for a user through their roles."""
        result = await db.execute(
            select(Permission)
            .join(Role.permissions)
            .join(UserRole)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.utcnow()
                    )
                )
            )
            .distinct()
        )
        return result.scalars().all()
    
    @staticmethod
    async def user_has_permission(
        db: AsyncSession,
        user_id: str,
        permission_name: str
    ) -> bool:
        """Check if a user has a specific permission."""
        # Check if user is superuser first
        user_result = await db.execute(
            select(User.is_superuser).where(User.id == user_id)
        )
        user_data = user_result.scalar_one_or_none()
        if user_data and user_data:  # is_superuser is True
            return True
        
        # Check through roles and permissions
        result = await db.execute(
            select(Permission.id)
            .join(Role.permissions)
            .join(UserRole)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Permission.name == permission_name,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.utcnow()
                    )
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def user_has_resource_permission(
        db: AsyncSession,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """Check if a user has permission for a specific resource and action."""
        # Check if user is superuser first
        user_result = await db.execute(
            select(User.is_superuser).where(User.id == user_id)
        )
        user_data = user_result.scalar_one_or_none()
        if user_data and user_data:  # is_superuser is True
            return True
        
        # Check through roles and permissions
        result = await db.execute(
            select(Permission.id)
            .join(Role.permissions)
            .join(UserRole)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Permission.resource == resource,
                    Permission.action == action,
                    or_(
                        UserRole.expires_at.is_(None),
                        UserRole.expires_at > datetime.utcnow()
                    )
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def check_resource_access(
        db: AsyncSession,
        user_id: str,
        resource: str,
        action: str,
        resource_owner_id: Optional[str] = None
    ) -> bool:
        """
        Check if user can access a resource with ownership consideration.
        
        Args:
            user_id: The user requesting access
            resource: The resource type (e.g., 'poker_hands', 'users')
            action: The action (e.g., 'read', 'write', 'delete')
            resource_owner_id: The ID of the resource owner (for ownership checks)
            
        Returns:
            bool: True if user has access, False otherwise
        """
        # Check if user is superuser first
        user_result = await db.execute(
            select(User.is_superuser).where(User.id == user_id)
        )
        user_data = user_result.scalar_one_or_none()
        if user_data and user_data:  # is_superuser is True
            return True
        
        # Check for "all" permissions (admin-level)
        if await RBACService.user_has_resource_permission(db, user_id, resource, f"{action}_all"):
            return True
        
        # Check for "own" permissions with ownership validation
        if resource_owner_id and str(user_id) == str(resource_owner_id):
            if (await RBACService.user_has_resource_permission(db, user_id, resource, f"{action}_own") or
                await RBACService.user_has_resource_permission(db, user_id, resource, action)):
                return True
        
        # Check for general permissions (without ownership restriction)
        return await RBACService.user_has_resource_permission(db, user_id, resource, action)
    
    @staticmethod
    async def create_role(
        db: AsyncSession,
        name: str,
        description: Optional[str] = None,
        permission_names: Optional[List[str]] = None
    ) -> Role:
        """Create a new role with optional permissions."""
        # Check if role already exists
        existing = await RBACService.get_role_by_name(db, name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{name}' already exists"
            )
        
        # Create role
        role = Role(
            name=name,
            description=description,
            is_system_role=False
        )
        
        # Add permissions if provided
        if permission_names:
            for perm_name in permission_names:
                permission = await RBACService.get_permission_by_name(db, perm_name)
                if permission:
                    role.permissions.append(permission)
        
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        return role
    
    @staticmethod
    async def delete_role(db: AsyncSession, role_name: str) -> bool:
        """Delete a role (only non-system roles)."""
        role = await RBACService.get_role_by_name(db, role_name)
        if not role:
            return False
        
        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete system roles"
            )
        
        await db.delete(role)
        await db.commit()
        return True
    
    @staticmethod
    async def assign_default_role(db: AsyncSession, user_id: str) -> UserRole:
        """Assign the default 'user' role to a new user."""
        return await RBACService.assign_role_to_user(db, user_id, "user")
    
    @staticmethod
    async def cleanup_expired_roles(db: AsyncSession) -> int:
        """Remove expired role assignments and return count of removed assignments."""
        result = await db.execute(
            select(UserRole).where(
                and_(
                    UserRole.expires_at.is_not(None),
                    UserRole.expires_at <= datetime.utcnow()
                )
            )
        )
        expired_roles = result.scalars().all()
        
        for user_role in expired_roles:
            await db.delete(user_role)
        
        await db.commit()
        return len(expired_roles)