"""
Authentication-related Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict


class PKCEAuthRequest(BaseModel):
    """PKCE authorization request."""
    client_id: str = Field(..., description="OAuth client ID")
    redirect_uri: str = Field(..., description="Redirect URI after authorization")
    code_challenge: str = Field(..., description="PKCE code challenge")
    code_challenge_method: str = Field("S256", description="Code challenge method")
    state: str = Field(..., description="State parameter for CSRF protection")
    scope: str = Field("read write", description="Requested scopes")


class PKCETokenRequest(BaseModel):
    """PKCE token exchange request."""
    grant_type: str = Field("authorization_code", description="OAuth grant type")
    client_id: str = Field(..., description="OAuth client ID")
    code: str = Field(..., description="Authorization code")
    redirect_uri: str = Field(..., description="Redirect URI used in authorization")
    code_verifier: str = Field(..., description="PKCE code verifier")


class AuthorizationResponse(BaseModel):
    """Authorization response with code."""
    code: str = Field(..., description="Authorization code")
    state: str = Field(..., description="State parameter")


class Token(BaseModel):
    """JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token for token renewal")
    scope: str = Field("read write", description="Granted scopes")


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str = Field(..., description="User ID from token")
    email: str = Field(..., description="User email from token")
    exp: int = Field(..., description="Token expiration timestamp")
    iat: int = Field(..., description="Token issued at timestamp")
    scope: str = Field(..., description="Token scopes")


class LoginRequest(BaseModel):
    """OAuth2 login request."""
    username: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets minimum security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one digit, and one special character'
            )
        
        return v


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str = Field(..., description="Valid refresh token")


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets minimum security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one digit, and one special character'
            )
        
        return v
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets minimum security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one digit, and one special character'
            )
        
        return v
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class UserMeResponse(BaseModel):
    """Current user information response."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    created_at: str = Field(..., description="Account creation date")
    preferences: dict = Field(default_factory=dict, description="User preferences")
    has_api_keys: dict = Field(default_factory=dict, description="Which API keys are configured")
    
    model_config = ConfigDict(from_attributes=True)