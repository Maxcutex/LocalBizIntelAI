"""Pydantic schemas for reports endpoints."""

from pydantic import BaseModel, Field


class FeasibilityReportRequest(BaseModel):
    city: str = Field(min_length=1)
    country: str = Field(min_length=1)
    business_type: str = Field(min_length=1)


class FeasibilityReportResponse(BaseModel):
    job_id: str
    status: str
