"""Spending ETL job.

Concrete ETL pipeline for the "spending" dataset.
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
from repositories.spending_repository import SpendingRepository

logger = logging.getLogger(__name__)


class SpendingRepositoryProtocol(Protocol):
    """Abstraction for spending persistence."""

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


class SpendingSourceClient(Protocol):
    """Interface for fetching raw spending rows from an external provider."""

    def fetch_spending(
        self,
        *,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
        settings: Settings,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class LocalStubSpendingSourceClient:
    """
    Deterministic local/dev source.

    In production, swap this for a real provider integration (e.g., SHS/CEX/ONS).
    """

    def fetch_spending(
        self,
        *,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
        settings: Settings,
    ) -> list[dict[str, Any]]:
        _ = settings
        resolved_country = country or "NA"
        resolved_city = city or "Unknown"
        slug = resolved_city.lower().replace(" ", "-")

        categories = options.get("categories")
        resolved_categories: list[str]
        if isinstance(categories, list) and all(isinstance(x, str) for x in categories):
            resolved_categories = list(categories)
        else:
            resolved_categories = ["groceries", "dining", "transport"]

        geo_ids = [f"{slug}-central", f"{slug}-north", f"{slug}-south"]

        rows: list[dict[str, Any]] = []
        base_spend_by_category = {
            "groceries": 350.0,
            "dining": 220.0,
            "transport": 180.0,
        }
        default_base = 200.0

        for geo_idx, geo_id in enumerate(geo_ids):
            region_multiplier = 1.0 + (geo_idx * 0.07)
            for cat_idx, category in enumerate(resolved_categories):
                base = float(base_spend_by_category.get(category, default_base))
                avg_monthly_spend = base * region_multiplier * (1.0 + (cat_idx * 0.03))
                # Keep spend_index a simple ratio to the category base.
                spend_index = avg_monthly_spend / base if base else None
                rows.append(
                    {
                        "geo_id": geo_id,
                        "country": resolved_country,
                        "city": resolved_city,
                        "category": category,
                        "avg_monthly_spend": avg_monthly_spend,
                        "spend_index": spend_index,
                    }
                )

        return rows


@dataclass
class SpendingEtlResult:
    """Result summary for a spending ETL run."""

    dataset_name: str
    status: str
    row_count: int
    country: str | None
    city: str | None


class SpendingEtlJob:
    """ETL job that loads spending rows into the database."""

    def __init__(
        self,
        *,
        spending_repository: SpendingRepositoryProtocol,
        data_freshness_repository: DataFreshnessRepositoryProtocol,
        source_client: SpendingSourceClient,
        settings: Settings,
    ) -> None:
        self._spending_repository = spending_repository
        self._data_freshness_repository = data_freshness_repository
        self._source_client = source_client
        self._settings = settings

    @classmethod
    def create_default(cls) -> "SpendingEtlJob":
        # TODO(architecture): Temporary local wiring. Move to a central
        # `dependencies`/bootstrap module once the ingestion worker runtime exists.
        settings = get_settings()
        return cls(
            spending_repository=SpendingRepository(),
            data_freshness_repository=DataFreshnessRepository(),
            source_client=LocalStubSpendingSourceClient(),
            settings=settings,
        )

    def run(
        self,
        *,
        db_session: Session,
        country: str | None,
        city: str | None,
        options: dict[str, Any],
    ) -> SpendingEtlResult:
        """
        Execute one spending ETL run.

        Fetches raw rows from the source client, upserts them, updates freshness,
        and records an `ETLLog`.
        """
        dataset_name = "spending"
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
            raw_rows = self._source_client.fetch_spending(
                country=country,
                city=city,
                options=resolved_options,
                settings=self._settings,
            )

            affected_rows = self._spending_repository.upsert_many(
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
            return SpendingEtlResult(
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
