"""Unit tests for structured logging configuration."""

import json
import logging
from contextlib import contextmanager
from typing import Any

import pytest

from api.config import Settings
from api.logging_config import JsonLogFormatter, configure_logging


@contextmanager
def _disable_dotenv_for_settings() -> Any:
    old_env_file = Settings.model_config.get("env_file")
    Settings.model_config["env_file"] = None
    try:
        yield
    finally:
        Settings.model_config["env_file"] = old_env_file


def test_json_log_formatter_emits_structured_payload() -> None:
    with _disable_dotenv_for_settings():
        settings = Settings()
    formatter = JsonLogFormatter(service_name=settings.log_service_name)
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )
    rendered = formatter.format(record)
    payload = json.loads(rendered)

    assert payload["level"] == "INFO"
    assert payload["service"] == settings.log_service_name
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "hello"
    assert "timestamp" in payload


def test_json_log_formatter_includes_extra_fields() -> None:
    formatter = JsonLogFormatter(service_name="svc")
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.user_id = "abc"  # type: ignore[attr-defined]
    record.city = "Toronto"  # type: ignore[attr-defined]

    payload = json.loads(formatter.format(record))
    assert payload["fields"]["user_id"] == "abc"
    assert payload["fields"]["city"] == "Toronto"


def test_configure_logging_with_provider_credentials_does_not_crash(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Provider auto-wiring should be safe even if SDKs are not installed."""
    previous_handlers = list(logging.getLogger().handlers)
    previous_level = logging.getLogger().level
    try:
        with _disable_dotenv_for_settings():
            settings = Settings(
                sentry_dsn="https://example@o0.ingest.sentry.io/0",
                datadog_api_key="dummy",
                gcp_logging_enabled=True,
                aws_cloudwatch_enabled=True,
                aws_cloudwatch_log_group="localbizintel-test",
            )
        # `configure_logging` replaces root handlers, which interferes with caplog's
        # handler. This test focuses on "does not crash" when credentials are present.
        configure_logging(settings)
    finally:
        root = logging.getLogger()
        root.handlers.clear()
        for h in previous_handlers:
            root.addHandler(h)
        root.setLevel(previous_level)
