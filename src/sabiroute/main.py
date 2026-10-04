from __future__ import annotations

from fastapi import FastAPI

from .api.admin import router as admin_router
from .api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="SabiRoute",
        description="Intelligent LLM routing gateway.",
        version="0.1.0",
    )

    app.include_router(health_router)
    app.include_router(admin_router)

    return app


app = create_app()
