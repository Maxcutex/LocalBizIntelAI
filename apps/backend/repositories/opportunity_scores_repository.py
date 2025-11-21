"""Opportunity scores repository implementation."""

from typing import cast

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.market import OpportunityScore


class OpportunityScoresRepository:
    """Data access for `opportunity_scores` table."""

    def list_by_city_and_business_type(
        self,
        db_session: Session,
        city: str,
        country: str | None,
        business_type: str | None,
    ) -> list[OpportunityScore]:
        query: Select = select(OpportunityScore).where(OpportunityScore.city == city)
        if country:
            query = query.where(OpportunityScore.country == country)
        if business_type:
            query = query.where(OpportunityScore.business_type == business_type)
        query = query.order_by(OpportunityScore.composite_score.desc().nullslast())
        result = db_session.execute(query).scalars().all()
        return cast(list[OpportunityScore], list(result))
