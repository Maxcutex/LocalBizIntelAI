"""Billing and usage metering service."""

from uuid import UUID

from sqlalchemy.orm import Session


class BillingService:
    """Handles plans, Stripe integration, and usage metering."""

    def check_report_quota(self, db_session: Session, tenant_id: UUID) -> bool:
        """
        Validate whether the tenant can create a new report job.

        TODO: Replace with real plan/quota lookup + usage metering.
        """
        _ = db_session
        _ = tenant_id
        return True
