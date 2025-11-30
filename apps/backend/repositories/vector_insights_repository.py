"""Vector insights repository implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.ai import VectorInsight


class VectorInsightsRepository:
    """Data access for `vector_insights` table (pgvector)."""

    def upsert_many(
        self,
        db_session: Session,
        rows: list[dict[str, Any]],
        created_at: datetime,
    ) -> int:
        """
        Insert or update vector insight rows keyed by (tenant_id, geo_id).

        Returns number of rows inserted/updated.
        """
        affected_rows = 0
        created_at_value = created_at.isoformat()

        for input_row in rows:
            geo_id = str(input_row["geo_id"])
            tenant_id = input_row.get("tenant_id")

            query: Select = select(VectorInsight).where(VectorInsight.geo_id == geo_id)
            if tenant_id is None:
                query = query.where(VectorInsight.tenant_id.is_(None))
            else:
                query = query.where(VectorInsight.tenant_id == tenant_id)

            existing = db_session.execute(query).scalars().first()
            if existing:
                existing.embedding = cast(list[float], input_row["embedding"])
                existing.metadata_json = cast(dict | None, input_row.get("metadata"))
                existing.created_at = created_at_value
            else:
                db_session.add(
                    VectorInsight(
                        tenant_id=tenant_id,
                        geo_id=geo_id,
                        embedding=cast(list[float], input_row["embedding"]),
                        metadata_json=cast(dict | None, input_row.get("metadata")),
                        created_at=created_at_value,
                    )
                )

            affected_rows += 1

        db_session.flush()
        return affected_rows

    def list_by_geo_ids(
        self, db_session: Session, *, geo_ids: list[str], tenant_id: Any | None
    ) -> list[VectorInsight]:
        query: Select = select(VectorInsight).where(VectorInsight.geo_id.in_(geo_ids))
        if tenant_id is None:
            query = query.where(VectorInsight.tenant_id.is_(None))
        else:
            query = query.where(VectorInsight.tenant_id == tenant_id)
        result = db_session.execute(query).scalars().all()
        return cast(list[VectorInsight], list(result))
