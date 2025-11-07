# backend/app/core/config.py

from functools import lru_cache
from typing import List, Optional, Union

from pydantic import AliasChoices, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database (Supabase Postgres via Prisma)
    DATABASE_URL: str
    DIRECT_URL: str

    # Supabase Auth (JWT)
    SUPABASE_JWT_SECRET: str = "your-jwt-secret"
    SUPABASE_PROJECT_URL: str

    # Cloudflare R2 (accept both naming styles)
    CLOUDFLARE_S3_ENDPOINT: str
    CLOUDFLARE_S3_ACCESS_KEY: str = Field(
        validation_alias=AliasChoices(
            "CLOUDFLARE_S3_ACCESS_KEY",
            "CLOUDFLARE_S3_ACCESS_KEY_ID",
        )
    )
    CLOUDFLARE_S3_SECRET_KEY: str = Field(
        validation_alias=AliasChoices(
            "CLOUDFLARE_S3_SECRET_KEY",
            "CLOUDFLARE_S3_SECRET_ACCESS_KEY",
        )
    )
    CLOUDFLARE_S3_BUCKET: str = Field(
        validation_alias=AliasChoices(
            "CLOUDFLARE_S3_BUCKET",
            "CLOUDFLARE_S3_BUCKET_NAME",
        )
    )
    # Optional API token if you ever use it for R2 ops
    CLOUDFLARE_API_TOKEN_VALUE: Optional[str] = None

    # Unsplash
    UNSPLASH_ACCESS_KEY: str
    UNSPLASH_SECRET_KEY: str

    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=list)

    # pydantic-settings v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Accepts:
        - JSON array: '["http://localhost:3000"]'
        - Comma-separated string: 'http://a.com,http://b.com'
        - Single string: 'http://localhost:3000'
        """
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                # Try JSON parse without importing json to keep deps minimal
                try:
                    import json

                    arr = json.loads(s)
                    if isinstance(arr, list):
                        return [str(x).strip() for x in arr]
                except Exception:
                    pass
            # fallback: comma-separated or single
            return [p.strip() for p in s.split(",") if p.strip()]
        raise ValidationError("CORS_ORIGINS must be a list or string")

@lru_cache()
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
