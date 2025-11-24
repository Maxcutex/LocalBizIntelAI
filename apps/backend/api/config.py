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

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", validation_alias="LOG_LEVEL"
    )
    log_json: bool = Field(default=True, validation_alias="LOG_JSON")
    log_service_name: str = Field(
        default="localbizintel-backend", validation_alias="LOG_SERVICE_NAME"
    )
    log_request_body: bool = Field(default=False, validation_alias="LOG_REQUEST_BODY")
    log_response_body: bool = Field(default=False, validation_alias="LOG_RESPONSE_BODY")
    log_body_max_bytes: int = Field(default=4096, validation_alias="LOG_BODY_MAX_BYTES")
    log_redact_keys: list[str] = Field(
        default_factory=lambda: [
            "password",
            "access_token",
            "refresh_token",
            "jwt",
            "api_key",
            "authorization",
        ],
        validation_alias="LOG_REDACT_KEYS",
    )

    # Observability providers (auto-enabled when credentials are present)
    # Sentry
    sentry_dsn: str | None = Field(default=None, validation_alias="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(
        default=0.0, validation_alias="SENTRY_TRACES_SAMPLE_RATE"
    )

    # Datadog: logs are shipped via agent; API key enables trace/log correlation.
    datadog_api_key: str | None = Field(
        default=None, validation_alias="DATADOG_API_KEY"
    )
    datadog_site: str = Field(default="datadoghq.com", validation_alias="DATADOG_SITE")
    datadog_service_name: str | None = Field(
        default=None, validation_alias="DATADOG_SERVICE_NAME"
    )

    # Google Cloud Logging direct handler (optional; stdout JSON also works with GCP)
    gcp_logging_enabled: bool = Field(
        default=False, validation_alias="GCP_LOGGING_ENABLED"
    )

    # AWS CloudWatch direct handler (optional; stdout JSON also works via agent).
    aws_cloudwatch_enabled: bool = Field(
        default=False, validation_alias="AWS_CLOUDWATCH_ENABLED"
    )
    aws_region: str | None = Field(default=None, validation_alias="AWS_REGION")
    aws_cloudwatch_log_group: str | None = Field(
        default=None, validation_alias="AWS_CLOUDWATCH_LOG_GROUP"
    )
    aws_cloudwatch_log_stream: str | None = Field(
        default=None, validation_alias="AWS_CLOUDWATCH_LOG_STREAM"
    )

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

    # OpenStreetMap / Overpass settings for business density ingestion
    osm_overpass_endpoint: str = Field(
        default="https://overpass-api.de/api/interpreter",
        validation_alias="OSM_OVERPASS_ENDPOINT",
    )
    osm_overpass_timeout_s: float = Field(
        default=45.0, validation_alias="OSM_OVERPASS_TIMEOUT_S"
    )
    osm_overpass_query_timeout_s: int = Field(
        default=30, validation_alias="OSM_OVERPASS_QUERY_TIMEOUT_S"
    )
    osm_overpass_user_agent: str = Field(
        default="LocalBizIntelAI/0.1",
        validation_alias="OSM_OVERPASS_USER_AGENT",
    )
    osm_max_coordinate_samples: int = Field(
        default=1000, validation_alias="OSM_MAX_COORDINATE_SAMPLES"
    )
    osm_default_country: str = Field(
        default="NA", validation_alias="OSM_DEFAULT_COUNTRY"
    )
    osm_city_geo_id_suffix: str = Field(
        default="citywide", validation_alias="OSM_CITY_GEO_ID_SUFFIX"
    )
    osm_business_type_specs: dict[str, dict[str, str]] = Field(
        default_factory=lambda: {
            "cafes": {"tag_key": "amenity", "tag_value": "cafe"},
            "restaurants": {"tag_key": "amenity", "tag_value": "restaurant"},
            "gyms": {"tag_key": "leisure", "tag_value": "fitness_centre"},
        },
        validation_alias="OSM_BUSINESS_TYPE_SPECS",
    )

    @property
    def cors_allowed_origins(self) -> list[str]:
        """Parse `CORS_ALLOWED_ORIGINS` into a list of allowed origins."""
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
