"""Market data access and aggregation service."""

from sqlalchemy.orm import Session

from repositories.business_density_repository import BusinessDensityRepository
from repositories.demographics_repository import DemographicsRepository


class MarketService:
    """Reads normalized market/demographic datasets for API endpoints."""

    def __init__(
        self,
        demographics_repository: DemographicsRepository | None = None,
        business_density_repository: BusinessDensityRepository | None = None,
    ) -> None:
        self._demographics_repository = (
            demographics_repository or DemographicsRepository()
        )
        self._business_density_repository = (
            business_density_repository or BusinessDensityRepository()
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
