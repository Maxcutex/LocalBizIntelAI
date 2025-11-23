"""Labour stats repository implementation."""

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
