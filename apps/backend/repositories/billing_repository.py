"""Billing repository implementation."""

from typing import cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.billing import BillingAccount


class BillingRepository:
    """Data access for billing and usage tables."""

    def __init__(self) -> None:
        pass

    def get_billing_account(
        self, db_session: Session, tenant_id: UUID
    ) -> BillingAccount | None:
        """Get the billing account row for a tenant, or None if missing."""
        query: Select = select(BillingAccount).where(
            BillingAccount.tenant_id == tenant_id
        )
        result = db_session.execute(query).scalars().first()
        return cast(BillingAccount | None, result)
