"""Demographics ETL job.

This is a concrete ETL pipeline for one dataset ("demographics").
It can be invoked by a future worker that consumes `ingestion-jobs` messages.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from sqlalchemy.orm import Session

from api.config import Settings, get_settings
from models.system import ETLLog
from repositories.data_freshness_repository import DataFreshnessRepository
from repositories.demographics_repository import DemographicsRepository


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
        demographics_repository: DemographicsRepository | None = None,
        data_freshness_repository: DataFreshnessRepository | None = None,
        source_client: DemographicsSourceClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._demographics_repository = (
            demographics_repository or DemographicsRepository()
        )
        self._data_freshness_repository = (
            data_freshness_repository or DataFreshnessRepository()
        )
        self._source_client = source_client or LocalStubDemographicsSourceClient()
        self._settings = settings or get_settings()

    def run(
        self,
        *,
        db_session: Session,
        country: str | None,
        city: str | None,
        options: dict[str, Any] | None = None,
    ) -> DemographicsEtlResult:
        """
        Execute one demographics ETL run.

        Fetches raw rows from the source client, upserts them, updates freshness,
        and records an `ETLLog`.
        """
        dataset_name = "demographics"
        now = datetime.now(timezone.utc)
        resolved_options = options or {}

        try:
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
            return DemographicsEtlResult(
                dataset_name=dataset_name,
                status="COMPLETED",
                row_count=affected_rows,
                country=country,
                city=city,
            )
        except Exception:
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
