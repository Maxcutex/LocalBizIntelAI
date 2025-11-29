"""Unit tests for configuration settings."""

from contextlib import contextmanager
from typing import Any

from api.config import Settings


@contextmanager
def _disable_dotenv_for_settings() -> Any:
    old_env_file = Settings.model_config.get("env_file")
    Settings.model_config["env_file"] = None
    try:
        yield
    finally:
        Settings.model_config["env_file"] = old_env_file


def test_settings_builds_sqlalchemy_uri_from_components():
    """SQLAlchemy URI is built correctly from PG_* components."""
    with _disable_dotenv_for_settings():
        settings = Settings(
            pg_host="db.example.com",
            pg_port=6543,
            pg_database="localbizintel_test",
            pg_user="testuser",
            pg_password="secret",
        )

    assert (
        settings.sqlalchemy_database_uri
        == "postgresql+psycopg://testuser:secret@db.example.com:6543/localbizintel_test"
    )
