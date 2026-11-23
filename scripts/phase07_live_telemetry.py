#!/usr/bin/env python3
"""Phase 07 — prove live-provider telemetry lands in the trackers and reads back.

Why this exists
---------------
Phase 07 (Observability) is recorded as *plumbing complete, live-provider
telemetry UNVERIFIED*. The trackers (``monitoring.metrics``,
``monitoring.latency``, ``monitoring.errors``, ``monitoring.usage``) are wired
into ``GatewayState`` and exposed by the admin router, and unit tests exercise
them against stubs. What had never been shown is the end-to-end claim:

    a REAL completion to a REAL provider, driven through the REAL ASGI app,
    produces telemetry that lands in those trackers and is readable back
    through the admin endpoints with the numbers you would expect.

There is no stub in the request path. The chain is:

    TestClient -> SabiRoute ASGI app -> LiteLLMClient -> LiteLLM Proxy
               -> real provider HTTPS -> real response

The proxy is started here from a config derived from the repository's own
``config/config.yaml`` (same ``model`` / ``api_key`` / ``account_id``), so the
provider routes are the production catalogue's, not invented ones.

Spend budget — deliberately tiny
--------------------------------
* at most three real requests, one per alias, in this order:
  ``sabiroute-groq``, ``sabiroute-cloudflare``, ``sabiroute-openrouter``;
* ``max_tokens=32``, sequential, no retries in the proxy
  (``num_retries: 0``) and no cross-alias fallback (an alias request resolves
  to exactly one candidate), so one request is one provider call;
* credentials are read from the environment and never printed — only the
  variable *name* and its ``set``/``EMPTY`` state appear in the output.

What "success" means here
-------------------------
Success is the **gateway's** definition, not a content-quality judgement: a
provider call that returned HTTP 200 is a successful execution and the gateway
records it as such (``metrics.requests_successful``, a latency sample, a usage
record, a health success). A ``200`` whose ``content`` is empty because a
reasoning model spent the whole ``max_tokens`` budget on reasoning
(``finish_reason == "length"``) is still a successful call; its content state
is reported separately (``empty_truncated``) and is never counted as a failure.
Getting this wrong made the first run of this harness report a false
"assertion failed" while the gateway telemetry was in fact perfectly
consistent — see ``--self-check``.

What is proven, and what a failure means
----------------------------------------
A real request may fail at the provider or routing layer. That is data, not
something to hide: the harness records the failure and its categorisation, and
never retries it. The invariants are stated over what actually happened:

* ``metrics.requests_total`` rose by exactly the number of requests attempted;
* ``metrics.requests_successful`` / ``requests_failed`` match the outcomes;
* ``latency`` has a positive sample for every alias that was attempted;
* ``usage`` carries real token counts for every alias that succeeded;
* ``errors`` recorded exactly one categorised record per failed attempt.

Modes
-----
* default — start a proxy, make the real requests, assert, print JSON + tables;
* ``--self-check`` — re-evaluate the captured 2026-11-23 run (below) through
  the same assertion logic with **zero network calls**. This regression-tests
  the evaluator on the real numbers the live run produced.

Exit codes: 0 pass (all invariants held and at least one real success),
1 assertion/invariant failure or no usable completion, 3 environment problem.
"""

from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tests"))

#: The runtime-working aliases (Phase 02 evidence, 2026-11-23). At most three.
ALIASES: tuple[str, ...] = (
    "sabiroute-groq",
    "sabiroute-cloudflare",
    "sabiroute-openrouter",
)

#: Hard ceiling on real provider calls. One request per alias, no retries.
MAX_REQUESTS = 3

PROMPT = "Reply with the single word OK."
MAX_TOKENS = 32
CALL_TIMEOUT = 60

#: Env var names that carry credentials. Values are never read into output;
#: the names double as the scrub list for any diagnostic text.
CREDENTIAL_VARS: dict[str, tuple[str, ...]] = {
    "sabiroute-groq": ("GROQ_API_KEY",),
    "sabiroute-cloudflare": ("CLOUDFLARE_API_KEY", "CLOUDFLARE_ACCOUNT_ID"),
    "sabiroute-openrouter": ("OPENROUTER_API_KEY",),
}

#: Generated per run and held only in this process's environment. Neither is
#: ever written to a file or printed.
PROXY_KEY_ENV = "PHASE07_PROXY_KEY"
ADMIN_KEY_ENV = "SABIROUTE_ADMIN_KEY"

ADMIN_ENDPOINTS: tuple[str, ...] = ("metrics", "latency", "errors", "usage", "health")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _load_env() -> None:
    """Load .env exactly as the application does. Values are never printed.

    ``.env`` is gitignored, so a git worktree of this repository does not have
    one — only the primary checkout does. ``SABIROUTE_ENV_FILE`` names an
    explicit file for that case instead of hardcoding a path.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dotenv is a declared dependency
        return
    explicit = os.environ.get("SABIROUTE_ENV_FILE")
    path = Path(explicit) if explicit else REPO_ROOT / ".env"
    if path.exists():
        load_dotenv(path, override=False)


def _scrub(text: str) -> str:
    """Remove any live credential or generated key from diagnostic text."""
    names = [name for group in CREDENTIAL_VARS.values() for name in group]
    names.extend([PROXY_KEY_ENV, ADMIN_KEY_ENV])
    for name in names:
        value = os.environ.get(name)
        if value:
            text = text.replace(value, "[REDACTED]")
    return text


def _missing_credentials() -> list[str]:
    missing: list[str] = []
    for names in CREDENTIAL_VARS.values():
        for name in names:
            if name not in missing and not os.environ.get(name):
                missing.append(name)
    return missing


def _proxy_config(names: tuple[str, ...]) -> Path:
    """Write a LiteLLM Proxy config for exactly ``names``, derived from the repo.

    Only the *routes* are taken from ``config/config.yaml``; retries are forced
    to zero so one harness request cannot become two provider calls.
    """
    from sabiroute.config.loader import load_config

    config = load_config(str(REPO_ROOT / "config" / "config.yaml"))
    by_name = {entry.model_name: entry for entry in config.model_list}

    lines: list[str] = ["model_list:"]
    for name in names:
        entry = by_name[name]
        params = entry.litellm_params
        lines.append(f"  - model_name: {name}")
        lines.append("    litellm_params:")
        lines.append(f"      model: {params.model}")
        if params.api_key:
            lines.append(f"      api_key: {params.api_key}")
        if params.account_id:
            lines.append(f"      account_id: {params.account_id}")
        if params.api_base:
            lines.append(f"      api_base: {params.api_base}")
        for key, value in (params.model_extra or {}).items():
            if key == "num_retries":
                continue
            lines.append(f"      {key}: {value}")
        lines.append("      num_retries: 0")

    lines.extend(
        [
            "litellm_settings:",
            "  drop_params: true",
            "  request_timeout: 60",
            "  num_retries: 0",
            "  set_verbose: false",
            "general_settings:",
            f"  master_key: os.environ/{PROXY_KEY_ENV}",
        ]
    )

    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".yaml", prefix="phase07-live-proxy-", delete=False
    )
    handle.write("\n".join(lines) + "\n")
    handle.close()
    return Path(handle.name)


def _start_proxy(
    config_path: Path, port: int, readiness_timeout: float = 240.0
) -> tuple[Any, str]:
    """Start LiteLLM Proxy and wait for readiness. Output is discarded.

    Proxy logs are not captured at all: a startup failure is reported as an
    environment problem, never by echoing a log that might contain a secret.
    """
    import httpx

    executable = Path(sys.executable).parent / "litellm"
    process = subprocess.Popen(  # noqa: S603 - fixed executable, generated config
        [
            str(executable),
            "--config",
            str(config_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + readiness_timeout
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("LiteLLM Proxy exited before becoming ready")
        try:
            if httpx.get(f"{url}/health/readiness", timeout=2.0).status_code == 200:
                return process, url
        except httpx.HTTPError:
            pass
        time.sleep(1.0)
    process.terminate()
    raise RuntimeError("LiteLLM Proxy did not become ready in time")


def _build(proxy_url: str, proxy_key: str) -> tuple[Any, Any, Any]:
    """Build real gateway state, a client-authenticated and an admin client."""
    from conftest import InMemoryApiKeyStore, provision_test_key
    from fastapi.testclient import TestClient

    from sabiroute.config.loader import load_config
    from sabiroute.gateway import build_gateway_state
    from sabiroute.main import create_app
    from sabiroute.providers.litellm_client import LiteLLMClient

    # The production catalogue, injected explicitly so the worktree's config
    # is the one used — never an ambient path from another checkout.
    config = load_config(str(REPO_ROOT / "config" / "config.yaml"))

    state = build_gateway_state(
        config=config,
        client=LiteLLMClient(
            base_url=proxy_url, api_key=proxy_key, timeout_seconds=float(CALL_TIMEOUT)
        ),
        key_store=InMemoryApiKeyStore(),
    )
    client_key = provision_test_key(state)

    # Provision the admin secret for THIS process. The admin boundary reads
    # SABIROUTE_ADMIN_KEY from the environment at request time; keeping the
    # secret internal means the harness never depends on, and never prints,
    # whatever the operator's .env happens to hold.
    admin_key = f"sk-phase07-admin-{secrets.token_hex(12)}"
    os.environ[ADMIN_KEY_ENV] = admin_key

    app = create_app(state=state)
    client = TestClient(app, headers={"Authorization": f"Bearer {client_key}"})
    admin = TestClient(app, headers={"Authorization": f"Bearer {admin_key}"})
    return client, admin, state


def _admin_snapshot(admin: Any) -> dict[str, Any]:
    """Read every admin telemetry endpoint and capture its body and status."""
    snapshot: dict[str, Any] = {}
    for name in ADMIN_ENDPOINTS:
        response = admin.get(f"/admin/{name}")
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text[:400]
        snapshot[name] = {"status": response.status_code, "body": body}
    return snapshot


def _content_of(body: Any) -> str:
    if isinstance(body, dict):
        choices = body.get("choices") or []
        if choices:
            return (choices[0].get("message") or {}).get("content") or ""
    return ""


def _finish_reason(body: Any) -> str | None:
    if isinstance(body, dict):
        choices = body.get("choices") or []
        if choices:
            return choices[0].get("finish_reason")
    return None


def _usage_of(body: Any) -> dict[str, Any] | None:
    if isinstance(body, dict) and isinstance(body.get("usage"), dict):
        return body["usage"]
    return None


def _failure_category(body: Any) -> str | None:
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            return error.get("failure_category") or error.get("type")
    return None


def _evaluate(
    results: list[dict[str, Any]],
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    """Assert the telemetry invariants over what actually happened.

    Success is HTTP 200, matching the gateway's own accounting. Content
    emptiness is reported but never reclassified as a failure.
    """
    before_metrics = before["metrics"]["body"]
    after_metrics = after["metrics"]["body"]
    before_errors = before["errors"]["body"]
    before_usage = before["usage"]["body"]

    successes = [item for item in results if int(item.get("status", 0)) == 200]
    failures = [item for item in results if int(item.get("status", 0)) != 200]
    success_aliases = [item["alias"] for item in successes]
    attempted_aliases = [item["alias"] for item in results]

    total_delta = after_metrics["requests_total"] - before_metrics["requests_total"]
    success_delta = (
        after_metrics["requests_successful"] - before_metrics["requests_successful"]
    )
    failure_delta = after_metrics["requests_failed"] - before_metrics["requests_failed"]
    error_delta = sum(after["errors"]["body"].values()) - sum(before_errors.values())

    latency = after["latency"]["body"]
    usage_totals = after["usage"]["body"]

    checks: dict[str, bool] = {
        "request_count_rose_by_attempts": total_delta == len(results),
        "success_count_matches": success_delta == len(successes),
        "failure_count_matches": failure_delta == len(failures),
        "latency_recorded_for_every_attempt": all(
            alias in latency
            and int(latency[alias].get("samples", 0)) >= 1
            and float(latency[alias].get("last_ms", 0.0)) > 0.0
            for alias in attempted_aliases
        ),
        "errors_categorised_per_failure": error_delta == len(failures),
    }

    usage_proven = bool(successes) and all(
        usage_totals.get(alias, 0) > before_usage.get(alias, 0)
        for alias in success_aliases
    )
    checks["usage_recorded_with_real_tokens"] = usage_proven

    passed = all(checks.values())
    if passed:
        verdict = "PASS"
    elif not successes and all(
        value for key, value in checks.items() if key != "usage_recorded_with_real_tokens"
    ):
        verdict = "NO_USABLE_COMPLETION"
    else:
        verdict = "ASSERTION_FAILED"

    return {
        "deltas": {
            "metrics_requests_total": total_delta,
            "metrics_requests_successful": success_delta,
            "metrics_requests_failed": failure_delta,
            "errors_records": error_delta,
        },
        "success_aliases": success_aliases,
        "checks": checks,
        "usage_proven": usage_proven,
        "verdict": verdict,
        "passed": passed,
    }


def _print_table(results: list[dict[str, Any]], after: dict[str, Any]) -> None:
    print("\nLive requests")
    print(
        f"  {'alias':<24}{'status':<8}{'outcome':<10}{'content':<16}"
        f"{'elapsed_ms':>11}{'prompt':>8}{'compl':>7}{'total':>7}  category"
    )
    for item in results:
        usage = item.get("usage") or {}
        print(
            f"  {item['alias']:<24}{item['status']:<8}{item['outcome']:<10}"
            f"{item['content_state']:<16}{item['elapsed_ms']:>11}"
            f"{usage.get('prompt_tokens', '-'):>8}"
            f"{usage.get('completion_tokens', '-'):>7}"
            f"{usage.get('total_tokens', '-'):>7}  {item.get('category') or '-'}"
        )

    print("\nAdmin /admin/metrics")
    metrics = after["metrics"]["body"]
    for key in (
        "requests_total",
        "requests_successful",
        "requests_failed",
        "requests_rate_limited",
    ):
        print(f"  {key:<24}{metrics.get(key)}")
    print(f"  requests_by_model        {metrics.get('requests_by_model')}")

    print("\nAdmin /admin/latency")
    latency = after["latency"]["body"]
    if latency:
        for deployment, stats in latency.items():
            print(
                f"  {deployment:<24}samples={stats.get('samples')} "
                f"average_ms={stats.get('average_ms'):.1f} "
                f"last_ms={stats.get('last_ms'):.1f}"
            )
    else:
        print("  (empty)")

    print("\nAdmin /admin/usage")
    usage_totals = after["usage"]["body"]
    if usage_totals:
        for deployment, total in usage_totals.items():
            print(f"  {deployment:<24}total_tokens={total}")
    else:
        print("  (empty)")

    print("\nAdmin /admin/errors")
    errors = after["errors"]["body"]
    if errors:
        for category, count in errors.items():
            print(f"  {category:<24}{count}")
    else:
        print("  (empty)")

    print("\nAdmin /admin/health")
    health = after["health"]["body"]
    for deployment, stats in health.items():
        print(
            f"  {deployment:<24}healthy={stats.get('healthy')} "
            f"successes={stats.get('total_successes')} "
            f"failures={stats.get('total_failures')}"
        )


def _run_live() -> int:
    _load_env()

    if len(ALIASES) > MAX_REQUESTS:
        print(
            json.dumps(
                {"verdict": "ENVIRONMENT", "reason": "alias list exceeds the spend budget"},
                indent=2,
            )
        )
        return 3

    missing = _missing_credentials()
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

    proxy_key = f"sk-phase07-{secrets.token_hex(12)}"
    os.environ[PROXY_KEY_ENV] = proxy_key
    port = _free_port()
    config_path = _proxy_config(ALIASES)

    process = None
    try:
        process, proxy_url = _start_proxy(config_path, port)
        client, admin, state = _build(proxy_url, proxy_key)

        before = _admin_snapshot(admin)

        results: list[dict[str, Any]] = []
        for alias in ALIASES:
            started = time.perf_counter()
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": alias,
                    "messages": [{"role": "user", "content": PROMPT}],
                    "max_tokens": MAX_TOKENS,
                },
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            try:
                body: Any = response.json()
            except ValueError:
                body = response.text[:400]

            content = _content_of(body)
            finish_reason = _finish_reason(body)
            if response.status_code != 200:
                outcome, content_state = "failure", "n/a"
            else:
                outcome = "success"
                if content.strip():
                    content_state = "non_empty"
                elif finish_reason == "length":
                    content_state = "empty_truncated"
                else:
                    content_state = "empty"

            results.append(
                {
                    "alias": alias,
                    "requested_model": alias,
                    "status": response.status_code,
                    "outcome": outcome,
                    "content_state": content_state,
                    "finish_reason": finish_reason,
                    "deployment_header": response.headers.get("X-SabiRoute-Deployment"),
                    "elapsed_ms": elapsed_ms,
                    "usage": _usage_of(body),
                    "content_preview": _scrub(content.strip()[:80]),
                    "category": None if outcome == "success" else _failure_category(body),
                    "body": body if outcome != "success" else None,
                }
            )

        after = _admin_snapshot(admin)

        bad_status = {
            name: snap["status"] for name, snap in after.items() if snap["status"] != 200
        }
        if bad_status:
            print(
                json.dumps(
                    {
                        "verdict": "ASSERTION_FAILED",
                        "reason": "an admin endpoint did not return 200",
                        "admin_status": bad_status,
                    },
                    indent=2,
                )
            )
            return 1

        evaluation = _evaluate(results, before, after)

        payload = {
            "verdict": evaluation["verdict"],
            "claim": (
                "real completions to real providers, driven through the real "
                "ASGI app, produced metrics/latency/usage/error telemetry that "
                "reads back through the admin endpoints with the expected numbers"
            ),
            "spend": {"real_requests": len(results), "ceiling": MAX_REQUESTS},
            "credentials": {
                alias: {
                    name: ("set" if os.environ.get(name) else "EMPTY")
                    for name in names
                }
                for alias, names in CREDENTIAL_VARS.items()
            },
            "admin_auth": {
                "mechanism": "SABIROUTE_ADMIN_KEY (generated per run)",
                "value_printed": False,
            },
            "before": before,
            "requests": results,
            "after": after,
            "evaluation": evaluation,
        }

        print(json.dumps(payload, indent=2, default=str))
        _print_table(results, after)
        return 0 if evaluation["passed"] else 1

    except Exception as exc:  # noqa: BLE001 - reported, not swallowed
        print(
            json.dumps(
                {"verdict": "ENVIRONMENT", "error": _scrub(f"{type(exc).__name__}: {exc}")},
                indent=2,
            )
        )
        return 3
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:  # pragma: no cover
                process.kill()
        config_path.unlink(missing_ok=True)


#: Values captured verbatim from the live run on 2026-11-23 (three real
#: requests, ~189 billed tokens). Kept only to regression-test ``_evaluate``
#: with zero network calls; it is NOT fresh provider evidence.
CAPTURED_RUN_2026_11_23: dict[str, Any] = {
    "before": {
        "metrics": {
            "status": 200,
            "body": {
                "requests_total": 0,
                "requests_successful": 0,
                "requests_failed": 0,
                "requests_rate_limited": 0,
                "requests_by_model": {},
            },
        },
        "latency": {"status": 200, "body": {}},
        "errors": {"status": 200, "body": {}},
        "usage": {"status": 200, "body": {}},
        "health": {"status": 200, "body": {}},
    },
    "requests": [
        {
            "alias": "sabiroute-groq",
            "status": 200,
            "elapsed_ms": 1377.5,
            "usage": {"prompt_tokens": 78, "completion_tokens": 32, "total_tokens": 110},
        },
        {
            "alias": "sabiroute-cloudflare",
            "status": 200,
            "elapsed_ms": 1402.7,
            "usage": {"prompt_tokens": 42, "completion_tokens": 2, "total_tokens": 44},
        },
        {
            "alias": "sabiroute-openrouter",
            "status": 200,
            "elapsed_ms": 9090.1,
            "usage": {"prompt_tokens": 7, "completion_tokens": 28, "total_tokens": 35},
        },
    ],
    "after": {
        "metrics": {
            "status": 200,
            "body": {
                "requests_total": 3,
                "requests_successful": 3,
                "requests_failed": 0,
                "requests_rate_limited": 0,
                "requests_by_model": {
                    "sabiroute-groq": 1,
                    "sabiroute-cloudflare": 1,
                    "sabiroute-openrouter": 1,
                },
            },
        },
        "latency": {
            "status": 200,
            "body": {
                "sabiroute-groq": {
                    "samples": 1,
                    "average_ms": 1363.626749953255,
                    "last_ms": 1363.626749953255,
                },
                "sabiroute-cloudflare": {
                    "samples": 1,
                    "average_ms": 1399.6659589465708,
                    "last_ms": 1399.6659589465708,
                },
                "sabiroute-openrouter": {
                    "samples": 1,
                    "average_ms": 9087.739584036171,
                    "last_ms": 9087.739584036171,
                },
            },
        },
        "errors": {"status": 200, "body": {}},
        "usage": {
            "status": 200,
            "body": {
                "sabiroute-groq": 110,
                "sabiroute-cloudflare": 44,
                "sabiroute-openrouter": 35,
            },
        },
        "health": {"status": 200, "body": {}},
    },
}


def _run_self_check() -> int:
    """Re-evaluate the captured live run through the real assertion logic."""
    captured = CAPTURED_RUN_2026_11_23
    evaluation = _evaluate(captured["requests"], captured["before"], captured["after"])
    print(
        json.dumps(
            {
                "mode": "self-check",
                "network_calls": 0,
                "source": "captured live run 2026-11-23",
                "evaluation": evaluation,
            },
            indent=2,
        )
    )
    return 0 if evaluation["passed"] else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--self-check"]:
        return _run_self_check()
    if args:
        print(
            json.dumps(
                {"verdict": "ENVIRONMENT", "reason": f"unknown arguments: {args}"},
                indent=2,
            )
        )
        return 3
    return _run_live()


if __name__ == "__main__":
    raise SystemExit(main())
