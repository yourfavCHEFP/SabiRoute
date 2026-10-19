"""SabiRoute application factory and console entry point."""

from __future__ import annotations

import inspect
import logging
import os
from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from .api.admin import router as admin_router
from .api.body_limit import BodySizeMiddleware, request_max_body_bytes
from .api.completions import router as completions_router
from .api.deadline import DeadlineMiddleware, request_deadline_seconds
from .api.health import router as health_router
from .api.shutdown import router as shutdown_router
from .gateway import GatewayState, build_gateway_state, empty_gateway_state

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

def create_app(state: GatewayState | None = None) -> FastAPI:
    """Create the SabiRoute app.

    Pass ``state`` to inject pre-built gateway state (tests, embedders);
    otherwise state is built from configuration when the server starts.
    """

    async def _purge_expired_sessions_once() -> None:
        """Best-effort purge of expired chat sessions at startup/shutdown.

        Runs the store's idempotent purge on a bounded worker via the
        gateway store executor so event-loop blocking is avoided. Never
        raises: purge is hygiene, not admission — failures are logged.
        """
        gateway_obj = getattr(app.state, "gateway", None)
        store = getattr(gateway_obj, "chat_store", None)
        purge = getattr(store, "purge_expired_sessions", None)
        if not callable(purge):
            return
        executor = getattr(gateway_obj, "store_executor", None)
        run = getattr(executor, "run", None)
        try:
            if callable(run):
                await run(purge)
            else:
                purge()
        except Exception as exc:  # noqa: BLE001 — hygiene must not break lifespan
            logger.warning("Session purge skipped: %s", type(exc).__name__)

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
        try:
            await _purge_expired_sessions_once()
            yield
        finally:
            await _purge_expired_sessions_once()
            gateway = getattr(app.state, "gateway", None)
            for resource_name in ("key_store", "rate_limiter", "chat_store"):
                resource = getattr(gateway, resource_name, None)
                close = getattr(resource, "close", None)
                if callable(close):
                    result = close()
                    if inspect.isawaitable(result):
                        await result

    docs_enabled = (os.environ.get("SABIROUTE_DOCS_ENABLED") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    doc_kwargs: dict[str, object] = (
        {}
        if docs_enabled
        else {
            "docs_url": None,
            "redoc_url": None,
            "openapi_url": None,
        }
    )
    app = FastAPI(
        title="SabiRoute",
        description="Intelligent LLM routing gateway.",
        version="0.1.0",
        lifespan=lifespan,
        **doc_kwargs,  # type: ignore[arg-type]
    )

    if state is not None:
        # Injected state is available immediately, not only once the
        # server starts, so test clients and embedders see it either way.
        app.state.gateway = state

    app.include_router(health_router)
    app.include_router(completions_router)
    app.include_router(admin_router)
    app.include_router(shutdown_router)

    app.add_middleware(
        DeadlineMiddleware, deadline_seconds=request_deadline_seconds()
    )
    app.add_middleware(
        BodySizeMiddleware, max_body_bytes=request_max_body_bytes()
    )

    return app

CLI_USAGE = """Usage: sabiroute [OPTIONS]

Run the SabiRoute API with uvicorn. Configuration comes from environment
variables (see .env.example); this command takes no positional arguments.

Options:
  -h, --help   Show this message without starting the server.
"""

def main(argv: Sequence[str] | None = None) -> None:
    """Console-script entry point (``sabiroute``): run the API with uvicorn."""
    import sys

    import uvicorn

    args = list(sys.argv[1:] if argv is None else argv)
    if args in (["-h"], ["--help"]):
        print(CLI_USAGE)
        return
    if args:
        print(CLI_USAGE, file=sys.stderr)
        raise SystemExit(f"Unknown arguments: {' '.join(args)}")

    uvicorn.run(
        "sabiroute.main:app",
        host=os.environ.get("SABIROUTE_HOST", "127.0.0.1"),
        port=int(os.environ.get("SABIROUTE_API_PORT", "8000")),
    )

app = create_app()
