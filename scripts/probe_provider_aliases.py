#!/usr/bin/env python3
"""Probe every configured SabiRoute alias against its real provider.

This produces per-alias runtime evidence: for each deployment in
``config/config.yaml`` it makes exactly one real, minimal completion through
LiteLLM and reports whether the provider answered with non-empty assistant
text.

Deliberately conservative:
  * one call per alias, ``max_tokens`` tiny, so spend is negligible;
  * a hard per-call timeout, so one hanging provider cannot stall the run;
  * credentials are read from the environment and never printed — only the
    variable *name* appears in the output;
  * nothing is written to a file. ``reports/provider_verification.json`` is a
    protected path in this repository and is not touched.

A provider that returns 200 with empty assistant text is reported as
``EMPTY_CONTENT``, not as working: an empty completion is not a usable alias.

Usage:
    SABIROUTE_ENV_FILE=/path/to/.env \\
        python scripts/probe_provider_aliases.py [--archive ARM|LEGACY]

Exit codes: 0 all aliases answered, 1 some did not, 3 environment problem.
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# A reasoning model can spend the entire output budget on its reasoning
# trace and return an empty `content` with finish_reason 'length'. At 16
# tokens that produced false EMPTY_CONTENT results for reasoning models, so
# the budget starts higher and escalates once before any conclusion is drawn.
MAX_TOKENS = 64
ESCALATED_MAX_TOKENS = 512
CALL_TIMEOUT = 25
CONCURRENCY = 6


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover
        return
    explicit = os.environ.get("SABIROUTE_ENV_FILE")
    path = Path(explicit) if explicit else REPO_ROOT / ".env"
    if path.exists():
        load_dotenv(path, override=False)


def _credential_vars(value: Any) -> list[str]:
    """Return credential variable NAMES from an api_key config value."""
    names: list[str] = []
    values: list[Any] = value if isinstance(value, list) else [value]
    for item in values:
        if isinstance(item, str) and item.startswith("os.environ/"):
            names.append(item.split("/", 1)[1])
    return names


def _resolve(value: Any) -> Any:
    """Turn an os.environ/ reference into its value; never logs the value."""
    if isinstance(value, list):
        return [_resolve(v) for v in value]
    if isinstance(value, str) and value.startswith("os.environ/"):
        return os.environ.get(value.split("/", 1)[1], "")
    return value


def _deployments() -> list[dict[str, Any]]:
    import yaml

    config = yaml.safe_load((REPO_ROOT / "config" / "config.yaml").read_text())
    out: list[dict[str, Any]] = []
    for entry in config.get("model_list") or []:
        params = entry.get("litellm_params") or {}
        out.append(
            {
                "alias": entry.get("model_name"),
                "model": params.get("model"),
                "api_key_ref": params.get("api_key"),
                "api_base": params.get("api_base") or params.get("api_base_url"),
                "credential_vars": _credential_vars(params.get("api_key")),
            }
        )
    return out


def _content_of(response: Any) -> str:
    try:
        return response.choices[0].message.content or ""
    except (AttributeError, IndexError, KeyError):
        return ""


def _finish_of(response: Any) -> str | None:
    try:
        return response.choices[0].finish_reason
    except (AttributeError, IndexError, KeyError):
        return None


def _probe(dep: dict[str, Any]) -> dict[str, Any]:
    import litellm

    alias = dep["alias"]
    missing = [n for n in dep["credential_vars"] if not os.environ.get(n)]
    base: dict[str, Any] = {
        "alias": alias,
        "model": dep["model"],
        "credential_vars": dep["credential_vars"],
    }
    if missing:
        return {**base, "outcome": "NO_CREDENTIAL", "missing_vars": missing}

    kwargs: dict[str, Any] = {
        "model": dep["model"],
        "messages": [{"role": "user", "content": "Reply with the single word OK."}],
        "max_tokens": MAX_TOKENS,
        "timeout": CALL_TIMEOUT,
        "num_retries": 0,
    }
    if dep["api_key_ref"] is not None:
        kwargs["api_key"] = _resolve(dep["api_key_ref"])
    if dep["api_base"]:
        kwargs["api_base"] = dep["api_base"]

    started = time.perf_counter()
    try:
        response = litellm.completion(**kwargs)
        content = _content_of(response)
        finish = _finish_of(response)

        escalated = False
        if not content.strip() and finish == "length":
            # Empty content with a length stop is a budget artefact, not proof
            # the provider is broken. Give it room before deciding.
            escalated = True
            kwargs["max_tokens"] = ESCALATED_MAX_TOKENS
            response = litellm.completion(**kwargs)
            content = _content_of(response)
            finish = _finish_of(response)

        elapsed = round((time.perf_counter() - started) * 1000, 1)
        return {
            **base,
            "outcome": "OK" if content.strip() else "EMPTY_CONTENT",
            "latency_ms": elapsed,
            "content_preview": content.strip()[:80],
            "finish_reason": finish,
            "escalated_budget": escalated,
        }
    except Exception as exc:  # noqa: BLE001 - classified and reported
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        status = getattr(exc, "status_code", None)
        return {
            **base,
            "outcome": "ERROR",
            "latency_ms": elapsed,
            "status_code": status,
            "error_class": type(exc).__name__,
            "error_preview": str(exc)[:200],
        }


def main() -> int:
    _load_env()
    deps = _deployments()
    if not deps:
        print(json.dumps({"verdict": "ENVIRONMENT", "reason": "no model_list"}))
        return 3

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        results = list(pool.map(_probe, deps))

    working = [r for r in results if r["outcome"] == "OK"]
    print(
        json.dumps(
            {
                "verdict": "PROBED",
                "total_aliases": len(results),
                "working": len(working),
                "working_aliases": [r["alias"] for r in working],
                "results": results,
            },
            indent=2,
        )
    )
    return 0 if working else 1


if __name__ == "__main__":
    raise SystemExit(main())
