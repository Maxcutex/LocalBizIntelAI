"""Unit tests for configuration settings."""

from api.config import Settings


def test_settings_builds_sqlalchemy_uri_from_components():
    """SQLAlchemy URI is built correctly from PG_* components."""
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
