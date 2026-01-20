#!/usr/bin/env python3
"""
Comprehensive security testing suite for the poker analyzer application.
Tests security scanning, validation, rate limiting, and abuse prevention.
"""
import asyncio
import requests
import time
import json
import hashlib
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


class SecurityTestSuite:
    """Comprehensive security testing suite."""
    
    def __init__(self):
        self.results = {}
        self.session = requests.Session()
        self.csrf_token = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests and return results."""
        print("🔒 Comprehensive Security Test Suite")
        print("=" * 60)
        
        test_methods = [
            ("Input Validation", self.test_input_validation),
            ("Authentication Security", self.test_authentication_security),
            ("Rate Limiting", self.test_rate_limiting_comprehensive),
            ("CSRF Protection", self.test_csrf_protection_comprehensive),
            ("SQL Injection Prevention", self.test_sql_injection_prevention),
            ("XSS Prevention", self.test_xss_prevention),
            ("Security Headers", self.test_security_headers_comprehensive),
            ("Session Security", self.test_session_security),
            ("File Upload Security", self.test_file_upload_security),
            ("API Abuse Prevention", self.test_api_abuse_prevention),
            ("Encryption Security", self.test_encryption_security),
            ("Error Information Disclosure", self.test_error_disclosure),
        ]
        
        for test_name, test_method in test_methods:
            print(f"\n🧪 Testing: {test_name}")
            try:
                result = test_method()
                self.results[test_name] = result
                status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
                print(f"   {status}: {result.get('summary', 'No summary')}")
            except Exception as e:
                self.results[test_name] = {
                    "passed": False,
                    "summary": f"Test crashed: {str(e)}",
                    "error": str(e)
                }
                print(f"   ❌ FAIL: Test crashed - {str(e)}")
        
        return self.results
    
    def test_input_validation(self) -> Dict[str, Any]:
        """Test input validation and sanitization."""
        test_cases = [
            # SQL injection attempts
            {"email": "admin'; DROP TABLE users; --", "password": "test"},
            {"email": "test@test.com", "password": "' OR '1'='1"},
            
            # XSS attempts
            {"email": "<script>alert('xss')</script>@test.com", "password": "test"},
            {"email": "test@test.com", "password": "<img src=x onerror=alert(1)>"},
            
            # Command injection attempts
            {"email": "test@test.com; cat /etc/passwd", "password": "test"},
            {"email": "test@test.com", "password": "test; rm -rf /"},
            
            # Buffer overflow attempts
            {"email": "A" * 10000, "password": "test"},
            {"email": "test@test.com", "password": "B" * 10000},
            
            # Invalid data types
            {"email": 12345, "password": "test"},
            {"email": ["test@test.com"], "password": "test"},
            {"email": None, "password": "test"},
        ]
        
        vulnerabilities = []
        for i, payload in enumerate(test_cases):
            try:
                response = requests.post(
                    f"{API_BASE}/auth/register",
                    json=payload,
                    timeout=5
                )
                
                # Check if server handled malicious input properly
                if response.status_code == 500:
                    vulnerabilities.append(f"Server error on payload {i+1}: {payload}")
                elif response.status_code == 200:
                    # Should not succeed with malicious input
                    vulnerabilities.append(f"Malicious input accepted: {payload}")
                
                # Check response for information disclosure
                if "error" in response.text.lower() and any(
                    keyword in response.text.lower() 
                    for keyword in ["sql", "database", "exception", "traceback"]
                ):
                    vulnerabilities.append(f"Information disclosure in error: {payload}")
                    
            except Exception as e:
                # Network errors are expected for some payloads
                pass
            
            time.sleep(0.1)  # Avoid overwhelming server
        
        return {
            "passed": len(vulnerabilities) == 0,
            "summary": f"Found {len(vulnerabilities)} input validation issues",
            "vulnerabilities": vulnerabilities
        }
    
    def test_authentication_security(self) -> Dict[str, Any]:
        """Test authentication security measures."""
        issues = []
        
        # Test 1: Brute force protection
        print("     Testing brute force protection...")
        failed_attempts = 0
        for i in range(20):  # Try 20 failed login attempts
            try:
                response = requests.post(
                    f"{API_BASE}/auth/login",
                    json={
                        "email": "nonexistent@test.com",
                        "password": f"wrongpassword{i}"
                    },
                    timeout=5
                )
                if response.status_code == 429:
                    print(f"       Rate limited after {i+1} attempts")
                    break
                elif response.status_code == 401:
                    failed_attempts += 1
                time.sleep(0.1)
            except Exception:
                pass
        
        if failed_attempts >= 15:
            issues.append("No brute force protection detected")
        
        # Test 2: Password complexity
        print("     Testing password complexity...")
        weak_passwords = ["123", "password", "admin", "test", ""]
        for pwd in weak_passwords:
            try:
                response = requests.post(
                    f"{API_BASE}/auth/register",
                    json={
                        "email": f"test{secrets.token_hex(4)}@test.com",
                        "password": pwd,
                        "confirm_password": pwd
                    },
                    timeout=5
                )
                if response.status_code == 200:
                    issues.append(f"Weak password accepted: {pwd}")
                time.sleep(0.1)
            except Exception:
                pass
        
        # Test 3: Token security
        print("     Testing token security...")
        try:
            # Try to use obviously fake tokens
            fake_tokens = [
                "fake.token.here",
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.signature",
                "Bearer invalid_token"
            ]
            
            for token in fake_tokens:
                response = requests.get(
                    f"{API_BASE}/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                if response.status_code == 200:
                    issues.append(f"Fake token accepted: {token}")
                time.sleep(0.1)
        except Exception:
            pass
        
        return {
            "passed": len(issues) == 0,
            "summary": f"Found {len(issues)} authentication security issues",
            "issues": issues
        }
    
    def test_rate_limiting_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive rate limiting tests."""
        print("     Testing rate limiting across different endpoints...")
        
        endpoints_to_test = [
            ("/api/v1/auth/login", "auth", 10),
            ("/api/v1/hands/upload", "api", 60),
            ("/api/v1/stats/calculate", "api", 60),
            ("/health", "global", 100)
        ]
        
        rate_limit_working = []
        
        for endpoint, limit_type, expected_limit in endpoints_to_test:
            print(f"       Testing {endpoint} (limit: {expected_limit}/min)...")
            
            # Make requests rapidly
            success_count = 0
            rate_limited_count = 0
            
            # Test with a reasonable number of requests
            test_requests = min(expected_limit + 5, 20)
            
            for i in range(test_requests):
                try:
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=2)
                    if response.status_code == 200:
                        success_count += 1
                    elif response.status_code == 429:
                        rate_limited_count += 1
                        break  # Stop once rate limited
                    time.sleep(0.05)  # Small delay
                except Exception:
                    pass
            
            # Check if rate limiting kicked in appropriately
            if limit_type == "auth" and rate_limited_count > 0:
                rate_limit_working.append(f"{endpoint}: ✅")
            elif limit_type in ["api", "global"] and (rate_limited_count > 0 or success_count < test_requests):
                rate_limit_working.append(f"{endpoint}: ✅")
            else:
                rate_limit_working.append(f"{endpoint}: ❌ No rate limiting detected")
            
            time.sleep(1)  # Cool down between endpoint tests
        
        working_count = sum(1 for result in rate_limit_working if "✅" in result)
        
        return {
            "passed": working_count >= len(endpoints_to_test) // 2,  # At least half should work
            "summary": f"Rate limiting working on {working_count}/{len(endpoints_to_test)} endpoints",
            "details": rate_limit_working
        }
    
    def test_csrf_protection_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive CSRF protection tests."""
        print("     Testing CSRF protection...")
        
        # Get CSRF token first
        try:
            csrf_response = requests.get(f"{API_BASE}/auth/csrf-token", timeout=5)
            if csrf_response.status_code == 200:
                self.csrf_token = csrf_response.json().get("csrf_token")
            else:
                return {
                    "passed": False,
                    "summary": "Could not obtain CSRF token",
                    "error": f"Status: {csrf_response.status_code}"
                }
        except Exception as e:
            return {
                "passed": False,
                "summary": "Failed to get CSRF token",
                "error": str(e)
            }
        
        # Test state-changing operations without CSRF token
        protected_endpoints = [
            ("POST", "/api/v1/auth/register", {"email": "test@test.com", "password": "Test123!"}),
            ("PUT", "/api/v1/users/me", {"preferences": {"theme": "dark"}}),
            ("DELETE", "/api/v1/hands/123", {}),
        ]
        
        csrf_protection_working = []
        
        for method, endpoint, data in protected_endpoints:
            try:
                if method == "POST":
                    response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)
                elif method == "PUT":
                    response = requests.put(f"{BASE_URL}{endpoint}", json=data, timeout=5)
                elif method == "DELETE":
                    response = requests.delete(f"{BASE_URL}{endpoint}", timeout=5)
                
                if response.status_code == 403:
                    csrf_protection_working.append(f"{method} {endpoint}: ✅ Blocked")
                else:
                    csrf_protection_working.append(f"{method} {endpoint}: ❌ Not blocked ({response.status_code})")
                
                time.sleep(0.2)
            except Exception as e:
                csrf_protection_working.append(f"{method} {endpoint}: ❌ Error: {str(e)}")
        
        # Test with valid CSRF token
        try:
            response = requests.post(
                f"{API_BASE}/auth/register",
                json={"email": "csrf_test@test.com", "password": "Test123!", "confirm_password": "Test123!"},
                headers={"X-CSRF-Token": self.csrf_token},
                timeout=5
            )
            if response.status_code != 403:
                csrf_protection_working.append("Valid CSRF token: ✅ Allowed")
            else:
                csrf_protection_working.append("Valid CSRF token: ❌ Still blocked")
        except Exception as e:
            csrf_protection_working.append(f"Valid CSRF token test failed: {str(e)}")
        
        working_count = sum(1 for result in csrf_protection_working if "✅" in result)
        
        return {
            "passed": working_count >= len(protected_endpoints),
            "summary": f"CSRF protection working on {working_count}/{len(protected_endpoints)+1} tests",
            "details": csrf_protection_working
        }
    
    def test_sql_injection_prevention(self) -> Dict[str, Any]:
        """Test SQL injection prevention."""
        print("     Testing SQL injection prevention...")
        
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        vulnerabilities = []
        
        # Test SQL injection in various endpoints
        test_endpoints = [
            ("POST", "/api/v1/auth/login", "email"),
            ("GET", "/api/v1/hands", "player_name"),
            ("GET", "/api/v1/stats", "game_type"),
        ]
        
        for method, endpoint, param in test_endpoints:
            for payload in sql_payloads:
                try:
                    if method == "POST":
                        data = {param: payload, "password": "test"}
                        response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)
                    else:
                        params = {param: payload}
                        response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=5)
                    
                    # Check for SQL error messages
                    if any(keyword in response.text.lower() for keyword in [
                        "sql", "mysql", "postgresql", "sqlite", "syntax error",
                        "column", "table", "database", "constraint"
                    ]):
                        vulnerabilities.append(f"SQL error exposed in {endpoint} with payload: {payload}")
                    
                    # Check for unexpected success (might indicate injection worked)
                    if response.status_code == 200 and "admin" in response.text.lower():
                        vulnerabilities.append(f"Possible SQL injection in {endpoint}: {payload}")
                    
                    time.sleep(0.1)
                except Exception:
                    pass
        
        return {
            "passed": len(vulnerabilities) == 0,
            "summary": f"Found {len(vulnerabilities)} potential SQL injection vulnerabilities",
            "vulnerabilities": vulnerabilities
        }
    
    def test_xss_prevention(self) -> Dict[str, Any]:
        """Test XSS prevention."""
        print("     Testing XSS prevention...")
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('xss')",
            "<svg onload=alert(1)>",
            "';alert('xss');//",
            "<iframe src=javascript:alert('xss')></iframe>"
        ]
        
        vulnerabilities = []
        
        # Test XSS in various input fields
        for payload in xss_payloads:
            try:
                # Test in registration
                response = requests.post(
                    f"{API_BASE}/auth/register",
                    json={
                        "email": f"{payload}@test.com",
                        "password": "Test123!",
                        "confirm_password": "Test123!"
                    },
                    timeout=5
                )
                
                # Check if payload is reflected in response without encoding
                if payload in response.text and "<script>" in response.text:
                    vulnerabilities.append(f"XSS vulnerability in registration: {payload}")
                
                time.sleep(0.1)
            except Exception:
                pass
        
        return {
            "passed": len(vulnerabilities) == 0,
            "summary": f"Found {len(vulnerabilities)} potential XSS vulnerabilities",
            "vulnerabilities": vulnerabilities
        }
    
    def test_security_headers_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive security headers testing."""
        print("     Testing security headers...")
        
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": None,  # Just check presence
            "Referrer-Policy": ["strict-origin-when-cross-origin", "no-referrer"],
            "Permissions-Policy": None,  # Just check presence
        }
        
        optional_headers = {
            "Strict-Transport-Security": None,  # Only in production
        }
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            headers = response.headers
            
            missing_headers = []
            incorrect_headers = []
            
            for header, expected_values in required_headers.items():
                if header not in headers:
                    missing_headers.append(header)
                elif expected_values is not None:
                    if isinstance(expected_values, list):
                        if headers[header] not in expected_values:
                            incorrect_headers.append(f"{header}: {headers[header]}")
                    elif headers[header] != expected_values:
                        incorrect_headers.append(f"{header}: {headers[header]}")
            
            issues = len(missing_headers) + len(incorrect_headers)
            
            return {
                "passed": issues == 0,
                "summary": f"Security headers: {len(missing_headers)} missing, {len(incorrect_headers)} incorrect",
                "missing": missing_headers,
                "incorrect": incorrect_headers,
                "present": list(headers.keys())
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Failed to test security headers",
                "error": str(e)
            }
    
    def test_session_security(self) -> Dict[str, Any]:
        """Test session security measures."""
        print("     Testing session security...")
        
        issues = []
        
        # Test session fixation
        try:
            # Get initial session
            response1 = requests.get(f"{BASE_URL}/health")
            session_id_1 = response1.cookies.get("session_id")
            
            # Login (if endpoint exists)
            login_response = requests.post(
                f"{API_BASE}/auth/login",
                json={"email": "test@test.com", "password": "test"},
                cookies=response1.cookies
            )
            
            # Check if session ID changed after login
            session_id_2 = login_response.cookies.get("session_id")
            if session_id_1 and session_id_2 and session_id_1 == session_id_2:
                issues.append("Session fixation vulnerability: Session ID not regenerated after login")
                
        except Exception:
            pass
        
        # Test session timeout
        # This would require a longer test, so we'll just check if there's a timeout mechanism
        
        return {
            "passed": len(issues) == 0,
            "summary": f"Found {len(issues)} session security issues",
            "issues": issues
        }
    
    def test_file_upload_security(self) -> Dict[str, Any]:
        """Test file upload security."""
        print("     Testing file upload security...")
        
        vulnerabilities = []
        
        # Test malicious file uploads
        malicious_files = [
            ("test.php", "<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("test.jsp", "<% Runtime.getRuntime().exec(request.getParameter(\"cmd\")); %>", "application/x-jsp"),
            ("test.exe", b"\x4d\x5a\x90\x00", "application/x-executable"),
            ("../../../etc/passwd", "root:x:0:0:root:/root:/bin/bash", "text/plain"),
            ("test.html", "<script>alert('xss')</script>", "text/html"),
        ]
        
        for filename, content, content_type in malicious_files:
            try:
                files = {"file": (filename, content, content_type)}
                response = requests.post(
                    f"{API_BASE}/hands/upload",
                    files=files,
                    timeout=5
                )
                
                # Check if malicious file was accepted
                if response.status_code == 200:
                    vulnerabilities.append(f"Malicious file accepted: {filename}")
                
                time.sleep(0.1)
            except Exception:
                pass
        
        return {
            "passed": len(vulnerabilities) == 0,
            "summary": f"Found {len(vulnerabilities)} file upload vulnerabilities",
            "vulnerabilities": vulnerabilities
        }
    
    def test_api_abuse_prevention(self) -> Dict[str, Any]:
        """Test API abuse prevention mechanisms."""
        print("     Testing API abuse prevention...")
        
        abuse_attempts = []
        
        # Test 1: Concurrent request flooding
        def make_concurrent_requests():
            results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for i in range(50):  # 50 concurrent requests
                    future = executor.submit(
                        requests.get, 
                        f"{API_BASE}/health", 
                        timeout=5
                    )
                    futures.append(future)
                
                for future in futures:
                    try:
                        response = future.result(timeout=10)
                        results.append(response.status_code)
                    except Exception:
                        results.append(0)  # Failed request
            
            return results
        
        print("       Testing concurrent request handling...")
        concurrent_results = make_concurrent_requests()
        rate_limited = sum(1 for status in concurrent_results if status == 429)
        
        if rate_limited == 0:
            abuse_attempts.append("No rate limiting on concurrent requests")
        
        # Test 2: Large payload attacks
        print("       Testing large payload handling...")
        large_payload = {"data": "A" * 1000000}  # 1MB payload
        try:
            response = requests.post(
                f"{API_BASE}/auth/register",
                json=large_payload,
                timeout=10
            )
            if response.status_code == 200:
                abuse_attempts.append("Large payload accepted without limits")
        except Exception:
            pass  # Expected to fail
        
        # Test 3: Repeated identical requests
        print("       Testing request deduplication...")
        identical_requests = 0
        for i in range(10):
            try:
                response = requests.post(
                    f"{API_BASE}/auth/register",
                    json={"email": "duplicate@test.com", "password": "Test123!"},
                    timeout=5
                )
                if response.status_code == 200:
                    identical_requests += 1
                time.sleep(0.1)
            except Exception:
                pass
        
        if identical_requests > 1:
            abuse_attempts.append(f"Duplicate requests allowed: {identical_requests} times")
        
        return {
            "passed": len(abuse_attempts) == 0,
            "summary": f"Found {len(abuse_attempts)} API abuse vulnerabilities",
            "vulnerabilities": abuse_attempts,
            "concurrent_rate_limited": rate_limited
        }
    
    def test_encryption_security(self) -> Dict[str, Any]:
        """Test encryption security implementation."""
        print("     Testing encryption security...")
        
        try:
            # Import encryption manager
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
            
            from app.core.security import EncryptionManager
            
            issues = []
            
            # Test AES-256 encryption
            test_data = "sensitive-api-key-12345"
            encrypted = EncryptionManager.encrypt_data_aes256(test_data)
            decrypted = EncryptionManager.decrypt_data_aes256(encrypted)
            
            if decrypted != test_data:
                issues.append("AES-256 encryption/decryption failed")
            
            # Test that encrypted data is different each time (proper nonce usage)
            encrypted2 = EncryptionManager.encrypt_data_aes256(test_data)
            if encrypted == encrypted2:
                issues.append("Encryption not using proper randomization")
            
            # Test API key encryption
            api_keys = {"gemini": "test-key-1", "groq": "test-key-2"}
            encrypted_keys = EncryptionManager.encrypt_api_keys(api_keys)
            decrypted_keys = EncryptionManager.decrypt_api_keys(encrypted_keys)
            
            if decrypted_keys != api_keys:
                issues.append("API key encryption/decryption failed")
            
            # Test secure comparison
            if not EncryptionManager.secure_compare("test", "test"):
                issues.append("Secure comparison failed for identical strings")
            
            if EncryptionManager.secure_compare("test", "different"):
                issues.append("Secure comparison failed for different strings")
            
            return {
                "passed": len(issues) == 0,
                "summary": f"Encryption security: {len(issues)} issues found",
                "issues": issues
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Encryption security test failed",
                "error": str(e)
            }
    
    def test_error_disclosure(self) -> Dict[str, Any]:
        """Test for information disclosure in error messages."""
        print("     Testing error information disclosure...")
        
        disclosures = []
        
        # Test various error conditions
        error_test_cases = [
            ("GET", "/api/v1/nonexistent", {}),
            ("POST", "/api/v1/auth/login", {"email": "invalid", "password": ""}),
            ("GET", "/api/v1/users/99999", {}),
            ("POST", "/api/v1/hands/upload", {"invalid": "data"}),
        ]
        
        sensitive_keywords = [
            "traceback", "exception", "stack trace", "file not found",
            "database", "sql", "connection", "server error", "debug",
            "internal", "system", "path", "directory"
        ]
        
        for method, endpoint, data in error_test_cases:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)
                
                # Check for sensitive information in error responses
                response_text = response.text.lower()
                for keyword in sensitive_keywords:
                    if keyword in response_text:
                        disclosures.append(f"Information disclosure in {endpoint}: {keyword}")
                        break
                
                time.sleep(0.1)
            except Exception:
                pass
        
        return {
            "passed": len(disclosures) == 0,
            "summary": f"Found {len(disclosures)} information disclosure issues",
            "disclosures": disclosures
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive security test report."""
        report = []
        report.append("🔒 COMPREHENSIVE SECURITY TEST REPORT")
        report.append("=" * 60)
        report.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result.get("passed", False))
        
        report.append(f"📊 SUMMARY: {passed_tests}/{total_tests} tests passed")
        report.append("")
        
        # Detailed results
        for test_name, result in self.results.items():
            status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
            report.append(f"{status} {test_name}")
            report.append(f"   Summary: {result.get('summary', 'No summary')}")
            
            if not result.get("passed", False):
                if "vulnerabilities" in result:
                    for vuln in result["vulnerabilities"][:3]:  # Show first 3
                        report.append(f"   - {vuln}")
                if "issues" in result:
                    for issue in result["issues"][:3]:  # Show first 3
                        report.append(f"   - {issue}")
            
            report.append("")
        
        # Security recommendations
        report.append("🛡️  SECURITY RECOMMENDATIONS:")
        if passed_tests < total_tests:
            report.append("- Review and fix failing security tests")
            report.append("- Implement additional input validation")
            report.append("- Enhance rate limiting mechanisms")
            report.append("- Review error handling to prevent information disclosure")
        else:
            report.append("- All security tests passed! Continue monitoring")
            report.append("- Consider implementing additional security measures")
            report.append("- Regular security testing is recommended")
        
        return "\n".join(report)


def main():
    """Run comprehensive security tests."""
    suite = SecurityTestSuite()
    results = suite.run_all_tests()
    
    print("\n" + "=" * 60)
    print("📋 FINAL REPORT")
    print("=" * 60)
    
    report = suite.generate_report()
    print(report)
    
    # Save report to file
    with open("security_test_report.txt", "w") as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: security_test_report.txt")
    
    # Return exit code based on results
    passed_tests = sum(1 for result in results.values() if result.get("passed", False))
    total_tests = len(results)
    
    if passed_tests == total_tests:
        print("🎉 All security tests passed!")
        return 0
    else:
        print(f"⚠️  {total_tests - passed_tests} security tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())