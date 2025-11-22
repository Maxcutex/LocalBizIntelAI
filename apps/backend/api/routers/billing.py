from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.schemas.billing import (
    BillingPlanResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
)
from services.billing_service import BillingService

router = APIRouter()


def get_billing_service() -> BillingService:
    return BillingService()


@router.get(
    "/plan",
    summary="Get current plan and usage",
)
def get_plan(
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    billing_service: BillingService = Depends(get_billing_service),
) -> BillingPlanResponse:
    result = billing_service.get_plan_and_usage(db, context.tenant_id)
    return BillingPlanResponse.model_validate(result)


@router.post(
    "/checkout-session",
    summary="Create checkout session",
)
def create_checkout_session(
    request: CheckoutSessionRequest,
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    billing_service: BillingService = Depends(get_billing_service),
) -> CheckoutSessionResponse:
    result = billing_service.create_checkout_session(
        db, context.tenant_id, request.target_plan
    )
    return CheckoutSessionResponse.model_validate(result)


@router.get(
    "/plans",
    summary="List available plans",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def list_plans(billing_service: BillingService = Depends(get_billing_service)) -> dict:
    """
    Return available subscription plans.
    """
    return {"detail": "Not implemented"}


@router.get(
    "/usage",
    summary="Get current usage",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def get_usage(billing_service: BillingService = Depends(get_billing_service)) -> dict:
    """
    Return current tenant usage and quotas.
    """
    return {"detail": "Not implemented"}
