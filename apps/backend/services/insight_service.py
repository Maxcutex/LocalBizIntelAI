"""Insight orchestration service."""

from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories.demographics_repository import DemographicsRepository
from repositories.labour_stats_repository import LabourStatsRepository
from repositories.opportunity_scores_repository import OpportunityScoresRepository
from repositories.spending_repository import SpendingRepository
from services.ai_engine_client import AiEngineClient


class InsightService:
    """Combines market data with AI-engine outputs to produce insights."""

    def __init__(
        self,
        demographics_repository: DemographicsRepository,
        spending_repository: SpendingRepository,
        labour_stats_repository: LabourStatsRepository,
        opportunity_scores_repository: OpportunityScoresRepository,
        ai_engine_client: AiEngineClient,
    ) -> None:
        self._demographics_repository = demographics_repository
        self._spending_repository = spending_repository
        self._labour_stats_repository = labour_stats_repository
        self._opportunity_scores_repository = opportunity_scores_repository
        self._ai_engine_client = ai_engine_client

    @staticmethod
    def _numeric_to_float(value: Any | None) -> float | None:
        if value is None:
            return None
        return float(cast(Decimal, value))

    def generate_market_summary(
        self,
        db_session: Session,
        city: str,
        country: str | None,
        tenant_id: UUID,
        regions: list[str] | None = None,
    ) -> dict:
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

        region_filter = set(regions) if regions else None

        demographics_payload = [
            {
                "geo_id": row.geo_id,
                "population_total": row.population_total,
                "median_income": self._numeric_to_float(row.median_income),
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
                "job_openings": row.job_openings,
                "median_salary": self._numeric_to_float(row.median_salary),
            }
            for row in labour_rows
            if region_filter is None or row.geo_id in region_filter
        ]

        payload = {
            "tenant_id": str(tenant_id),
            "city": city,
            "country": country,
            "demographics": demographics_payload,
            "spending": spending_payload,
            "labour_stats": labour_payload,
        }

        ai_summary = self._ai_engine_client.generate_market_summary(payload)

        return {
            "city": city,
            "country": country,
            "stats": {
                "demographics": demographics_payload,
                "spending": spending_payload,
                "labour_stats": labour_payload,
            },
            "stats_used": payload,
            "ai_summary": ai_summary,
        }

    def find_opportunities(
        self,
        db_session: Session,
        city: str,
        business_type: str | None,
        constraints: dict[str, Any] | None,
        country: str | None,
        tenant_id: UUID,
    ) -> dict:
        rows = self._opportunity_scores_repository.list_by_city_and_business_type(
            db_session, city, country, business_type
        )
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No opportunities found for city",
            )

        min_composite_score = None
        max_competition_score = None
        if constraints:
            min_composite_score = constraints.get("min_composite_score")
            max_competition_score = constraints.get("max_competition_score")

        ranked_regions: list[dict[str, Any]] = []
        for row in rows:
            composite_score = self._numeric_to_float(row.composite_score)
            competition_score = self._numeric_to_float(row.competition_score)

            if min_composite_score is not None and (
                composite_score is None or composite_score < min_composite_score
            ):
                continue
            if max_competition_score is not None and (
                competition_score is None or competition_score > max_competition_score
            ):
                continue

            ranked_regions.append(
                {
                    "geo_id": row.geo_id,
                    "country": row.country,
                    "city": row.city,
                    "business_type": row.business_type,
                    "demand_score": self._numeric_to_float(row.demand_score),
                    "supply_score": self._numeric_to_float(row.supply_score),
                    "competition_score": competition_score,
                    "composite_score": composite_score,
                    "calculated_at": row.calculated_at,
                }
            )

        if not ranked_regions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No opportunities match constraints",
            )

        ranked_regions.sort(
            key=lambda region: region.get("composite_score") or 0.0,
            reverse=True,
        )

        try:
            ai_commentary = self._ai_engine_client.generate_opportunity_commentary(
                ranked_regions
            )
        except Exception:
            ai_commentary = {
                "commentary": "AI commentary unavailable at the moment.",
                "regions": ranked_regions,
            }

        # tenant_id accepted for future tenant scoping, unused for now.
        return {
            "city": city,
            "country": country,
            "business_type": business_type,
            "opportunities": ranked_regions,
            "stats_used": {
                "business_type": business_type,
                "constraints": constraints,
                "ranked_regions": ranked_regions,
            },
            "ai_commentary": ai_commentary,
        }
