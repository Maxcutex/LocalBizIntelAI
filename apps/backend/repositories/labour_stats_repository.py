"""Labour stats repository implementation."""

from datetime import datetime
from typing import cast

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from models.market import LabourStats


class LabourStatsRepository:
    """Data access for `labour_stats` table."""

    def get_city_aggregates(
        self, db_session: Session, city: str, country: str | None
    ) -> dict:
        """Compute city-level labour aggregates (unemployment, salaries, openings)."""
        query: Select = select(
            func.avg(LabourStats.unemployment_rate).label("avg_unemployment_rate"),
            func.avg(LabourStats.median_salary).label("avg_median_salary"),
            func.sum(LabourStats.job_openings).label("total_job_openings"),
            func.avg(LabourStats.labour_force_participation).label(
                "avg_labour_force_participation"
            ),
        ).where(LabourStats.city == city)
        if country:
            query = query.where(LabourStats.country == country)

        row = db_session.execute(query).mappings().one()
        return {
            "avg_unemployment_rate": row["avg_unemployment_rate"],
            "avg_median_salary": row["avg_median_salary"],
            "total_job_openings": row["total_job_openings"],
            "avg_labour_force_participation": row["avg_labour_force_participation"],
        }

    def get_for_regions(
        self, db_session: Session, city: str, country: str | None
    ) -> list[LabourStats]:
        """List labour stats rows for all regions in a city."""
        query: Select = select(LabourStats).where(LabourStats.city == city)
        if country:
            query = query.where(LabourStats.country == country)
        query = query.order_by(LabourStats.geo_id)
        result = db_session.execute(query).scalars().all()
        return cast(list[LabourStats], list(result))

    def upsert_many(
        self,
        db_session: Session,
        rows: list[dict[str, object]],
        last_updated: datetime,
    ) -> int:
        """
        Insert or update labour stats rows keyed by (geo_id, city, country).

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
                    select(LabourStats).where(
                        LabourStats.geo_id == geo_id,
                        LabourStats.city == city,
                        LabourStats.country == country,
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
                    LabourStats(
                        tenant_id=input_row.get("tenant_id"),
                        geo_id=geo_id,
                        city=city,
                        country=country,
                        unemployment_rate=input_row.get("unemployment_rate"),
                        job_openings=input_row.get("job_openings"),
                        median_salary=input_row.get("median_salary"),
                        labour_force_participation=input_row.get(
                            "labour_force_participation"
                        ),
                        last_updated=last_updated_value,
                    )
                )

            affected_rows += 1

        db_session.flush()
        return affected_rows
