"""
Application configuration module.

Central place for environment-driven configuration using Pydantic.
"""

import json
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )

    # App metadata
    app_name: str = "LocalBizIntel Backend API"
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    debug: bool = True

    # JWT / auth settings
    jwt_secret_key: str = Field(default="change-me", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_issuer: str = Field(default="localbizintel", validation_alias="JWT_ISSUER")
    jwt_audience: str = Field(
        default="localbizintel-clients", validation_alias="JWT_AUDIENCE"
    )
    jwt_access_token_ttl_min: int = Field(
        default=30, validation_alias="JWT_ACCESS_TOKEN_TTL_MIN"
    )

    cors_allowed_origins_raw: str | None = Field(
        default=None, validation_alias="CORS_ALLOWED_ORIGINS"
    )

    # OpenAI / LLM settings
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_timeout_s: float = Field(default=25.0, validation_alias="OPENAI_TIMEOUT_S")

    # Postgres configuration (explicit components, not a single URL)
    pg_host: str = Field(default="localhost", validation_alias="PG_HOST")
    pg_port: int = Field(default=5432, validation_alias="PG_PORT")
    pg_database: str = Field(default="localbizintel", validation_alias="PG_DATABASE")
    pg_user: str = Field(default="localbizintel", validation_alias="PG_USER")
    pg_password: str = Field(default="localbizintel", validation_alias="PG_PASSWORD")

    @property
    def cors_allowed_origins(self) -> list[str]:
        raw_value = self.cors_allowed_origins_raw
        if raw_value is None:
            return []

        stripped = str(raw_value).strip()
        if not stripped:
            return []

        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass

        return [origin.strip() for origin in stripped.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        Build a SQLAlchemy-compatible database URI from individual PG_* components.

        Example:
            postgresql+psycopg://user:password@host:port/database
        """

        return (
            f"postgresql+psycopg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached access to application settings.

    Using a cache here ensures we only read and parse environment
    variables once per process.
    """

    return Settings()
