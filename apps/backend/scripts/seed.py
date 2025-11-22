"""
Seed the database with demo data for local development.

Usage (from apps/backend):
    uv run python scripts/seed.py

Or via Makefile:
    make seed
"""

import argparse
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.core import Tenant, User
from models.db import SessionLocal
from models.market import (
    BusinessDensity,
    Demographics,
    LabourStats,
    OpportunityScore,
    Spending,
)
from models.reports import ReportJob

SEED_CITIES: list[tuple[str, str]] = [
    ("Toronto", "CA"),
    ("New York City", "US"),
]


def build_seed_records(
    seed_tenant_id: uuid.UUID, now: datetime
) -> dict[str, list[Any]]:
    """
    Build ORM instances for demo data. This is pure (no DB), used by tests and seeding.
    """
    demographics_rows: list[Demographics] = []
    spending_rows: list[Spending] = []
    labour_rows: list[LabourStats] = []
    density_rows: list[BusinessDensity] = []
    opportunity_rows: list[OpportunityScore] = []
    report_job_rows: list[ReportJob] = []

    toronto_regions = [
        ("toronto-downtown", {"lat": 43.6532, "lng": -79.3832}),
        ("toronto-north-york", {"lat": 43.7615, "lng": -79.4111}),
        ("toronto-scarborough", {"lat": 43.7764, "lng": -79.2318}),
    ]
    nyc_regions = [
        ("nyc-manhattan", {"lat": 40.7831, "lng": -73.9712}),
        ("nyc-brooklyn", {"lat": 40.6782, "lng": -73.9442}),
        ("nyc-queens", {"lat": 40.7282, "lng": -73.7949}),
    ]

    def add_city_data(
        city: str,
        country: str,
        regions: list[tuple[str, dict[str, float]]],
        base_population: int,
        base_income: float,
    ) -> None:
        for region_index, (geo_id, coordinates) in enumerate(regions):
            population_total = base_population + (region_index * 55_000)
            median_income = base_income + (region_index * 6_000)

            demographics_rows.append(
                Demographics(
                    tenant_id=None,
                    geo_id=geo_id,
                    country=country,
                    city=city,
                    population_total=population_total,
                    median_income=median_income,
                    age_distribution={
                        "0-17": 0.17,
                        "18-34": 0.28,
                        "35-54": 0.30,
                        "55+": 0.25,
                    },
                    education_levels={
                        "high_school_or_less": 0.34,
                        "college": 0.29,
                        "bachelors_plus": 0.37,
                    },
                    household_size_avg=2.4 + (region_index * 0.1),
                    immigration_ratio=0.32,
                    coordinates=coordinates,
                    last_updated=now,
                )
            )

            labour_rows.append(
                LabourStats(
                    tenant_id=None,
                    geo_id=geo_id,
                    country=country,
                    city=city,
                    unemployment_rate=0.055 - (region_index * 0.003),
                    job_openings=1200 + (region_index * 150),
                    median_salary=58_000 + (region_index * 4_000),
                    labour_force_participation=0.66 + (region_index * 0.01),
                    last_updated=now,
                )
            )

            for category, avg_spend, spend_index in [
                ("food_and_beverage", 240.0 + region_index * 15, 1.05),
                ("retail", 180.0 + region_index * 10, 0.98),
                ("services", 130.0 + region_index * 8, 1.02),
            ]:
                spending_rows.append(
                    Spending(
                        tenant_id=None,
                        geo_id=geo_id,
                        country=country,
                        city=city,
                        category=category,
                        avg_monthly_spend=avg_spend,
                        spend_index=spend_index,
                        last_updated=now,
                    )
                )

            for business_type, count, density_score in [
                ("restaurant", 420 + region_index * 40, 0.72),
                ("grocery", 120 + region_index * 10, 0.45),
                ("salon", 95 + region_index * 8, 0.38),
            ]:
                density_rows.append(
                    BusinessDensity(
                        tenant_id=None,
                        geo_id=geo_id,
                        country=country,
                        city=city,
                        business_type=business_type,
                        count=count,
                        density_score=density_score,
                        coordinates=coordinates,
                        last_updated=now,
                    )
                )

            for business_type, demand, supply, competition, composite in [
                ("restaurant", 0.78, 0.62, 0.55, 0.70),
                ("grocery", 0.66, 0.58, 0.60, 0.62),
                ("salon", 0.59, 0.46, 0.43, 0.56),
            ]:
                opportunity_rows.append(
                    OpportunityScore(
                        tenant_id=None,
                        geo_id=geo_id,
                        country=country,
                        city=city,
                        business_type=business_type,
                        demand_score=demand,
                        supply_score=supply,
                        competition_score=competition,
                        composite_score=composite,
                        calculated_at=now,
                    )
                )

    add_city_data(
        "Toronto", "CA", toronto_regions, base_population=250_000, base_income=65_000
    )
    add_city_data(
        "New York City", "US", nyc_regions, base_population=350_000, base_income=72_000
    )

    report_job_rows.extend(
        [
            ReportJob(
                tenant_id=seed_tenant_id,
                city="Toronto",
                country="CA",
                business_type="restaurant",
                status="COMPLETED",
                pdf_url="https://example.com/demo-toronto.pdf",
                error_message=None,
                created_at=now,
                updated_at=now,
            ),
            ReportJob(
                tenant_id=seed_tenant_id,
                city="New York City",
                country="US",
                business_type="grocery",
                status="PENDING",
                pdf_url=None,
                error_message=None,
                created_at=now,
                updated_at=now,
            ),
        ]
    )

    return {
        "demographics": demographics_rows,
        "spending": spending_rows,
        "labour_stats": labour_rows,
        "business_density": density_rows,
        "opportunity_scores": opportunity_rows,
        "report_jobs": report_job_rows,
    }


def get_or_create_tenant(db_session: Session, now: datetime) -> Tenant:
    existing = (
        db_session.execute(select(Tenant).where(Tenant.name == "Demo Tenant"))
        .scalars()
        .first()
    )
    if existing:
        return existing

    tenant = Tenant(
        id=uuid.uuid4(),
        name="Demo Tenant",
        plan="starter",
        created_at=now,
        updated_at=now,
    )
    db_session.add(tenant)
    db_session.flush()
    return tenant


def get_or_create_user(
    db_session: Session,
    tenant_id: uuid.UUID,
    email: str,
    name: str,
    role: str,
    now: datetime,
) -> User:
    existing = (
        db_session.execute(select(User).where(User.email == email)).scalars().first()
    )
    if existing:
        return existing

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=email,
        name=name,
        role=role,
        created_at=now,
    )
    db_session.add(user)
    db_session.flush()
    return user


def clear_city_seed_data(db_session: Session) -> None:
    for city, country in SEED_CITIES:
        db_session.execute(
            delete(Demographics).where(
                Demographics.city == city, Demographics.country == country
            )
        )
        db_session.execute(
            delete(Spending).where(Spending.city == city, Spending.country == country)
        )
        db_session.execute(
            delete(LabourStats).where(
                LabourStats.city == city, LabourStats.country == country
            )
        )
        db_session.execute(
            delete(BusinessDensity).where(
                BusinessDensity.city == city, BusinessDensity.country == country
            )
        )
        db_session.execute(
            delete(OpportunityScore).where(
                OpportunityScore.city == city, OpportunityScore.country == country
            )
        )


def clear_report_jobs_for_tenant(db_session: Session, tenant_id: uuid.UUID) -> None:
    db_session.execute(delete(ReportJob).where(ReportJob.tenant_id == tenant_id))


def seed_database(reset: bool = False) -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal() as db_session:
        if reset:
            tenant = (
                db_session.execute(select(Tenant).where(Tenant.name == "Demo Tenant"))
                .scalars()
                .first()
            )
            if tenant:
                clear_report_jobs_for_tenant(db_session, tenant.id)

        clear_city_seed_data(db_session)

        tenant = get_or_create_tenant(db_session, now)
        _ = get_or_create_user(
            db_session,
            tenant_id=tenant.id,
            email="admin@demo.local",
            name="Demo Admin",
            role="ADMIN",
            now=now,
        )
        _ = get_or_create_user(
            db_session,
            tenant_id=tenant.id,
            email="user@demo.local",
            name="Demo User",
            role="USER",
            now=now,
        )

        records = build_seed_records(tenant.id, now)
        for table_name in [
            "demographics",
            "spending",
            "labour_stats",
            "business_density",
            "opportunity_scores",
            "report_jobs",
        ]:
            db_session.add_all(records[table_name])

        db_session.commit()

    counts = {name: len(values) for name, values in records.items()}
    print("Seed completed.")
    print(counts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the LocalBizIntelAI database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing demo report jobs (city seed data is always refreshed).",
    )
    args = parser.parse_args()
    seed_database(reset=args.reset)


if __name__ == "__main__":
    main()
