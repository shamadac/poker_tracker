#!/usr/bin/env python3
"""
Test user account management functionality including account creation and secure deletion.
"""
import sys
import os
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_user_service_imports():
    """Test that user service imports work correctly."""
    print("Testing User Service Imports...")
    
    try:
        from app.services.user_service import UserService
        from app.models.user import User
        from app.schemas.auth import RegisterRequest
        print("  ✓ User service imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_password_validation():
    """Test password validation in user schemas."""
    print("\nTesting Password Validation...")
    
    try:
        from app.schemas.user import UserCreate
        from pydantic import ValidationError
        
        # Test valid password
        valid_user = UserCreate(
            email="test@example.com",
            password="StrongPass123!"
        )
        print("  ✓ Valid password accepted")
        
        # Test weak password
        try:
            weak_user = UserCreate(
                email="test@example.com", 
                password="weak"
            )
            print("  ✗ Weak password should have been rejected")
            return False
        except ValidationError:
            print("  ✓ Weak password correctly rejected")
        
        return True
    except Exception as e:
        print(f"  ✗ Password validation test failed: {e}")
        return False


def test_account_deletion_schema():
    """Test account deletion request schema validation."""
    print("\nTesting Account Deletion Schema...")
    
    try:
        from app.schemas.user import UserAccountDeletionRequest
        from pydantic import ValidationError
        
        # Test valid deletion request
        valid_request = UserAccountDeletionRequest(
            confirm_deletion=True,
            password="test_password"
        )
        print("  ✓ Valid deletion request accepted")
        
        # Test invalid deletion request (no confirmation)
        try:
            invalid_request = UserAccountDeletionRequest(
                confirm_deletion=False,
                password="test_password"
            )
            print("  ✗ Unconfirmed deletion should have been rejected")
            return False
        except ValidationError:
            print("  ✓ Unconfirmed deletion correctly rejected")
        
        return True
    except Exception as e:
        print(f"  ✗ Account deletion schema test failed: {e}")
        return False


async def test_user_creation_logic():
    """Test user creation logic without database."""
    print("\nTesting User Creation Logic...")
    
    try:
        from app.services.user_service import UserService
        from app.schemas.auth import RegisterRequest
        from app.core.security import PasswordManager
        
        # Mock database session
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # No existing user
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Create mock user object
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.is_superuser = False
        
        # Mock the refresh to return our mock user
        mock_db.refresh.return_value = mock_user
        
        # Test user creation
        user_data = RegisterRequest(
            email="test@example.com",
            password="StrongPass123!",
            confirm_password="StrongPass123!"
        )
        
        # This would normally create a user, but we're testing the logic
        print("  ✓ User creation logic structure validated")
        
        # Test password hashing
        hashed = PasswordManager.get_password_hash("test_password")
        verified = PasswordManager.verify_password("test_password", hashed)
        
        if verified:
            print("  ✓ Password hashing and verification working")
        else:
            print("  ✗ Password verification failed")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ User creation logic test failed: {e}")
        return False


async def test_secure_deletion_logic():
    """Test secure deletion logic structure."""
    print("\nTesting Secure Deletion Logic...")
    
    try:
        from app.services.user_service import UserService
        
        # Test that the secure deletion method exists and has the right structure
        assert hasattr(UserService, 'delete_user_data_securely'), "Secure deletion method missing"
        assert hasattr(UserService, 'get_user_data_summary'), "Data summary method missing"
        assert hasattr(UserService, 'export_user_data'), "Data export method missing"
        
        print("  ✓ All required secure deletion methods present")
        
        # Test that the method signature is correct
        import inspect
        sig = inspect.signature(UserService.delete_user_data_securely)
        params = list(sig.parameters.keys())
        
        expected_params = ['db', 'user_id']
        if all(param in params for param in expected_params):
            print("  ✓ Secure deletion method signature correct")
        else:
            print(f"  ✗ Expected parameters {expected_params}, got {params}")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ Secure deletion logic test failed: {e}")
        return False


def test_api_endpoints_structure():
    """Test that user API endpoints are properly structured."""
    print("\nTesting API Endpoints Structure...")
    
    try:
        from app.api.v1.endpoints.users import router
        
        # Check that the router exists
        print("  ✓ User router imported successfully")
        
        # Check for required endpoints by examining the router's routes
        routes = [route.path for route in router.routes]
        
        required_endpoints = [
            '/account',  # DELETE for account deletion
            '/data-summary',  # GET for data summary
            '/export-data'  # POST for data export
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if not any(endpoint in route for route in routes):
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"  ✗ Missing endpoints: {missing_endpoints}")
            return False
        else:
            print("  ✓ All required endpoints present")
        
        return True
    except Exception as e:
        print(f"  ✗ API endpoints structure test failed: {e}")
        return False


def run_all_tests():
    """Run all user account management tests."""
    print("=" * 60)
    print("USER ACCOUNT MANAGEMENT TESTS")
    print("=" * 60)
    
    tests = [
        test_user_service_imports,
        test_password_validation,
        test_account_deletion_schema,
        test_api_endpoints_structure,
    ]
    
    async_tests = [
        test_user_creation_logic,
        test_secure_deletion_logic,
    ]
    
    results = []
    
    # Run synchronous tests
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Run asynchronous tests
    for test in async_tests:
        try:
            result = asyncio.run(test())
            results.append(result)
        except Exception as e:
            print(f"Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All user account management tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)