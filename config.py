import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""

    # MySQL connection string
    DATABASE_URL: str = "sqlite:///./aurex_hms.db"

    # Secret keys for signing session tokens and CSRF protection
    APP_SECRET_KEY: str = "aurex-hms-secret-key-super-secure-at-least-32-chars-long"
    CSRF_SECRET_KEY: str = "aurex-hms-csrf-secret-key-at-least-32-chars-long"

    # Frontend origins permitted for CORS (comma-separated)
    FRONTEND_ORIGINS: str = (
        "http://127.0.0.1:3001,http://localhost:3001,"
        "http://127.0.0.1:3000,http://localhost:3000,"
        "http://127.0.0.1:5173,http://localhost:5173"
    )

    # Cookie settings
    COOKIE_SECURE: bool = False  # Set to True in production with HTTPS
    SESSION_TTL_HOURS: int = 8

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return list of allowed CORS origins."""
        return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]


# Global settings singleton
settings = Settings()
