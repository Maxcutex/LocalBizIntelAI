"""ETL orchestration service."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from services.dependencies import EtlOrchestrationServiceDependencies


class ETLOrchestrationService:
    """Triggers and monitors ETL workflows from admin endpoints."""

    def __init__(self, dependencies: EtlOrchestrationServiceDependencies) -> None:
        self._pubsub_client = dependencies.pubsub_client

    def trigger_adhoc_etl(
        self,
        db_session: Session,
        dataset: str,
        country: str | None,
        city: str | None,
        options: dict[str, Any] | None,
        triggered_by_user_id: UUID,
        triggered_by_tenant_id: UUID,
    ) -> dict[str, Any]:
        """
        Publish a request to run an ad-hoc ETL job.

        Args:
            dataset: Dataset identifier to ingest (e.g., "demographics").
            country: Optional country filter for ingestion.
            city: Optional city filter for ingestion.
            options: Optional provider/job options.
            triggered_by_user_id: Admin user triggering the run.
            triggered_by_tenant_id: Tenant of the admin user.
        """
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "dataset": dataset,
            "country": country,
            "city": city,
            "options": options or {},
            "requested_at": now.isoformat(),
            "triggered_by_user_id": str(triggered_by_user_id),
            "triggered_by_tenant_id": str(triggered_by_tenant_id),
        }

        self._pubsub_client.publish_ingestion_job(
            topic="ingestion-jobs",
            message=payload,
        )

        logging.getLogger(__name__).info(
            "Queued ingestion job",
            extra={
                "job_name": "adhoc-etl-run",
                "dataset": dataset,
                "country": country,
                "city": city,
                "requested_at": payload["requested_at"],
                "triggered_by_user_id": str(triggered_by_user_id),
                "triggered_by_tenant_id": str(triggered_by_tenant_id),
            },
        )

        # TODO: Optionally persist this request to an `admin_actions` table once
        # the model/migration is introduced.
        _ = db_session

        return {"status": "QUEUED", "payload": payload}
