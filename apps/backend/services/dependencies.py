"""Dependency bundles for service constructors.

These keep service initialization SOLID and readable by grouping required
repositories/clients into explicit dataclasses.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from repositories.billing_repository import BillingRepository
from repositories.business_density_repository import BusinessDensityRepository
from repositories.data_freshness_repository import DataFreshnessRepository
from repositories.demographics_repository import DemographicsRepository
from repositories.labour_stats_repository import LabourStatsRepository
from repositories.opportunity_scores_repository import OpportunityScoresRepository
from repositories.report_jobs_repository import ReportJobsRepository
from repositories.spending_repository import SpendingRepository
from repositories.tenant_repository import TenantRepository
from repositories.usage_repository import UsageRepository
from repositories.user_repository import UserRepository
from services.ai_engine_client import AiEngineClient
from services.pubsub_client import PubSubClient
from services.stripe_client import StripeClient


@dataclass(frozen=True)
class MarketServiceDependencies:
    """Concrete dependencies required by `MarketService`."""

    demographics_repository: DemographicsRepository
    business_density_repository: BusinessDensityRepository
    spending_repository: SpendingRepository
    labour_stats_repository: LabourStatsRepository


@dataclass(frozen=True)
class InsightServiceDependencies:
    """Concrete dependencies required by `InsightService`."""

    demographics_repository: DemographicsRepository
    spending_repository: SpendingRepository
    labour_stats_repository: LabourStatsRepository
    opportunity_scores_repository: OpportunityScoresRepository
    ai_engine_client: AiEngineClient


@dataclass(frozen=True)
class PersonaServiceDependencies:
    """Concrete dependencies required by `PersonaService`."""

    demographics_repository: DemographicsRepository
    spending_repository: SpendingRepository
    labour_stats_repository: LabourStatsRepository
    ai_engine_client: AiEngineClient


@dataclass(frozen=True)
class ReportServiceDependencies:
    """Concrete dependencies required by `ReportService`."""

    report_jobs_repository: ReportJobsRepository
    billing_service: "BillingService"
    pubsub_client: PubSubClient


@dataclass(frozen=True)
class BillingServiceDependencies:
    """Concrete dependencies required by `BillingService`."""

    billing_repository: BillingRepository
    usage_repository: UsageRepository
    stripe_client: StripeClient


@dataclass(frozen=True)
class AdminServiceDependencies:
    """Concrete dependencies required by `AdminService`."""

    user_repository: UserRepository
    tenant_repository: TenantRepository
    data_freshness_repository: DataFreshnessRepository
    report_jobs_repository: ReportJobsRepository


@dataclass(frozen=True)
class AuthServiceDependencies:
    """Concrete dependencies required by `AuthService`."""

    user_repository: UserRepository
    tenant_repository: TenantRepository


@dataclass(frozen=True)
class TenantServiceDependencies:
    """Concrete dependencies required by `TenantService`."""

    tenant_repository: TenantRepository


@dataclass(frozen=True)
class EtlOrchestrationServiceDependencies:
    """Concrete dependencies required by `ETLOrchestrationService`."""

    pubsub_client: PubSubClient


if TYPE_CHECKING:
    from services.billing_service import BillingService
