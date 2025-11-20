from fastapi import FastAPI

from .routers import health


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

    # Routers
    app.include_router(health.router, prefix="/health", tags=["health"])

    return app


app = create_app()


