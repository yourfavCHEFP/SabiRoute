"""SabiRoute application factory and console entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from .api.admin import router as admin_router
from .api.completions import router as completions_router
from .api.health import router as health_router
from .gateway import GatewayState, build_gateway_state, empty_gateway_state

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


def create_app(state: GatewayState | None = None) -> FastAPI:
    """Create the SabiRoute app.

    Pass ``state`` to inject pre-built gateway state (tests, embedders);
    otherwise state is built from configuration when the server starts.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if state is not None:
            app.state.gateway = state
        else:
            try:
                app.state.gateway = build_gateway_state()
            except Exception as exc:
                # Keep liveness/admin endpoints up in a degraded state;
                # completions returns 503 with the startup error.
                logger.warning("Gateway startup failed: %s", exc)
                degraded = empty_gateway_state()
                degraded.startup_error = str(exc)
                app.state.gateway = degraded
        yield

    app = FastAPI(
        title="SabiRoute",
        description="Intelligent LLM routing gateway.",
        version="0.1.0",
        lifespan=lifespan,
    )

    if state is not None:
        # Injected state is available immediately, not only once the
        # server starts, so test clients and embedders see it either way.
        app.state.gateway = state

    app.include_router(health_router)
    app.include_router(completions_router)
    app.include_router(admin_router)

    return app


def main() -> None:
    """Console-script entry point (``sabiroute``): run the API with uvicorn."""

    import uvicorn

    uvicorn.run(
        "sabiroute.main:app",
        host=os.environ.get("SABIROUTE_HOST", "127.0.0.1"),
        port=int(os.environ.get("SABIROUTE_API_PORT", "8000")),
    )


app = create_app()
