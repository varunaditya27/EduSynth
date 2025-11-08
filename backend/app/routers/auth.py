"""
Authentication API Router - Endpoints for user authentication.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from prisma import Prisma

from app.db import get_client
from app.deps.auth import get_current_user, CurrentUser
from app.models.auth import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    GoogleAuthRequest,
    ChangePasswordRequest,
    ErrorResponse
)
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter()  # Prefix added in main.py as /v1/auth


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password. Returns JWT access token.",
    responses={
        201: {"description": "User created successfully"},
        400: {"model": ErrorResponse, "description": "Email already exists"},
        422: {"description": "Validation error"}
    }
)
async def signup(
    request: SignupRequest,
    db: Prisma = Depends(get_client)
):
    """
    Register a new user account.
    
    - **name**: User's full name
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters)
    
    Returns JWT access token and user information.
    """
    try:
        result = await auth_service.register_user(
            db=db,
            name=request.name,
            email=request.email,
            password=request.password
        )
        
        return AuthResponse(
            access_token=result["access_token"],
            token_type="bearer",
            user=UserResponse(
                id=result["user"].id,
                email=result["user"].email,
                name=result["user"].name,
                created_at=result["user"].createdAt
            )
        )
    
    except ValueError as e:
        if str(e) == "EMAIL_ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login user",
    description="Authenticate user with email and password. Returns JWT access token.",
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        422: {"description": "Validation error"}
    }
)
async def login(
    request: LoginRequest,
    db: Prisma = Depends(get_client)
):
    """
    Login with email and password.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT access token and user information.
    """
    try:
        result = await auth_service.login_user(
            db=db,
            email=request.email,
            password=request.password
        )
        
        return AuthResponse(
            access_token=result["access_token"],
            token_type="bearer",
            user=UserResponse(
                id=result["user"].id,
                email=result["user"].email,
                name=result["user"].name,
                created_at=result["user"].createdAt
            )
        )
    
    except ValueError as e:
        if str(e) == "INVALID_CREDENTIALS":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information. Requires JWT token.",
    responses={
        200: {"description": "User information retrieved"},
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
    db: Prisma = Depends(get_client)
):
    """
    Get current authenticated user's information.
    
    Requires valid JWT token in Authorization header.
    """
    try:
        user = await auth_service.get_user_by_id(db, current_user.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.createdAt
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.post(
    "/google",
    response_model=AuthResponse,
    summary="Google OAuth login",
    description="Authenticate with Google OAuth ID token. Creates user if doesn't exist.",
    responses={
        200: {"description": "Login successful"},
        400: {"model": ErrorResponse, "description": "Invalid token"},
        422: {"description": "Validation error"}
    }
)
async def google_auth(
    request: GoogleAuthRequest,
    db: Prisma = Depends(get_client)
):
    """
    Authenticate with Google OAuth.
    
    - **id_token**: Google ID token from OAuth flow
    
    Returns JWT access token and user information.
    """
    try:
        # TODO: Implement Google OAuth verification
        # For now, return a placeholder error
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not yet implemented. Use email/password authentication."
        )
        
        # Example implementation:
        # from google.oauth2 import id_token
        # from google.auth.transport import requests
        # 
        # idinfo = id_token.verify_oauth2_token(
        #     request.id_token,
        #     requests.Request(),
        #     settings.GOOGLE_CLIENT_ID
        # )
        # 
        # email = idinfo['email']
        # name = idinfo.get('name', '')
        # 
        # # Find or create user
        # user = await auth_service.get_user_by_email(db, email)
        # if not user:
        #     result = await auth_service.register_user(db, name, email, "")
        # else:
        #     result = {
        #         "user": user,
        #         "access_token": auth_service.create_access_token(user.id, user.email)
        #     }
        # 
        # return AuthResponse(...)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google token"
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Logout current user (client should discard JWT token).",
    responses={
        204: {"description": "Logout successful"},
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def logout(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Logout current user.
    
    Since JWT tokens are stateless, this endpoint mainly serves as a confirmation.
    The client should discard the JWT token after calling this endpoint.
    """
    logger.info(f"User logged out: {current_user.user_id}")
    return None


@router.get(
    "/health",
    summary="Health check",
    description="Check if the authentication service is operational."
)
async def health_check():
    """
    Health check endpoint for authentication service.
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "jwt_configured": bool(auth_service.secret_key)
    }
