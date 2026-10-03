from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "FinSentry"

    API_SECRET_KEY: str = Field(default="dev_secret_key_change_in_production")

    OPENAI_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")

    FAST_MODEL: str = "gpt-4o-mini"
    REASONING_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "sec_financial_filings"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    LANGFUSE_PUBLIC_KEY: str = Field(default="")
    LANGFUSE_SECRET_KEY: str = Field(default="")
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    SEC_EDGAR_USER_AGENT: str = Field(
        default="FinSentryAuditEngine analyst@finsentry.org",
        description="Required user agent for SEC EDGAR API compliance."
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
