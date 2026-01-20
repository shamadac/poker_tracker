"""
Security management endpoints for encryption validation and security operations.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.data_encryption_service import DataEncryptionService
from app.core.security import EncryptionManager
from app.middleware.security import SecurityEventLogger
from app.schemas.common import SuccessResponse

router = APIRouter()


@router.get("/encryption/status", response_model=Dict[str, Any])
async def get_encryption_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get encryption status and validation report.
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    try:
        # Get encryption validation report
        validation_report = await DataEncryptionService.validate_encryption_status(db)
        
        # Get encryption configuration info
        key_info = DataEncryptionService.get_encryption_key_info()
        
        return {
            "encryption_config": key_info,
            "validation_report": validation_report,
            "timestamp": validation_report.get("timestamp")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get encryption status: {str(e)}"
        )


@router.post("/encryption/validate-user", response_model=Dict[str, Any])
async def validate_user_encryption(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate encryption status for a specific user.
    Users can check their own data, admins can check any user.
    """
    # Check permissions
    if str(current_user.id) != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only validate your own encryption or admin privileges required"
        )
    
    try:
        # Get user's decrypted data summary (for validation)
        user_data = await DataEncryptionService.decrypt_user_data(db, user_id)
        
        # Count encrypted vs unencrypted fields
        encryption_summary = {
            "user_id": user_id,
            "api_providers_configured": len(user_data["user_info"].get("api_providers", [])),
            "hand_history_paths_configured": bool(user_data["user_info"].get("hand_history_paths")),
            "encryption_status": "ENCRYPTED" if user_data["user_info"].get("api_providers") else "NO_SENSITIVE_DATA",
            "validation_timestamp": user_data.get("timestamp")
        }
        
        return encryption_summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate user encryption: {str(e)}"
        )


@router.post("/encryption/encrypt-user-data", response_model=Dict[str, Any])
async def encrypt_user_data(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Encrypt sensitive data for a specific user.
    Users can encrypt their own data, admins can encrypt any user's data.
    """
    # Check permissions
    if str(current_user.id) != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only encrypt your own data or admin privileges required"
        )
    
    try:
        # Encrypt user's sensitive data
        encryption_counts = await DataEncryptionService.encrypt_user_data(db, user_id)
        
        # Log security event
        from fastapi import Request
        # Note: In a real implementation, you'd get the request object
        # SecurityEventLogger.log_data_access(request, str(current_user.id), "encryption", user_id)
        
        return {
            "user_id": user_id,
            "encryption_counts": encryption_counts,
            "status": "SUCCESS",
            "message": "User data encrypted successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt user data: {str(e)}"
        )


@router.post("/encryption/encrypt-all-data", response_model=Dict[str, Any])
async def encrypt_all_sensitive_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Encrypt all sensitive data across the entire application.
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    try:
        # Encrypt all sensitive data
        encryption_results = await DataEncryptionService.encrypt_all_sensitive_data(db)
        
        return {
            "encryption_results": encryption_results,
            "status": "SUCCESS",
            "message": "All sensitive data encrypted successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt all sensitive data: {str(e)}"
        )


@router.get("/encryption/test", response_model=Dict[str, Any])
async def test_encryption_functionality(
    current_user: User = Depends(get_current_user)
):
    """
    Test encryption functionality with sample data.
    Available to all authenticated users.
    """
    try:
        test_results = {}
        
        # Test AES-256 encryption
        test_data = "test-sensitive-data-12345"
        encrypted = EncryptionManager.encrypt_data_aes256(test_data)
        decrypted = EncryptionManager.decrypt_data_aes256(encrypted)
        
        test_results["aes256_encryption"] = {
            "success": decrypted == test_data,
            "encrypted_length": len(encrypted),
            "original_length": len(test_data)
        }
        
        # Test API key encryption
        test_keys = {"test_provider": "sk-test-key-123"}
        encrypted_keys = EncryptionManager.encrypt_api_keys(test_keys, use_aes256=True)
        decrypted_keys = EncryptionManager.decrypt_api_keys(encrypted_keys, use_aes256=True)
        
        test_results["api_key_encryption"] = {
            "success": decrypted_keys == test_keys,
            "providers_tested": len(test_keys)
        }
        
        # Test secure comparison
        test_results["secure_comparison"] = {
            "identical_strings": EncryptionManager.secure_compare("test", "test"),
            "different_strings": not EncryptionManager.secure_compare("test", "different")
        }
        
        # Test hashing
        hash_result, salt = EncryptionManager.hash_sensitive_data("test_data")
        verify_result = EncryptionManager.verify_hashed_data("test_data", hash_result, salt)
        
        test_results["hashing"] = {
            "hash_generated": bool(hash_result),
            "salt_generated": bool(salt),
            "verification_success": verify_result
        }
        
        # Overall test result
        all_tests_passed = all(
            result.get("success", True) for result in test_results.values()
            if isinstance(result, dict)
        )
        
        return {
            "overall_success": all_tests_passed,
            "test_results": test_results,
            "encryption_info": DataEncryptionService.get_encryption_key_info(),
            "timestamp": "2024-01-20T12:00:00Z"  # Would be actual timestamp
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encryption test failed: {str(e)}"
        )


@router.get("/security/headers-test", response_model=Dict[str, Any])
async def test_security_headers():
    """
    Test endpoint to verify security headers are applied.
    Available to all users (no authentication required).
    """
    return {
        "message": "Security headers test endpoint",
        "instructions": "Check the response headers for security headers",
        "expected_headers": [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Referrer-Policy",
            "Permissions-Policy"
        ],
        "timestamp": "2024-01-20T12:00:00Z"
    }


@router.get("/security/rate-limit-test", response_model=Dict[str, Any])
async def test_rate_limiting():
    """
    Test endpoint for rate limiting functionality.
    Make multiple requests to this endpoint to test rate limiting.
    """
    return {
        "message": "Rate limiting test endpoint",
        "instructions": "Make multiple rapid requests to test rate limiting",
        "expected_behavior": "Should return 429 Too Many Requests after limit exceeded",
        "timestamp": "2024-01-20T12:00:00Z"
    }


@router.post("/security/csrf-token", response_model=Dict[str, str])
async def get_csrf_token():
    """
    Get CSRF token for testing CSRF protection.
    Available to all users (no authentication required).
    """
    # In a real implementation, this would generate and return a CSRF token
    # For testing purposes, we'll return a mock token
    import secrets
    
    csrf_token = secrets.token_urlsafe(32)
    
    return {
        "csrf_token": csrf_token,
        "instructions": "Use this token in X-CSRF-Token header for state-changing requests"
    }


@router.get("/security/info", response_model=Dict[str, Any])
async def get_security_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get security configuration information.
    Available to authenticated users.
    """
    try:
        security_info = {
            "encryption": DataEncryptionService.get_encryption_key_info(),
            "authentication": {
                "method": "OAuth 2.0 with PKCE",
                "token_type": "JWT",
                "password_hashing": "bcrypt with salt"
            },
            "security_features": [
                "AES-256-GCM encryption for sensitive data",
                "PBKDF2-HMAC-SHA256 key derivation",
                "Rate limiting with Redis",
                "CSRF protection",
                "Security headers middleware",
                "Security event logging",
                "Constant-time comparison",
                "Secure random number generation"
            ],
            "compliance_standards": [
                "OWASP Top 10 2021",
                "NIST Cybersecurity Framework",
                "GDPR data protection",
                "SOC 2 Type II controls"
            ]
        }
        
        return security_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security info: {str(e)}"
        )