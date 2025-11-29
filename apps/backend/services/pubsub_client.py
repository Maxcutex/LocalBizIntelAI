"""Pub/Sub publisher client.

This publishes messages to GCP Pub/Sub when configured; otherwise it degrades to
a safe no-op (useful for local/dev and unit tests).
"""

from __future__ import annotations

import importlib
import json
import logging
import os
from typing import Any

from api.config import Settings, get_settings

logger = logging.getLogger(__name__)


def _try_import_pubsub() -> Any | None:
    """
    Import the GCP Pub/Sub SDK lazily.

    We avoid importing at module import time because some environments (sandboxed
    runners, minimal containers) restrict filesystem operations performed by the
    SDK import machinery. When import fails, we degrade safely to a no-op.
    """
    try:
        return importlib.import_module("google.cloud.pubsub_v1")
    except (ModuleNotFoundError, ImportError, PermissionError, OSError) as exc:
        logger.warning(
            "Pub/Sub SDK unavailable; will no-op publishes",
            extra={"error": str(exc), "sdk_module": "google.cloud.pubsub_v1"},
        )
        return None


class PubSubClient:
    """Publish messages to background worker topics."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        publisher_client: Any | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._publisher_client = publisher_client

    def publish_report_job(self, topic: str, message: dict[str, Any]) -> None:
        self._publish(topic=topic, message=message, kind="report_job")

    def publish_ingestion_job(self, topic: str, message: dict[str, Any]) -> None:
        self._publish(topic=topic, message=message, kind="ingestion_job")

    def publish_embedding_job(self, topic: str, message: dict[str, Any]) -> None:
        self._publish(topic=topic, message=message, kind="embedding_job")

    def _publish(self, *, topic: str, message: dict[str, Any], kind: str) -> None:
        if not self._settings.pubsub_enabled:
            logger.info(
                "Pub/Sub disabled; skipping publish",
                extra={"topic": topic, "kind": kind},
            )
            return

        pubsub_v1 = _try_import_pubsub()
        if pubsub_v1 is None:
            return

        project_id = (
            self._settings.gcp_project_id
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
            or os.environ.get("GCP_PROJECT")
        )
        if not project_id:
            logger.warning(
                "Missing GCP project id; skipping publish",
                extra={"topic": topic, "kind": kind},
            )
            return

        publisher = self._publisher_client or pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic)
        data = json.dumps(message, default=str).encode("utf-8")

        try:
            publisher.publish(topic_path, data=data)
            logger.info(
                "Published Pub/Sub message",
                extra={"topic": topic, "kind": kind, "topic_path": topic_path},
            )
        except Exception:
            logger.error(
                "Failed to publish Pub/Sub message",
                exc_info=True,
                extra={"topic": topic, "kind": kind, "topic_path": topic_path},
            )
            raise
