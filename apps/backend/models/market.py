"""Market and demographic ORM models."""

import uuid

from sqlalchemy import JSON, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Demographics(Base):
    __tablename__ = "demographics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    geo_id: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    population_total: Mapped[int] = mapped_column(Integer)
    median_income: Mapped[Numeric] = mapped_column(Numeric)
    age_distribution: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    education_levels: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    household_size_avg: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    immigration_ratio: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    # coordinates stored as geometry in DB; represented as generic JSON here for ORM
    coordinates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_updated: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )


class Spending(Base):
    __tablename__ = "spending"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    geo_id: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    avg_monthly_spend: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    spend_index: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    last_updated: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )


class LabourStats(Base):
    __tablename__ = "labour_stats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    geo_id: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    unemployment_rate: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    job_openings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    median_salary: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    labour_force_participation: Mapped[Numeric | None] = mapped_column(
        Numeric, nullable=True
    )
    last_updated: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )


class BusinessDensity(Base):
    __tablename__ = "business_density"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    geo_id: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    business_type: Mapped[str] = mapped_column(String, nullable=False)
    count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    density_score: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    # coordinates stored as geometry in DB; represented as generic JSON here
    coordinates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_updated: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )


class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )
    geo_id: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    business_type: Mapped[str] = mapped_column(String, nullable=False)
    demand_score: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    supply_score: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    competition_score: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    composite_score: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    calculated_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )


