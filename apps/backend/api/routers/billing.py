from fastapi import APIRouter, Depends, status

from services.billing_service import BillingService

router = APIRouter()


def get_billing_service() -> BillingService:
    return BillingService()


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
