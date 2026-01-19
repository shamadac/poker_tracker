"""
Authentication endpoints.
"""
from datetime import timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import (
    TokenManager, 
    PKCEChallenge, 
    generate_state, 
    verify_state
)
from app.schemas.auth import (
    Token,
    PKCEAuthRequest,
    PKCETokenRequest,
    AuthorizationResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserMeResponse
)
from app.schemas.common import ErrorResponse, SuccessResponse
from app.models.user import User
from app.services.user_service import UserService

router = APIRouter()

# In-memory storage for PKCE challenges and states (use Redis in production)
pkce_challenges: Dict[str, Dict[str, Any]] = {}


@router.post("/register", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def register_user(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Register a new user account.
    
    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit, special char)
    - **confirm_password**: Password confirmation
    """
    try:
        user = await UserService.create_user(db, user_data)
        return SuccessResponse(
            message="User registered successfully",
            data={"email": user.email, "id": str(user.id)}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        ) from e


@router.get("/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
    state: str = None,
    scope: str = "read write"
) -> Dict[str, str]:
    """
    OAuth 2.0 authorization endpoint with PKCE.
    
    This endpoint initiates the OAuth flow by validating the PKCE challenge
    and returning an authorization URL for the client.
    """
    # Validate client_id
    if client_id != settings.OAUTH_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    # Validate redirect_uri
    if redirect_uri != settings.OAUTH_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri"
        )
    
    # Validate code_challenge_method
    if code_challenge_method != "S256":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only S256 code_challenge_method is supported"
        )
    
    # Generate state if not provided
    if not state:
        state = generate_state()
    
    # Store PKCE challenge for later verification
    auth_code = generate_state()  # Use as authorization code
    pkce_challenges[auth_code] = {
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": scope
    }
    
    return {
        "authorization_url": f"/auth/login?code={auth_code}&state={state}",
        "state": state
    }


@router.post("/login", response_model=Token, responses={401: {"model": ErrorResponse}})
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    - **username**: User email address
    - **password**: User password
    """
    from app.middleware.security import SecurityEventLogger
    
    # Authenticate user
    user = await UserService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Log failed authentication attempt
        SecurityEventLogger.log_authentication_attempt(
            request=request,
            user_id=None,
            success=False,
            failure_reason="incorrect_credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log successful authentication
    SecurityEventLogger.log_authentication_attempt(
        request=request,
        user_id=str(user.id),
        success=True
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = TokenManager.create_access_token(
        data={"sub": str(user.id), "email": user.email, "scope": "read write"},
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = TokenManager.create_refresh_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        scope="read write"
    )


@router.post("/token", response_model=Token, responses={400: {"model": ErrorResponse}})
async def exchange_code_for_token(
    request: PKCETokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Exchange authorization code for access token using PKCE.
    
    - **grant_type**: Must be "authorization_code"
    - **client_id**: OAuth client ID
    - **code**: Authorization code from /authorize
    - **redirect_uri**: Same redirect URI used in authorization
    - **code_verifier**: PKCE code verifier
    """
    # Validate grant type
    if request.grant_type != "authorization_code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid grant_type"
        )
    
    # Get stored PKCE challenge
    challenge_data = pkce_challenges.get(request.code)
    if not challenge_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired authorization code"
        )
    
    # Validate client_id
    if request.client_id != challenge_data["client_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    # Validate redirect_uri
    if request.redirect_uri != challenge_data["redirect_uri"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri"
        )
    
    # Verify PKCE challenge
    if not PKCEChallenge.verify_code_challenge(
        request.code_verifier, 
        challenge_data["code_challenge"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code_verifier"
        )
    
    # Clean up used challenge
    del pkce_challenges[request.code]
    
    # For this implementation, we'll create a token for a demo user
    # In a real implementation, this would be tied to the authenticated user
    # from the authorization step
    
    # Create tokens (using a placeholder user for now)
    token_data = {"sub": "demo-user", "email": "demo@example.com", "scope": challenge_data["scope"]}
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = TokenManager.create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = TokenManager.create_refresh_token(
        data=token_data,
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        scope=challenge_data["scope"]
    )


@router.post("/refresh", response_model=Token, responses={401: {"model": ErrorResponse}})
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    """
    try:
        # Verify refresh token
        payload = TokenManager.verify_token(request.refresh_token, "refresh")
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify user still exists
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = TokenManager.create_access_token(
            data={"sub": user_id, "email": email, "scope": "read write"},
            expires_delta=access_token_expires
        )
        
        # Create new refresh token
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = TokenManager.create_refresh_token(
            data={"sub": user_id, "email": email},
            expires_delta=refresh_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=new_refresh_token,
            scope="read write"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        ) from e


@router.get("/me", response_model=UserMeResponse, responses={401: {"model": ErrorResponse}})
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> UserMeResponse:
    """
    Get current user information.
    """
    return UserMeResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
        preferences=current_user.preferences or {},
        has_api_keys={
            "gemini": "gemini" in (current_user.api_keys or {}),
            "groq": "groq" in (current_user.api_keys or {})
        }
    )


@router.post("/password-reset", response_model=SuccessResponse, responses={404: {"model": ErrorResponse}})
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Request password reset for user account.
    
    - **email**: Email address of account to reset
    """
    # Check if user exists
    user = await UserService.get_user_by_email(db, request.email)
    
    # Always return success to prevent email enumeration
    if user:
        # Generate password reset token
        reset_token = TokenManager.create_password_reset_token(request.email)
        
        # TODO: Send email with reset token
        # In a real implementation, you would send an email here
        # For now, we'll just log it or return it in development
        
        # Store the token temporarily (use Redis in production)
        # This is just for demonstration
        pass
    
    return SuccessResponse(
        message="Password reset email sent if account exists"
    )


@router.post("/password-reset/confirm", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Confirm password reset with token.
    
    - **token**: Password reset token from email
    - **new_password**: New password
    - **confirm_password**: Password confirmation
    """
    try:
        # Verify password reset token
        email = TokenManager.verify_password_reset_token(request.token)
        
        # Get user by email
        user = await UserService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        # Update password
        await UserService.update_password(db, str(user.id), request.new_password)
        
        return SuccessResponse(
            message="Password reset successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        ) from e


@router.get("/csrf-token", response_model=dict)
async def get_csrf_token():
    """
    Get CSRF token for secure form submissions.
    
    Returns:
        dict: CSRF token for client-side use
    """
    from app.middleware.security import CSRFProtectionMiddleware
    
    # Generate a new CSRF token
    csrf_middleware = CSRFProtectionMiddleware(None)
    token = csrf_middleware._generate_csrf_token()
    
    return {
        "csrf_token": token,
        "expires_in": 3600  # 1 hour
    }


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> SuccessResponse:
    """
    Logout user and invalidate tokens.
    
    Args:
        current_user: Currently authenticated user
        
    Returns:
        dict: Logout confirmation
    """
    from app.middleware.security import SecurityEventLogger
    
    # Log the logout event
    SecurityEventLogger.log_authentication_attempt(
        request=request,
        user_id=str(current_user.id),
        success=True
    )
    
    # In a production system, you would:
    # 1. Add the token to a blacklist in Redis
    # 2. Clear any session data
    # 3. Invalidate refresh tokens
    
    return SuccessResponse(
        message="Successfully logged out"
    )


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify router is working."""
    return {"message": "Auth router is working!"}


@router.get("/pkce/challenge")
async def generate_pkce_challenge() -> Dict[str, str]:
    """
    Generate PKCE challenge for client applications.
    
    Returns code_verifier and code_challenge for OAuth PKCE flow.
    """
    code_verifier = PKCEChallenge.generate_code_verifier()
    code_challenge = PKCEChallenge.generate_code_challenge(code_verifier)
    
    return {
        "code_verifier": code_verifier,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }