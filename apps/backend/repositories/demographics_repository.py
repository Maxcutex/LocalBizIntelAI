"""Demographics repository implementation."""

from datetime import datetime
from typing import Any, cast

from sqlalchemy import Select, distinct, func, select
from sqlalchemy.orm import Session

from models.market import Demographics


class DemographicsRepository:
    """Data access for `demographics` table."""

    def distinct_cities(self, db_session: Session, country: str | None) -> list[str]:
        """Return distinct city names with demographics rows, optionally filtered."""
        query: Select = select(distinct(Demographics.city)).order_by(Demographics.city)
        if country:
            query = query.where(Demographics.country == country)
        result = db_session.execute(query).scalars().all()
        return [city for city in result if city]

    def list_by_city(
        self, db_session: Session, city: str, country: str | None
    ) -> list[Demographics]:
        """List demographics rows for all regions in a city."""
        query: Select = select(Demographics).where(Demographics.city == city)
        if country:
            query = query.where(Demographics.country == country)
        query = query.order_by(Demographics.geo_id)
        result = db_session.execute(query).scalars().all()
        return cast(list[Demographics], list(result))

    def get_for_regions(
        self, db_session: Session, city: str, country: str | None
    ) -> list[Demographics]:
        """Alias for `list_by_city`; services may filter by `geo_id` downstream."""
        return self.list_by_city(db_session, city, country)

    def get_city_aggregates(
        self, db_session: Session, city: str, country: str | None
    ) -> dict:
        """Compute per-city aggregates (population, median income, etc.)."""
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

    def upsert_many(
        self,
        db_session: Session,
        rows: list[dict[str, Any]],
        last_updated: datetime,
    ) -> int:
        """
        Insert or update demographics rows keyed by (geo_id, city, country).

        Returns number of rows inserted/updated.
        """

        affected_rows = 0
        last_updated_value = last_updated.isoformat()
        for input_row in rows:
            geo_id = str(input_row["geo_id"])
            city = str(input_row["city"])
            country = str(input_row["country"])

            existing = (
                db_session.execute(
                    select(Demographics).where(
                        Demographics.geo_id == geo_id,
                        Demographics.city == city,
                        Demographics.country == country,
                    )
                )
                .scalars()
                .first()
            )

            if existing:
                for field_name, field_value in input_row.items():
                    if field_name in {"geo_id", "city", "country", "tenant_id"}:
                        continue
                    setattr(existing, field_name, field_value)
                existing.last_updated = last_updated_value
            else:
                db_session.add(
                    Demographics(
                        tenant_id=input_row.get("tenant_id"),
                        geo_id=geo_id,
                        city=city,
                        country=country,
                        population_total=input_row.get("population_total", 0),
                        median_income=input_row.get("median_income", 0),
                        age_distribution=input_row.get("age_distribution"),
                        education_levels=input_row.get("education_levels"),
                        household_size_avg=input_row.get("household_size_avg"),
                        immigration_ratio=input_row.get("immigration_ratio"),
                        coordinates=input_row.get("coordinates"),
                        last_updated=last_updated_value,
                    )
                )

            affected_rows += 1

        db_session.flush()
        return affected_rows
