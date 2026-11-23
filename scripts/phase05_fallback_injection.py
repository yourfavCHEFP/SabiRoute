"""Phase 05 — live fallback failure-injection evidence.

WHY THIS EXISTS
---------------
``tests/test_fallback_injection.py`` proves the attempt loop's decisions using an
in-process stub client that raises a hand-built ``LiteLLMClientError``. That proves
the *branching logic*. It does not prove the seam between that logic and a real
HTTP conversation: whether an actual non-2xx response becomes a
``LiteLLMClientError`` carrying the status the retry classifier reads, whether a
timeout is classified as retryable, whether an SSE failure is caught before the
stream is handed to the caller, and whether health cooldown reacts to real
failures.

This script closes that gap with no provider credentials and no network egress:

    SabiRoute app  ->  real LiteLLMClient (httpx)  ->  stub provider on a real socket

Every scenario drives the real ASGI app through ``TestClient``, so the request
crosses a real TCP connection to the stub and comes back through the real
``LiteLLMClientError`` mapping. The stub picks a fault by the ``model`` field,
which SabiRoute sets to the deployment alias it chose, so the recorded call
sequence is direct evidence of which deployment was attempted, in what order.

Not a pytest module on purpose: it is an experiment that prints its evidence and
exits non-zero on mismatch, so it can be cited as a documented run rather than
counted as a unit test.

Usage:
    ./.venv/bin/python scripts/phase05_fallback_injection.py

Exit code 0 only when every scenario matches its expectation.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tests"))

# The stub authenticates nothing. The variable exists only so configuration can
# carry an environment reference instead of a literal credential.
os.environ.setdefault("SABIROUTE_PHASE05_STUB_KEY", "sk-stub-not-a-credential")

from conftest import InMemoryApiKeyStore, provision_test_key  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from sabiroute.config.loader import validate_config  # noqa: E402
from sabiroute.config.models import SabiRouteConfig  # noqa: E402
from sabiroute.gateway import build_gateway_state  # noqa: E402
from sabiroute.main import create_app  # noqa: E402
from sabiroute.providers.litellm_client import LiteLLMClient  # noqa: E402

OK_BODY = {
    "id": "chatcmpl-stub",
    "object": "chat.completion",
    "model": "stub",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "ok"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
}

# Authenticates nothing: it only unlocks the locally-spawned proxy, and both ends
# live inside this process's lifetime.
PROXY_MASTER_KEY = "sk-phase05-proxy-master-not-a-credential"

SSE_FRAMES = (
    b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
    b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
    b'data: {"choices":[],"usage":{"prompt_tokens":3,"completion_tokens":2,'
    b'"total_tokens":5}}\n\n'
    b"data: [DONE]\n\n"
)


@dataclass
class Fault:
    """Fault behaviour for one deployment alias."""

    status: int | None = None
    delay_seconds: float = 0.0
    fail_forever: bool = False
    calls: int = 0


@dataclass
class StubProvider:
    """An OpenAI-compatible endpoint on a real socket with per-alias faults."""

    faults: dict[str, Fault] = field(default_factory=dict)
    calls: list[str] = field(default_factory=list)
    url: str = ""
    _server: ThreadingHTTPServer | None = None

    def start(self) -> str:
        stub = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args: Any) -> None:  # keep output clean
                pass

            def _send(self, status: int, content_type: str, body: bytes) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:  # noqa: N802 - stdlib naming
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    payload = json.loads(raw or b"{}")
                except ValueError:
                    payload = {}

                alias = str(payload.get("model") or "")
                streaming = bool(payload.get("stream"))
                stub.calls.append(alias)

                fault = stub.faults.get(alias)
                if fault is not None:
                    fault.calls += 1
                    if fault.delay_seconds:
                        time.sleep(fault.delay_seconds)
                    if fault.fail_forever and fault.status is not None:
                        error = json.dumps(
                            {
                                "error": {
                                    "message": f"stub fault {fault.status} for {alias}",
                                    "type": "stub_error",
                                    "code": fault.status,
                                }
                            }
                        ).encode()
                        self._send(fault.status, "application/json", error)
                        return

                if streaming:
                    self._send(200, "text/event-stream", SSE_FRAMES)
                    return

                self._send(200, "application/json", json.dumps(OK_BODY).encode())

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server = server
        threading.Thread(target=server.serve_forever, daemon=True).start()
        host, port = server.server_address[:2]
        self.url = f"http://{host}:{port}"
        return self.url

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None


@dataclass
class Scenario:
    name: str
    description: str
    primary_status: int | None
    expect_status: int
    expect_calls: list[str]
    stream: bool = False
    timeout_seconds: float = 5.0
    delay_seconds: float = 0.0
    secondary_fails: bool = False
    expect_error_type: str | None = None


SCENARIOS = [
    Scenario(
        name="A_retryable_500_falls_back",
        description="Upstream 500 on the first candidate falls back and succeeds.",
        primary_status=500,
        expect_status=200,
        expect_calls=["primary", "secondary"],
    ),
    Scenario(
        name="B_retryable_429_falls_back",
        description="429 is in RETRYABLE_STATUS_CODES and falls back.",
        primary_status=429,
        expect_status=200,
        expect_calls=["primary", "secondary"],
    ),
    Scenario(
        name="C_retryable_401_falls_back",
        description="401 is a deployment-credential fault and falls back.",
        primary_status=401,
        expect_status=200,
        expect_calls=["primary", "secondary"],
    ),
    Scenario(
        name="D_non_retryable_404_stops",
        description=(
            "404 does not fall back, and the caller receives the classified 502 "
            "sabiroute_upstream_error rather than the upstream status."
        ),
        primary_status=404,
        expect_status=502,
        expect_calls=["primary"],
        expect_error_type="sabiroute_upstream_error",
    ),
    Scenario(
        name="E_non_retryable_400_stops",
        description="400 does not fall back; the classified 502 is returned.",
        primary_status=400,
        expect_status=502,
        expect_calls=["primary"],
        expect_error_type="sabiroute_upstream_error",
    ),
    Scenario(
        name="F_all_candidates_fail_is_classified",
        description="Every candidate failing yields a classified error, not a crash.",
        primary_status=500,
        expect_status=502,
        expect_calls=["primary", "secondary"],
        secondary_fails=True,
    ),
    Scenario(
        name="G_streaming_failure_falls_back",
        description="An SSE error before the stream opens falls back.",
        primary_status=500,
        expect_status=200,
        expect_calls=["primary", "secondary"],
        stream=True,
    ),
    Scenario(
        name="H_timeout_is_retryable",
        description="A client-side timeout carries no status and falls back.",
        primary_status=None,
        expect_status=200,
        expect_calls=["primary", "secondary"],
        timeout_seconds=0.25,
        delay_seconds=2.0,
    ),
]


def build_client(
    stub_url: str,
    deployments: list[str],
    timeout_seconds: float,
    api_key: str | None = None,
):
    config = validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": name,
                        "capabilities": {"chat": True, "streaming": True},
                        "litellm_params": {
                            "model": f"openai/{name}",
                            # Repository credential policy forbids a literal key in
                            # configuration, so the stub uses an environment reference
                            # pointing at a value that authenticates nothing.
                            "api_key": "os.environ/SABIROUTE_PHASE05_STUB_KEY",
                        },
                    }
                    for name in deployments
                ]
            }
        )
    )
    state = build_gateway_state(
        config=config,
        client=LiteLLMClient(
            base_url=stub_url, api_key=api_key, timeout_seconds=timeout_seconds
        ),
        key_store=InMemoryApiKeyStore(),
    )
    key = provision_test_key(state)
    client = TestClient(
        create_app(state=state), headers={"Authorization": f"Bearer {key}"}
    )
    return client, state


def run_scenario(
    stub: StubProvider,
    deployments: list[str],
    scenario: Scenario,
    base_url: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    stub.calls.clear()
    stub.faults["primary"] = Fault(
        status=scenario.primary_status,
        delay_seconds=scenario.delay_seconds,
        fail_forever=scenario.primary_status is not None,
    )
    stub.faults["secondary"] = Fault(
        status=500 if scenario.secondary_fails else None,
        fail_forever=scenario.secondary_fails,
    )

    client, state = build_client(
        base_url or stub.url, deployments, scenario.timeout_seconds, api_key=api_key
    )
    payload: dict[str, Any] = {
        "model": "fast",
        "messages": [{"role": "user", "content": "hi"}],
    }
    if scenario.stream:
        payload["stream"] = True

    started = time.perf_counter()
    response = client.post("/v1/chat/completions", json=payload)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if scenario.stream and response.status_code == 200:
        body: Any = response.text[:200]
    else:
        try:
            body = response.json()
        except ValueError:
            body = response.text[:400]

    calls = list(stub.calls)
    # LiteLLM performs its own execution-level retries before returning to
    # SabiRoute, so one SabiRoute attempt can appear as several upstream calls to
    # the same alias. The claim under test is the ORDER of aliases SabiRoute
    # moved through, not how many times the executor retried each one, so
    # consecutive duplicates are collapsed.
    sequence: list[str] = []
    for alias in calls:
        if not sequence or sequence[-1] != alias:
            sequence.append(alias)

    error_type = body.get("error", {}).get("type") if isinstance(body, dict) else None
    type_ok = scenario.expect_error_type is None or error_type == scenario.expect_error_type
    return {
        "name": scenario.name,
        "description": scenario.description,
        "status": response.status_code,
        "expected_status": scenario.expect_status,
        "error_type": error_type,
        "calls": calls,
        "alias_sequence": sequence,
        "expected_calls": scenario.expect_calls,
        "elapsed_ms": round(elapsed_ms, 1),
        "health": state.health.snapshot(),
        "body": body,
        "ok": response.status_code == scenario.expect_status
        and sequence == scenario.expect_calls
        and type_ok,
    }


def run_cooldown(stub: StubProvider) -> dict[str, Any]:
    """Trip the failure threshold on every candidate, then observe refusal."""
    stub.calls.clear()
    stub.faults["primary"] = Fault(status=500, fail_forever=True)
    stub.faults["secondary"] = Fault(status=500, fail_forever=True)
    client, state = build_client(stub.url, ["primary", "secondary"], 5.0)

    body = {"model": "fast", "messages": [{"role": "user", "content": "hi"}]}
    trip_statuses = [client.post("/v1/chat/completions", json=body).status_code for _ in range(3)]
    calls_before = list(stub.calls)
    snapshot = state.health.snapshot()
    fourth = client.post("/v1/chat/completions", json=body)
    calls_after = list(stub.calls)

    return {
        "name": "I_cooldown_stops_upstream_calls",
        "description": (
            "After both candidates trip the 3-failure threshold, a further request "
            "is refused without any new upstream call."
        ),
        "status": fourth.status_code,
        "expected_status": 503,
        "trip_statuses": trip_statuses,
        "calls": calls_after,
        "expected_calls": calls_before,
        "elapsed_ms": None,
        "health": snapshot,
        "body": fourth.text[:400],
        "ok": fourth.status_code == 503 and calls_after == calls_before,
    }


def run_recovery(stub: StubProvider) -> dict[str, Any]:
    """Prove the half-open path: after cooldown expiry the candidate is retried."""
    stub.calls.clear()
    stub.faults["primary"] = Fault(status=500, fail_forever=True)
    stub.faults["secondary"] = Fault(status=None)
    client, state = build_client(stub.url, ["primary"], 5.0)
    body = {"model": "fast", "messages": [{"role": "user", "content": "hi"}]}

    for _ in range(3):
        client.post("/v1/chat/completions", json=body)
    blocked = client.post("/v1/chat/completions", json=body)
    blocked_calls = len(stub.calls)
    cooldown_snapshot = state.health.snapshot()

    # Move the cooldown deadline into the past rather than sleeping for the
    # configured 30s. Note the trap this records: setting ``cooldown_until`` to
    # None while ``healthy`` is False is a PERMANENT removal, not a reset --
    # ``is_available()`` returns False for a None deadline on an unhealthy
    # deployment. Only an expired deadline re-enters the half-open path.
    health = state.health.deployments["primary"]
    health.cooldown_until = datetime.now(UTC) - timedelta(seconds=1)
    recovered = client.post("/v1/chat/completions", json=body)
    recovery_snapshot = state.health.snapshot()
    recovery_health = recovery_snapshot["primary"]

    return {
        "name": "J_half_open_recovery_after_cooldown",
        "description": (
            "Once the cooldown deadline passes, the deployment re-enters rotation "
            "with a fresh failure budget instead of staying excluded."
        ),
        "status": recovered.status_code,
        "expected_status": 502,
        "blocked_status": blocked.status_code,
        "calls_before_recovery": blocked_calls,
        "calls_total": len(stub.calls),
        "cooldown_health": cooldown_snapshot,
        "recovery_health": recovery_snapshot,
        "body": recovered.text[:300],
        "ok": blocked.status_code == 503
        and recovered.status_code == 502
        and len(stub.calls) == blocked_calls + 1
        and recovery_health["consecutive_failures"] == 1,
    }


def _free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_proxy(stub_url: str, readiness_timeout: float = 90.0) -> tuple[Any, str]:
    """Boot the real LiteLLM Proxy pointing both aliases at the stub provider.

    The proxy config carries only ``api_base`` at the stub and a stub key that
    authenticates nothing, so no provider credential and no egress are involved.
    """
    import subprocess
    import tempfile

    port = _free_port()
    config = f"""model_list:
  - model_name: primary
    litellm_params:
      model: openai/primary
      api_key: os.environ/SABIROUTE_PHASE05_STUB_KEY
      api_base: {stub_url}/v1
  - model_name: secondary
    litellm_params:
      model: openai/secondary
      api_key: os.environ/SABIROUTE_PHASE05_STUB_KEY
      api_base: {stub_url}/v1
general_settings:
  master_key: {PROXY_MASTER_KEY}
"""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".yaml", prefix="phase05-proxy-", delete=False
    )
    handle.write(config)
    handle.close()

    executable = Path(sys.executable).parent / "litellm"
    process = subprocess.Popen(  # noqa: S603 - fixed executable, generated config
        [str(executable), "--config", handle.name, "--host", "127.0.0.1",
         "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"

    import httpx

    deadline = time.time() + readiness_timeout
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("LiteLLM Proxy exited before becoming ready")
        try:
            probe = httpx.get(f"{url}/health/readiness", timeout=2.0)
            if probe.status_code == 200:
                return process, url
        except httpx.HTTPError:
            pass
        time.sleep(1.0)
    process.terminate()
    raise RuntimeError("LiteLLM Proxy did not become ready in time")


def main() -> int:
    argv = sys.argv[1:]
    via_proxy = "--via-proxy" in argv
    only: str | None = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1]
    stub = StubProvider()
    stub.start()
    proxy_process: Any = None
    results: list[dict[str, Any]] = []
    try:
        scenarios = SCENARIOS
        if via_proxy:
            # Cooldown and recovery probe gateway-side health directly and do not
            # depend on the transport, so they are excluded to keep this bounded.
            scenarios = [
                s for s in SCENARIOS if s.name[0] in {"A", "B", "C", "D", "E", "F", "G"}
            ]
        if only is not None:
            scenarios = [s for s in scenarios if s.name.startswith(only)]

        for scenario in scenarios:
            proxy_process = None
            upstream_url = stub.url
            upstream_key: str | None = None
            if via_proxy:
                # A fresh proxy per scenario. A shared proxy carries its own
                # deployment-failure state between scenarios and changes which
                # alias answers a request, which contaminates the matrix.
                proxy_process, upstream_url = start_proxy(stub.url)
                # The proxy enforces its configured master key, so SabiRoute must
                # present it; without it every call is refused before the stub is
                # reached.
                upstream_key = PROXY_MASTER_KEY
            try:
                results.append(
                    run_scenario(
                        stub,
                        ["primary", "secondary"],
                        scenario,
                        base_url=upstream_url,
                        api_key=upstream_key,
                    )
                )
            finally:
                if proxy_process is not None:
                    proxy_process.terminate()
                    try:
                        proxy_process.wait(timeout=10)
                    except Exception:  # noqa: BLE001 - teardown must not mask results
                        proxy_process.kill()

        if not via_proxy:
            results.append(run_cooldown(stub))
            results.append(run_recovery(stub))
    finally:
        stub.stop()

    print(json.dumps(results, indent=2, default=str))
    failed = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} scenarios matched expectation")
    for r in failed:
        print(
            f"MISMATCH {r['name']}: status {r['status']} "
            f"(expected {r['expected_status']}), calls {r.get('calls')} "
            f"(expected {r.get('expected_calls')})"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
