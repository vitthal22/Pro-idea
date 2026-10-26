"""Application settings.

Single source of truth for configuration. Values come from environment
variables (a `.env` file at the backend root is supported). Different
environments differ only in their env values — never in code.
"""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration, loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str | None = None
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "resume_roaster"
    redis_url: str = "redis://localhost:6379/0"

    # AI provider (never hardcode models in code — read from here)
    ai_provider: str = "openai"
    ai_model: str = "gpt-4o"
    ai_fast_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Auth
    jwt_secret_key: str = "change-this-to-a-random-string-at-least-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # Storage
    storage_backend: str = "local"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    # App
    app_env: str = "development"
    app_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    # Rate limiting
    rate_limit_free: int = 3
    rate_limit_pro: int = 50
    login_rate_limit_per_hour: int = 10

    # User store: "memory" (tests, zero infra) or "postgres" (real database)
    user_store: str = "memory"

    # Revoked-token store: "memory" now; "redis" once Redis is available
    denylist_store: str = "memory"

    # Demo account seeded at startup when both values are set
    demo_user_email: str | None = None
    demo_user_password: str | None = None
    demo_user_name: str = "Demo User"

    @property
    def database_dsn(self) -> str:
        """Async SQLAlchemy DSN.

        ``DATABASE_URL`` wins when set; otherwise the DSN is assembled from
        the ``DB_*`` parts. The password is URL-encoded so characters like
        ``@`` cannot break the URL.
        """
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.db_user}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse the comma-separated CORS_ORIGINS env var."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def cookie_secure(self) -> bool:
        """Send auth cookies over HTTPS only outside local development."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()


settings = get_settings()
