"""Demographics repository implementation."""

from sqlalchemy import Select, distinct, select
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
