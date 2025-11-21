"""Authentication and authorization service."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.schemas.core import TenantRead, UserRead
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


class AuthService:
    """Handles login, JWT validation, roles/permissions, and auth integrations."""

    def __init__(
        self,
        user_repository: UserRepository | None = None,
        tenant_repository: TenantRepository | None = None,
    ) -> None:
        self._user_repository = user_repository or UserRepository()
        self._tenant_repository = tenant_repository or TenantRepository()

    def get_current_user_profile(self, db_session: Session, user_id: UUID) -> dict:
        user = self._user_repository.get_by_id(db_session, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        tenant = self._tenant_repository.get_by_id(db_session, user.tenant_id)
        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        return {
            "user": UserRead.model_validate(user),
            "tenant": TenantRead.model_validate(tenant),
        }
