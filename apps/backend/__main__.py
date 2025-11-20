"""
CLI entrypoint for running the FastAPI app with uvicorn.

Usage:
    python -m apps.backend
"""

import uvicorn


def main() -> None:
    uvicorn.run(
        "apps.backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()


