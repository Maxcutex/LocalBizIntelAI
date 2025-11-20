"""
Application configuration module.

Central place for environment-driven configuration using Pydantic.
"""

from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "LocalBizIntel Backend API"
    environment: str = "local"
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached access to application settings.

    Using a cache here ensures we only read and parse environment
    variables once per process.
    """

    return Settings()


