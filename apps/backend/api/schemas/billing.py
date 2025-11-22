"""Pydantic schemas for billing endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class BillingPlanResponse(BaseModel):
    plan: str | None
    status: str | None
    usage: dict[str, Any]


class CheckoutSessionRequest(BaseModel):
    target_plan: str = Field(min_length=1)


class CheckoutSessionResponse(BaseModel):
    checkout_session_id: str
    url: str
