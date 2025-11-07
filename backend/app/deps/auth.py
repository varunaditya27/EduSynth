"""
Authentication dependency for FastAPI routes.
"""
from typing import Optional
from fastapi import Header, HTTPException
from pydantic import BaseModel
from jose import JWTError, jwt

from app.core.config import settings


class CurrentUser(BaseModel):
    """Authenticated user information."""
    user_id: str
    email: Optional[str] = None


async def get_current_user(authorization: str = Header(...)) -> CurrentUser:
    """
    Extract and verify JWT token from Authorization header.
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        CurrentUser with user_id and optional email
        
    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="UNAUTHENTICATED",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="UNAUTHENTICATED",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify JWT with HS256
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase tokens may not have aud
        )
        
        # Extract user_id (prefer 'sub', fallback to 'uid')
        user_id = payload.get("sub") or payload.get("uid")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="UNAUTHENTICATED",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Try to extract email if present
        email = payload.get("email")
        
        return CurrentUser(user_id=user_id, email=email)
        
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="UNAUTHENTICATED",
            headers={"WWW-Authenticate": "Bearer"},
        )