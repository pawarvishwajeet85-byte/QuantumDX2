"""Phase 1 skeleton: app factory + minimal /health. Auth, RBAC, middleware arrive in Phases 3-5."""
from fastapi import FastAPI

from app.core.config import get_settings


def create_app() -> FastAPI:
    s = get_settings()
    # Interactive docs are disabled outside development so no schema is exposed in production.
    dev = s.ENVIRONMENT.value == "development"
    app = FastAPI(
        title="QuantumDX API",
        debug=False,  # never enable framework debug tracebacks
        docs_url="/api/docs" if dev else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if dev else None,
    )

    @app.get("/health", tags=["health"])  # access class: PUBLIC, minimal payload only
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
