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

from .db import Base
from .ai import AILog, VectorInsight
from .billing import BillingAccount, UsageRecord
from .core import Organization, Tenant, User
from .market import (
    BusinessDensity,
    Demographics,
    LabourStats,
    OpportunityScore,
    Spending,
)
from .reports import ReportJob, ReportSection
from .system import DataFreshness, ETLLog

