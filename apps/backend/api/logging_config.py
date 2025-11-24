"""Structured logging configuration.

Default behavior:
- Emit JSON logs to stdout (portable across Datadog, GCP, AWS, ELK, etc.).

Optional direct provider handlers:
- If provider credentials/config are present AND the relevant SDK is installed,
  we auto-wire a handler/SDK:
  - Sentry: capture errors/exceptions.
  - GCP Cloud Logging: direct Cloud Logging handler.
  - AWS CloudWatch Logs: direct CloudWatch handler.
  - Datadog: enable trace/log correlation when ddtrace is installed.

This keeps logging provider-agnostic while making it plug-and-play.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from api.config import Settings


class JsonLogFormatter(logging.Formatter):
    """Formats log records as a single-line JSON object."""

    def __init__(self, *, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "service": self._service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Attach user-provided structured fields (logger.info("msg", extra={...}))
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key
            not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }
        }
        if extra_fields:
            payload["fields"] = extra_fields

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings) -> None:
    """Configure root logging for the application."""

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    base_handler = logging.StreamHandler(stream=sys.stdout)
    if settings.log_json:
        formatter: logging.Formatter = JsonLogFormatter(
            service_name=settings.log_service_name
        )
        base_handler.setFormatter(formatter)
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        base_handler.setFormatter(formatter)

    # Replace existing handlers to avoid duplicate logs under Uvicorn.
    root_logger.handlers.clear()
    root_logger.addHandler(base_handler)

    _configure_optional_providers(settings, root_logger, formatter)

    # Ensure Uvicorn loggers propagate through the root handler.
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(uvicorn_logger_name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
        uv_logger.setLevel(settings.log_level)


def _configure_optional_providers(
    settings: Settings, root_logger: logging.Logger, formatter: logging.Formatter
) -> None:
    """Attach optional provider integrations based on settings + installed SDKs."""
    _try_configure_sentry(settings)
    _try_configure_datadog(settings)
    _try_attach_gcp_handler(settings, root_logger, formatter)
    _try_attach_aws_cloudwatch_handler(settings, root_logger, formatter)


def _try_configure_sentry(settings: Settings) -> None:
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk  # type: ignore[import-untyped,import-not-found]

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            environment=settings.environment,
            release=None,
        )
        logging.getLogger(__name__).info(
            "Sentry logging enabled",
            extra={"provider": "sentry", "environment": settings.environment},
        )
    except ImportError:
        logging.getLogger(__name__).warning(
            "Sentry DSN provided but sentry-sdk not installed",
            extra={"provider": "sentry"},
        )


def _try_configure_datadog(settings: Settings) -> None:
    """Enable Datadog trace/log correlation when ddtrace is installed.

    Datadog logs are usually shipped via agent from stdout; this enables
    correlation IDs automatically when DATADOG_API_KEY is set.
    """
    if not settings.datadog_api_key:
        return
    try:
        from ddtrace import (  # type: ignore[import-untyped,import-not-found]
            patch,
            tracer,
        )

        patch(logging=True)
        service = settings.datadog_service_name or settings.log_service_name
        tracer.configure(
            settings={"SERVICE": service},
        )
        logging.getLogger(__name__).info(
            "Datadog trace/log correlation enabled",
            extra={"provider": "datadog", "service": service},
        )
    except ImportError:
        logging.getLogger(__name__).warning(
            "Datadog API key provided but ddtrace not installed",
            extra={"provider": "datadog"},
        )


def _try_attach_gcp_handler(
    settings: Settings, root_logger: logging.Logger, formatter: logging.Formatter
) -> None:
    if not settings.gcp_logging_enabled:
        return
    try:
        import importlib

        gcp_logging = importlib.import_module(
            "google.cloud.logging"
        )  # type: ignore[import-not-found]
        handlers_mod = importlib.import_module(
            "google.cloud.logging.handlers"
        )  # type: ignore[import-not-found]
        CloudLoggingHandler = getattr(handlers_mod, "CloudLoggingHandler")

        client = gcp_logging.Client()
        handler = CloudLoggingHandler(client, name=settings.log_service_name)
        handler.setLevel(settings.log_level)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        logging.getLogger(__name__).info(
            "GCP Cloud Logging handler attached",
            extra={"provider": "gcp"},
        )
    except ImportError:
        logging.getLogger(__name__).warning(
            "GCP logging enabled but google-cloud-logging not installed",
            extra={"provider": "gcp"},
        )


def _try_attach_aws_cloudwatch_handler(
    settings: Settings, root_logger: logging.Logger, formatter: logging.Formatter
) -> None:
    if not settings.aws_cloudwatch_enabled:
        return
    if not settings.aws_cloudwatch_log_group:
        logging.getLogger(__name__).warning(
            "AWS CloudWatch enabled but log group not configured",
            extra={"provider": "aws"},
        )
        return
    try:
        import watchtower  # type: ignore[import-untyped,import-not-found]

        handler = watchtower.CloudWatchLogHandler(
            log_group=settings.aws_cloudwatch_log_group,
            stream_name=settings.aws_cloudwatch_log_stream,
            region_name=settings.aws_region,
        )
        handler.setLevel(settings.log_level)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        logging.getLogger(__name__).info(
            "AWS CloudWatch handler attached",
            extra={"provider": "aws"},
        )
    except ImportError:
        logging.getLogger(__name__).warning(
            "AWS CloudWatch enabled but watchtower not installed",
            extra={"provider": "aws"},
        )
