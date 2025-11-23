"""Persona generation service."""

from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from services.dependencies import PersonaServiceDependencies


class PersonaService:
    """Generates customer personas from demographics and AI-engine."""

    def __init__(
        self,
        dependencies: PersonaServiceDependencies,
    ) -> None:
        self._demographics_repository = dependencies.demographics_repository
        self._spending_repository = dependencies.spending_repository
        self._labour_stats_repository = dependencies.labour_stats_repository
        self._ai_engine_client = dependencies.ai_engine_client

    @staticmethod
    def _numeric_to_float(value: Any | None) -> float | None:
        if value is None:
            return None
        return float(cast(Decimal, value))

    def generate_personas(
        self,
        db_session: Session,
        city: str,
        country: str | None,
        geo_ids: list[str] | None,
        business_type: str | None,
        tenant_id: UUID,
    ) -> dict:
        """
        Generate AI personas for a city or subset of regions.

        Pulls demographics, spending, and labour stats for the requested area,
        then delegates persona synthesis to the AI engine.

        Args:
            geo_ids: Optional region `geo_id` filters. When None, uses all regions.
            business_type: Optional business type to tailor personas.
        """
        demographics_rows = self._demographics_repository.get_for_regions(
            db_session, city, country
        )
        spending_rows = self._spending_repository.get_for_regions(
            db_session, city, country
        )
        labour_rows = self._labour_stats_repository.get_for_regions(
            db_session, city, country
        )

        if not demographics_rows and not spending_rows and not labour_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No market data found for city",
            )

        region_filter = set(geo_ids) if geo_ids else None

        demographics_payload = [
            {
                "geo_id": row.geo_id,
                "population_total": row.population_total,
                "median_income": self._numeric_to_float(row.median_income),
                "age_distribution": row.age_distribution,
            }
            for row in demographics_rows
            if region_filter is None or row.geo_id in region_filter
        ]

        spending_payload = [
            {
                "geo_id": row.geo_id,
                "category": row.category,
                "avg_monthly_spend": self._numeric_to_float(row.avg_monthly_spend),
                "spend_index": self._numeric_to_float(row.spend_index),
            }
            for row in spending_rows
            if region_filter is None or row.geo_id in region_filter
        ]

        labour_payload = [
            {
                "geo_id": row.geo_id,
                "unemployment_rate": self._numeric_to_float(row.unemployment_rate),
                "median_salary": self._numeric_to_float(row.median_salary),
                "job_openings": row.job_openings,
            }
            for row in labour_rows
            if region_filter is None or row.geo_id in region_filter
        ]

        input_payload = {
            "tenant_id": str(tenant_id),
            "city": city,
            "country": country,
            "business_type": business_type,
            "demographics": demographics_payload,
            "spending": spending_payload,
            "labour_stats": labour_payload,
        }

        personas = self._ai_engine_client.generate_personas(input_payload)

        return {
            "city": city,
            "country": country,
            "business_type": business_type,
            "personas": personas,
        }
