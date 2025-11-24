"""Demographics ETL job.

This is a concrete ETL pipeline for one dataset ("demographics").
It can be invoked by a future worker that consumes `ingestion-jobs` messages.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from api.config import Settings, get_settings
from models.system import ETLLog
from repositories.data_freshness_repository import DataFreshnessRepository
from repositories.demographics_repository import DemographicsRepository


class EtlDbSession(Protocol):
    """Minimal DB session interface needed by ETL jobs."""

    def add(self, obj: Any) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError


class DemographicsRepositoryProtocol(Protocol):
    """Abstraction for demographics persistence."""

    def upsert_many(
        self,
        db_session: Any,
        rows: list[dict[str, Any]],
        last_updated: datetime,
    ) -> int:
        raise NotImplementedError


class DataFreshnessRepositoryProtocol(Protocol):
    """Abstraction for data freshness persistence."""

    def upsert_status(
        self,
        *,
        db_session: Any,
        dataset_name: str,
        last_run: datetime,
        row_count: int,
        status: str,
    ) -> Any:
        raise NotImplementedError


logger = logging.getLogger(__name__)


class DemographicsSourceClient(Protocol):
    """Interface for fetching raw demographics rows from an external provider."""

    def fetch_demographics(
        self,
        *,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
        settings: Settings,
    ) -> list[dict[str, Any]]:
        """Fetch raw demographics rows from a provider."""
        raise NotImplementedError


class LocalStubDemographicsSourceClient:
    """
    Deterministic local/dev source.

    In production, swap this for a real government data provider client.
    """

    def fetch_demographics(
        self,
        *,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
        settings: Settings,
    ) -> list[dict[str, Any]]:
        """Return deterministic stub demographics for local/dev use."""
        _ = options
        _ = settings
        resolved_country = country or "NA"
        resolved_city = city or "Unknown"

        base_population = 150_000
        base_income = 50_000
        geo_ids = [
            f"{resolved_city.lower().replace(' ', '-')}-central",
            f"{resolved_city.lower().replace(' ', '-')}-north",
            f"{resolved_city.lower().replace(' ', '-')}-south",
        ]

        rows: list[dict[str, Any]] = []
        for index, geo_id in enumerate(geo_ids):
            rows.append(
                {
                    "geo_id": geo_id,
                    "country": resolved_country,
                    "city": resolved_city,
                    "population_total": base_population + (index * 20_000),
                    "median_income": base_income + (index * 5_000),
                    "age_distribution": None,
                    "education_levels": None,
                    "household_size_avg": None,
                    "immigration_ratio": None,
                    "coordinates": None,
                }
            )

        return rows


@dataclass
class DemographicsEtlResult:
    """Result summary for a demographics ETL run."""

    dataset_name: str
    status: str
    row_count: int
    country: str | None
    city: str | None


class DemographicsEtlJob:
    """ETL job that loads demographics rows into the database."""

    def __init__(
        self,
        *,
        demographics_repository: DemographicsRepositoryProtocol,
        data_freshness_repository: DataFreshnessRepositoryProtocol,
        source_client: DemographicsSourceClient,
        settings: Settings,
    ) -> None:
        self._demographics_repository = demographics_repository
        self._data_freshness_repository = data_freshness_repository
        self._source_client = source_client
        self._settings = settings

    @classmethod
    def create_default(cls) -> "DemographicsEtlJob":
        # TODO(architecture): Temporary local wiring. Move to a central
        # `dependencies`/bootstrap module once the ingestion worker runtime exists.
        settings = get_settings()
        return cls(
            demographics_repository=DemographicsRepository(),
            data_freshness_repository=DataFreshnessRepository(),
            source_client=LocalStubDemographicsSourceClient(),
            settings=settings,
        )

    def run(
        self,
        *,
        db_session: EtlDbSession,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
    ) -> DemographicsEtlResult:
        """
        Execute one demographics ETL run.

        Fetches raw rows from the source client, upserts them, updates freshness,
        and records an `ETLLog`.
        """
        dataset_name = "demographics"
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
            raw_rows = self._source_client.fetch_demographics(
                country=country,
                city=city,
                options=resolved_options,
                settings=self._settings,
            )

            affected_rows = self._demographics_repository.upsert_many(
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
            return DemographicsEtlResult(
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
