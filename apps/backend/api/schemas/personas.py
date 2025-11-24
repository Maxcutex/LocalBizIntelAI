"""Pydantic schemas for personas endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class PersonaGenerateRequest(BaseModel):
    """Request payload for `/personas/generate`."""

    city: str = Field(min_length=1)
    country: str | None = None
    geo_ids: list[str] | None = None
    business_type: str | None = None


class PersonaGenerateResponse(BaseModel):
    """Response payload for generated personas."""

    city: str
    country: str | None
    business_type: str | None
    personas: dict[str, Any]
