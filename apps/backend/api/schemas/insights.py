"""Pydantic schemas for insights endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class MarketSummaryRequest(BaseModel):
    city: str = Field(min_length=1)
    country: str | None = None
    regions: list[str] | None = None


class MarketSummaryResponse(BaseModel):
    city: str
    country: str | None
    stats: dict[str, Any]
    ai_summary: dict[str, Any]


class OpportunitiesRequest(BaseModel):
    city: str = Field(min_length=1)
    country: str | None = None
    business_type: str | None = None
    constraints: dict[str, Any] | None = None


class OpportunitiesResponse(BaseModel):
    city: str
    country: str | None
    business_type: str | None
    opportunities: list[dict[str, Any]]
    ai_commentary: dict[str, Any]
