"""Data freshness repository implementation."""

from datetime import datetime
from typing import cast

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.system import DataFreshness


class DataFreshnessRepository:
    """Data access for `data_freshness` table."""

    def list_all(self, db_session: Session) -> list[DataFreshness]:
        """List all dataset freshness records ordered by dataset name."""
        query: Select = select(DataFreshness).order_by(DataFreshness.dataset_name.asc())
        result = db_session.execute(query).scalars().all()
        return cast(list[DataFreshness], list(result))

    def upsert_status(
        self,
        db_session: Session,
        dataset_name: str,
        last_run: datetime,
        row_count: int,
        status: str,
    ) -> DataFreshness:
        """
        Insert or update freshness status for a dataset.

        Args:
            dataset_name: Canonical dataset identifier (e.g., "demographics").
            last_run: Timestamp of the ETL run.
            row_count: Rows written/updated in the run.
            status: Status string (e.g., "SUCCESS", "FAILED").
        """
        last_run_value = last_run.isoformat()
        existing = (
            db_session.execute(
                select(DataFreshness).where(DataFreshness.dataset_name == dataset_name)
            )
            .scalars()
            .first()
        )

        if existing:
            existing.last_run = last_run_value
            existing.row_count = row_count
            existing.status = status
            record = existing
        else:
            record = DataFreshness(
                dataset_name=dataset_name,
                last_run=last_run_value,
                row_count=row_count,
                status=status,
            )
            db_session.add(record)

        db_session.flush()
        return record
