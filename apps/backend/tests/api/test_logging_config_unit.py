"""Unit tests for structured logging configuration."""

import json
import logging

import pytest

from api.config import Settings
from api.logging_config import JsonLogFormatter, configure_logging


def test_json_log_formatter_emits_structured_payload() -> None:
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
        settings = Settings(
            sentry_dsn="https://example@o0.ingest.sentry.io/0",
            datadog_api_key="dummy",
            gcp_logging_enabled=True,
            aws_cloudwatch_enabled=True,
            aws_cloudwatch_log_group="localbizintel-test",
        )
        with caplog.at_level(logging.WARNING):
            configure_logging(settings)
        # We expect warnings if SDKs are missing, but no exception.
        assert any("not installed" in record.message for record in caplog.records)
    finally:
        root = logging.getLogger()
        root.handlers.clear()
        for h in previous_handlers:
            root.addHandler(h)
        root.setLevel(previous_level)
