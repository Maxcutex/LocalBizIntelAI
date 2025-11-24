"""Pydantic schemas for billing endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class BillingPlanResponse(BaseModel):
    """Response schema for current plan and usage."""

    plan: str | None
    status: str | None
    usage: dict[str, Any]


class CheckoutSessionRequest(BaseModel):
    """Request payload for creating a checkout session."""

    target_plan: str = Field(min_length=1)


class CheckoutSessionResponse(BaseModel):
    """Response payload containing checkout session URL."""

    checkout_session_id: str
    url: str
