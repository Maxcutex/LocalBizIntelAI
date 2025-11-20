### Backend (FastAPI) Overview

This directory contains the FastAPI backend for LocalBizIntelAI with a focus on clear separation of concerns:

- **`api/`**: FastAPI app, routers, dependencies, and API-specific config.
  - `main.py`: App factory and router registration.
  - `routers/`: Feature-based `APIRouter` modules (e.g. `health.py`).
  - `dependencies.py`: Shared dependency-injected objects for routes.
  - `config.py`: Pydantic-based settings loaded from environment.
- **`models/`**: Domain and persistence models (ORM, Pydantic schemas, etc.).
- **`services/`**: Application services containing business logic, independent of HTTP.
- **`pipelines/` and `workflows/`**: Data and workflow orchestration components.
- **`jobs/`**: Background or scheduled jobs.

#### Running the API locally

From the backend project directory (`apps/backend`), using `make` and `uv`:

```bash
cd apps/backend

# Install backend deps (uses uv + pyproject.toml)
make install

# Run the API with auto-reload on http://localhost:8000
make dev
```

From the monorepo root you can also use the delegating targets:

```bash
# Install backend deps
make backend-install

# Run the backend API
make backend-dev
```

> Note: This setup assumes you have `uv` installed (`pipx install uv` or consult the uv docs).  
> If you prefer plain `uvicorn`, you can still run from `apps/backend` with:
> `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`.


