"""Spending repository implementation."""

from typing import cast

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from models.market import Spending


class SpendingRepository:
    """Data access for `spending` table."""

    def get_city_aggregates(
        self, db_session: Session, city: str, country: str | None
    ) -> dict:
        """Compute average spend and spend index for a city."""
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

    def get_for_regions(
        self, db_session: Session, city: str, country: str | None
    ) -> list[Spending]:
        """List spending rows by category for all regions in a city."""
        query: Select = select(Spending).where(Spending.city == city)
        if country:
            query = query.where(Spending.country == country)
        query = query.order_by(Spending.category)
        result = db_session.execute(query).scalars().all()
        return cast(list[Spending], list(result))
