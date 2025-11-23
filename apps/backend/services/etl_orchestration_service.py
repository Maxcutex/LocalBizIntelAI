"""ETL orchestration service."""

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

        # TODO: Optionally persist this request to an `admin_actions` table once
        # the model/migration is introduced.
        _ = db_session

        return {"status": "QUEUED", "payload": payload}
