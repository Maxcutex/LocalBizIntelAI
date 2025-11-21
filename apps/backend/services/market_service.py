"""Market data access and aggregation service."""

from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories.business_density_repository import BusinessDensityRepository
from repositories.demographics_repository import DemographicsRepository
from repositories.labour_stats_repository import LabourStatsRepository
from repositories.spending_repository import SpendingRepository


class MarketService:
    """Reads normalized market/demographic datasets for API endpoints."""

    @staticmethod
    def _numeric_to_float(value: Any | None) -> float | None:
        if value is None:
            return None
        return float(cast(Decimal, value))

    def __init__(
        self,
        demographics_repository: DemographicsRepository | None = None,
        business_density_repository: BusinessDensityRepository | None = None,
        spending_repository: SpendingRepository | None = None,
        labour_stats_repository: LabourStatsRepository | None = None,
    ) -> None:
        self._demographics_repository = (
            demographics_repository or DemographicsRepository()
        )
        self._business_density_repository = (
            business_density_repository or BusinessDensityRepository()
        )
        self._spending_repository = spending_repository or SpendingRepository()
        self._labour_stats_repository = (
            labour_stats_repository or LabourStatsRepository()
        )

    def list_cities(self, db_session: Session, country: str | None) -> list[str]:
        demographics_cities = self._demographics_repository.distinct_cities(
            db_session, country
        )
        business_density_cities = self._business_density_repository.distinct_cities(
            db_session, country
        )

        if business_density_cities:
            business_density_city_set = set(business_density_cities)
            return [
                city
                for city in demographics_cities
                if city in business_density_city_set
            ]

        return demographics_cities

    def get_overview(
        self,
        db_session: Session,
        city: str,
        country: str | None,
        tenant_id: UUID,
    ) -> dict:
        demographics_summary = self._demographics_repository.get_city_aggregates(
            db_session, city, country
        )
        spending_summary = self._spending_repository.get_city_aggregates(
            db_session, city, country
        )
        labour_summary = self._labour_stats_repository.get_city_aggregates(
            db_session, city, country
        )
        business_density_summary = self._business_density_repository.get_summary(
            db_session, city, country
        )

        # tenant_id is accepted for future RLS/tenant scoping, unused for now.
        return {
            "city": city,
            "country": country,
            "demographics": demographics_summary,
            "spending": spending_summary,
            "labour_stats": labour_summary,
            "business_density": business_density_summary,
        }

    def get_demographics_by_region(
        self, db_session: Session, city: str, country: str | None
    ) -> list[dict]:
        demographics_rows = self._demographics_repository.list_by_city(
            db_session, city, country
        )
        if not demographics_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Demographics not found for city",
            )

        return [
            {
                "geo_id": row.geo_id,
                "country": row.country,
                "city": row.city,
                "population_total": row.population_total,
                "median_income": self._numeric_to_float(row.median_income),
                "age_distribution": row.age_distribution,
                "education_levels": row.education_levels,
                "household_size_avg": self._numeric_to_float(row.household_size_avg),
                "immigration_ratio": self._numeric_to_float(row.immigration_ratio),
                "coordinates": row.coordinates,
                "last_updated": row.last_updated,
            }
            for row in demographics_rows
        ]
