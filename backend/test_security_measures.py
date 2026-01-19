#!/usr/bin/env python3
"""
Test script for security measures implementation.
Tests rate limiting, CSRF protection, security event logging, and AES-256 encryption.
"""
import asyncio
import requests
import time
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


def test_rate_limiting():
    """Test rate limiting functionality."""
    print("Testing Rate Limiting...")
    
    # Make rapid requests to trigger rate limiting
    auth_url = f"{API_BASE}/auth/test"
    
    success_count = 0
    rate_limited_count = 0
    
    for i in range(15):  # Try 15 requests (limit is 10 per minute for auth endpoints)
        try:
            response = requests.get(auth_url, timeout=5)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"  ✓ Rate limit triggered on request {i+1}")
            time.sleep(0.1)  # Small delay between requests
        except Exception as e:
            print(f"  ✗ Request failed: {e}")
    
    print(f"  Successful requests: {success_count}")
    print(f"  Rate limited requests: {rate_limited_count}")
    
    if rate_limited_count > 0:
        print("  ✓ Rate limiting is working!")
        return True
    else:
        print("  ⚠ Rate limiting may not be working (Redis might be unavailable)")
        return False


def test_csrf_protection():
    """Test CSRF protection functionality."""
    print("\nTesting CSRF Protection...")
    
    # First, get a CSRF token
    try:
        csrf_response = requests.get(f"{API_BASE}/auth/csrf-token", timeout=5)
        if csrf_response.status_code == 200:
            csrf_token = csrf_response.json().get("csrf_token")
            print(f"  ✓ CSRF token obtained: {csrf_token[:20]}...")
        else:
            print(f"  ✗ Failed to get CSRF token: {csrf_response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Failed to get CSRF token: {e}")
        return False
    
    # Test POST request without CSRF token (should fail)
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "confirm_password": "TestPassword123!"
            },
            timeout=5
        )
        if response.status_code == 403:
            print("  ✓ POST request without CSRF token was blocked")
        else:
            print(f"  ⚠ POST request without CSRF token returned: {response.status_code}")
    except Exception as e:
        print(f"  ✗ CSRF test failed: {e}")
        return False
    
    # Test POST request with CSRF token (should work or fail for other reasons)
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json={
                "email": "test@example.com", 
                "password": "TestPassword123!",
                "confirm_password": "TestPassword123!"
            },
            headers={"X-CSRF-Token": csrf_token},
            timeout=5
        )
        if response.status_code != 403:
            print("  ✓ POST request with CSRF token was allowed")
            return True
        else:
            print("  ✗ POST request with CSRF token was still blocked")
            return False
    except Exception as e:
        print(f"  ✗ CSRF test with token failed: {e}")
        return False


def test_security_headers():
    """Test security headers in responses."""
    print("\nTesting Security Headers...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        headers = response.headers
        
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": True,  # Just check if present
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        all_present = True
        for header, expected_value in security_headers.items():
            if header in headers:
                if expected_value is True or headers[header] == expected_value:
                    print(f"  ✓ {header}: {headers[header]}")
                else:
                    print(f"  ✗ {header}: Expected '{expected_value}', got '{headers[header]}'")
                    all_present = False
            else:
                print(f"  ✗ Missing header: {header}")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"  ✗ Security headers test failed: {e}")
        return False


def test_aes256_encryption():
    """Test AES-256 encryption functionality."""
    print("\nTesting AES-256 Encryption...")
    
    try:
        # Import the encryption manager
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
        
        from app.core.security import EncryptionManager
        
        # Test data
        test_data = "sk-test-api-key-1234567890abcdef"
        
        # Test AES-256 encryption
        encrypted = EncryptionManager.encrypt_data_aes256(test_data)
        print(f"  ✓ Data encrypted (length: {len(encrypted)})")
        
        # Test decryption
        decrypted = EncryptionManager.decrypt_data_aes256(encrypted)
        
        if decrypted == test_data:
            print("  ✓ AES-256 encryption/decryption working correctly")
            return True
        else:
            print(f"  ✗ Decryption failed: expected '{test_data}', got '{decrypted}'")
            return False
            
    except Exception as e:
        print(f"  ✗ AES-256 encryption test failed: {e}")
        return False


def test_api_endpoints():
    """Test that API endpoints are accessible."""
    print("\nTesting API Endpoints...")
    
    endpoints = [
        ("/health", "Health check"),
        ("/api/v1/auth/test", "Auth test endpoint"),
        ("/api/v1/auth/pkce/challenge", "PKCE challenge endpoint"),
        ("/api/v1/auth/csrf-token", "CSRF token endpoint")
    ]
    
    all_working = True
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"  ✓ {description}: {response.status_code}")
            else:
                print(f"  ⚠ {description}: {response.status_code}")
                all_working = False
        except Exception as e:
            print(f"  ✗ {description}: {e}")
            all_working = False
    
    return all_working


def main():
    """Run all security tests."""
    print("🔒 Security Measures Test Suite")
    print("=" * 50)
    
    tests = [
        ("API Endpoints", test_api_endpoints),
        ("Security Headers", test_security_headers),
        ("AES-256 Encryption", test_aes256_encryption),
        ("CSRF Protection", test_csrf_protection),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"  ✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All security measures are working correctly!")
        return 0
    else:
        print("⚠️  Some security measures need attention.")
        return 1


if __name__ == "__main__":
    exit(main())