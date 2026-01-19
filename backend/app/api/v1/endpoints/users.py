"""
User management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.user import (
    UserResponse,
    UserPreferencesUpdate,
    APIKeyUpdate,
    APIKeyValidationRequest,
    APIKeyValidationResponse,
    UserProfile,
    UserAccountDeletionRequest,
    UserAccountDeletionResponse
)
from app.schemas.common import ErrorResponse, SuccessResponse
from app.models.user import User


router = APIRouter()


@router.get("/profile", response_model=UserProfile, responses={401: {"model": ErrorResponse}})
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserProfile:
    """
    Get current user profile information.
    
    Returns comprehensive user profile including preferences, 
    API key status, and quick statistics summary.
    """
    # TODO: Implement user profile retrieval with statistics
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
        preferences=current_user.preferences,
        api_keys_configured={
            "gemini": "gemini" in current_user.api_keys,
            "groq": "groq" in current_user.api_keys
        },
        hand_history_paths=current_user.hand_history_paths
    )


@router.put("/preferences", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def update_user_preferences(
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Update user preferences.
    
    - **ai_provider**: Preferred AI provider (gemini or groq)
    - **hand_history_paths**: Directory paths for hand history files
    - **analysis_preferences**: Analysis-related preferences
    - **ui_preferences**: UI and display preferences
    - **notification_preferences**: Notification settings
    """
    # TODO: Implement preferences update
    return SuccessResponse(
        message="Preferences updated successfully"
    )


@router.put("/api-keys", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def update_api_key(
    api_key_data: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Update AI provider API key.
    
    API keys are encrypted before storage and never exposed in logs.
    
    - **provider**: AI provider (gemini or groq)
    - **api_key**: API key for the provider (min 10 characters)
    """
    # TODO: Implement API key update with encryption
    return SuccessResponse(
        message="API key updated successfully",
        data={"provider": api_key_data.provider}
    )


@router.post("/api-keys/validate", response_model=APIKeyValidationResponse, responses={400: {"model": ErrorResponse}})
async def validate_api_key(
    request: APIKeyValidationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> APIKeyValidationResponse:
    """
    Validate an API key before saving.
    
    Tests the API key with the provider to ensure it's valid and active.
    
    - **provider**: AI provider to validate key for
    - **api_key**: API key to validate
    """
    # TODO: Implement API key validation
    return APIKeyValidationResponse(
        provider=request.provider,
        valid=True,
        error_message=None
    )


@router.delete("/api-keys/{provider}", response_model=SuccessResponse, responses={404: {"model": ErrorResponse}})
async def delete_api_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Delete API key for specified provider.
    
    - **provider**: AI provider to remove key for (gemini or groq)
    """
    # TODO: Implement API key deletion
    if provider not in ["gemini", "groq"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must be 'gemini' or 'groq'"
        )
    
    return SuccessResponse(
        message=f"API key for {provider} deleted successfully"
    )


@router.delete("/account", response_model=UserAccountDeletionResponse, responses={400: {"model": ErrorResponse}})
async def delete_user_account(
    request: UserAccountDeletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserAccountDeletionResponse:
    """
    Delete user account and all associated data.
    
    This action is irreversible and will permanently delete:
    - User account and preferences
    - All hand history data
    - All analysis results
    - All statistics cache
    - All file monitoring settings
    
    - **confirm_deletion**: Must be true to confirm deletion
    - **password**: Current password for verification
    """
    # TODO: Implement secure account deletion
    from datetime import datetime
    return UserAccountDeletionResponse(
        message="Account deleted successfully",
        deleted_at=datetime.utcnow().isoformat(),
        data_removed={
            "hands": 0,
            "analyses": 0,
            "statistics_cache": 0,
            "file_monitoring": 0
        }
    )