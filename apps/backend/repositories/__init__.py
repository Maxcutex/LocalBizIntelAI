"""
Repository (data-access) layer.

Repositories encapsulate all persistence logic and should not contain
business rules. Services depend on repositories.
"""

from .billing_repository import BillingRepository  # noqa: F401
from .business_density_repository import BusinessDensityRepository  # noqa: F401
from .data_freshness_repository import DataFreshnessRepository  # noqa: F401
from .demographics_repository import DemographicsRepository  # noqa: F401
from .etl_logs_repository import EtlLogsRepository  # noqa: F401
from .labour_stats_repository import LabourStatsRepository  # noqa: F401
from .opportunity_scores_repository import OpportunityScoresRepository  # noqa: F401
from .report_jobs_repository import ReportJobsRepository  # noqa: F401
from .spending_repository import SpendingRepository  # noqa: F401
from .tenant_repository import TenantRepository  # noqa: F401
from .user_repository import UserRepository  # noqa: F401
from .vector_insights_repository import VectorInsightsRepository  # noqa: F401

__all__ = [
    "UserRepository",
    "TenantRepository",
    "DemographicsRepository",
    "LabourStatsRepository",
    "SpendingRepository",
    "BusinessDensityRepository",
    "OpportunityScoresRepository",
    "VectorInsightsRepository",
    "ReportJobsRepository",
    "BillingRepository",
    "DataFreshnessRepository",
    "EtlLogsRepository",
]
