#!/usr/bin/env python3
"""
Unit tests for Role-Based Access Control (RBAC).

Feature: professional-poker-analyzer-rebuild
Property 21: Role-Based Access Control

This test validates that for any data access request, the system should enforce 
proper authorization ensuring users can only access their own data and appropriate 
system resources according to Requirement 8.4.

**Validates: Requirements 8.4**
"""

import asyncio
import uuid
import pytest
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# Import the RBAC components to test
from app.services.rbac_service import RBACService
from app.services.user_service import UserService
from app.models.user import User
from app.models.rbac import Role, Permission, UserRole
from app.schemas.auth import RegisterRequest
from app.core.database import async_session_maker


class TestRBACAccessControlUnit:
    """Unit tests for Role-Based Access Control."""

    @pytest.fixture(autouse=True)
    async def setup_and_cleanup(self):
        """Setup and cleanup for each test."""
        self.test_users = []
        
        yield
        
        # Cleanup test data
        async with async_session_maker() as db:
            try:
                for user_id in self.test_users:
                    await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
                    await db.execute(delete(User).where(User.id == user_id))
                await db.commit()
            except Exception:
                await db.rollback()

    async def create_test_user(self, db: AsyncSession, email: str, is_superuser: bool = False) -> User:
        """Create a test user and track for cleanup."""
        # Add unique suffix to avoid conflicts
        unique_email = f"{uuid.uuid4().hex[:8]}_{email}"
        
        user_data = RegisterRequest(
            email=unique_email,
            password="Test123!",
            confirm_password="Test123!"
        )
        
        user = await UserService.create_user(db, user_data)
        if is_superuser:
            user.is_superuser = True
            await db.commit()
            await db.refresh(user)
        
        self.test_users.append(str(user.id))
        return user

    @pytest.mark.asyncio
    async def test_users_cannot_access_other_users_data(self):
        """
        Test: Users can only access their own data unless they have admin privileges.
        
        **Validates: Requirements 8.4**
        """
        async with async_session_maker() as db:
            # Create two test users
            user1 = await self.create_test_user(db, "test1@example.com")
            user2 = await self.create_test_user(db, "test2@example.com")
            
            # Assign default user role to both users
            await RBACService.assign_role_to_user(db, str(user1.id), "user")
            await RBACService.assign_role_to_user(db, str(user2.id), "user")
            
            # Test that user1 cannot access user2's poker hands
            has_access = await RBACService.check_resource_access(
                db, str(user1.id), "poker_hands", "read", str(user2.id)
            )
            
            # Regular users should not have access to other users' data
            assert not has_access, "User should not have read access to other user's poker_hands"
            
            # Test that user2 can access their own poker hands
            has_own_access = await RBACService.check_resource_access(
                db, str(user2.id), "poker_hands", "read", str(user2.id)
            )
            
            # Users should have access to their own data
            assert has_own_access, "User should have read access to their own poker_hands"

    @pytest.mark.asyncio
    async def test_admin_users_have_elevated_access(self):
        """
        Test: Admin users should have elevated access to system resources.
        
        **Validates: Requirements 8.4**
        """
        async with async_session_maker() as db:
            # Create regular user and admin user
            regular_user = await self.create_test_user(db, "user@example.com")
            admin_user = await self.create_test_user(db, "admin@example.com")
            
            # Assign roles
            await RBACService.assign_role_to_user(db, str(regular_user.id), "user")
            await RBACService.assign_role_to_user(db, str(admin_user.id), "admin")
            
            # Check if admin has elevated access to users
            admin_has_access = await RBACService.check_resource_access(
                db, str(admin_user.id), "users", "read_all", None
            )
            
            # Admins should have elevated access
            assert admin_has_access, "Admin should have read_all access to users"
            
            # Regular user should not have elevated access
            regular_has_elevated = await RBACService.check_resource_access(
                db, str(regular_user.id), "users", "read_all", None
            )
            
            assert not regular_has_elevated, "Regular user should not have read_all access to users"

    @pytest.mark.asyncio
    async def test_superuser_bypasses_all_access_controls(self):
        """
        Test: Superusers should bypass all access control checks.
        
        **Validates: Requirements 8.4**
        """
        async with async_session_maker() as db:
            # Create superuser
            superuser = await self.create_test_user(db, "super@example.com", is_superuser=True)
            
            # Create another user to own resources
            other_user = await self.create_test_user(db, "other@example.com")
            await RBACService.assign_role_to_user(db, str(other_user.id), "user")
            
            # Superuser should have access to everything
            has_access = await RBACService.check_resource_access(
                db, str(superuser.id), "poker_hands", "read", str(other_user.id)
            )
            
            assert has_access, "Superuser should have read access to any poker_hands"
            
            # Test specific permission check (should also pass for superuser)
            has_permission = await RBACService.user_has_resource_permission(
                db, str(superuser.id), "poker_hands", "read"
            )
            
            assert has_permission, "Superuser should have poker_hands:read permission"

    @pytest.mark.asyncio
    async def test_role_based_permission_inheritance(self):
        """
        Test: Users should inherit permissions from their assigned roles.
        
        **Validates: Requirements 8.4**
        """
        async with async_session_maker() as db:
            # Create test user
            user = await self.create_test_user(db, "roletest@example.com")
            
            # Test with user role
            role_name = "user"
            
            # Get the role and its permissions
            role = await RBACService.get_role_by_name(db, role_name)
            assert role is not None, f"Role {role_name} should exist"
            
            # Assign role to user explicitly
            await RBACService.assign_role_to_user(db, str(user.id), role_name)
            
            # Get user's roles and permissions
            user_roles = await RBACService.get_user_roles(db, str(user.id))
            user_permissions = await RBACService.get_user_permissions(db, str(user.id))
            
            # Verify user has the assigned role
            role_names = [r.name for r in user_roles]
            assert role_name in role_names, f"User should have {role_name} role"
            
            # Check that user inherits permissions from role
            role_permission_names = [p.name for p in role.permissions]
            user_permission_names = [p.name for p in user_permissions]
            
            # All role permissions should be inherited by user
            for perm_name in role_permission_names:
                assert perm_name in user_permission_names, f"User should inherit permission {perm_name} from role {role_name}"

    @pytest.mark.asyncio
    async def test_role_expiration_enforcement(self):
        """
        Test: Expired role assignments should not grant permissions.
        
        **Validates: Requirements 8.4**
        """
        async with async_session_maker() as db:
            # Create test user
            user = await self.create_test_user(db, "expiretest@example.com")
            
            # Assign default user role first
            await RBACService.assign_role_to_user(db, str(user.id), "user")
            
            # Assign admin role with immediate expiration
            expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            await RBACService.assign_role_to_user(
                db, str(user.id), "admin", expires_at=expires_at
            )
            
            # Verify user does not have admin permissions (role is already expired)
            has_admin_perm = await RBACService.user_has_permission(
                db, str(user.id), "read_all_users"
            )
            
            assert not has_admin_perm, "User should not have admin permissions with expired role"
            
            # User should still have basic user permissions
            has_basic_perm = await RBACService.user_has_permission(
                db, str(user.id), "read_own_hands"
            )
            
            assert has_basic_perm, "User should still have basic user permissions"

    @pytest.mark.asyncio
    async def test_rbac_system_comprehensive_validation(self):
        """
        Comprehensive test validating multiple RBAC scenarios.
        
        **Validates: Requirements 8.4**
        """
        async with async_session_maker() as db:
            # Create users with different roles
            regular_user = await self.create_test_user(db, "regular@example.com")
            admin_user = await self.create_test_user(db, "admin@example.com")
            superuser = await self.create_test_user(db, "super@example.com", is_superuser=True)
            
            # Assign roles
            await RBACService.assign_role_to_user(db, str(regular_user.id), "user")
            await RBACService.assign_role_to_user(db, str(admin_user.id), "admin")
            
            # Test scenarios
            test_cases = [
                # (user_id, resource, action, owner_id, expected_result, description)
                (str(regular_user.id), "poker_hands", "read", str(regular_user.id), True, "User can read own poker hands"),
                (str(regular_user.id), "poker_hands", "read", str(admin_user.id), False, "User cannot read other's poker hands"),
                (str(admin_user.id), "users", "read_all", None, True, "Admin can read all users"),
                (str(regular_user.id), "users", "read_all", None, False, "Regular user cannot read all users"),
                (str(superuser.id), "poker_hands", "read", str(regular_user.id), True, "Superuser can read any poker hands"),
                (str(superuser.id), "users", "delete_all", None, True, "Superuser can delete all users"),
            ]
            
            for user_id, resource, action, owner_id, expected, description in test_cases:
                result = await RBACService.check_resource_access(db, user_id, resource, action, owner_id)
                assert result == expected, f"Failed: {description} (expected {expected}, got {result})"


if __name__ == "__main__":
    # Run a simple test to verify the test setup works
    async def test_setup():
        test_instance = TestRBACAccessControlUnit()
        print("RBAC Unit Test setup complete")
        
    asyncio.run(test_setup())