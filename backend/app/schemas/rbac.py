"""
RBAC-related Pydantic schemas.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    """Base permission schema."""
    name: str = Field(..., description="Permission name")
    resource: str = Field(..., description="Resource type")
    action: str = Field(..., description="Action type")
    description: Optional[str] = Field(None, description="Permission description")


class PermissionCreate(PermissionBase):
    """Schema for creating permissions."""
    pass


class Permission(PermissionBase):
    """Permission response schema."""
    id: str = Field(..., description="Permission ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")


class RoleCreate(RoleBase):
    """Schema for creating roles."""
    permission_names: Optional[List[str]] = Field(
        default_factory=list, 
        description="List of permission names to assign to this role"
    )


class RoleUpdate(BaseModel):
    """Schema for updating roles."""
    description: Optional[str] = Field(None, description="Role description")
    permission_names: Optional[List[str]] = Field(
        None, 
        description="List of permission names to assign to this role"
    )


class Role(RoleBase):
    """Role response schema."""
    id: str = Field(..., description="Role ID")
    is_system_role: bool = Field(..., description="Whether this is a system role")
    permissions: List[Permission] = Field(default_factory=list, description="Role permissions")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class UserRoleBase(BaseModel):
    """Base user role assignment schema."""
    expires_at: Optional[datetime] = Field(None, description="Role expiration date")


class UserRoleAssign(UserRoleBase):
    """Schema for assigning roles to users."""
    role_name: str = Field(..., description="Role name to assign")


class UserRole(UserRoleBase):
    """User role assignment response schema."""
    user_id: str = Field(..., description="User ID")
    role_id: str = Field(..., description="Role ID")
    role: Role = Field(..., description="Role details")
    assigned_by: Optional[str] = Field(None, description="ID of user who assigned this role")
    assigned_at: datetime = Field(..., description="Assignment timestamp")
    
    class Config:
        from_attributes = True


class UserWithRoles(BaseModel):
    """User schema with roles included."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    is_active: bool = Field(..., description="Whether user is active")
    is_superuser: bool = Field(..., description="Whether user is superuser")
    roles: List[Role] = Field(default_factory=list, description="User roles")
    created_at: datetime = Field(..., description="Account creation date")
    
    class Config:
        from_attributes = True


class AccessCheckRequest(BaseModel):
    """Schema for checking access permissions."""
    resource: str = Field(..., description="Resource type")
    action: str = Field(..., description="Action type")
    resource_owner_id: Optional[str] = Field(None, description="Resource owner ID")


class AccessCheckResponse(BaseModel):
    """Schema for access check response."""
    has_access: bool = Field(..., description="Whether user has access")
    reason: Optional[str] = Field(None, description="Reason for access decision")


class RolePermissionUpdate(BaseModel):
    """Schema for updating role permissions."""
    permission_names: List[str] = Field(..., description="List of permission names")


class BulkRoleAssignment(BaseModel):
    """Schema for bulk role assignments."""
    user_ids: List[str] = Field(..., description="List of user IDs")
    role_name: str = Field(..., description="Role name to assign")
    expires_at: Optional[datetime] = Field(None, description="Role expiration date")


class RoleStatistics(BaseModel):
    """Schema for role usage statistics."""
    role_name: str = Field(..., description="Role name")
    user_count: int = Field(..., description="Number of users with this role")
    active_assignments: int = Field(..., description="Number of active assignments")
    expired_assignments: int = Field(..., description="Number of expired assignments")


class PermissionCheck(BaseModel):
    """Schema for permission check requests."""
    permission_name: str = Field(..., description="Permission name to check")


class ResourcePermissionCheck(BaseModel):
    """Schema for resource permission check requests."""
    resource: str = Field(..., description="Resource type")
    action: str = Field(..., description="Action type")


class UserPermissionSummary(BaseModel):
    """Schema for user permission summary."""
    user_id: str = Field(..., description="User ID")
    roles: List[str] = Field(..., description="Role names")
    permissions: List[str] = Field(..., description="Permission names")
    is_superuser: bool = Field(..., description="Whether user is superuser")
    is_active: bool = Field(..., description="Whether user is active")