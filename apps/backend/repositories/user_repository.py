"""User repository implementation."""

from typing import cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.core import User


class UserRepository:
    """Data access for `users` table."""

    def get_by_id(self, db_session: Session, user_id: UUID) -> User | None:
        return db_session.get(User, user_id)

    def admin_list(
        self,
        db_session: Session,
        email_contains: str | None = None,
        role: str | None = None,
        tenant_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        query: Select = select(User)
        if tenant_id is not None:
            query = query.where(User.tenant_id == tenant_id)
        if role:
            query = query.where(User.role == role)
        if email_contains:
            query = query.where(User.email.ilike(f"%{email_contains}%"))
        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = db_session.execute(query).scalars().all()
        return cast(list[User], list(result))
