from __future__ import annotations
from supabase import create_client, Client
from app.core.config import settings

_client: Client | None = None

def get_supabase_client() -> Client:
    """
    Returns a singleton Supabase client using SUPABASE_PROJECT_URL and
    SUPABASE_JWT_SECRET (or SUPABASE_KEY as fallback).
    """
    global _client
    if _client is not None:
        return _client

    url = settings.SUPABASE_PROJECT_URL
    key = settings.SUPABASE_JWT_SECRET or settings.SUPABASE_KEY
    if not url or not key:
        raise RuntimeError(
            "Supabase credentials missing: set SUPABASE_PROJECT_URL and SUPABASE_JWT_SECRET/SUPABASE_KEY in .env"
        )

    _client = create_client(url, key)
    return _client
