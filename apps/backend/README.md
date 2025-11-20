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

From the project root:

```bash
cd apps/backend
uvicorn api.main:app --reload
```

or using the module entrypoint:

```bash
python -m apps.backend
```


