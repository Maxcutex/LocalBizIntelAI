"""Labour stats ETL job.

Concrete ETL pipeline for the "labour_stats" dataset.
It can be invoked by the ingestion worker consuming `ingestion-jobs` messages.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from sqlalchemy.orm import Session

from api.config import Settings, get_settings
from models.system import ETLLog
from repositories.data_freshness_repository import DataFreshnessRepository
from repositories.labour_stats_repository import LabourStatsRepository

logger = logging.getLogger(__name__)


class LabourStatsRepositoryProtocol(Protocol):
    """Abstraction for labour stats persistence."""

    def upsert_many(
        self,
        db_session: Session,
        rows: list[dict[str, Any]],
        last_updated: datetime,
    ) -> int:
        raise NotImplementedError


class DataFreshnessRepositoryProtocol(Protocol):
    """Abstraction for data freshness persistence."""

    def upsert_status(
        self,
        *,
        db_session: Session,
        dataset_name: str,
        last_run: datetime,
        row_count: int,
        status: str,
    ) -> Any:
        raise NotImplementedError


class LabourStatsSourceClient(Protocol):
    """Interface for fetching raw labour stats rows from an external provider."""

    def fetch_labour_stats(
        self,
        *,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
        settings: Settings,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class LocalStubLabourStatsSourceClient:
    """
    Deterministic local/dev source.

    In production, swap this for a real provider integration (e.g., BLS/ONS/StatCan).
    """

    def fetch_labour_stats(
        self,
        *,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
        settings: Settings,
    ) -> list[dict[str, Any]]:
        _ = options
        _ = settings

        resolved_country = country or "NA"
        resolved_city = city or "Unknown"
        slug = resolved_city.lower().replace(" ", "-")
        geo_ids = [f"{slug}-central", f"{slug}-north", f"{slug}-south"]

        rows: list[dict[str, Any]] = []
        for idx, geo_id in enumerate(geo_ids):
            # Keep these deterministic, stable, and within realistic ranges.
            rows.append(
                {
                    "geo_id": geo_id,
                    "country": resolved_country,
                    "city": resolved_city,
                    "unemployment_rate": 4.0 + (idx * 0.7),
                    "job_openings": 1000 + (idx * 250),
                    "median_salary": 55000 + (idx * 3000),
                    "labour_force_participation": 61.0 + (idx * 0.8),
                }
            )

        return rows


@dataclass
class LabourStatsEtlResult:
    """Result summary for a labour stats ETL run."""

    dataset_name: str
    status: str
    row_count: int
    country: str | None
    city: str | None


class LabourStatsEtlJob:
    """ETL job that loads labour stats rows into the database."""

    def __init__(
        self,
        *,
        labour_stats_repository: LabourStatsRepositoryProtocol,
        data_freshness_repository: DataFreshnessRepositoryProtocol,
        source_client: LabourStatsSourceClient,
        settings: Settings,
    ) -> None:
        self._labour_stats_repository = labour_stats_repository
        self._data_freshness_repository = data_freshness_repository
        self._source_client = source_client
        self._settings = settings

    @classmethod
    def create_default(cls) -> "LabourStatsEtlJob":
        # TODO(architecture): Temporary local wiring. Move to a central
        # `dependencies`/bootstrap module once the ingestion worker runtime exists.
        settings = get_settings()
        return cls(
            labour_stats_repository=LabourStatsRepository(),
            data_freshness_repository=DataFreshnessRepository(),
            source_client=LocalStubLabourStatsSourceClient(),
            settings=settings,
        )

    def run(
        self,
        *,
        db_session: Session,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
    ) -> LabourStatsEtlResult:
        """
        Execute one labour stats ETL run.

        Fetches raw rows from the source client, upserts them, updates freshness,
        and records an `ETLLog`.
        """
        dataset_name = "labour_stats"
        now = datetime.now(timezone.utc)
        resolved_options = options

        try:
            logger.info(
                "Starting ETL run",
                extra={
                    "dataset": dataset_name,
                    "country": country,
                    "city": city,
                    "job": dataset_name,
                },
            )
            raw_rows = self._source_client.fetch_labour_stats(
                country=country,
                city=city,
                options=resolved_options,
                settings=self._settings,
            )

            affected_rows = self._labour_stats_repository.upsert_many(
                db_session, raw_rows, last_updated=now
            )

            self._data_freshness_repository.upsert_status(
                db_session=db_session,
                dataset_name=dataset_name,
                last_run=now,
                row_count=affected_rows,
                status="COMPLETED",
            )

            db_session.add(
                ETLLog(
                    job_name=dataset_name,
                    payload={
                        "country": country,
                        "city": city,
                        "options": resolved_options,
                    },
                    status="COMPLETED",
                    created_at=now.isoformat(),
                )
            )
            db_session.flush()

            logger.info(
                "ETL run completed",
                extra={
                    "dataset": dataset_name,
                    "country": country,
                    "city": city,
                    "row_count": affected_rows,
                    "status": "COMPLETED",
                },
            )
            return LabourStatsEtlResult(
                dataset_name=dataset_name,
                status="COMPLETED",
                row_count=affected_rows,
                country=country,
                city=city,
            )
        except Exception:
            logger.error(
                "ETL run failed",
                exc_info=True,
                extra={
                    "dataset": dataset_name,
                    "country": country,
                    "city": city,
                    "status": "FAILED",
                },
            )
            self._data_freshness_repository.upsert_status(
                db_session=db_session,
                dataset_name=dataset_name,
                last_run=now,
                row_count=0,
                status="FAILED",
            )
            db_session.add(
                ETLLog(
                    job_name=dataset_name,
                    payload={
                        "country": country,
                        "city": city,
                        "options": resolved_options,
                    },
                    status="FAILED",
                    created_at=now.isoformat(),
                )
            )
            db_session.flush()
            raise
