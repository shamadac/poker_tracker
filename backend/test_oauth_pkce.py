"""
Test OAuth 2.0 with PKCE implementation.
"""
import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.main import app
from app.core.config import settings
from app.core.database import Base
from app.api.deps import get_db
from app.core.security import PKCEChallenge, TokenManager
from app.services.user_service import UserService
from app.schemas.auth import RegisterRequest

# Import all models to ensure they're registered with Base.metadata
from app.models import *

# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine and session
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """Override database dependency for testing."""
    async with TestSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Mock Redis to avoid connection issues in tests
class MockRedis:
    async def get(self, key):
        return None
    
    async def setex(self, key, time, value):
        assert True
    
    async def incr(self, key):
        return 1
    
    async def ping(self):
        assert True


# Override the dependency and patch Redis
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Set up test database."""
    async def _setup():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def _teardown():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    # Run setup
    asyncio.run(_setup())
    yield
    # Run teardown
    asyncio.run(_teardown())


@pytest.fixture
def test_user(setup_database):
    """Create a test user."""
    async def _create_user():
        async with TestSessionLocal() as db:
            user_data = RegisterRequest(
                email="test@example.com",
                password="TestPass123!",
                confirm_password="TestPass123!"
            )
            user = await UserService.create_user(db, user_data)
            return user
    
    return asyncio.run(_create_user())


def test_pkce_challenge_generation():
    """Test PKCE challenge generation."""
    # Generate code verifier and challenge
    code_verifier = PKCEChallenge.generate_code_verifier()
    code_challenge = PKCEChallenge.generate_code_challenge(code_verifier)
    
    # Verify the challenge
    assert PKCEChallenge.verify_code_challenge(code_verifier, code_challenge)
    
    # Verify wrong verifier fails
    wrong_verifier = PKCEChallenge.generate_code_verifier()
    assert not PKCEChallenge.verify_code_challenge(wrong_verifier, code_challenge)


def test_generate_pkce_challenge_endpoint():
    """Test PKCE challenge generation endpoint."""
    response = client.get("/api/v1/auth/pkce/challenge")
    assert response.status_code == 200
    
    data = response.json()
    assert "code_verifier" in data
    assert "code_challenge" in data
    assert "code_challenge_method" in data
    assert data["code_challenge_method"] == "S256"
    
    # Verify the challenge is valid
    assert PKCEChallenge.verify_code_challenge(
        data["code_verifier"], 
        data["code_challenge"]
    )


def test_oauth_authorize_endpoint():
    """Test OAuth authorization endpoint."""
    # Test with valid parameters
    response = client.get("/api/v1/auth/authorize", params={
        "client_id": settings.OAUTH_CLIENT_ID,
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
        "code_challenge": "test_challenge",
        "code_challenge_method": "S256",
        "state": "test_state",
        "scope": "read write"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "state" in data
    assert data["state"] == "test_state"


def test_oauth_authorize_invalid_client():
    """Test OAuth authorization with invalid client_id."""
    response = client.get("/api/v1/auth/authorize", params={
        "client_id": "invalid_client",
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
        "code_challenge": "test_challenge",
        "code_challenge_method": "S256"
    })
    
    assert response.status_code == 400
    assert "Invalid client_id" in response.json()["detail"]


def test_user_registration(setup_database):
    """Test user registration."""
    with patch('redis.asyncio.from_url', return_value=MockRedis()):
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "confirm_password": "NewPass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["data"]["email"] == "newuser@example.com"


def test_user_login(setup_database, test_user):
    """Test user login."""
    with patch('redis.asyncio.from_url', return_value=MockRedis()):
        response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "TestPass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["scope"] == "read write"


def test_token_refresh(setup_database, test_user):
    """Test token refresh."""
    with patch('redis.asyncio.from_url', return_value=MockRedis()):
        # First login to get tokens
        login_response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "TestPass123!"
        })
        
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]
        
        # Use refresh token to get new access token
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert "refresh_token" in data


def test_token_verification():
    """Test JWT token creation and verification."""
    # Create a test token
    token_data = {"sub": "test_user", "email": "test@example.com", "scope": "read write"}
    token = TokenManager.create_access_token(token_data)
    
    # Verify the token
    payload = TokenManager.verify_token(token, "access")
    assert payload["sub"] == "test_user"
    assert payload["email"] == "test@example.com"
    assert payload["type"] == "access"


def test_password_reset_token():
    """Test password reset token creation and verification."""
    email = "test@example.com"
    
    # Create password reset token
    token = TokenManager.create_password_reset_token(email)
    
    # Verify the token
    verified_email = TokenManager.verify_password_reset_token(token)
    assert verified_email == email


if __name__ == "__main__":
    # Run basic tests
    test_pkce_challenge_generation()
    test_generate_pkce_challenge_endpoint()
    test_oauth_authorize_endpoint()
    test_oauth_authorize_invalid_client()
    test_token_verification()
    test_password_reset_token()
    
    print("All OAuth 2.0 with PKCE tests passed!")
