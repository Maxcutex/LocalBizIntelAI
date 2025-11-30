"""Embeddings rebuild job.

Implements the `rebuild-embeddings` ETL described in
`docs/data-pipeline/etl-jobs-spec.md`.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, TypeVar

from sqlalchemy.orm import Session

from api.config import Settings, get_settings
from models.system import ETLLog
from repositories.business_density_repository import BusinessDensityRepository
from repositories.demographics_repository import DemographicsRepository
from repositories.labour_stats_repository import LabourStatsRepository
from repositories.spending_repository import SpendingRepository
from repositories.vector_insights_repository import VectorInsightsRepository
from services.embedding_client import EmbeddingClient

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


class DemographicsRepositoryProtocol(Protocol):
    def get_for_regions(
        self, db_session: Session, city: str, country: str | None
    ) -> list[Any]:
        raise NotImplementedError


class SpendingRepositoryProtocol(Protocol):
    def get_for_regions(
        self, db_session: Session, city: str, country: str | None
    ) -> list[Any]:
        raise NotImplementedError


class LabourStatsRepositoryProtocol(Protocol):
    def get_for_regions(
        self, db_session: Session, city: str, country: str | None
    ) -> list[Any]:
        raise NotImplementedError


class BusinessDensityRepositoryProtocol(Protocol):
    def list_by_city_and_type(
        self,
        db_session: Session,
        city: str,
        country: str | None,
        business_type: str | None,
    ) -> list[Any]:
        raise NotImplementedError


class VectorInsightsRepositoryProtocol(Protocol):
    def upsert_many(
        self,
        db_session: Session,
        rows: list[dict[str, Any]],
        created_at: datetime,
    ) -> int:
        raise NotImplementedError


class EmbeddingClientProtocol(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


@dataclass
class RebuildEmbeddingsResult:
    job_name: str
    status: str
    row_count: int
    country: str | None
    city: str | None
    region_count: int | None


class RebuildEmbeddingsJob:
    def __init__(
        self,
        *,
        demographics_repository: DemographicsRepositoryProtocol,
        spending_repository: SpendingRepositoryProtocol,
        labour_stats_repository: LabourStatsRepositoryProtocol,
        business_density_repository: BusinessDensityRepositoryProtocol,
        vector_insights_repository: VectorInsightsRepositoryProtocol,
        embedding_client: EmbeddingClientProtocol,
        settings: Settings,
    ) -> None:
        self._demographics_repository = demographics_repository
        self._spending_repository = spending_repository
        self._labour_stats_repository = labour_stats_repository
        self._business_density_repository = business_density_repository
        self._vector_insights_repository = vector_insights_repository
        self._embedding_client = embedding_client
        self._settings = settings

    @classmethod
    def create_default(cls) -> "RebuildEmbeddingsJob":
        settings = get_settings()
        return cls(
            demographics_repository=DemographicsRepository(),
            spending_repository=SpendingRepository(),
            labour_stats_repository=LabourStatsRepository(),
            business_density_repository=BusinessDensityRepository(),
            vector_insights_repository=VectorInsightsRepository(),
            embedding_client=EmbeddingClient(settings=settings),
            settings=settings,
        )

    def run(
        self,
        *,
        db_session: Session,
        country: str | None,
        city: str | None,
        regions: list[str] | None,
        options: dict[str, Any],
        tenant_id: Any | None = None,
    ) -> RebuildEmbeddingsResult:
        job_name = "rebuild-embeddings"
        now = datetime.now(timezone.utc)

        if not city:
            raise ValueError("city is required for rebuild-embeddings")

        try:
            logger.info(
                "Starting embeddings rebuild",
                extra={
                    "job_name": job_name,
                    "country": country,
                    "city": city,
                    "region_count": len(regions) if regions else None,
                },
            )

            demographics_rows = self._demographics_repository.get_for_regions(
                db_session, city, country
            )
            spending_rows = self._spending_repository.get_for_regions(
                db_session, city, country
            )
            labour_rows = self._labour_stats_repository.get_for_regions(
                db_session, city, country
            )
            density_rows = self._business_density_repository.list_by_city_and_type(
                db_session, city, country, business_type=None
            )

            region_filter = set(regions) if regions else None
            geo_ids: set[str] = set()
            for row in demographics_rows:
                geo_ids.add(row.geo_id)
            for row in spending_rows:
                geo_ids.add(row.geo_id)
            for row in labour_rows:
                geo_ids.add(row.geo_id)
            for row in density_rows:
                geo_ids.add(row.geo_id)

            if region_filter is not None:
                geo_ids = {geo_id for geo_id in geo_ids if geo_id in region_filter}

            ordered_geo_ids = sorted(geo_ids)
            documents: list[str] = []
            metadatas: list[dict[str, Any]] = []
            for geo_id in ordered_geo_ids:
                doc = self._build_region_document(
                    geo_id=geo_id,
                    city=city,
                    country=country,
                    demographics_rows=demographics_rows,
                    spending_rows=spending_rows,
                    labour_rows=labour_rows,
                    density_rows=density_rows,
                    options=options,
                )
                documents.append(doc)
                metadatas.append(
                    {
                        "geo_id": geo_id,
                        "city": city,
                        "country": country,
                        "options": options,
                    }
                )

            embeddings = self._embedding_client.embed_texts(documents)
            if any(
                len(vec) != self._settings.openai_embedding_dimensions
                for vec in embeddings
            ):
                raise ValueError("Embedding dimensions mismatch with configured schema")

            upsert_rows: list[dict[str, Any]] = []
            for idx, geo_id in enumerate(ordered_geo_ids):
                upsert_rows.append(
                    {
                        "tenant_id": tenant_id,
                        "geo_id": geo_id,
                        "embedding": embeddings[idx],
                        "metadata": metadatas[idx],
                    }
                )

            affected_rows = self._vector_insights_repository.upsert_many(
                db_session, upsert_rows, created_at=now
            )

            db_session.add(
                ETLLog(
                    job_name=job_name,
                    payload={
                        "country": country,
                        "city": city,
                        "regions": regions,
                        "options": options,
                    },
                    status="COMPLETED",
                    created_at=now.isoformat(),
                )
            )
            db_session.flush()

            logger.info(
                "Embeddings rebuild completed",
                extra={
                    "job_name": job_name,
                    "country": country,
                    "city": city,
                    "row_count": affected_rows,
                },
            )
            return RebuildEmbeddingsResult(
                job_name=job_name,
                status="COMPLETED",
                row_count=affected_rows,
                country=country,
                city=city,
                region_count=len(ordered_geo_ids),
            )
        except Exception:
            logger.error(
                "Embeddings rebuild failed",
                exc_info=True,
                extra={"job_name": job_name, "country": country, "city": city},
            )
            db_session.add(
                ETLLog(
                    job_name=job_name,
                    payload={
                        "country": country,
                        "city": city,
                        "regions": regions,
                        "options": options,
                    },
                    status="FAILED",
                    created_at=now.isoformat(),
                )
            )
            db_session.flush()
            raise

    @staticmethod
    def _build_region_document(
        *,
        geo_id: str,
        city: str,
        country: str | None,
        demographics_rows: list[Any],
        spending_rows: list[Any],
        labour_rows: list[Any],
        density_rows: list[Any],
        options: dict[str, Any],
    ) -> str:
        def _first(rows: list[_T]) -> _T | None:
            for r in rows:
                if getattr(r, "geo_id", None) == geo_id:
                    return r
            return None

        demographics = _first(demographics_rows)
        labour = _first(labour_rows)
        spending_for_geo = [
            r for r in spending_rows if getattr(r, "geo_id", None) == geo_id
        ]
        density_for_geo = [
            r for r in density_rows if getattr(r, "geo_id", None) == geo_id
        ]

        snapshot = {
            "geo_id": geo_id,
            "city": city,
            "country": country,
            "demographics": (
                {
                    "population_total": getattr(demographics, "population_total", None),
                    "median_income": (
                        str(getattr(demographics, "median_income", None))
                        if getattr(demographics, "median_income", None) is not None
                        else None
                    ),
                }
                if demographics
                else None
            ),
            "labour_stats": (
                {
                    "unemployment_rate": (
                        str(getattr(labour, "unemployment_rate", None))
                        if getattr(labour, "unemployment_rate", None) is not None
                        else None
                    ),
                    "median_salary": (
                        str(getattr(labour, "median_salary", None))
                        if getattr(labour, "median_salary", None) is not None
                        else None
                    ),
                    "job_openings": getattr(labour, "job_openings", None),
                }
                if labour
                else None
            ),
            "spending": [
                {
                    "category": getattr(r, "category", None),
                    "avg_monthly_spend": (
                        str(getattr(r, "avg_monthly_spend", None))
                        if getattr(r, "avg_monthly_spend", None) is not None
                        else None
                    ),
                    "spend_index": (
                        str(getattr(r, "spend_index", None))
                        if getattr(r, "spend_index", None) is not None
                        else None
                    ),
                }
                for r in spending_for_geo
            ],
            "business_density": [
                {
                    "business_type": getattr(r, "business_type", None),
                    "count": getattr(r, "count", None),
                    "density_score": (
                        str(getattr(r, "density_score", None))
                        if getattr(r, "density_score", None) is not None
                        else None
                    ),
                }
                for r in density_for_geo
            ],
            "options": options,
        }

        # Keep it stable and compact.
        return json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
