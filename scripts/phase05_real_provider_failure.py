#!/usr/bin/env python3
"""Phase 05 — prove fallback is driven by a REAL provider failure.

``scripts/phase05_fallback_injection.py`` proves the fallback *state machine* by
driving a controllable stub that can be told to fail on demand. That is strong
evidence that the code branches correctly, and it is deliberately free of
provider credentials and egress.

It is not evidence that a real provider's real failure produces a real
fallback. This harness closes that gap, with no stub anywhere in the path:

    SabiRoute -> LiteLLM Proxy -> primary   = openai/gpt-6-luna
                                -> secondary = nvidia_nim/nvidia/nemotron-3.5-bolt-e4b

Both legs are real HTTPS calls to real providers carrying real credentials.

The premise is load-bearing
---------------------------
A "fallback worked" claim is worthless if nothing failed. This harness therefore
distinguishes three outcomes and refuses to conflate them:

    PREMISE_NOT_MET     the primary provider answered, so no failure occurred and
                        no fallback claim can be made. Exit 2. This is not a pass.
    PREMISE_UNREACHABLE the primary provider's failure was not observable, e.g.
                        the proxy never started. Exit 3.
    PASS                primary failed, SabiRoute failed over, secondary answered.

Exit codes: 0 pass, 1 assertion failure, 2 premise not met, 3 environment.
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

# These must equal the SabiRoute deployment names below: SabiRoute asks the
# proxy for a deployment by that name, so the two sides share one namespace.
PROXY_PRIMARY = "primary"
PROXY_SECONDARY = "secondary"

# Neither of these is a credential. The primary carries the repository's real
# Gemini credential; the proxy master key is generated per run and lives only in
# this process's environment, so it is never written to a file or a log.
PROXY_KEY_ENV = "PHASE05_PROXY_KEY"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _load_env() -> None:
    """Load .env exactly as the application does. Values are never printed.

    ``.env`` is gitignored, so a git worktree of this repository does not have
    one — only the primary checkout does. ``SABIROUTE_ENV_FILE`` names an
    explicit file for that case instead of the harness hardcoding a path.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dotenv is a declared dependency
        return
    explicit = os.environ.get("SABIROUTE_ENV_FILE")
    path = Path(explicit) if explicit else REPO_ROOT / ".env"
    if path.exists():
        load_dotenv(path, override=False)


def _write_proxy_config(port: int) -> Path:
    config = f"""model_list:
  - model_name: {PROXY_PRIMARY}
    litellm_params:
      model: openai/gpt-6-luna
      api_key: os.environ/OPENAI_API_KEY
      num_retries: 0
  - model_name: {PROXY_SECONDARY}
    litellm_params:
      model: nvidia_nim/nvidia/nemotron-3.5-bolt-e4b
      api_key: os.environ/NVIDIA_NIM_API_KEY
      num_retries: 0
litellm_settings:
  drop_params: true
  request_timeout: 60
  num_retries: 0
  set_verbose: false
general_settings:
  master_key: os.environ/{PROXY_KEY_ENV}
"""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".yaml", prefix="phase05-real-proxy-", delete=False
    )
    handle.write(config)
    handle.close()
    return Path(handle.name)


def _start_proxy(config_path: Path, port: int, readiness_timeout: float = 180.0) -> Any:
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


def build_gateway(proxy_url: str, proxy_key: str):
    from conftest import InMemoryApiKeyStore, provision_test_key
    from fastapi.testclient import TestClient

    from sabiroute.config.loader import validate_config
    from sabiroute.config.models import SabiRouteConfig
    from sabiroute.gateway import build_gateway_state
    from sabiroute.main import create_app
    from sabiroute.providers.litellm_client import LiteLLMClient

    config = validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": name,
                        "capabilities": {"chat": True, "streaming": True},
                        "litellm_params": {
                            "model": f"openai/{upstream}",
                            "api_key": f"os.environ/{PROXY_KEY_ENV}",
                        },
                    }
                    for name, upstream in (
                        ("primary", PROXY_PRIMARY),
                        ("secondary", PROXY_SECONDARY),
                    )
                ]
            }
        )
    )
    state = build_gateway_state(
        config=config,
        client=LiteLLMClient(
            base_url=proxy_url, api_key=proxy_key, timeout_seconds=300.0
        ),
        key_store=InMemoryApiKeyStore(),
    )
    key = provision_test_key(state)
    client = TestClient(
        create_app(state=state), headers={"Authorization": f"Bearer {key}"}
    )
    return client, state


def main() -> int:
    _load_env()

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

    proxy_key = f"sk-phase05-{secrets.token_hex(12)}"
    os.environ[PROXY_KEY_ENV] = proxy_key
    port = _free_port()
    config_path = _write_proxy_config(port)

    process = None
    try:
        process, proxy_url = _start_proxy(config_path, port)
        client, state = build_gateway(proxy_url, proxy_key)

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

        health = state.health.snapshot()
        primary = health.get("primary", {})
        secondary = health.get("secondary", {})

        primary_failures = int(primary.get("total_failures") or 0)
        primary_successes = int(primary.get("total_successes") or 0)
        secondary_successes = int(secondary.get("total_successes") or 0)

        content = ""
        if isinstance(body, dict):
            choices = body.get("choices") or []
            if choices:
                content = (choices[0].get("message") or {}).get("content") or ""

        # The premise, checked before the claim it licenses.
        if primary_failures == 0:
            verdict = (
                "PREMISE_NOT_MET" if primary_successes > 0 else "PREMISE_UNREACHABLE"
            )
            print(
                json.dumps(
                    {
                        "verdict": verdict,
                        "reason": (
                            "the primary provider answered, so no failure occurred "
                            "and no fallback claim is warranted"
                            if primary_successes > 0
                            else "no failure and no success was recorded against primary"
                        ),
                        "status": response.status_code,
                        "elapsed_ms": elapsed_ms,
                        "health": health,
                        "body": body,
                    },
                    indent=2,
                    default=str,
                )
            )
            return 2 if primary_successes > 0 else 3

        checks = {
            "status_200": response.status_code == 200,
            "non_empty_text": bool(content.strip()),
            "primary_recorded_failure": primary_failures >= 1,
            "secondary_recorded_success": secondary_successes >= 1,
            "primary_never_succeeded": primary_successes == 0,
        }
        passed = all(checks.values())

        print(
            json.dumps(
                {
                    "verdict": "PASS" if passed else "ASSERTION_FAILED",
                    "claim": (
                        "a real provider failure on the primary deployment caused "
                        "SabiRoute to fail over to a real secondary provider, which "
                        "answered with real content"
                    ),
                    "status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "content_preview": content.strip()[:120],
                    "checks": checks,
                    "health": health,
                    "body": body,
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
            except subprocess.TimeoutExpired:  # pragma: no cover
                process.kill()
        config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
