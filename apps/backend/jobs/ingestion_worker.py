"""Local ingestion worker stub.

Consumes a Pub/Sub-style JSON payload and dispatches to concrete ETL jobs.
This mirrors the eventual background worker runtime.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.orm import Session

from jobs.business_density_etl_job import BusinessDensityEtlJob
from jobs.demographics_etl_job import DemographicsEtlJob
from jobs.labour_stats_etl_job import LabourStatsEtlJob
from jobs.spending_etl_job import SpendingEtlJob

logger = logging.getLogger(__name__)


@dataclass
class IngestionMessage:
    """Canonical ingestion message structure."""

    job_name: str | None
    dataset: str
    country: str | None
    city: str | None
    options: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "IngestionMessage":
        job_name = payload.get("job_name")
        resolved_job_name = str(job_name) if isinstance(job_name, str) else None

        dataset_value = payload.get("dataset")
        if isinstance(dataset_value, str) and dataset_value.strip():
            dataset = dataset_value
        elif resolved_job_name:
            # Support the spec's envelope where `job_name` may drive the handler.
            dataset = resolved_job_name
        else:
            dataset = ""
        return cls(
            job_name=resolved_job_name,
            dataset=dataset,
            country=payload.get("country"),
            city=payload.get("city"),
            options=payload.get("options") or {},
        )


class IngestionHandler(Protocol):
    """Interface for dataset-specific ingestion jobs."""

    def run(
        self,
        *,
        db_session: Session,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
    ) -> Any:
        raise NotImplementedError


class IngestionWorker:
    """Dispatch ingestion messages to dataset-specific jobs."""

    def __init__(self, *, handlers_by_dataset: dict[str, IngestionHandler]) -> None:
        self._handlers_by_dataset = {
            self._normalize_dataset_name(name): handler
            for name, handler in handlers_by_dataset.items()
        }

    @classmethod
    def create_default(cls) -> "IngestionWorker":
        # TODO(architecture): Temporary local wiring. Move to a central
        # `dependencies`/bootstrap module once the ingestion worker runtime exists.
        business_density_job = BusinessDensityEtlJob.create_default()
        demographics_job = DemographicsEtlJob.create_default()
        labour_stats_job = LabourStatsEtlJob.create_default()
        spending_job = SpendingEtlJob.create_default()
        return cls(
            handlers_by_dataset={
                "business_density": business_density_job,
                "business-density-refresh": business_density_job,
                "demographics": demographics_job,
                "census-demographics-refresh": demographics_job,
                "labour": labour_stats_job,
                "labour-stats-refresh": labour_stats_job,
                "labour_stats": labour_stats_job,
                "spending": spending_job,
                "spending-stats-refresh": spending_job,
            }
        )

    def consume(
        self, *, db_session: Session, payload: dict[str, Any]
    ) -> dict[str, Any]:
        message = IngestionMessage.from_payload(payload)
        normalized_dataset = self._normalize_dataset_name(message.dataset)
        handler = self._handlers_by_dataset.get(normalized_dataset)
        if not handler:
            logger.error(
                "Unsupported ingestion dataset",
                extra={"dataset": message.dataset},
            )
            raise ValueError(f"Unsupported ingestion dataset: {message.dataset}")

        logger.info(
            "Consuming ingestion message",
            extra={
                "dataset": normalized_dataset,
                "country": message.country,
                "city": message.city,
            },
        )
        result = handler.run(
            db_session=db_session,
            country=message.country,
            city=message.city,
            options=message.options,
        )
        output = result.__dict__
        logger.info(
            "Ingestion message processed",
            extra={
                "dataset": normalized_dataset,
                "status": output.get("status"),
                "row_count": output.get("row_count"),
            },
        )
        return output

    def _normalize_dataset_name(self, dataset_name: str) -> str:
        return dataset_name.lower().replace("-", "_").strip()
