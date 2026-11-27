#!/usr/bin/env python3
"""Phase 07 — capture the admin telemetry surfaces under a real induced failure.

Why this exists
---------------
``scripts/phase07_live_telemetry.py`` proves the **success** path: a real completion to a real
provider lands in the trackers and reads back through the admin endpoints. Its recorded run is
``artifacts/sprint-4/PHASE07-LIVE-TELEMETRY-2026-11-23.md`` (verdict PASS).

What it deliberately does not do is fail. It drives one alias per request with no cross-alias
fallback, so every request it issues succeeds.

The scorecard's remaining gap for Phase 07 is therefore narrower than "telemetry unverified":

    "no stored failure-metric evidence; trackers are process-local and reset on restart"
    next action: "capture an admin metrics snapshot under induced failure"

That is the only claim this harness makes:

    SabiRoute -> LiteLLM Proxy -> primary   (real provider, really fails)
                                -> secondary (real provider, really answers)

    GET /admin/{metrics,errors,latency,usage} before and after the request.

The failure is not stubbed. It is the same credential-carrying provider path Phase 05 proves
failover on, so these are the counters a real operator would see during an incident. Phase 05
establishes *that* the failover happened; this establishes that it was **observable through
the administrative surfaces**, which is the Phase 07 claim.

Deliberately not claimed
------------------------
Capturing a snapshot is not durability. ``Metrics``, ``ErrorTracker`` and ``UsageTracker`` are
in-process dataclasses and still reset on restart. ``monitoring/signals_store.py`` persists
health/latency *signals* over a pluggable backend, but not these counters. This harness stores
the snapshot as a file; it does not make the counters durable, and the report says so rather
than letting a green result imply otherwise.

Exit codes: 0 pass, 1 assertion failure, 2 premise not met, 3 environment.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

# The proxy plumbing, gateway builder, env loading and port selection are shared with the
# Phase 05 harness on purpose: one instrument, two observations. Importing rather than copying
# means the two phases cannot drift into testing different things. ``phase06_health_cooldown_live``
# already reuses Phase 05 the same way.
import phase05_real_provider_failure as p05  # noqa: E402

ADMIN_KEY_ENV = "SABIROUTE_ADMIN_KEY"
ADMIN_SURFACES = ("metrics", "errors", "latency", "usage")


def _admin_snapshot(client: Any, admin_key: str) -> dict[str, Any]:
    """Read every admin telemetry surface with administrative credentials."""
    headers = {"Authorization": f"Bearer {admin_key}"}
    snapshot: dict[str, Any] = {}
    for name in ADMIN_SURFACES:
        response = client.get(f"/admin/{name}", headers=headers)
        try:
            payload: Any = response.json()
        except ValueError:
            payload = response.text[:400]
        snapshot[name] = {"status": response.status_code, "body": payload}
    return snapshot


def _int_fields(payload: Any) -> dict[str, int]:
    """Flat integer counters only; nested maps such as requests_by_model are compared apart."""
    if not isinstance(payload, dict):
        return {}
    return {key: value for key, value in payload.items() if isinstance(value, int)}


def _delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    return {
        key: after.get(key, 0) - before.get(key, 0)
        for key in sorted(set(before) | set(after))
    }


def main() -> int:
    p05._load_env()

    missing = [
        name
        for name in ("OPENAI_API_KEY", "NVIDIA_NIM_API_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        print(
            json.dumps(
                {
                    "verdict": "ENVIRONMENT",
                    "reason": "provider credential absent",
                    "absent_variables": missing,
                },
                indent=2,
            )
        )
        return 3

    # A per-run administrative secret: never a client key prefix, never the proxy master key.
    admin_key = f"sk-admin-phase07-{secrets.token_hex(12)}"
    os.environ[ADMIN_KEY_ENV] = admin_key

    proxy_key = f"sk-phase05-{secrets.token_hex(12)}"
    os.environ[p05.PROXY_KEY_ENV] = proxy_key
    port = p05._free_port()
    config_path = p05._write_proxy_config(port)

    process = None
    try:
        process, proxy_url = p05._start_proxy(config_path, port)
        client, state = p05.build_gateway(proxy_url, proxy_key)

        # Baseline first; it doubles as a check of the admin boundary itself.
        before = _admin_snapshot(client, admin_key)
        unreachable = {
            name: entry for name, entry in before.items() if entry["status"] != 200
        }
        if unreachable:
            print(
                json.dumps(
                    {
                        "verdict": "ENVIRONMENT",
                        "reason": "administrative telemetry surface not reachable",
                        "surfaces": unreachable,
                    },
                    indent=2,
                    default=str,
                )
            )
            return 3

        started = time.perf_counter()
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "fast",
                "messages": [{"role": "user", "content": "Reply with the word OK."}],
            },
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

        try:
            body: Any = response.json()
        except ValueError:
            body = response.text[:400]

        after = _admin_snapshot(client, admin_key)

        health = state.health.snapshot()
        primary = health.get("primary", {})
        secondary = health.get("secondary", {})
        primary_failures = int(primary.get("total_failures") or 0)
        primary_successes = int(primary.get("total_successes") or 0)

        content = ""
        if isinstance(body, dict):
            choices = body.get("choices") or []
            if choices:
                content = (choices[0].get("message") or {}).get("content") or ""

        # The premise, checked before the claim it licenses. Without a real failure the
        # counters below would prove nothing about failure observability.
        if primary_failures == 0:
            verdict = (
                "PREMISE_NOT_MET" if primary_successes > 0 else "PREMISE_UNREACHABLE"
            )
            print(
                json.dumps(
                    {
                        "verdict": verdict,
                        "reason": (
                            "the primary provider answered, so no failure occurred and "
                            "no failure-observability claim is warranted"
                            if primary_successes > 0
                            else "no failure and no success was recorded against primary"
                        ),
                        "status": response.status_code,
                        "before": before,
                        "after": after,
                        "health": health,
                        "body": body,
                    },
                    indent=2,
                    default=str,
                )
            )
            return 2 if primary_successes > 0 else 3

        metrics_before = _int_fields(before["metrics"]["body"])
        metrics_after = _int_fields(after["metrics"]["body"])
        metrics_delta = _delta(metrics_before, metrics_after)

        errors_before = _int_fields(before["errors"]["body"])
        errors_after = _int_fields(after["errors"]["body"])
        errors_delta = _delta(errors_before, errors_after)

        latency_body = after["latency"]["body"]
        latency_models = sorted(latency_body) if isinstance(latency_body, dict) else []

        checks = {
            "status_200": response.status_code == 200,
            "non_empty_text": bool(content.strip()),
            "primary_recorded_failure": primary_failures >= 1,
            "secondary_recorded_success": int(secondary.get("total_successes") or 0) >= 1,
            "metrics_counted_the_request": metrics_delta.get("requests_total", 0) >= 1,
            "metrics_counted_a_failure": metrics_delta.get("requests_failed", 0) >= 1,
            "metrics_counted_a_success": metrics_delta.get("requests_successful", 0) >= 1,
            "error_tracker_recorded_failure": any(
                value >= 1 for value in errors_delta.values()
            ),
            "latency_tracker_recorded_deployment": bool(
                {"primary", "secondary"} & set(latency_models)
            ),
        }
        passed = all(checks.values())

        print(
            json.dumps(
                {
                    "verdict": "PASS" if passed else "ASSERTION_FAILED",
                    "claim": (
                        "a real provider failure was observable through SabiRoute's "
                        "administrative telemetry surfaces: metrics counted the failure "
                        "and the success, the error tracker classified it, and the "
                        "latency tracker recorded the serving deployment"
                    ),
                    "status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "content_preview": content.strip()[:120],
                    "served_model": (
                        body.get("model") if isinstance(body, dict) else None
                    ),
                    "checks": checks,
                    "health": health,
                    "metrics": {
                        "before": metrics_before,
                        "after": metrics_after,
                        "delta": metrics_delta,
                        "requests_by_model": (
                            after["metrics"]["body"].get("requests_by_model")
                            if isinstance(after["metrics"]["body"], dict)
                            else None
                        ),
                    },
                    "errors": {
                        "before": errors_before,
                        "after": errors_after,
                        "delta": errors_delta,
                    },
                    "latency": {"body": latency_body},
                    "usage": {"body": after["usage"]["body"]},
                    "durability_note": (
                        "counters are in-process and still reset on restart; this "
                        "snapshot is stored evidence, not persistence"
                    ),
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
            except Exception:  # noqa: BLE001 - best effort teardown
                process.kill()
        config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
