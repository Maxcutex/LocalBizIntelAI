"""User repository implementation."""

from uuid import UUID

from sqlalchemy.orm import Session

from models.core import User


class UserRepository:
    """Data access for `users` table."""

    def get_by_id(self, db_session: Session, user_id: UUID) -> User | None:
        return db_session.get(User, user_id)
