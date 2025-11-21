"""Business density repository implementation."""

from sqlalchemy import Select, distinct, func, select
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

    def get_summary(self, db_session: Session, city: str, country: str | None) -> dict:
        query: Select = select(
            func.sum(BusinessDensity.count).label("total_business_count"),
            func.avg(BusinessDensity.density_score).label("avg_density_score"),
            func.count(distinct(BusinessDensity.business_type)).label(
                "business_type_count"
            ),
        ).where(BusinessDensity.city == city)
        if country:
            query = query.where(BusinessDensity.country == country)

        row = db_session.execute(query).mappings().one()
        return {
            "total_business_count": row["total_business_count"],
            "avg_density_score": row["avg_density_score"],
            "business_type_count": row["business_type_count"],
        }
