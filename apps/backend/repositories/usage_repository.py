"""Usage repository implementation."""

from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from models.billing import UsageRecord


class UsageRepository:
    """Data access for usage records."""

    def get_current_usage(self, db_session: Session, tenant_id: UUID) -> dict[str, Any]:
        """Return current usage totals by metric for a tenant."""
        query: Select = (
            select(
                UsageRecord.metric,
                func.sum(UsageRecord.quantity).label("quantity"),
            )
            .where(UsageRecord.tenant_id == tenant_id)
            .group_by(UsageRecord.metric)
        )

        rows = db_session.execute(query).all()
        return {metric: quantity for metric, quantity in rows}
