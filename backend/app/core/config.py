# backend/app/core/config.py

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file from backend directory
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)


class Settings(BaseSettings):
    # Database (Supabase Postgres via Prisma)
    DATABASE_URL: str
    DIRECT_URL: str

    # Supabase Auth (JWT)
    SUPABASE_JWT_SECRET: str = "your-jwt-secret"
    SUPABASE_PROJECT_URL: str
    SUPABASE_KEY: Optional[str] = None

    # Cloudflare R2 - matching exact .env variable names
    CLOUDFLARE_S3_ENDPOINT: str
    CLOUDFLARE_S3_ACCESS_KEY_ID: str  # Matches .env exactly
    CLOUDFLARE_S3_SECRET_ACCESS_KEY: str  # Matches .env exactly
    CLOUDFLARE_S3_BUCKET_NAME: str  # Matches .env exactly
    CLOUDFLARE_API_TOKEN_VALUE: Optional[str] = None

    # Unsplash
    UNSPLASH_ACCESS_KEY: str
    UNSPLASH_SECRET_KEY: str

    # AI APIs
    GEMINI_API_KEY: str
    GROQ_API_KEY: str
    ELEVEN_API_KEY: str

    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        """Parse CORS_ORIGINS from JSON array string or comma-separated"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except:
                    pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return ["http://localhost:3000"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
