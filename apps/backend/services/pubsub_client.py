"""Local stub Pub/Sub client for background report jobs.

TODO: Replace with real GCP Pub/Sub publisher when infrastructure is ready.
"""

from typing import Any


class PubSubClient:
    """Publish messages to background worker topics."""

    def publish_report_job(self, topic: str, message: dict[str, Any]) -> None:
        # TODO: Implement real publish. For now this is a no-op stub.
        _ = topic
        _ = message

    def publish_ingestion_job(self, topic: str, message: dict[str, Any]) -> None:
        # TODO: Implement real publish. For now this is a no-op stub.
        _ = topic
        _ = message
