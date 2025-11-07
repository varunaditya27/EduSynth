from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


class CurrentUser(BaseModel):
    user_id: str
    email: Optional[str] = None


def _dev_bypass_enabled() -> bool:
    # Any truthy value enables bypass (true/1/yes)
    return os.getenv("SUPABASE_DEV_BYPASS", "false").strip().lower() in {"true", "1", "yes"}


def _unauthenticated() -> HTTPException:
    return HTTPException(status_code=401, detail="UNAUTHENTICATED")


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> CurrentUser:
    """
    Dev-friendly auth dependency:
    - If SUPABASE_DEV_BYPASS=true -> returns a fixed dev user regardless of header
    - Else requires 'Authorization: Bearer <jwt>' and verifies with SUPABASE_JWT_SECRET (HS256)
    - On any failure, raises 401 (NOT 422)
    """
    # Local dev bypass
    if _dev_bypass_enabled():
        return CurrentUser(user_id="dev-user", email="dev@local")

    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthenticated()

    token = authorization.split(" ", 1)[1].strip()
    secret = settings.SUPABASE_JWT_SECRET
    if not secret:
        # If secret is not configured, fail fast (or allow only in dev via bypass)
        raise _unauthenticated()

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError:
        raise _unauthenticated()

    # prefer 'sub', fallback 'uid'
    user_id = (payload.get("sub") or payload.get("uid"))
    if not user_id:
        raise _unauthenticated()

    email = payload.get("email")
    return CurrentUser(user_id=str(user_id), email=email)
