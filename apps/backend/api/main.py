"""FastAPI application factory and router wiring."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings

from .routers import (
    admin,
    auth,
    billing,
    etl,
    health,
    insights,
    markets,
    me,
    personas,
    reports,
    tenants,
)


def create_app() -> FastAPI:
    """
    Application factory for the FastAPI app.

    This keeps app creation centralized so we can
    attach middleware, event handlers, and shared
    configuration in one place.
    """
    app = FastAPI(
        title="LocalBizIntel Backend API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    settings = get_settings()
    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(me.router, tags=["auth"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
    app.include_router(markets.router, prefix="/markets", tags=["markets"])
    app.include_router(insights.router, prefix="/insights", tags=["insights"])
    app.include_router(personas.router, prefix="/personas", tags=["personas"])
    app.include_router(reports.router, prefix="/reports", tags=["reports"])
    app.include_router(billing.router, prefix="/billing", tags=["billing"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])
    app.include_router(etl.router, prefix="/admin/etl", tags=["admin", "etl"])

    return app


app = create_app()
