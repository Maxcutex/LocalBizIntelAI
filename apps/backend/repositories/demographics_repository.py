"""Demographics repository implementation."""

from sqlalchemy import Select, distinct, func, select
from sqlalchemy.orm import Session

from models.market import Demographics


class DemographicsRepository:
    """Data access for `demographics` table."""

    def distinct_cities(self, db_session: Session, country: str | None) -> list[str]:
        query: Select = select(distinct(Demographics.city)).order_by(Demographics.city)
        if country:
            query = query.where(Demographics.country == country)
        result = db_session.execute(query).scalars().all()
        return [city for city in result if city]

    def get_city_aggregates(
        self, db_session: Session, city: str, country: str | None
    ) -> dict:
        query: Select = select(
            func.sum(Demographics.population_total).label("population_total"),
            func.avg(Demographics.median_income).label("median_income"),
            func.avg(Demographics.household_size_avg).label("household_size_avg"),
            func.avg(Demographics.immigration_ratio).label("immigration_ratio"),
        ).where(Demographics.city == city)
        if country:
            query = query.where(Demographics.country == country)

        row = db_session.execute(query).mappings().one()
        return {
            "population_total": row["population_total"],
            "median_income": row["median_income"],
            "household_size_avg": row["household_size_avg"],
            "immigration_ratio": row["immigration_ratio"],
        }
