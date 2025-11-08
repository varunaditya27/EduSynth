"""
Authentication models for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    """Request model for user signup."""
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=72, description="User's password (min 8 chars, max 72 bytes for bcrypt)")


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., max_length=72, description="User's password")


class AuthResponse(BaseModel):
    """Response model for successful authentication."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: "UserResponse" = Field(..., description="Authenticated user information")


class UserResponse(BaseModel):
    """User information response."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User's email address")
    name: Optional[str] = Field(None, description="User's full name")
    created_at: datetime = Field(..., description="Account creation timestamp")


class GoogleAuthRequest(BaseModel):
    """Request model for Google OAuth authentication."""
    id_token: str = Field(..., description="Google ID token from OAuth flow")


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""
    email: EmailStr = Field(..., description="User's email address")


class PasswordResetConfirm(BaseModel):
    """Request model to confirm password reset with token."""
    token: str = Field(..., description="Reset token from email")
    new_password: str = Field(..., min_length=8, max_length=72, description="New password (max 72 bytes for bcrypt)")


class ChangePasswordRequest(BaseModel):
    """Request model to change password (authenticated user)."""
    current_password: str = Field(..., max_length=72, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=72, description="New password (max 72 bytes for bcrypt)")
