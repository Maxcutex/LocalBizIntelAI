"""Spending repository implementation."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from models.market import Spending


class SpendingRepository:
    """Data access for `spending` table."""

    def get_city_aggregates(
        self, db_session: Session, city: str, country: str | None
    ) -> dict:
        query: Select = select(
            func.avg(Spending.avg_monthly_spend).label("avg_monthly_spend"),
            func.avg(Spending.spend_index).label("avg_spend_index"),
        ).where(Spending.city == city)
        if country:
            query = query.where(Spending.country == country)

        row = db_session.execute(query).mappings().one()
        return {
            "avg_monthly_spend": row["avg_monthly_spend"],
            "avg_spend_index": row["avg_spend_index"],
        }
