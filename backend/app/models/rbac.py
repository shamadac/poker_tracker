"""
Role-Based Access Control (RBAC) models.
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import String, Boolean, Text, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


"""
Role-Based Access Control (RBAC) models.
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import String, Boolean, Text, DateTime, ForeignKey, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=False), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', UUID(as_uuid=False), ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default='now()', nullable=False)
)


class Role(Base, UUIDMixin, TimestampMixin):
    """Role model for RBAC system."""
    
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        index=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )
    
    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a system-defined role that cannot be deleted"
    )
    
    # Relationships
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )
    
    users: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has a specific permission."""
        return any(perm.name == permission_name for perm in self.permissions)
    
    def has_resource_action(self, resource: str, action: str) -> bool:
        """Check if role has permission for a specific resource and action."""
        return any(
            perm.resource == resource and perm.action == action 
            for perm in self.permissions
        )


class Permission(Base, UUIDMixin, TimestampMixin):
    """Permission model for RBAC system."""
    
    __tablename__ = "permissions"
    
    name: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False
    )
    
    resource: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="The resource this permission applies to (e.g., 'poker_hands', 'users')"
    )
    
    action: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="The action this permission allows (e.g., 'read', 'write', 'delete')"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True
    )
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
    
    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name={self.name}, resource={self.resource}, action={self.action})>"


class UserRole(Base, TimestampMixin):
    """User-Role association model with additional metadata."""
    
    __tablename__ = "user_roles"
    
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True
    )
    
    role_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('roles.id', ondelete='CASCADE'),
        primary_key=True
    )
    
    assigned_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="User who assigned this role"
    )
    
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='now()',
        nullable=False
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this role assignment expires (null = never expires)"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="user_roles"
    )
    
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
        lazy="selectin"
    )
    
    assigned_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_by]
    )
    
    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
    
    def is_expired(self) -> bool:
        """Check if this role assignment has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at