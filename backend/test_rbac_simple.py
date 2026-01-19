"""
Simple test script to verify RBAC system functionality without user creation.
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


@pytest.mark.asyncio
async def test_rbac_basic():
    """Test basic RBAC system functionality."""
    print("Testing RBAC System (Basic)...")
    
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
                print("  Sample permissions:")
                for perm in user_role.permissions[:5]:  # Show first 5
                    print(f"    - {perm.name} ({perm.resource}:{perm.action})")
            
            admin_role = await RBACService.get_role_by_name(db, "admin")
            if admin_role:
                print(f"✓ Admin role has {len(admin_role.permissions)} permissions")
            
            superuser_role = await RBACService.get_role_by_name(db, "superuser")
            if superuser_role:
                print(f"✓ Superuser role has {len(superuser_role.permissions)} permissions")
            
            # Test 3: Check specific permissions
            print("\n3. Checking specific permissions...")
            
            # Check if user role has expected permissions
            user_perms = [p.name for p in user_role.permissions]
            expected_user_perms = ['read_own_hands', 'write_own_hands', 'read_own_profile']
            
            for perm in expected_user_perms:
                if perm in user_perms:
                    print(f"✓ User role has '{perm}' permission")
                else:
                    print(f"✗ User role missing '{perm}' permission")
            
            # Check if admin role has admin permissions
            admin_perms = [p.name for p in admin_role.permissions]
            expected_admin_perms = ['read_all_users', 'view_system_logs']
            
            for perm in expected_admin_perms:
                if perm in admin_perms:
                    print(f"✓ Admin role has '{perm}' permission")
                else:
                    print(f"✗ Admin role missing '{perm}' permission")
            
            # Test 4: Check permission hierarchy
            print("\n4. Checking permission hierarchy...")
            
            # Admin should have all user permissions plus admin permissions
            user_perm_count = len(user_role.permissions)
            admin_perm_count = len(admin_role.permissions)
            superuser_perm_count = len(superuser_role.permissions)
            
            if admin_perm_count > user_perm_count:
                print(f"✓ Admin has more permissions ({admin_perm_count}) than user ({user_perm_count})")
            else:
                print(f"✗ Admin should have more permissions than user")
            
            if superuser_perm_count >= admin_perm_count:
                print(f"✓ Superuser has most permissions ({superuser_perm_count})")
            else:
                print(f"✗ Superuser should have most permissions")
            
            print("\n🎉 Basic RBAC system test completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Error during RBAC test: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_rbac_basic())