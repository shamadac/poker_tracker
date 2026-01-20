"""
Unit tests for OAuth 2.0 implementation and JWT handling.

This test file specifically validates Requirements 8.1 and 8.2:
- 8.1: OAuth 2.0 with PKCE for secure user authentication
- 8.2: JWT tokens with proper expiration and refresh
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from jose import jwt, JWTError
from fastapi import HTTPException

from app.core.security import (
    PKCEChallenge,
    TokenManager,
    generate_state,
    verify_state
)
from app.core.config import settings


class TestPKCEImplementation:
    """Test PKCE (Proof Key for Code Exchange) implementation for OAuth 2.0."""
    
    def test_code_verifier_generation(self):
        """Test PKCE code verifier generation meets security requirements."""
        # Generate multiple verifiers to test randomness
        verifiers = [PKCEChallenge.generate_code_verifier() for _ in range(10)]
        
        # Verify all verifiers are unique (randomness test)
        assert len(set(verifiers)) == 10, "Code verifiers should be unique"
        
        # Verify verifier format and length
        for verifier in verifiers:
            assert isinstance(verifier, str), "Code verifier should be string"
            assert len(verifier) >= 43, "Code verifier should be at least 43 characters"
            assert len(verifier) <= 128, "Code verifier should be at most 128 characters"
            # Verify URL-safe base64 characters only
            valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
            assert all(c in valid_chars for c in verifier), "Code verifier should use URL-safe base64 characters"
    
    def test_code_challenge_generation(self):
        """Test PKCE code challenge generation from verifier."""
        verifier = PKCEChallenge.generate_code_verifier()
        challenge = PKCEChallenge.generate_code_challenge(verifier)
        
        # Verify challenge format
        assert isinstance(challenge, str), "Code challenge should be string"
        assert len(challenge) == 43, "Code challenge should be 43 characters (SHA256 base64url)"
        
        # Verify same verifier produces same challenge (deterministic)
        challenge2 = PKCEChallenge.generate_code_challenge(verifier)
        assert challenge == challenge2, "Same verifier should produce same challenge"
        
        # Verify different verifiers produce different challenges
        verifier2 = PKCEChallenge.generate_code_verifier()
        challenge3 = PKCEChallenge.generate_code_challenge(verifier2)
        assert challenge != challenge3, "Different verifiers should produce different challenges"
    
    def test_code_challenge_verification(self):
        """Test PKCE code challenge verification."""
        verifier = PKCEChallenge.generate_code_verifier()
        challenge = PKCEChallenge.generate_code_challenge(verifier)
        
        # Test correct verification
        assert PKCEChallenge.verify_code_challenge(verifier, challenge), "Valid verifier should verify challenge"
        
        # Test incorrect verifier
        wrong_verifier = PKCEChallenge.generate_code_verifier()
        assert not PKCEChallenge.verify_code_challenge(wrong_verifier, challenge), "Wrong verifier should fail verification"
        
        # Test empty/invalid inputs
        assert not PKCEChallenge.verify_code_challenge("", challenge), "Empty verifier should fail"
        assert not PKCEChallenge.verify_code_challenge(verifier, ""), "Empty challenge should fail"
        assert not PKCEChallenge.verify_code_challenge("invalid", "invalid"), "Invalid inputs should fail"
    
    def test_state_parameter_handling(self):
        """Test OAuth state parameter generation and verification."""
        # Test state generation
        state1 = generate_state()
        state2 = generate_state()
        
        assert isinstance(state1, str), "State should be string"
        assert len(state1) >= 32, "State should be at least 32 characters"
        assert state1 != state2, "States should be unique"
        
        # Test state verification
        assert verify_state(state1, state1), "Same state should verify"
        assert not verify_state(state1, state2), "Different states should not verify"
        assert not verify_state("", state1), "Empty state should not verify"
        assert not verify_state(state1, ""), "Empty expected state should not verify"


class TestJWTTokenManagement:
    """Test JWT token creation, verification, and refresh functionality."""
    
    def test_access_token_creation(self):
        """Test JWT access token creation with proper claims."""
        token_data = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "scope": "read write"
        }
        
        token = TokenManager.create_access_token(token_data)
        
        # Verify token is a string
        assert isinstance(token, str), "Token should be string"
        assert len(token) > 0, "Token should not be empty"
        
        # Decode and verify token structure
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Verify required claims
        assert payload["sub"] == "test-user-123", "Subject claim should match"
        assert payload["email"] == "test@example.com", "Email claim should match"
        assert payload["scope"] == "read write", "Scope claim should match"
        assert payload["type"] == "access", "Token type should be access"
        
        # Verify timing claims
        assert "exp" in payload, "Token should have expiration"
        assert "iat" in payload, "Token should have issued at"
        
        # Verify expiration is in the future
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        assert exp_time > now, "Token should not be expired"
        
        # Verify expiration is within expected range (default 30 minutes)
        expected_exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60, "Token expiration should be within 1 minute of expected"
    
    def test_refresh_token_creation(self):
        """Test JWT refresh token creation with longer expiration."""
        token_data = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        token = TokenManager.create_refresh_token(token_data)
        
        # Verify token is a string
        assert isinstance(token, str), "Refresh token should be string"
        assert len(token) > 0, "Refresh token should not be empty"
        
        # Decode and verify token structure
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Verify required claims
        assert payload["sub"] == "test-user-123", "Subject claim should match"
        assert payload["email"] == "test@example.com", "Email claim should match"
        assert payload["type"] == "refresh", "Token type should be refresh"
        
        # Verify timing claims
        assert "exp" in payload, "Refresh token should have expiration"
        assert "iat" in payload, "Refresh token should have issued at"
        
        # Verify expiration is longer than access token (7 days default)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_exp = now + timedelta(days=7)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 3600, "Refresh token expiration should be within 1 hour of expected"
    
    def test_token_verification_success(self):
        """Test successful JWT token verification."""
        token_data = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "scope": "read write"
        }
        
        # Create and verify access token
        access_token = TokenManager.create_access_token(token_data)
        payload = TokenManager.verify_token(access_token, "access")
        
        assert payload["sub"] == "test-user-123", "Subject should match"
        assert payload["email"] == "test@example.com", "Email should match"
        assert payload["type"] == "access", "Type should be access"
        
        # Create and verify refresh token
        refresh_token = TokenManager.create_refresh_token(token_data)
        payload = TokenManager.verify_token(refresh_token, "refresh")
        
        assert payload["sub"] == "test-user-123", "Subject should match"
        assert payload["type"] == "refresh", "Type should be refresh"
    
    def test_token_verification_failures(self):
        """Test JWT token verification failure scenarios."""
        token_data = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "scope": "read write"
        }
        
        access_token = TokenManager.create_access_token(token_data)
        refresh_token = TokenManager.create_refresh_token(token_data)
        
        # Test wrong token type
        with pytest.raises(HTTPException) as exc_info:
            TokenManager.verify_token(access_token, "refresh")
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)
        
        with pytest.raises(HTTPException) as exc_info:
            TokenManager.verify_token(refresh_token, "access")
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)
        
        # Test invalid token
        with pytest.raises(HTTPException) as exc_info:
            TokenManager.verify_token("invalid.token.here", "access")
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
        
        # Test empty token
        with pytest.raises(HTTPException) as exc_info:
            TokenManager.verify_token("", "access")
        assert exc_info.value.status_code == 401
    
    def test_expired_token_handling(self):
        """Test handling of expired JWT tokens."""
        token_data = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "scope": "read write"
        }
        
        # Create token with very short expiration
        short_expiry = timedelta(seconds=-1)  # Already expired
        expired_token = TokenManager.create_access_token(token_data, short_expiry)
        
        # Verify expired token raises appropriate exception
        with pytest.raises(HTTPException) as exc_info:
            TokenManager.verify_token(expired_token, "access")
        assert exc_info.value.status_code == 401
        assert "Token has expired" in str(exc_info.value.detail)
    
    def test_custom_token_expiration(self):
        """Test JWT token creation with custom expiration times."""
        token_data = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Test custom access token expiration
        custom_expiry = timedelta(minutes=60)
        token = TokenManager.create_access_token(token_data, custom_expiry)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_exp = now + custom_expiry
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60, "Custom expiration should be respected"
        
        # Test custom refresh token expiration
        custom_refresh_expiry = timedelta(days=14)
        refresh_token = TokenManager.create_refresh_token(token_data, custom_refresh_expiry)
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = now + custom_refresh_expiry
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 3600, "Custom refresh expiration should be respected"
    
    def test_password_reset_token_functionality(self):
        """Test password reset token creation and verification."""
        email = "test@example.com"
        
        # Create password reset token
        reset_token = TokenManager.create_password_reset_token(email)
        
        # Verify token structure
        assert isinstance(reset_token, str), "Reset token should be string"
        payload = jwt.decode(reset_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["email"] == email, "Email should match"
        assert payload["type"] == "password_reset", "Type should be password_reset"
        assert "exp" in payload, "Reset token should have expiration"
        
        # Verify expiration is 1 hour
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_exp = now + timedelta(hours=1)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 300, "Reset token should expire in 1 hour"
        
        # Test verification
        verified_email = TokenManager.verify_password_reset_token(reset_token)
        assert verified_email == email, "Verified email should match"
        
        # Test invalid reset token
        with pytest.raises(HTTPException) as exc_info:
            TokenManager.verify_password_reset_token("invalid.token")
        assert exc_info.value.status_code == 400
        assert "Invalid or expired password reset token" in str(exc_info.value.detail)


class TestOAuthFlowIntegration:
    """Test complete OAuth 2.0 flow integration."""
    
    def test_complete_pkce_flow(self):
        """Test complete PKCE OAuth flow from start to finish."""
        # Step 1: Generate PKCE challenge
        code_verifier = PKCEChallenge.generate_code_verifier()
        code_challenge = PKCEChallenge.generate_code_challenge(code_verifier)
        state = generate_state()
        
        # Step 2: Simulate authorization (would normally involve user login)
        # In a real flow, this would redirect to login page and back
        auth_code = generate_state()  # Simulated authorization code
        
        # Step 3: Verify PKCE challenge (as would happen in token exchange)
        assert PKCEChallenge.verify_code_challenge(code_verifier, code_challenge), "PKCE verification should succeed"
        assert verify_state(state, state), "State verification should succeed"
        
        # Step 4: Create tokens after successful verification
        token_data = {
            "sub": "user-123",
            "email": "user@example.com",
            "scope": "read write"
        }
        
        access_token = TokenManager.create_access_token(token_data)
        refresh_token = TokenManager.create_refresh_token(token_data)
        
        # Step 5: Verify tokens work correctly
        access_payload = TokenManager.verify_token(access_token, "access")
        refresh_payload = TokenManager.verify_token(refresh_token, "refresh")
        
        assert access_payload["sub"] == "user-123", "Access token should contain user ID"
        assert refresh_payload["sub"] == "user-123", "Refresh token should contain user ID"
        assert access_payload["type"] == "access", "Access token type should be correct"
        assert refresh_payload["type"] == "refresh", "Refresh token type should be correct"
    
    def test_token_refresh_flow(self):
        """Test token refresh flow maintains security."""
        import time
        
        # Create initial tokens
        token_data = {
            "sub": "user-123",
            "email": "user@example.com",
            "scope": "read write"
        }
        
        original_access = TokenManager.create_access_token(token_data)
        original_refresh = TokenManager.create_refresh_token(token_data)
        
        # Verify original tokens
        original_access_payload = TokenManager.verify_token(original_access, "access")
        original_refresh_payload = TokenManager.verify_token(original_refresh, "refresh")
        
        # Wait a moment to ensure different timestamps
        time.sleep(1)
        
        # Simulate token refresh (create new tokens using refresh token data)
        new_access = TokenManager.create_access_token({
            "sub": original_refresh_payload["sub"],
            "email": original_refresh_payload["email"],
            "scope": "read write"
        })
        new_refresh = TokenManager.create_refresh_token({
            "sub": original_refresh_payload["sub"],
            "email": original_refresh_payload["email"]
        })
        
        # Verify new tokens
        new_access_payload = TokenManager.verify_token(new_access, "access")
        new_refresh_payload = TokenManager.verify_token(new_refresh, "refresh")
        
        # Verify continuity
        assert new_access_payload["sub"] == original_access_payload["sub"], "User ID should be preserved"
        assert new_access_payload["email"] == original_access_payload["email"], "Email should be preserved"
        
        # Verify tokens have different issued at times
        assert new_access_payload["iat"] > original_access_payload["iat"], "New access token should have later issued time"
        assert new_refresh_payload["iat"] > original_refresh_payload["iat"], "New refresh token should have later issued time"
        
        # Verify tokens are different (due to different timestamps)
        assert new_access != original_access, "New access token should be different"
        assert new_refresh != original_refresh, "New refresh token should be different"
    
    def test_security_requirements_compliance(self):
        """Test that OAuth implementation meets security requirements."""
        # Test Requirement 8.1: OAuth 2.0 with PKCE
        
        # PKCE code verifier should be cryptographically random
        verifiers = [PKCEChallenge.generate_code_verifier() for _ in range(100)]
        assert len(set(verifiers)) == 100, "PKCE verifiers should be cryptographically random"
        
        # PKCE challenge should use SHA256
        verifier = PKCEChallenge.generate_code_verifier()
        challenge = PKCEChallenge.generate_code_challenge(verifier)
        assert len(challenge) == 43, "PKCE challenge should be SHA256 hash (43 chars base64url)"
        
        # State parameter should be cryptographically random
        states = [generate_state() for _ in range(100)]
        assert len(set(states)) == 100, "State parameters should be cryptographically random"
        
        # Test Requirement 8.2: JWT tokens with proper expiration and refresh
        
        token_data = {"sub": "user-123", "email": "user@example.com", "scope": "read write"}
        
        # Access tokens should have short expiration
        access_token = TokenManager.create_access_token(token_data)
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        access_exp = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        access_lifetime = (access_exp - now).total_seconds()
        
        # Access token should expire within reasonable time (default 30 minutes)
        assert access_lifetime <= 1800, "Access token should have short expiration (≤30 minutes)"
        assert access_lifetime > 0, "Access token should not be expired"
        
        # Refresh tokens should have longer expiration
        refresh_token = TokenManager.create_refresh_token(token_data)
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
        refresh_lifetime = (refresh_exp - now).total_seconds()
        
        # Refresh token should have longer expiration (default 7 days)
        assert refresh_lifetime >= 86400, "Refresh token should have long expiration (≥1 day)"
        assert refresh_lifetime <= 604800, "Refresh token should not exceed 7 days"
        
        # Tokens should have proper type identification
        assert access_payload["type"] == "access", "Access token should have correct type"
        assert refresh_payload["type"] == "refresh", "Refresh token should have correct type"
        
        # Tokens should include issued at timestamp
        assert "iat" in access_payload, "Access token should have issued at timestamp"
        assert "iat" in refresh_payload, "Refresh token should have issued at timestamp"


if __name__ == "__main__":
    # Run all tests
    import sys
    
    test_classes = [TestPKCEImplementation, TestJWTTokenManagement, TestOAuthFlowIntegration]
    
    for test_class in test_classes:
        print(f"\nRunning {test_class.__name__}...")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    print(f"  Running {method_name}...")
                    getattr(instance, method_name)()
                    print(f"  ✓ {method_name} passed")
                except Exception as e:
                    print(f"  ✗ {method_name} failed: {e}")
                    sys.exit(1)
    
    print("\n✓ All OAuth unit tests passed!")
    print("\nRequirements validated:")
    print("  ✓ 8.1: OAuth 2.0 with PKCE for secure user authentication")
    print("  ✓ 8.2: JWT tokens with proper expiration and refresh")