#!/usr/bin/env python3
"""Serve SabiRoute with seeded telemetry so the Phase 15 dashboard can be
verified in a real browser.

This is a **UI verification harness, not evidence about providers.** The
telemetry it seeds is FIXTURE DATA that exists so the dashboard has something
worth rendering. Real provider telemetry was verified separately:

* Phase 07 - three real completions through the real ASGI app, read back from
  all four admin endpoints (`scripts/phase07_live_telemetry.py`).
* Phase 12 - real requests persisted six signal keys to Redis, hydrated by a
  fresh process.

Nothing here contacts a provider, spends credit, or makes a claim about one.

Usage:
    SABIROUTE_ADMIN_KEY=<key> \\
    PYTHONPATH=<worktree>/src \\
    ./.venv/bin/python scripts/phase15_browser_verify.py

Then open http://127.0.0.1:8099/admin/dashboard/ and paste the same key.
"""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from sabiroute.config.loader import load_config
from sabiroute.gateway import GatewayState, build_gateway_state
from sabiroute.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[1]

ADMIN_KEY_ENV = "SABIROUTE_ADMIN_KEY"
HOST = os.environ.get("SABIROUTE_P15_HOST", "127.0.0.1")
PORT = int(os.environ.get("SABIROUTE_P15_PORT", "8099"))

# (model, latency_ms, prompt_tokens, completion_tokens)
SEED_SUCCESS: tuple[tuple[str, float, int, int], ...] = (
    ("sabiroute-groq", 640.0, 80, 30),
    ("sabiroute-cloudflare", 810.0, 42, 2),
    ("sabiroute-nvidia", 1180.0, 66, 14),
    ("sabiroute-pollinations", 3520.0, 51, 9),
)

# (model, latency_ms, category, message)
SEED_FAILURE: tuple[tuple[str, float, str, str], ...] = (
    ("sabiroute-openai", 2245.0, "server", "429 no credits remaining"),
    ("sabiroute-together", 2058.0, "auth", "401 invalid API key provided"),
)


def seed(state: GatewayState) -> None:
    """Populate every admin-visible tracker with FIXTURE telemetry.

    One failure per deployment stays below HealthRegistry's failure_threshold
    of 3, so nothing trips cooldown and every deployment still renders as
    available.
    """
    for model, latency_ms, prompt_tokens, completion_tokens in SEED_SUCCESS:
        state.metrics.record_request(model)
        state.metrics.record_success()
        state.health.mark_success(model)
        state.latency.record(model, latency_ms)
        state.usage.record(model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

    for model, latency_ms, category, message in SEED_FAILURE:
        state.metrics.record_request(model)
        state.metrics.record_failure()
        state.health.mark_failure(model)
        state.latency.record(model, latency_ms)
        state.errors.record(category, model, message)


def main() -> int:
    if not os.environ.get(ADMIN_KEY_ENV):
        print(f"refusing to start: {ADMIN_KEY_ENV} must be set")
        return 2

    config = load_config(str(REPO_ROOT / "config" / "config.yaml"))
    state = build_gateway_state(config=config)
    seed(state)
    app = create_app(state=state)

    print(f"dashboard: http://{HOST}:{PORT}/admin/dashboard/")
    print(f"admin key: taken from {ADMIN_KEY_ENV} (value never printed)")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
