"""Business density repository implementation."""

from sqlalchemy import Select, distinct, select
from sqlalchemy.orm import Session

from models.market import BusinessDensity


class BusinessDensityRepository:
    """Data access for `business_density` table."""

    def distinct_cities(self, db_session: Session, country: str | None) -> list[str]:
        query: Select = select(distinct(BusinessDensity.city)).order_by(
            BusinessDensity.city
        )
        if country:
            query = query.where(BusinessDensity.country == country)
        result = db_session.execute(query).scalars().all()
        return [city for city in result if city]
