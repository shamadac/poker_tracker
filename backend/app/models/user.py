"""
User model for authentication and user management.
"""
from typing import Dict, Any, Optional, List

from sqlalchemy import String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model for storing user accounts and preferences."""
    
    __tablename__ = "users"
    
    # Basic user information
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    
    # Encrypted API keys for AI providers
    api_keys: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Encrypted API keys for Gemini and Groq providers"
    )
    
    # Hand history directory paths for different platforms
    hand_history_paths: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Directory paths for PokerStars and GGPoker hand histories"
    )
    
    # User preferences and settings
    preferences: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="User preferences including UI settings and analysis options"
    )
    
    # User status fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user account is active"
    )
    
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user has superuser privileges"
    )
    
    # Relationships
    poker_hands = relationship("PokerHand", back_populates="user", cascade="all, delete-orphan")
    statistics_cache = relationship("StatisticsCache", back_populates="user", cascade="all, delete-orphan")
    file_monitoring = relationship("FileMonitoring", back_populates="user", cascade="all, delete-orphan")
    file_processing_tasks = relationship("FileProcessingTask", back_populates="user", cascade="all, delete-orphan")
    user_roles = relationship(
        "UserRole", 
        back_populates="user", 
        cascade="all, delete-orphan",
        foreign_keys="UserRole.user_id"
    )
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    # Encyclopedia relationships
    created_encyclopedia_entries = relationship(
        "EncyclopediaEntry",
        foreign_keys="EncyclopediaEntry.created_by",
        cascade="all, delete-orphan"
    )
    approved_encyclopedia_entries = relationship(
        "EncyclopediaEntry",
        foreign_keys="EncyclopediaEntry.approved_by"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
    
    def get_roles(self) -> List["Role"]:
        """Get all active roles for this user."""
        from .rbac import Role
        active_roles = []
        for user_role in self.user_roles:
            if not user_role.is_expired():
                active_roles.append(user_role.role)
        return active_roles
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.get_roles())
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission through any of their roles."""
        for role in self.get_roles():
            if role.has_permission(permission_name):
                return True
        return False
    
    def has_resource_permission(self, resource: str, action: str) -> bool:
        """Check if user has permission for a specific resource and action."""
        # Superusers have all permissions
        if self.is_superuser:
            return True
            
        for role in self.get_roles():
            if role.has_resource_action(resource, action):
                return True
        return False
    
    def can_access_resource(self, resource: str, action: str, resource_owner_id: Optional[str] = None) -> bool:
        """
        Check if user can access a resource with ownership consideration.
        
        Args:
            resource: The resource type (e.g., 'poker_hands', 'users')
            action: The action (e.g., 'read', 'write', 'delete')
            resource_owner_id: The ID of the resource owner (for ownership checks)
            
        Returns:
            bool: True if user has access, False otherwise
        """
        # Superusers have access to everything
        if self.is_superuser:
            return True
        
        # Check for "all" permissions (admin-level)
        if self.has_resource_permission(resource, f"{action}_all"):
            return True
        
        # Check for "own" permissions with ownership validation
        if resource_owner_id and str(self.id) == str(resource_owner_id):
            if self.has_resource_permission(resource, f"{action}_own") or self.has_resource_permission(resource, action):
                return True
        
        # Check for general permissions (without ownership restriction)
        return self.has_resource_permission(resource, action)