"""Spending repository implementation."""

from datetime import datetime
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

    def upsert_many(
        self,
        db_session: Session,
        rows: list[dict[str, object]],
        last_updated: datetime,
    ) -> int:
        """
        Insert or update spending rows keyed by (geo_id, city, country, category).

        Returns number of rows inserted/updated.
        """
        affected_rows = 0
        last_updated_value = last_updated.isoformat()

        for input_row in rows:
            geo_id = str(input_row["geo_id"])
            city = str(input_row["city"])
            country = str(input_row["country"])
            category = str(input_row["category"])

            existing = (
                db_session.execute(
                    select(Spending).where(
                        Spending.geo_id == geo_id,
                        Spending.city == city,
                        Spending.country == country,
                        Spending.category == category,
                    )
                )
                .scalars()
                .first()
            )

            if existing:
                for field_name, field_value in input_row.items():
                    if field_name in {
                        "geo_id",
                        "city",
                        "country",
                        "category",
                        "tenant_id",
                    }:
                        continue
                    setattr(existing, field_name, field_value)
                existing.last_updated = last_updated_value
            else:
                db_session.add(
                    Spending(
                        tenant_id=input_row.get("tenant_id"),
                        geo_id=geo_id,
                        country=country,
                        city=city,
                        category=category,
                        avg_monthly_spend=input_row.get("avg_monthly_spend"),
                        spend_index=input_row.get("spend_index"),
                        last_updated=last_updated_value,
                    )
                )

            affected_rows += 1

        db_session.flush()
        return affected_rows
