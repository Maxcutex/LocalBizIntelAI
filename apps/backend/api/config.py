"""
Application configuration module.

Central place for environment-driven configuration using Pydantic.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # App metadata
    app_name: str = "LocalBizIntel Backend API"
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    debug: bool = True

    # Postgres configuration (explicit components, not a single URL)
    pg_host: str = Field(default="localhost", validation_alias="PG_HOST")
    pg_port: int = Field(default=5432, validation_alias="PG_PORT")
    pg_database: str = Field(default="localbizintel", validation_alias="PG_DATABASE")
    pg_user: str = Field(default="localbizintel", validation_alias="PG_USER")
    pg_password: str = Field(default="localbizintel", validation_alias="PG_PASSWORD")

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
