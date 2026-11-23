#!/usr/bin/env python3
"""Phase 06 — prove the health lifecycle live, against real providers.

Phase 06's design decision is passive cooldown, recorded in ``docs/routing.md``.
The accounting half was already observed live by the Phase 05 run: a real
failure against the primary and a real success against the secondary. What had
never been observed live is the part that actually changes routing — the
threshold tripping, the deployment being skipped, and half-open recovery.

This harness reuses the Phase 05 plumbing (real LiteLLM Proxy, real providers)
and walks the whole lifecycle in five requests:

    1-3   primary fails with a real 429; each failure is counted
    3rd   consecutive failure reaches the threshold: unhealthy + cooldown
    4th   primary is skipped entirely; the request still succeeds via secondary
    5th   after the cooldown deadline is expired, primary is attempted again

The 4th request is the load-bearing one. A health system that counts failures
but never removes a deployment has not done anything; the observable proof is
that the failing deployment stops being attempted while traffic keeps flowing.

No stub is in the path. Exit codes: 0 pass, 1 assertion failure, 3 environment.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS.parent / "tests"))


def _load_phase05() -> Any:
    spec = importlib.util.spec_from_file_location(
        "phase05_real_provider_failure", SCRIPTS / "phase05_real_provider_failure.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ask(client: Any) -> tuple[int, str]:
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "fast",
            "messages": [{"role": "user", "content": "Reply with the word OK."}],
        },
    )
    content = ""
    try:
        choices = response.json().get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
    except (ValueError, AttributeError):
        pass
    return response.status_code, content.strip()


def main() -> int:
    p05 = _load_phase05()
    p05._load_env()

    missing = [
        name
        for name in ("OPENAI_API_KEY", "NVIDIA_NIM_API_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        print(
            json.dumps({"verdict": "ENVIRONMENT", "absent_variables": missing}, indent=2)
        )
        return 3

    proxy_key = f"sk-phase06-{os.urandom(12).hex()}"
    os.environ[p05.PROXY_KEY_ENV] = proxy_key
    port = p05._free_port()
    config_path = p05._write_proxy_config(port)

    process = None
    try:
        process, proxy_url = p05._start_proxy(config_path, port)
        client, state = p05.build_gateway(proxy_url, proxy_key)
        registry = state.health
        threshold = registry.failure_threshold
        cooldown_seconds = registry.cooldown_seconds

        steps: list[dict[str, Any]] = []

        # Three failures to trip the threshold.
        for index in range(threshold):
            status, content = _ask(client)
            snap = registry.snapshot()["primary"]
            steps.append(
                {
                    "step": f"failure_{index + 1}",
                    "status": status,
                    "content": content,
                    "primary_failures": snap["total_failures"],
                    "primary_healthy": snap["healthy"],
                    "primary_available": snap["available"],
                    "cooldown_until": snap["cooldown_until"],
                }
            )

        after_trip = registry.snapshot()["primary"]
        tripped = (
            after_trip["healthy"] is False
            and after_trip["cooldown_until"] is not None
            and registry.available("primary") is False
        )

        # Fourth request: primary must be skipped, and traffic must still flow.
        failures_before_skip = after_trip["total_failures"]
        status, content = _ask(client)
        after_skip = registry.snapshot()["primary"]
        skipped = after_skip["total_failures"] == failures_before_skip
        steps.append(
            {
                "step": "while_cooling_down",
                "status": status,
                "content": content,
                "primary_failures": after_skip["total_failures"],
                "primary_attempted": not skipped,
                "primary_available": after_skip["available"],
            }
        )

        # Expire the deadline: half-open recovery must re-admit the deployment.
        # NOTE: clearing cooldown_until to None would make the deployment
        # permanently unavailable (is_available() returns False for a None
        # deadline on an unhealthy deployment). An *expired* deadline is the
        # only correct way to re-enter the half-open path.
        deadline = registry.deployments["primary"]
        deadline.cooldown_until = datetime.now(UTC) - timedelta(seconds=1)
        recovered = registry.available("primary") is True

        status, content = _ask(client)
        after_recovery = registry.snapshot()["primary"]
        retried = after_recovery["total_failures"] > after_skip["total_failures"]
        steps.append(
            {
                "step": "after_cooldown_expired",
                "status": status,
                "content": content,
                "primary_failures": after_recovery["total_failures"],
                "primary_attempted": retried,
                "primary_available": after_recovery["available"],
            }
        )

        checks = {
            "threshold_tripped": tripped,
            "unavailable_during_cooldown": after_trip["available"] is False,
            "skipped_while_cooling_down": skipped,
            "traffic_flowed_during_cooldown": steps[threshold]["status"] == 200
            and bool(steps[threshold]["content"]),
            "half_open_recovery": recovered,
            "retried_after_recovery": retried,
        }
        passed = all(checks.values())

        print(
            json.dumps(
                {
                    "verdict": "PASS" if passed else "ASSERTION_FAILED",
                    "claim": (
                        "with real provider failures, the passive registry trips at "
                        "its threshold, removes the failing deployment from routing "
                        "while traffic continues, and re-admits it after the cooldown "
                        "deadline expires"
                    ),
                    "threshold": threshold,
                    "cooldown_seconds": cooldown_seconds,
                    "checks": checks,
                    "steps": steps,
                },
                indent=2,
                default=str,
            )
        )
        return 0 if passed else 1
    except Exception as exc:  # noqa: BLE001 - reported, not swallowed
        print(
            json.dumps(
                {"verdict": "ENVIRONMENT", "error": f"{type(exc).__name__}: {exc}"},
                indent=2,
            )
        )
        return 3
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except Exception:  # noqa: BLE001
                process.kill()
        config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
