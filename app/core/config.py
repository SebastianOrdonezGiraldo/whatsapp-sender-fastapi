"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(default="WhatsApp Sender API", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")

    # Database
    db_host: str = Field(..., alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(..., alias="DB_NAME")
    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    database_url: Optional[str] = None

    @validator("database_url", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """Build database URL from components."""
        if isinstance(v, str):
            return v
        return (
            f"postgresql+asyncpg://{values.get('db_user')}:"
            f"{values.get('db_password')}@{values.get('db_host')}:"
            f"{values.get('db_port')}/{values.get('db_name')}"
        )

    # Redis
    redis_host: str = Field(..., alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_url: Optional[str] = None

    @validator("redis_url", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        """Build Redis URL from components."""
        if isinstance(v, str):
            return v
        password = values.get("redis_password")
        auth = f":{password}@" if password else ""
        return (
            f"redis://{auth}{values.get('redis_host')}:"
            f"{values.get('redis_port')}/{values.get('redis_db')}"
        )

    # WhatsApp API
    whatsapp_access_token: str = Field(..., alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field(..., alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_business_account_id: str = Field(..., alias="WHATSAPP_BUSINESS_ACCOUNT_ID")

    # Campaign Settings
    campaign_max_recipients: int = Field(default=1000, alias="CAMPAIGN_MAX_RECIPIENTS")
    campaign_batch_size: int = Field(default=50, alias="CAMPAIGN_BATCH_SIZE")
    campaign_delay_between_batches: int = Field(default=60, alias="CAMPAIGN_DELAY_BETWEEN_BATCHES")

    # Retry Settings
    max_retry_attempts: int = Field(default=3, alias="MAX_RETRY_ATTEMPTS")
    retry_delay_seconds: int = Field(default=5, alias="RETRY_DELAY_SECONDS")
    retry_backoff_multiplier: int = Field(default=2, alias="RETRY_BACKOFF_MULTIPLIER")

    # Cost Settings
    cost_per_message: float = Field(default=0.005, alias="COST_PER_MESSAGE")
    currency: str = Field(default="USD", alias="CURRENCY")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS"
    )

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Sentry (Optional)
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()