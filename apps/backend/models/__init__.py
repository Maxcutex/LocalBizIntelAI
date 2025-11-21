"""
Domain models layer.

This package contains:
- `db` for the SQLAlchemy engine, session, and `Base`
- ORM model modules grouped by concern:
  - `core` for tenants, users, organizations
  - `market` for demographics, spending, labour, business density, opportunity scores
  - `ai` for vector insights and AI logs
  - `reports` for report jobs and sections
  - `billing` for billing accounts and usage records
  - `system` for ETL and data freshness metadata
"""

from .ai import AILog, VectorInsight  # noqa: F401
from .billing import BillingAccount, UsageRecord  # noqa: F401
from .core import Organization, Tenant, User  # noqa: F401
from .db import Base  # noqa: F401
from .market import (  # noqa: F401
    BusinessDensity,
    Demographics,
    LabourStats,
    OpportunityScore,
    Spending,
)
from .reports import ReportJob, ReportSection  # noqa: F401
from .system import DataFreshness, ETLLog  # noqa: F401

__all__ = [
    "Base",
    "Tenant",
    "User",
    "Organization",
    "Demographics",
    "Spending",
    "LabourStats",
    "BusinessDensity",
    "OpportunityScore",
    "VectorInsight",
    "AILog",
    "ReportJob",
    "ReportSection",
    "BillingAccount",
    "UsageRecord",
    "DataFreshness",
    "ETLLog",
]
