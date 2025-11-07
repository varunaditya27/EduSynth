# backend/app/deps/auth.py

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

from app.core.config import settings

security = HTTPBearer()


class CurrentUser(BaseModel):
    """Current authenticated user model"""
    user_id: str
    email: Optional[str] = None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Verify Supabase JWT token and extract user information.
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        CurrentUser with user_id and optional email
        
    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    token = credentials.credentials
    
    try:
        # Decode JWT using HS256 algorithm with Supabase secret
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase tokens may not have aud
        )
        
        # Extract user_id from 'sub' claim (standard JWT claim for subject)
        # Fallback to 'uid' if 'sub' is not present (some auth systems use uid)
        user_id = payload.get("sub") or payload.get("uid")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="UNAUTHENTICATED: Missing user identifier in token"
            )
        
        # Extract email if present (optional claim)
        email = payload.get("email")
        
        return CurrentUser(user_id=user_id, email=email)
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"UNAUTHENTICATED: Invalid token - {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"UNAUTHENTICATED: {str(e)}"
        )