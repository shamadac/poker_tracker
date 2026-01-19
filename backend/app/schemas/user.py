"""
User-related Pydantic schemas.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr, validator
from .common import UUIDMixin, TimestampMixin


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, description="User password")
    
    @validator('password')
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


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = Field(None, description="Updated email address")
    password: Optional[str] = Field(None, min_length=8, description="Updated password")
    
    @validator('password')
    def validate_password_strength(cls, v):
        if v is not None:
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


class UserResponse(UserBase, UUIDMixin, TimestampMixin):
    """Schema for user response data."""
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    has_api_keys: Dict[str, bool] = Field(default_factory=dict, description="Which API keys are configured")
    hand_history_paths: Dict[str, str] = Field(default_factory=dict, description="Configured hand history paths")
    
    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    ai_provider: Optional[str] = Field(None, pattern="^(gemini|groq)$", description="Preferred AI provider")
    hand_history_paths: Optional[Dict[str, str]] = Field(None, description="Hand history directory paths")
    analysis_preferences: Optional[Dict[str, Any]] = Field(None, description="Analysis preferences")
    ui_preferences: Optional[Dict[str, Any]] = Field(None, description="UI preferences")
    notification_preferences: Optional[Dict[str, Any]] = Field(None, description="Notification preferences")
    
    @validator('ai_provider')
    def validate_ai_provider(cls, v):
        if v is not None:
            allowed_providers = ['gemini', 'groq']
            if v not in allowed_providers:
                raise ValueError(f'AI provider must be one of: {", ".join(allowed_providers)}')
        return v
    
    @validator('hand_history_paths')
    def validate_hand_history_paths(cls, v):
        if v is not None:
            allowed_platforms = ['pokerstars', 'ggpoker']
            for platform in v.keys():
                if platform not in allowed_platforms:
                    raise ValueError(f'Platform must be one of: {", ".join(allowed_platforms)}')
        return v


class APIKeyUpdate(BaseModel):
    """Schema for updating AI provider API keys."""
    provider: str = Field(..., pattern="^(gemini|groq)$", description="AI provider")
    api_key: str = Field(..., min_length=10, description="API key for the provider")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['gemini', 'groq']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        return v
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if len(v) < 10:
            raise ValueError('API key must be at least 10 characters long')
        
        # Basic validation - API keys should not contain spaces
        if ' ' in v:
            raise ValueError('API key should not contain spaces')
        
        return v


class APIKeyValidationRequest(BaseModel):
    """Schema for validating API keys."""
    provider: str = Field(..., pattern="^(gemini|groq)$", description="AI provider")
    api_key: str = Field(..., description="API key to validate")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['gemini', 'groq']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        return v


class APIKeyValidationResponse(BaseModel):
    """Schema for API key validation response."""
    provider: str = Field(..., description="AI provider")
    valid: bool = Field(..., description="Whether the API key is valid")
    error_message: Optional[str] = Field(None, description="Error message if validation failed")


class UserProfile(BaseModel):
    """Comprehensive user profile information."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    created_at: str = Field(..., description="Account creation date")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    api_keys_configured: Dict[str, bool] = Field(default_factory=dict, description="Which API keys are configured")
    hand_history_paths: Dict[str, str] = Field(default_factory=dict, description="Configured paths")
    statistics_summary: Optional[Dict[str, Any]] = Field(None, description="Quick statistics summary")
    
    class Config:
        from_attributes = True


class UserAccountDeletionRequest(BaseModel):
    """Schema for account deletion confirmation."""
    confirm_deletion: bool = Field(..., description="Confirmation that user wants to delete account")
    password: str = Field(..., description="Current password for verification")
    
    @validator('confirm_deletion')
    def validate_confirmation(cls, v):
        if not v:
            raise ValueError('Account deletion must be explicitly confirmed')
        return v


class UserAccountDeletionResponse(BaseModel):
    """Schema for account deletion response."""
    message: str = Field(..., description="Deletion confirmation message")
    deleted_at: str = Field(..., description="Deletion timestamp")
    data_removed: Dict[str, int] = Field(..., description="Count of removed data by type")