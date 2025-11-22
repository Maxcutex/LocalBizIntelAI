"""Data freshness repository implementation."""

from typing import cast

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.system import DataFreshness


class DataFreshnessRepository:
    """Data access for `data_freshness` table."""

    def list_all(self, db_session: Session) -> list[DataFreshness]:
        query: Select = select(DataFreshness).order_by(DataFreshness.dataset_name.asc())
        result = db_session.execute(query).scalars().all()
        return cast(list[DataFreshness], list(result))
