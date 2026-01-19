"""
RBAC (Role-Based Access Control) API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_admin_user, get_current_superuser
from app.models.user import User
from app.services.rbac_service import RBACService
from app.schemas.rbac import (
    Role, RoleCreate, RoleUpdate, Permission, UserRole, UserRoleAssign,
    UserWithRoles, AccessCheckRequest, AccessCheckResponse, RolePermissionUpdate,
    BulkRoleAssignment, RoleStatistics, PermissionCheck, ResourcePermissionCheck,
    UserPermissionSummary
)
from app.middleware.authorization import require_permission, require_role, require_superuser

router = APIRouter()


# Role Management Endpoints
@router.get("/roles", response_model=List[Role])
async def get_all_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all roles (admin only)."""
    return await RBACService.get_all_roles(db)


@router.get("/roles/{role_name}", response_model=Role)
async def get_role(
    role_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get role by name (admin only)."""
    role = await RBACService.get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )
    return role


@router.post("/roles", response_model=Role, status_code=status.HTTP_201_CREATED)
@require_superuser
async def create_role(
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Create a new role (superuser only)."""
    return await RBACService.create_role(
        db, 
        role_data.name, 
        role_data.description, 
        role_data.permission_names
    )


@router.put("/roles/{role_name}", response_model=Role)
@require_superuser
async def update_role(
    role_name: str,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Update role (superuser only)."""
    role = await RBACService.get_role_by_name(db, role_name)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )
    
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles"
        )
    
    # Update description if provided
    if role_data.description is not None:
        role.description = role_data.description
    
    # Update permissions if provided
    if role_data.permission_names is not None:
        role.permissions.clear()
        for perm_name in role_data.permission_names:
            permission = await RBACService.get_permission_by_name(db, perm_name)
            if permission:
                role.permissions.append(permission)
    
    await db.commit()
    await db.refresh(role)
    return role


@router.delete("/roles/{role_name}")
@require_superuser
async def delete_role(
    role_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Delete role (superuser only)."""
    success = await RBACService.delete_role(db, role_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )
    return {"message": f"Role '{role_name}' deleted successfully"}


# User Role Assignment Endpoints
@router.post("/users/{user_id}/roles", response_model=UserRole, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: str,
    role_assignment: UserRoleAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Assign role to user (admin only)."""
    return await RBACService.assign_role_to_user(
        db, 
        user_id, 
        role_assignment.role_name,
        str(current_user.id),
        role_assignment.expires_at
    )


@router.delete("/users/{user_id}/roles/{role_name}")
async def remove_role_from_user(
    user_id: str,
    role_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Remove role from user (admin only)."""
    success = await RBACService.remove_role_from_user(db, user_id, role_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User does not have role '{role_name}'"
        )
    return {"message": f"Role '{role_name}' removed from user"}


@router.get("/users/{user_id}/roles", response_model=List[Role])
async def get_user_roles(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's roles (users can see their own, admins can see any)."""
    # Users can only see their own roles, admins can see any
    if str(current_user.id) != user_id and not (current_user.has_role("admin") or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return await RBACService.get_user_roles(db, user_id)


@router.get("/users/{user_id}/permissions", response_model=List[Permission])
async def get_user_permissions(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's permissions (users can see their own, admins can see any)."""
    # Users can only see their own permissions, admins can see any
    if str(current_user.id) != user_id and not (current_user.has_role("admin") or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return await RBACService.get_user_permissions(db, user_id)


# Permission Check Endpoints
@router.post("/check-access", response_model=AccessCheckResponse)
async def check_access(
    access_request: AccessCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if current user has access to a resource."""
    has_access = await RBACService.check_resource_access(
        db,
        str(current_user.id),
        access_request.resource,
        access_request.action,
        access_request.resource_owner_id
    )
    
    reason = None
    if not has_access:
        if current_user.is_superuser:
            reason = "Superuser has all access"
        elif access_request.resource_owner_id and str(current_user.id) == access_request.resource_owner_id:
            reason = "User owns the resource but lacks permission"
        else:
            reason = f"User lacks {access_request.action} permission for {access_request.resource}"
    
    return AccessCheckResponse(has_access=has_access, reason=reason)


@router.post("/check-permission")
async def check_permission(
    permission_check: PermissionCheck,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if current user has a specific permission."""
    has_permission = await RBACService.user_has_permission(
        db, str(current_user.id), permission_check.permission_name
    )
    
    return {"has_permission": has_permission, "permission": permission_check.permission_name}


@router.post("/check-resource-permission")
async def check_resource_permission(
    resource_check: ResourcePermissionCheck,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if current user has permission for a resource/action."""
    has_permission = await RBACService.user_has_resource_permission(
        db, str(current_user.id), resource_check.resource, resource_check.action
    )
    
    return {
        "has_permission": has_permission,
        "resource": resource_check.resource,
        "action": resource_check.action
    }


# User Management with RBAC
@router.get("/users-with-roles", response_model=List[UserWithRoles])
async def get_users_with_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all users with their roles (admin only)."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    
    users_with_roles = []
    for user in users:
        user_roles = [ur.role for ur in user.user_roles if not ur.is_expired()]
        users_with_roles.append(UserWithRoles(
            id=str(user.id),
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=user_roles,
            created_at=user.created_at
        ))
    
    return users_with_roles


@router.get("/my-permissions", response_model=UserPermissionSummary)
async def get_my_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's permission summary."""
    roles = await RBACService.get_user_roles(db, str(current_user.id))
    permissions = await RBACService.get_user_permissions(db, str(current_user.id))
    
    return UserPermissionSummary(
        user_id=str(current_user.id),
        roles=[role.name for role in roles],
        permissions=[perm.name for perm in permissions],
        is_superuser=current_user.is_superuser,
        is_active=current_user.is_active
    )


# Bulk Operations
@router.post("/bulk-assign-roles")
@require_superuser
async def bulk_assign_roles(
    bulk_assignment: BulkRoleAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Bulk assign role to multiple users (superuser only)."""
    results = []
    errors = []
    
    for user_id in bulk_assignment.user_ids:
        try:
            user_role = await RBACService.assign_role_to_user(
                db, user_id, bulk_assignment.role_name,
                str(current_user.id), bulk_assignment.expires_at
            )
            results.append({"user_id": user_id, "status": "success"})
        except Exception as e:
            errors.append({"user_id": user_id, "error": str(e)})
    
    return {
        "successful_assignments": len(results),
        "failed_assignments": len(errors),
        "results": results,
        "errors": errors
    }


# Statistics and Monitoring
@router.get("/role-statistics", response_model=List[RoleStatistics])
async def get_role_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get role usage statistics (admin only)."""
    from sqlalchemy import select, func
    from app.models.rbac import UserRole
    from datetime import datetime
    
    roles = await RBACService.get_all_roles(db, timezone)
    statistics = []
    
    for role in roles:
        # Count total assignments
        total_result = await db.execute(
            select(func.count(UserRole.user_id)).where(UserRole.role_id == role.id)
        )
        total_count = total_result.scalar() or 0
        
        # Count active assignments
        active_result = await db.execute(
            select(func.count(UserRole.user_id)).where(
                UserRole.role_id == role.id,
                (UserRole.expires_at.is_(None) | (UserRole.expires_at > datetime.now(timezone.utc)))
            )
        )
        active_count = active_result.scalar() or 0
        
        expired_count = total_count - active_count
        
        statistics.append(RoleStatistics(
            role_name=role.name,
            user_count=total_count,
            active_assignments=active_count,
            expired_assignments=expired_count
        ))
    
    return statistics


# Maintenance Operations
@router.post("/cleanup-expired-roles")
@require_superuser
async def cleanup_expired_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Remove expired role assignments (superuser only)."""
    removed_count = await RBACService.cleanup_expired_roles(db)
    return {"message": f"Removed {removed_count} expired role assignments"}