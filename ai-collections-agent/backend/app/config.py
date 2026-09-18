"""
Configuration module — loads all environment variables via pydantic-settings.
No secrets are hardcoded; everything comes from .env or environment.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # ── Paytm ──────────────────────────────────────────────────────────────
    PAYTM_MID: str = "YOUR_TEST_MID"
    PAYTM_MERCHANT_KEY: str = "YOUR_TEST_KEY"
    PAYTM_WEBSITE: str = "WEBSTAGING"
    PAYTM_ENVIRONMENT: str = "STAGING"
    PAYTM_CALLBACK_URL: str = "http://localhost:8000/webhooks/paytm"
    PAYTM_STAGING_BASE: str = "https://securegw-stage.paytm.in"

    # ── Gemini ─────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = "your_gemini_key"

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/ai_collections"

    # ── Redis ──────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── App ────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
