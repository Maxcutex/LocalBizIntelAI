"""Pydantic schemas for admin ETL endpoints."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class EtlRunRequest(BaseModel):
    """Request payload for triggering an ETL run."""

    dataset: str = Field(min_length=1)
    country: str | None = None
    city: str | None = None
    options: dict[str, Any] | None = None


class EtlRunResponse(BaseModel):
    """Response payload for queued ETL runs."""

    status: Literal["QUEUED"]
    payload: dict[str, Any]
