"""Pydantic schemas for reports endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class FeasibilityReportRequest(BaseModel):
    city: str = Field(min_length=1)
    country: str = Field(min_length=1)
    business_type: str = Field(min_length=1)


class FeasibilityReportResponse(BaseModel):
    job_id: str
    status: str


class ReportJobRead(BaseModel):
    id: UUID
    city: str
    country: str
    business_type: str
    status: str
    pdf_url: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ReportsListResponse(BaseModel):
    reports: list[ReportJobRead]


class ReportGetResponse(BaseModel):
    report: ReportJobRead
