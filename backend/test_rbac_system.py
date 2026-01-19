"""
Test script to verify RBAC system functionality.
"""
import asyncio
import sys
import os
import pytest

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.services.rbac_service import RBACService
from app.services.user_service import UserService
from app.schemas.auth import RegisterRequest


@pytest.mark.asyncio
async def test_rbac_system():
    """Test the RBAC system functionality."""
    print("Testing RBAC System...")
    
    async with async_session_maker() as db:
        try:
            # Test 1: Check if default roles exist
            print("\n1. Checking default roles...")
            roles = await RBACService.get_all_roles(db)
            role_names = [role.name for role in roles]
            print(f"Available roles: {role_names}")
            
            expected_roles = ['user', 'admin', 'superuser']
            for role_name in expected_roles:
                if role_name in role_names:
                    print(f"✓ Role '{role_name}' exists")
                else:
                    print(f"✗ Role '{role_name}' missing")
            
            # Test 2: Check role permissions
            print("\n2. Checking role permissions...")
            user_role = await RBACService.get_role_by_name(db, "user")
            if user_role:
                print(f"✓ User role has {len(user_role.permissions)} permissions")
                for perm in user_role.permissions[:3]:  # Show first 3
                    print(f"  - {perm.name} ({perm.resource}:{perm.action})")
            
            admin_role = await RBACService.get_role_by_name(db, "admin")
            if admin_role:
                print(f"✓ Admin role has {len(admin_role.permissions)} permissions")
            
            superuser_role = await RBACService.get_role_by_name(db, "superuser")
            if superuser_role:
                print(f"✓ Superuser role has {len(superuser_role.permissions)} permissions")
            
            # Test 3: Create a test user and check role assignment
            print("\n3. Testing user creation and role assignment...")
            test_email = "test_rbac@example.com"
            
            # Check if user already exists and delete if so
            existing_user = await UserService.get_user_by_email(db, test_email)
            if existing_user:
                await UserService.delete_user(db, str(existing_user.id))
                print("✓ Cleaned up existing test user")
            
            # Create new user
            user_data = RegisterRequest(
                email=test_email,
                password="Test123!",
                confirm_password="Test123!"
            )
            
            new_user = await UserService.create_user(db, user_data)
            print(f"✓ Created test user: {new_user.email}")
            
            # Check if user got default role
            user_roles = await RBACService.get_user_roles(db, str(new_user.id))
            print(f"✓ User has {len(user_roles)} roles: {[role.name for role in user_roles]}")
            
            # Test 4: Check permissions
            print("\n4. Testing permission checks...")
            
            # Test basic permission
            has_read_own = await RBACService.user_has_permission(
                db, str(new_user.id), "read_own_hands"
            )
            print(f"✓ User has 'read_own_hands' permission: {has_read_own}")
            
            # Test resource access
            has_access = await RBACService.check_resource_access(
                db, str(new_user.id), "poker_hands", "read", str(new_user.id)
            )
            print(f"✓ User can read own poker hands: {has_access}")
            
            # Test access to other user's data (should be False)
            has_access_other = await RBACService.check_resource_access(
                db, str(new_user.id), "poker_hands", "read", "other-user-id"
            )
            print(f"✓ User cannot read other's poker hands: {not has_access_other}")
            
            # Test 5: Test admin role assignment
            print("\n5. Testing admin role assignment...")
            await RBACService.assign_role_to_user(db, str(new_user.id), "admin")
            
            # Check if user now has admin permissions
            has_admin_perm = await RBACService.user_has_permission(
                db, str(new_user.id), "read_all_users"
            )
            print(f"✓ User has admin permission 'read_all_users': {has_admin_perm}")
            
            # Test access to other user's data as admin
            has_admin_access = await RBACService.check_resource_access(
                db, str(new_user.id), "users", "read_all", "other-user-id"
            )
            print(f"✓ Admin can read all users: {has_admin_access}")
            
            # Clean up
            await UserService.delete_user(db, str(new_user.id))
            print("✓ Cleaned up test user")
            
            print("\n🎉 RBAC system test completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Error during RBAC test: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_rbac_system())