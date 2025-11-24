"""Business density repository implementation."""

from datetime import datetime
from typing import Any, cast

from sqlalchemy import Select, distinct, func, select
from sqlalchemy.orm import Session

from models.market import BusinessDensity


class BusinessDensityRepository:
    """Data access for `business_density` table."""

    def distinct_cities(self, db_session: Session, country: str | None) -> list[str]:
        """
        Return distinct city names with business density rows, optionally filtered.
        """
        query: Select = select(distinct(BusinessDensity.city)).order_by(
            BusinessDensity.city
        )
        if country:
            query = query.where(BusinessDensity.country == country)
        result = db_session.execute(query).scalars().all()
        return [city for city in result if city]

    def list_by_city_and_type(
        self,
        db_session: Session,
        city: str,
        country: str | None,
        business_type: str | None,
    ) -> list[BusinessDensity]:
        """List business density rows for a city and optional business type."""
        query: Select = select(BusinessDensity).where(BusinessDensity.city == city)
        if country:
            query = query.where(BusinessDensity.country == country)
        if business_type:
            query = query.where(BusinessDensity.business_type == business_type)
        query = query.order_by(BusinessDensity.business_type)
        result = db_session.execute(query).scalars().all()
        return cast(list[BusinessDensity], list(result))

    def get_summary(self, db_session: Session, city: str, country: str | None) -> dict:
        """Compute city-level density summary (counts and average scores)."""
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

    def upsert_many(
        self,
        db_session: Session,
        rows: list[dict[str, Any]],
        last_updated: datetime,
    ) -> int:
        """
        Insert or update business density rows keyed by
        (geo_id, city, country, business_type).

        Returns number of rows inserted/updated.
        """

        affected_rows = 0
        last_updated_value = last_updated.isoformat()
        for input_row in rows:
            geo_id = str(input_row["geo_id"])
            city = str(input_row["city"])
            country = str(input_row["country"])
            business_type = str(input_row["business_type"])

            existing = (
                db_session.execute(
                    select(BusinessDensity).where(
                        BusinessDensity.geo_id == geo_id,
                        BusinessDensity.city == city,
                        BusinessDensity.country == country,
                        BusinessDensity.business_type == business_type,
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
                        "business_type",
                        "tenant_id",
                    }:
                        continue
                    setattr(existing, field_name, field_value)
                existing.last_updated = last_updated_value
            else:
                db_session.add(
                    BusinessDensity(
                        tenant_id=input_row.get("tenant_id"),
                        geo_id=geo_id,
                        city=city,
                        country=country,
                        business_type=business_type,
                        count=input_row.get("count"),
                        density_score=input_row.get("density_score"),
                        coordinates=input_row.get("coordinates"),
                        last_updated=last_updated_value,
                    )
                )

            affected_rows += 1

        db_session.flush()
        return affected_rows
