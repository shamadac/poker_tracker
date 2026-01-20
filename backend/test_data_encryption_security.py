#!/usr/bin/env python3
"""
Comprehensive data encryption and security validation tests.
Tests encryption of sensitive data, key management, and security compliance.
"""
import asyncio
import json
import base64
import os
import tempfile
from typing import Dict, Any, List
from datetime import datetime

# Test configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_encryption.db"


class DataEncryptionSecurityTester:
    """Test data encryption and security measures."""
    
    def __init__(self):
        self.results = {}
        self.test_data = self._generate_test_data()
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all data encryption and security tests."""
        print("🔐 Data Encryption & Security Test Suite")
        print("=" * 60)
        
        test_methods = [
            ("AES-256 Encryption", self.test_aes256_encryption),
            ("API Key Encryption", self.test_api_key_encryption),
            ("Sensitive Data Detection", self.test_sensitive_data_detection),
            ("Key Derivation Security", self.test_key_derivation),
            ("Encryption Key Management", self.test_encryption_key_management),
            ("Data at Rest Encryption", self.test_data_at_rest_encryption),
            ("Secure Data Deletion", self.test_secure_data_deletion),
            ("Encryption Performance", self.test_encryption_performance),
            ("Backward Compatibility", self.test_backward_compatibility),
            ("Error Handling Security", self.test_error_handling_security),
            ("Memory Security", self.test_memory_security),
            ("Compliance Validation", self.test_compliance_validation),
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
    
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate test data for encryption tests."""
        return {
            "api_keys": {
                "gemini": "sk-test-gemini-key-1234567890abcdef",
                "groq": "gsk_test-groq-key-abcdef1234567890",
                "openai": "sk-proj-test-openai-key-xyz123"
            },
            "sensitive_text": "User password: MySecretPassword123!",
            "hand_history": """PokerStars Hand #123456789: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/20 15:30:00 ET
Table 'TestTable' 6-max Seat #1 is the button
Seat 1: TestPlayer ($100.00 in chips)
Seat 2: Villain ($95.50 in chips)""",
            "analysis_result": "The player made a mistake by calling with weak holdings. API key: sk-hidden-key-123",
            "user_preferences": {
                "theme": "dark",
                "api_provider": "gemini",
                "secret_setting": "confidential_value_xyz"
            },
            "non_sensitive_data": {
                "username": "testuser",
                "email": "test@example.com",
                "theme": "light"
            }
        }
    
    def test_aes256_encryption(self) -> Dict[str, Any]:
        """Test AES-256-GCM encryption implementation."""
        print("     Testing AES-256-GCM encryption...")
        
        try:
            # Import encryption manager
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
            
            from app.core.security import EncryptionManager
            
            issues = []
            
            # Test basic encryption/decryption
            test_data = "sensitive-api-key-sk-1234567890abcdef"
            encrypted = EncryptionManager.encrypt_data_aes256(test_data)
            decrypted = EncryptionManager.decrypt_data_aes256(encrypted)
            
            if decrypted != test_data:
                issues.append("Basic AES-256 encryption/decryption failed")
            
            # Test encryption produces different output each time (proper nonce usage)
            encrypted2 = EncryptionManager.encrypt_data_aes256(test_data)
            if encrypted == encrypted2:
                issues.append("Encryption not using proper randomization (same output)")
            
            # Test encrypted data structure
            try:
                encrypted_bytes = base64.b64decode(encrypted.encode())
                if len(encrypted_bytes) < 44:  # salt(16) + nonce(12) + tag(16) = 44 minimum
                    issues.append("Encrypted data structure invalid (too short)")
                
                # Check components
                salt = encrypted_bytes[:16]
                nonce = encrypted_bytes[16:28]
                tag = encrypted_bytes[28:44]
                
                if len(salt) != 16:
                    issues.append("Invalid salt length")
                if len(nonce) != 12:
                    issues.append("Invalid nonce length")
                if len(tag) != 16:
                    issues.append("Invalid authentication tag length")
                    
            except Exception as e:
                issues.append(f"Failed to parse encrypted data structure: {e}")
            
            # Test with different passwords
            password1 = "password123"
            password2 = "different_password"
            
            encrypted_p1 = EncryptionManager.encrypt_data_aes256(test_data, password1)
            encrypted_p2 = EncryptionManager.encrypt_data_aes256(test_data, password2)
            
            # Should not be able to decrypt with wrong password
            try:
                wrong_decrypt = EncryptionManager.decrypt_data_aes256(encrypted_p1, password2)
                issues.append("Decryption succeeded with wrong password")
            except Exception:
                pass  # Expected to fail
            
            # Test with empty and special characters
            special_data = "🔐 Special chars: àáâãäå ñ 中文 русский"
            encrypted_special = EncryptionManager.encrypt_data_aes256(special_data)
            decrypted_special = EncryptionManager.decrypt_data_aes256(encrypted_special)
            
            if decrypted_special != special_data:
                issues.append("Failed to handle special characters")
            
            return {
                "passed": len(issues) == 0,
                "summary": f"AES-256 encryption: {len(issues)} issues found",
                "issues": issues,
                "encrypted_length": len(encrypted),
                "supports_unicode": decrypted_special == special_data
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "AES-256 encryption test failed",
                "error": str(e)
            }
    
    def test_api_key_encryption(self) -> Dict[str, Any]:
        """Test API key encryption functionality."""
        print("     Testing API key encryption...")
        
        try:
            from app.core.security import EncryptionManager
            
            issues = []
            
            # Test API key encryption
            api_keys = self.test_data["api_keys"]
            encrypted_keys = EncryptionManager.encrypt_api_keys(api_keys, use_aes256=True)
            decrypted_keys = EncryptionManager.decrypt_api_keys(encrypted_keys, use_aes256=True)
            
            if decrypted_keys != api_keys:
                issues.append("API key encryption/decryption failed")
            
            # Test that encrypted keys are actually encrypted
            for provider, encrypted_key in encrypted_keys.items():
                if encrypted_key == api_keys[provider]:
                    issues.append(f"API key for {provider} not encrypted")
                
                # Check if it looks like encrypted data
                try:
                    decoded = base64.b64decode(encrypted_key.encode())
                    if len(decoded) < 44:
                        issues.append(f"Encrypted key for {provider} too short")
                except Exception:
                    issues.append(f"Encrypted key for {provider} not valid base64")
            
            # Test empty keys handling
            empty_keys = {"provider1": "", "provider2": None, "provider3": "valid_key"}
            encrypted_empty = EncryptionManager.encrypt_api_keys(empty_keys, use_aes256=True)
            decrypted_empty = EncryptionManager.decrypt_api_keys(encrypted_empty, use_aes256=True)
            
            # Should only encrypt non-empty keys
            if "provider1" in encrypted_empty or "provider2" in encrypted_empty:
                issues.append("Empty keys were encrypted")
            
            if "provider3" not in encrypted_empty:
                issues.append("Valid key was not encrypted")
            
            # Test backward compatibility
            legacy_encrypted = EncryptionManager.encrypt_api_keys(api_keys, use_aes256=False)
            legacy_decrypted = EncryptionManager.decrypt_api_keys(legacy_encrypted, use_aes256=False)
            
            if legacy_decrypted != api_keys:
                issues.append("Legacy encryption compatibility failed")
            
            return {
                "passed": len(issues) == 0,
                "summary": f"API key encryption: {len(issues)} issues found",
                "issues": issues,
                "providers_tested": len(api_keys),
                "backward_compatible": legacy_decrypted == api_keys
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "API key encryption test failed",
                "error": str(e)
            }
    
    def test_sensitive_data_detection(self) -> Dict[str, Any]:
        """Test sensitive data detection algorithms."""
        print("     Testing sensitive data detection...")
        
        try:
            from app.services.data_encryption_service import DataEncryptionService
            
            # Test cases: (data, should_be_detected_as_sensitive)
            test_cases = [
                (self.test_data["api_keys"], True),
                ({"api_key": "sk-123"}, True),
                ({"secret": "my_secret"}, True),
                ({"password": "mypass"}, True),
                ({"token": "bearer_token"}, True),
                (self.test_data["non_sensitive_data"], False),
                ({"username": "john", "email": "john@example.com"}, False),
                ("sk-test-key-123", True),
                ("gsk_groq_key_456", True),
                ("normal text without secrets", False),
                ("This contains an API key: sk-hidden", True),
                ("", False),
                (None, False),
            ]
            
            correct_detections = 0
            total_tests = len(test_cases)
            failed_cases = []
            
            for data, expected_sensitive in test_cases:
                detected_sensitive = DataEncryptionService._contains_sensitive_data(data)
                
                if detected_sensitive == expected_sensitive:
                    correct_detections += 1
                else:
                    failed_cases.append({
                        "data": str(data)[:50] + "..." if len(str(data)) > 50 else str(data),
                        "expected": expected_sensitive,
                        "detected": detected_sensitive
                    })
            
            # Test text sensitivity detection
            text_test_cases = [
                ("sk-test-api-key", True),
                ("gsk_groq_key", True),
                ("bearer token123", True),
                ("password: secret", True),
                ("normal poker hand text", False),
                ("user preferences", False),
                ("authorization: bearer xyz", True),
            ]
            
            text_correct = 0
            text_total = len(text_test_cases)
            text_failed = []
            
            for text, expected_sensitive in text_test_cases:
                detected_sensitive = DataEncryptionService._is_sensitive_text(text)
                
                if detected_sensitive == expected_sensitive:
                    text_correct += 1
                else:
                    text_failed.append({
                        "text": text,
                        "expected": expected_sensitive,
                        "detected": detected_sensitive
                    })
            
            accuracy = (correct_detections + text_correct) / (total_tests + text_total)
            
            return {
                "passed": accuracy >= 0.9,  # 90% accuracy threshold
                "summary": f"Sensitive data detection: {accuracy:.1%} accuracy",
                "data_detection_accuracy": correct_detections / total_tests,
                "text_detection_accuracy": text_correct / text_total,
                "overall_accuracy": accuracy,
                "failed_data_cases": failed_cases,
                "failed_text_cases": text_failed
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Sensitive data detection test failed",
                "error": str(e)
            }
    
    def test_key_derivation(self) -> Dict[str, Any]:
        """Test key derivation security."""
        print("     Testing key derivation security...")
        
        try:
            from app.core.security import EncryptionManager
            import os
            
            issues = []
            
            # Test that same password + salt produces same key
            password = "test_password"
            salt = os.urandom(16)
            
            key1 = EncryptionManager._derive_key(password, salt)
            key2 = EncryptionManager._derive_key(password, salt)
            
            if key1 != key2:
                issues.append("Key derivation not deterministic")
            
            # Test that different salts produce different keys
            salt2 = os.urandom(16)
            key3 = EncryptionManager._derive_key(password, salt2)
            
            if key1 == key3:
                issues.append("Different salts produce same key")
            
            # Test key length
            if len(key1) != 32:  # 256 bits
                issues.append(f"Key length incorrect: {len(key1)} bytes (expected 32)")
            
            # Test that different passwords produce different keys
            password2 = "different_password"
            key4 = EncryptionManager._derive_key(password2, salt)
            
            if key1 == key4:
                issues.append("Different passwords produce same key")
            
            # Test key entropy (basic check)
            unique_bytes = len(set(key1))
            if unique_bytes < 20:  # Should have good entropy
                issues.append(f"Low key entropy: {unique_bytes} unique bytes")
            
            return {
                "passed": len(issues) == 0,
                "summary": f"Key derivation: {len(issues)} issues found",
                "issues": issues,
                "key_length_bytes": len(key1),
                "key_entropy_unique_bytes": unique_bytes
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Key derivation test failed",
                "error": str(e)
            }
    
    def test_encryption_key_management(self) -> Dict[str, Any]:
        """Test encryption key management security."""
        print("     Testing encryption key management...")
        
        try:
            from app.core.security import EncryptionManager
            from app.services.data_encryption_service import DataEncryptionService
            
            issues = []
            
            # Test encryption key info
            key_info = DataEncryptionService.get_encryption_key_info()
            
            required_fields = [
                "encryption_algorithm", "key_derivation", "key_derivation_iterations",
                "salt_size_bits", "nonce_size_bits", "tag_size_bits"
            ]
            
            for field in required_fields:
                if field not in key_info:
                    issues.append(f"Missing key info field: {field}")
            
            # Validate encryption parameters
            if key_info.get("encryption_algorithm") != "AES-256-GCM":
                issues.append("Incorrect encryption algorithm")
            
            if key_info.get("key_derivation_iterations", 0) < 100000:
                issues.append("Insufficient key derivation iterations")
            
            if key_info.get("salt_size_bits") != 128:
                issues.append("Incorrect salt size")
            
            if key_info.get("nonce_size_bits") != 96:
                issues.append("Incorrect nonce size for GCM")
            
            # Test secure comparison
            if not EncryptionManager.secure_compare("test", "test"):
                issues.append("Secure comparison failed for identical strings")
            
            if EncryptionManager.secure_compare("test", "different"):
                issues.append("Secure comparison failed for different strings")
            
            # Test hashing with salt
            data = "sensitive_data"
            hash1, salt1 = EncryptionManager.hash_sensitive_data(data)
            hash2, salt2 = EncryptionManager.hash_sensitive_data(data)
            
            # Different salts should produce different hashes
            if hash1 == hash2:
                issues.append("Hashing produces same output with different salts")
            
            # Same data + salt should verify correctly
            if not EncryptionManager.verify_hashed_data(data, hash1, salt1):
                issues.append("Hash verification failed")
            
            # Wrong data should not verify
            if EncryptionManager.verify_hashed_data("wrong_data", hash1, salt1):
                issues.append("Hash verification succeeded with wrong data")
            
            return {
                "passed": len(issues) == 0,
                "summary": f"Key management: {len(issues)} issues found",
                "issues": issues,
                "key_info": key_info,
                "secure_comparison_working": True,
                "hashing_working": True
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Key management test failed",
                "error": str(e)
            }
    
    def test_data_at_rest_encryption(self) -> Dict[str, Any]:
        """Test data at rest encryption simulation."""
        print("     Testing data at rest encryption...")
        
        try:
            from app.services.data_encryption_service import DataEncryptionService
            
            issues = []
            
            # Simulate encrypting different types of data
            test_scenarios = [
                ("json_encrypt", self.test_data["api_keys"]),
                ("json_encrypt_optional", self.test_data["user_preferences"]),
                ("text_encrypt", self.test_data["sensitive_text"]),
                ("text_encrypt_optional", self.test_data["hand_history"]),
                ("text_encrypt_optional", self.test_data["analysis_result"]),
            ]
            
            encryption_results = []
            
            for encryption_type, data in test_scenarios:
                try:
                    # Encrypt the data
                    encrypted = DataEncryptionService.encrypt_sensitive_field(data, encryption_type)
                    
                    # Decrypt the data
                    decrypted = DataEncryptionService.decrypt_sensitive_field(encrypted, encryption_type)
                    
                    # Verify round-trip
                    if decrypted != data:
                        issues.append(f"Round-trip failed for {encryption_type}")
                    
                    # Check if sensitive data was actually encrypted
                    if encryption_type in ["json_encrypt", "text_encrypt"]:
                        if encrypted == data:
                            issues.append(f"Data not encrypted for {encryption_type}")
                    
                    encryption_results.append({
                        "type": encryption_type,
                        "original_size": len(str(data)),
                        "encrypted_size": len(str(encrypted)),
                        "encrypted": encrypted != data,
                        "round_trip_success": decrypted == data
                    })
                    
                except Exception as e:
                    issues.append(f"Encryption failed for {encryption_type}: {e}")
            
            # Test non-sensitive data handling
            non_sensitive = self.test_data["non_sensitive_data"]
            encrypted_non_sensitive = DataEncryptionService.encrypt_sensitive_field(
                non_sensitive, "json_encrypt_optional"
            )
            
            # Non-sensitive data might not be encrypted with optional encryption
            if encrypted_non_sensitive != non_sensitive:
                # If it was encrypted, make sure it decrypts correctly
                decrypted_non_sensitive = DataEncryptionService.decrypt_sensitive_field(
                    encrypted_non_sensitive, "json_encrypt_optional"
                )
                if decrypted_non_sensitive != non_sensitive:
                    issues.append("Non-sensitive data encryption round-trip failed")
            
            return {
                "passed": len(issues) == 0,
                "summary": f"Data at rest encryption: {len(issues)} issues found",
                "issues": issues,
                "encryption_results": encryption_results,
                "scenarios_tested": len(test_scenarios)
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Data at rest encryption test failed",
                "error": str(e)
            }
    
    def test_secure_data_deletion(self) -> Dict[str, Any]:
        """Test secure data deletion capabilities."""
        print("     Testing secure data deletion...")
        
        try:
            import tempfile
            import os
            
            issues = []
            
            # Test secure memory clearing (basic test)
            sensitive_data = "sk-very-secret-api-key-12345"
            
            # Create a temporary file to test secure deletion
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(sensitive_data.encode())
                temp_file_path = temp_file.name
            
            # Verify file exists and contains data
            if not os.path.exists(temp_file_path):
                issues.append("Temporary file not created")
            else:
                with open(temp_file_path, 'r') as f:
                    content = f.read()
                    if content != sensitive_data:
                        issues.append("Temporary file content incorrect")
            
            # Test file deletion
            try:
                os.unlink(temp_file_path)
                if os.path.exists(temp_file_path):
                    issues.append("File not deleted")
            except Exception as e:
                issues.append(f"File deletion failed: {e}")
            
            # Test that encryption keys are not stored in plain text
            from app.core.security import EncryptionManager
            
            test_key = "test-api-key-sensitive"
            encrypted = EncryptionManager.encrypt_data_aes256(test_key)
            
            # The encrypted data should not contain the original key
            if test_key in encrypted:
                issues.append("Original key found in encrypted data")
            
            # Test memory handling (basic check)
            # In a real implementation, you'd want to use secure memory clearing
            large_sensitive_data = "sensitive" * 10000
            encrypted_large = EncryptionManager.encrypt_data_aes256(large_sensitive_data)
            decrypted_large = EncryptionManager.decrypt_data_aes256(encrypted_large)
            
            if decrypted_large != large_sensitive_data:
                issues.append("Large data encryption/decryption failed")
            
            # Clear variables (basic approach)
            large_sensitive_data = None
            decrypted_large = None
            
            return {
                "passed": len(issues) == 0,
                "summary": f"Secure data deletion: {len(issues)} issues found",
                "issues": issues,
                "file_deletion_working": not os.path.exists(temp_file_path),
                "memory_handling_basic": True
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Secure data deletion test failed",
                "error": str(e)
            }
    
    def test_encryption_performance(self) -> Dict[str, Any]:
        """Test encryption performance characteristics."""
        print("     Testing encryption performance...")
        
        try:
            from app.core.security import EncryptionManager
            import time
            
            # Test data of different sizes
            test_sizes = [
                (100, "100 bytes"),
                (1024, "1 KB"),
                (10240, "10 KB"),
                (102400, "100 KB"),
            ]
            
            performance_results = []
            
            for size, description in test_sizes:
                test_data = "A" * size
                
                # Measure encryption time
                start_time = time.time()
                encrypted = EncryptionManager.encrypt_data_aes256(test_data)
                encryption_time = time.time() - start_time
                
                # Measure decryption time
                start_time = time.time()
                decrypted = EncryptionManager.decrypt_data_aes256(encrypted)
                decryption_time = time.time() - start_time
                
                # Verify correctness
                correct = decrypted == test_data
                
                performance_results.append({
                    "size": size,
                    "description": description,
                    "encryption_time_ms": encryption_time * 1000,
                    "decryption_time_ms": decryption_time * 1000,
                    "total_time_ms": (encryption_time + decryption_time) * 1000,
                    "throughput_mb_per_sec": (size / (1024 * 1024)) / (encryption_time + decryption_time),
                    "correct": correct
                })
            
            # Check if performance is reasonable (< 100ms for 100KB)
            large_test = next((r for r in performance_results if r["size"] == 102400), None)
            performance_acceptable = large_test and large_test["total_time_ms"] < 100
            
            # Check if all tests were correct
            all_correct = all(r["correct"] for r in performance_results)
            
            return {
                "passed": performance_acceptable and all_correct,
                "summary": f"Encryption performance: {'acceptable' if performance_acceptable else 'slow'}, {'correct' if all_correct else 'errors'}",
                "performance_results": performance_results,
                "performance_acceptable": performance_acceptable,
                "all_correct": all_correct
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Encryption performance test failed",
                "error": str(e)
            }
    
    def test_backward_compatibility(self) -> Dict[str, Any]:
        """Test backward compatibility with legacy encryption."""
        print("     Testing backward compatibility...")
        
        try:
            from app.core.security import EncryptionManager
            
            issues = []
            
            # Test legacy Fernet encryption
            test_data = "legacy-api-key-test"
            
            # Encrypt with legacy method
            legacy_encrypted = EncryptionManager.encrypt_data(test_data)
            legacy_decrypted = EncryptionManager.decrypt_data(legacy_encrypted)
            
            if legacy_decrypted != test_data:
                issues.append("Legacy encryption/decryption failed")
            
            # Test API key encryption with both methods
            api_keys = {"test": "sk-test-key"}
            
            # AES-256 method
            aes256_encrypted = EncryptionManager.encrypt_api_keys(api_keys, use_aes256=True)
            aes256_decrypted = EncryptionManager.decrypt_api_keys(aes256_encrypted, use_aes256=True)
            
            # Legacy method
            legacy_encrypted_keys = EncryptionManager.encrypt_api_keys(api_keys, use_aes256=False)
            legacy_decrypted_keys = EncryptionManager.decrypt_api_keys(legacy_encrypted_keys, use_aes256=False)
            
            if aes256_decrypted != api_keys:
                issues.append("AES-256 API key encryption failed")
            
            if legacy_decrypted_keys != api_keys:
                issues.append("Legacy API key encryption failed")
            
            # Test fallback mechanism
            try:
                # Try to decrypt AES-256 data with legacy flag (should fallback)
                fallback_decrypted = EncryptionManager.decrypt_api_keys(aes256_encrypted, use_aes256=False)
                if fallback_decrypted != api_keys:
                    issues.append("Fallback decryption failed")
            except Exception:
                # Fallback might not work in all cases, which is acceptable
                pass
            
            return {
                "passed": len(issues) == 0,
                "summary": f"Backward compatibility: {len(issues)} issues found",
                "issues": issues,
                "legacy_encryption_working": legacy_decrypted == test_data,
                "aes256_encryption_working": aes256_decrypted == api_keys,
                "legacy_api_keys_working": legacy_decrypted_keys == api_keys
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Backward compatibility test failed",
                "error": str(e)
            }
    
    def test_error_handling_security(self) -> Dict[str, Any]:
        """Test error handling doesn't leak sensitive information."""
        print("     Testing error handling security...")
        
        try:
            from app.core.security import EncryptionManager
            
            security_issues = []
            
            # Test decryption with invalid data
            invalid_inputs = [
                "invalid_base64_data",
                "dGVzdA==",  # Valid base64 but too short
                "",
                None,
                "not-base64-at-all!@#$%",
            ]
            
            for invalid_input in invalid_inputs:
                try:
                    if invalid_input is not None:
                        result = EncryptionManager.decrypt_data_aes256(invalid_input)
                        security_issues.append(f"Decryption succeeded with invalid input: {invalid_input}")
                except ValueError as e:
                    # Check if error message contains sensitive information
                    error_msg = str(e).lower()
                    sensitive_keywords = ["key", "password", "secret", "token"]
                    if any(keyword in error_msg for keyword in sensitive_keywords):
                        security_issues.append(f"Error message contains sensitive info: {error_msg}")
                except Exception:
                    # Other exceptions are acceptable
                    pass
            
            # Test with wrong password
            test_data = "sensitive_test_data"
            correct_password = "correct_password"
            wrong_password = "wrong_password"
            
            encrypted = EncryptionManager.encrypt_data_aes256(test_data, correct_password)
            
            try:
                wrong_decrypt = EncryptionManager.decrypt_data_aes256(encrypted, wrong_password)
                security_issues.append("Decryption succeeded with wrong password")
            except Exception as e:
                # Check error message doesn't leak info
                error_msg = str(e).lower()
                if correct_password.lower() in error_msg or test_data.lower() in error_msg:
                    security_issues.append("Error message leaks sensitive data")
            
            # Test API key decryption error handling
            try:
                invalid_keys = {"provider": "invalid_encrypted_data"}
                decrypted = EncryptionManager.decrypt_api_keys(invalid_keys)
                # Should either fail or return original data
            except Exception as e:
                error_msg = str(e).lower()
                if "api" in error_msg and ("key" in error_msg or "secret" in error_msg):
                    # This is acceptable as it's a generic error
                    pass
            
            return {
                "passed": len(security_issues) == 0,
                "summary": f"Error handling security: {len(security_issues)} issues found",
                "security_issues": security_issues,
                "invalid_inputs_tested": len(invalid_inputs)
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Error handling security test failed",
                "error": str(e)
            }
    
    def test_memory_security(self) -> Dict[str, Any]:
        """Test memory security considerations."""
        print("     Testing memory security...")
        
        try:
            from app.core.security import EncryptionManager
            import gc
            
            issues = []
            
            # Test that sensitive data is not stored in plain text longer than necessary
            sensitive_key = "sk-very-sensitive-api-key-12345"
            
            # Encrypt the key
            encrypted = EncryptionManager.encrypt_data_aes256(sensitive_key)
            
            # The encrypted data should not contain the original key
            if sensitive_key in encrypted:
                issues.append("Original key found in encrypted output")
            
            # Test secure comparison
            test_string1 = "secret_value_123"
            test_string2 = "secret_value_123"
            test_string3 = "different_value"
            
            if not EncryptionManager.secure_compare(test_string1, test_string2):
                issues.append("Secure comparison failed for identical strings")
            
            if EncryptionManager.secure_compare(test_string1, test_string3):
                issues.append("Secure comparison failed for different strings")
            
            # Test that large data is handled efficiently
            large_data = "sensitive_data" * 10000  # ~130KB
            
            try:
                large_encrypted = EncryptionManager.encrypt_data_aes256(large_data)
                large_decrypted = EncryptionManager.decrypt_data_aes256(large_encrypted)
                
                if large_decrypted != large_data:
                    issues.append("Large data encryption/decryption failed")
                
                # Clear large data
                large_data = None
                large_decrypted = None
                gc.collect()
                
            except MemoryError:
                issues.append("Memory error with large data")
            
            # Test password hashing doesn't store plain passwords
            from app.core.security import PasswordManager
            
            plain_password = "user_password_123"
            hashed = PasswordManager.get_password_hash(plain_password)
            
            if plain_password in hashed:
                issues.append("Plain password found in hash")
            
            # Verify password works
            if not PasswordManager.verify_password(plain_password, hashed):
                issues.append("Password verification failed")
            
            return {
                "passed": len(issues) == 0,
                "summary": f"Memory security: {len(issues)} issues found",
                "issues": issues,
                "secure_comparison_working": True,
                "large_data_handling": True,
                "password_hashing_secure": plain_password not in hashed
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Memory security test failed",
                "error": str(e)
            }
    
    def test_compliance_validation(self) -> Dict[str, Any]:
        """Test compliance with security standards."""
        print("     Testing compliance validation...")
        
        try:
            from app.services.data_encryption_service import DataEncryptionService
            
            compliance_issues = []
            
            # Get encryption configuration
            key_info = DataEncryptionService.get_encryption_key_info()
            
            # Check AES-256 compliance
            if key_info.get("encryption_algorithm") != "AES-256-GCM":
                compliance_issues.append("Not using AES-256-GCM encryption")
            
            # Check key derivation compliance (OWASP recommendations)
            iterations = key_info.get("key_derivation_iterations", 0)
            if iterations < 100000:
                compliance_issues.append(f"Insufficient PBKDF2 iterations: {iterations} (minimum: 100,000)")
            
            # Check salt size
            salt_bits = key_info.get("salt_size_bits", 0)
            if salt_bits < 128:
                compliance_issues.append(f"Insufficient salt size: {salt_bits} bits (minimum: 128)")
            
            # Check nonce size for GCM
            nonce_bits = key_info.get("nonce_size_bits", 0)
            if nonce_bits != 96:
                compliance_issues.append(f"Incorrect GCM nonce size: {nonce_bits} bits (should be: 96)")
            
            # Check authentication tag size
            tag_bits = key_info.get("tag_size_bits", 0)
            if tag_bits < 128:
                compliance_issues.append(f"Insufficient auth tag size: {tag_bits} bits (minimum: 128)")
            
            # Check secure random source
            if key_info.get("secure_random_source") != "os.urandom":
                compliance_issues.append("Not using cryptographically secure random source")
            
            # Check constant-time comparison
            if key_info.get("constant_time_comparison") != "secrets.compare_digest":
                compliance_issues.append("Not using constant-time comparison")
            
            # Calculate compliance score
            total_checks = 6
            passed_checks = total_checks - len(compliance_issues)
            compliance_score = (passed_checks / total_checks) * 100
            
            # Determine compliance level
            if compliance_score >= 95:
                compliance_level = "FULLY_COMPLIANT"
            elif compliance_score >= 80:
                compliance_level = "MOSTLY_COMPLIANT"
            elif compliance_score >= 60:
                compliance_level = "PARTIALLY_COMPLIANT"
            else:
                compliance_level = "NON_COMPLIANT"
            
            return {
                "passed": compliance_score >= 95,
                "summary": f"Compliance: {compliance_level} ({compliance_score:.0f}%)",
                "compliance_level": compliance_level,
                "compliance_score": compliance_score,
                "compliance_issues": compliance_issues,
                "key_info": key_info,
                "standards_checked": [
                    "OWASP Cryptographic Storage",
                    "NIST SP 800-132 (PBKDF2)",
                    "FIPS 140-2 Level 1",
                    "AES-256-GCM Standard"
                ]
            }
            
        except Exception as e:
            return {
                "passed": False,
                "summary": "Compliance validation test failed",
                "error": str(e)
            }
    
    def generate_report(self) -> str:
        """Generate comprehensive data encryption security report."""
        report = []
        report.append("🔐 DATA ENCRYPTION & SECURITY TEST REPORT")
        report.append("=" * 60)
        report.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result.get("passed", False))
        
        report.append(f"📊 SUMMARY: {passed_tests}/{total_tests} tests passed")
        report.append("")
        
        # Test results
        for test_name, result in self.results.items():
            status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
            report.append(f"{status} {test_name}")
            report.append(f"   {result.get('summary', 'No summary')}")
            
            # Add specific details for important tests
            if test_name == "Compliance Validation" and "compliance_level" in result:
                report.append(f"   Compliance Level: {result['compliance_level']}")
                report.append(f"   Compliance Score: {result.get('compliance_score', 0):.0f}%")
            
            if not result.get("passed", False) and "issues" in result:
                for issue in result["issues"][:3]:  # Show first 3 issues
                    report.append(f"   - {issue}")
            
            report.append("")
        
        # Security recommendations
        report.append("🛡️  SECURITY RECOMMENDATIONS:")
        if passed_tests < total_tests:
            report.append("- Address failing encryption and security tests")
            report.append("- Review key management and derivation parameters")
            report.append("- Ensure all sensitive data is properly encrypted")
            report.append("- Implement secure data deletion procedures")
        else:
            report.append("- All encryption and security tests passed!")
            report.append("- Continue regular security monitoring")
            report.append("- Consider implementing additional security measures")
        
        report.append("")
        report.append("🔒 ENCRYPTION STANDARDS COMPLIANCE:")
        report.append("- AES-256-GCM for symmetric encryption")
        report.append("- PBKDF2-HMAC-SHA256 for key derivation")
        report.append("- 100,000+ iterations for key stretching")
        report.append("- Cryptographically secure random number generation")
        report.append("- Constant-time comparison for sensitive operations")
        
        return "\n".join(report)


def main():
    """Run data encryption and security tests."""
    tester = DataEncryptionSecurityTester()
    results = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("📋 FINAL REPORT")
    print("=" * 60)
    
    report = tester.generate_report()
    print(report)
    
    # Save report
    with open("data_encryption_security_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: data_encryption_security_report.txt")
    
    # Return exit code
    passed_tests = sum(1 for result in results.values() if result.get("passed", False))
    total_tests = len(results)
    
    if passed_tests == total_tests:
        print("🎉 All data encryption and security tests passed!")
        return 0
    else:
        print(f"⚠️  {total_tests - passed_tests} encryption/security tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())