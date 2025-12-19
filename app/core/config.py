"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="WhatsApp Sender API", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(default="change-this-secret-key-in-production", alias="SECRET_KEY")

    # Database
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="whatsapp_sender", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="postgres123", alias="DB_PASSWORD")

    @property
    def database_url(self) -> str:
        """Build database URL from components."""
        return (
            f"postgresql+asyncpg://{self.db_user}:"
            f"{self.db_password}@{self.db_host}:"
            f"{self.db_port}/{self.db_name}"
        )

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

    @property
    def redis_url(self) -> str:
        """Build Redis URL from components."""
        password = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{password}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # WhatsApp API
    whatsapp_access_token: str = Field(default="your-token-here", alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field(default="your-phone-id", alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_business_account_id: str = Field(default="your-waba-id", alias="WHATSAPP_BUSINESS_ACCOUNT_ID")

    # Campaign Settings
    campaign_max_recipients: int = Field(default=1000, alias="CAMPAIGN_MAX_RECIPIENTS")
    campaign_batch_size:  int = Field(default=50, alias="CAMPAIGN_BATCH_SIZE")
    campaign_delay_between_batches: int = Field(default=60, alias="CAMPAIGN_DELAY_BETWEEN_BATCHES")

    # Retry Settings
    max_retry_attempts: int = Field(default=3, alias="MAX_RETRY_ATTEMPTS")
    retry_delay_seconds: int = Field(default=5, alias="RETRY_DELAY_SECONDS")
    retry_backoff_multiplier: int = Field(default=2, alias="RETRY_BACKOFF_MULTIPLIER")

    # Cost Settings
    cost_per_message: float = Field(default=0.005, alias="COST_PER_MESSAGE")
    currency: str = Field(default="USD", alias="CURRENCY")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        alias="CORS_ORIGINS"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from string to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Sentry (Optional)
    sentry_dsn:  Optional[str] = Field(default=None, alias="SENTRY_DSN")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()