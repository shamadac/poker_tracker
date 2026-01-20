"""
User management endpoints.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.services.user_service import UserService
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
import logging

logger = logging.getLogger(__name__)
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
    try:
        # Get API keys status
        api_keys = await UserService.get_user_api_keys(db, str(current_user.id))
        
        return UserProfile(
            id=str(current_user.id),
            email=current_user.email,
            created_at=current_user.created_at.isoformat() if current_user.created_at else None,
            preferences=current_user.preferences or {},
            api_keys_configured={
                "gemini": "gemini" in api_keys,
                "groq": "groq" in api_keys
            },
            hand_history_paths=current_user.hand_history_paths or {}
        )
    except Exception as e:
        logger.error("Failed to get user profile", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
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
    try:
        # Convert Pydantic model to dict, excluding None values
        preferences_dict = preferences.dict(exclude_none=True)
        
        await UserService.update_user_preferences(
            db, str(current_user.id), preferences_dict
        )
        
        return SuccessResponse(
            message="Preferences updated successfully"
        )
    except Exception as e:
        logger.error("Failed to update preferences", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
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
    try:
        # Validate provider
        if api_key_data.provider not in ["gemini", "groq"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider must be 'gemini' or 'groq'"
            )
        
        # Update API key
        api_keys = {api_key_data.provider: api_key_data.api_key}
        await UserService.update_user_api_keys(
            db, str(current_user.id), api_keys
        )
        
        return SuccessResponse(
            message="API key updated successfully",
            data={"provider": api_key_data.provider}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update API key", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API key"
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
    try:
        # Validate provider
        if request.provider not in ["gemini", "groq"]:
            return APIKeyValidationResponse(
                provider=request.provider,
                valid=False,
                error_message="Provider must be 'gemini' or 'groq'"
            )
        
        # Test API key with provider
        from app.services.ai_providers import AIProviderService
        ai_service = AIProviderService()
        
        try:
            # Test the API key with a simple request
            is_valid = await ai_service.validate_api_key(request.provider, request.api_key)
            
            return APIKeyValidationResponse(
                provider=request.provider,
                valid=is_valid,
                error_message=None if is_valid else "API key is invalid or inactive"
            )
        except Exception as validation_error:
            return APIKeyValidationResponse(
                provider=request.provider,
                valid=False,
                error_message=str(validation_error)
            )
            
    except Exception as e:
        logger.error("Failed to validate API key", user_id=str(current_user.id), error=str(e))
        return APIKeyValidationResponse(
            provider=request.provider,
            valid=False,
            error_message="Validation service temporarily unavailable"
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
    try:
        if provider not in ["gemini", "groq"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider must be 'gemini' or 'groq'"
            )
        
        # Get current API keys
        current_keys = await UserService.get_user_api_keys(db, str(current_user.id))
        
        if provider not in current_keys:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No API key found for provider '{provider}'"
            )
        
        # Remove the specific provider key
        del current_keys[provider]
        
        # Update with remaining keys
        await UserService.update_user_api_keys(db, str(current_user.id), current_keys)
        
        return SuccessResponse(
            message=f"API key for {provider} deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete API key", user_id=str(current_user.id), provider=provider, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
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
    try:
        # Validate confirmation
        if not request.confirm_deletion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deletion must be confirmed"
            )
        
        # Verify password
        from app.core.security import PasswordManager
        if not PasswordManager.verify_password(request.password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password verification failed"
            )
        
        # Perform secure data deletion
        deleted_data = await UserService.delete_user_data_securely(db, str(current_user.id))
        
        deletion_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Log the deletion for audit purposes
        logger.info("User account deleted", 
                   user_id=str(current_user.id),
                   email=current_user.email,
                   deleted_data=deleted_data,
                   timestamp=deletion_timestamp)
        
        return UserAccountDeletionResponse(
            message="Account and all associated data deleted successfully",
            deleted_at=deletion_timestamp,
            data_removed={
                "hands": deleted_data.get("poker_hands", 0),
                "analyses": deleted_data.get("analysis_results", 0),
                "statistics_cache": deleted_data.get("statistics_cache", 0),
                "file_monitoring": deleted_data.get("file_processing_tasks", 0)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete account", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.get("/data-summary")
async def get_user_data_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary of user's data across all tables.
    
    Returns count of records by table for transparency before deletion.
    """
    try:
        data_summary = await UserService.get_user_data_summary(db, str(current_user.id))
        total_records = sum(data_summary.values())
        
        return {
            "user_id": str(current_user.id),
            "data_counts": data_summary,
            "total_records": total_records,
            "summary_generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error("Failed to get data summary", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data summary"
        )


@router.post("/export-data")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export all user data for GDPR compliance.
    
    Returns complete user data in structured format.
    """
    try:
        user_data = await UserService.export_user_data(db, str(current_user.id))
        
        return {
            "message": "Data export completed successfully",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "user_data": user_data
        }
    except Exception as e:
        logger.error("Failed to export user data", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export user data"
        )