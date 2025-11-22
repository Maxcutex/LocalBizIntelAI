"""Pydantic schemas for admin endpoints."""

from pydantic import BaseModel

from api.schemas.core import TenantRead, UserRead


class AdminUsersListResponse(BaseModel):
    users: list[UserRead]


class AdminTenantsListResponse(BaseModel):
    tenants: list[TenantRead]
