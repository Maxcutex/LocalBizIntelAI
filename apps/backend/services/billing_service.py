"""Billing and usage metering service."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories.billing_repository import BillingRepository
from repositories.usage_repository import UsageRepository
from services.stripe_client import StripeClient


class BillingService:
    """Handles plans, Stripe integration, and usage metering."""

    def __init__(
        self,
        billing_repository: BillingRepository | None = None,
        usage_repository: UsageRepository | None = None,
        stripe_client: StripeClient | None = None,
    ) -> None:
        self._billing_repository = billing_repository or BillingRepository()
        self._usage_repository = usage_repository or UsageRepository()
        self._stripe_client = stripe_client or StripeClient()

    def check_report_quota(self, db_session: Session, tenant_id: UUID) -> bool:
        """
        Validate whether the tenant can create a new report job.

        TODO: Replace with real plan/quota lookup + usage metering.
        """
        _ = db_session
        _ = tenant_id
        return True

    def get_plan_and_usage(
        self, db_session: Session, tenant_id: UUID
    ) -> dict[str, Any]:
        billing_account = self._billing_repository.get_billing_account(
            db_session, tenant_id
        )
        usage = self._usage_repository.get_current_usage(db_session, tenant_id)
        if billing_account is None:
            return {"plan": None, "status": None, "usage": usage}
        return {
            "plan": billing_account.plan,
            "status": billing_account.status,
            "usage": usage,
        }

    def create_checkout_session(
        self, db_session: Session, tenant_id: UUID, target_plan: str
    ) -> dict[str, Any]:
        _ = db_session
        if not target_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target plan is required",
            )
        return self._stripe_client.create_checkout_session(
            tenant_id=str(tenant_id), target_plan=target_plan
        )
