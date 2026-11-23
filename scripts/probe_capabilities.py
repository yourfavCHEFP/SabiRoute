#!/usr/bin/env python3
"""Probe three capabilities for the six runtime-verified SabiRoute aliases.

Phase 11's stated gap is "capability evidence missing for most deployments".
``sabiroute-groq``, ``sabiroute-cloudflare``, ``sabiroute-openrouter``,
``sabiroute-nvidia``, ``sabiroute-cohere`` and ``sabiroute-pollinations`` are
runtime-verified to answer a plain chat completion. Nothing else about them has
been measured. This script measures exactly three more capabilities:

``streaming``
    A ``stream=True`` completion that yields at least one non-empty content
    delta.
``json`` + ``structured_output``
    A completion sent with ``response_format={"type": "json_object"}`` whose
    assistant content parses as JSON. One probe substantiates both capability
    flags, because the routing classifier requires both for ``json_object``.
``tool_use``
    A completion offered one function tool with ``tool_choice="auto"`` that
    either emits a ``tool_calls`` entry or does not.

One logical request per capability per alias: six aliases x three capabilities
= 18 probes. The inherited 64 -> 512 token escalation may add a second HTTP
call *inside* a cell, but only when an empty ``content`` arrived alongside
``finish_reason == "length"`` -- the reasoning-model artefact documented in
``scripts/probe_provider_aliases.py``. Nothing else is retried, and no call is
repeated for a provider error.

A provider that rejects a parameter is a finding, not a failure: the cell is
recorded as ``ERROR_<status>`` with the first 120 characters of the provider's
error. An error is never collapsed into ``UNSUPPORTED``.

OUTCOMES (per cell, deterministic):
    SUPPORTED        provider answered and satisfied the capability's test
    UNSUPPORTED      provider answered, capability test not satisfied
    ERROR_<status>   HTTP/provider error carrying a status code
    ERROR_TIMEOUT    no complete answer inside the wall-clock cap
    ERROR_NO_STATUS  provider/transport error without a status code
    NO_CREDENTIAL    a referenced credential variable is unset

Standards: JSON goes to stdout and nothing else does; the human-readable
summary matrix goes to stderr. Credential *variable names* are printed, never
values. No file is written; ``reports/provider_verification.json`` is a
protected path and is not touched.

Usage:
    SABIROUTE_ENV_FILE=/path/to/.env \\
    PYTHONPATH=<repo>/src \\
    python scripts/probe_capabilities.py

Exit codes: 0 measurement completed, 3 environment problem (no config or no
target deployments). Provider errors do not change the exit code; the run
still completed.
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# The aliases with 2026-11-23 ``chat`` runtime evidence. Order is fixed so the
# matrix is byte-stable across runs.
TARGET_ALIASES = (
    "sabiroute-groq",
    "sabiroute-cloudflare",
    "sabiroute-openrouter",
    "sabiroute-nvidia",
    "sabiroute-cohere",
    "sabiroute-pollinations",
)
CAPABILITIES = ("streaming", "json", "tool_use")

# A reasoning model can spend the entire output budget on its reasoning trace
# and return empty ``content`` with ``finish_reason == "length"``. Start with
# room, and escalate once before concluding anything. See
# ``scripts/probe_provider_aliases.py`` for the original artefact.
MAX_TOKENS = 64
ESCALATED_MAX_TOKENS = 512
CALL_TIMEOUT = 25
CONCURRENCY = 6
ERROR_PREVIEW_CHARS = 120

CHAT_PROMPT = "Reply with the single word OK."
JSON_PROMPT = 'Reply with only this JSON object: {"status": "ok", "count": 3}'
TOOL_PROMPT = "What is the weather in Lagos right now? Use the get_weather tool."

TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. Lagos"},
            },
            "required": ["city"],
        },
    },
}


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover
        return
    explicit = os.environ.get("SABIROUTE_ENV_FILE")
    path = Path(explicit) if explicit else REPO_ROOT / ".env"
    if path.exists():
        load_dotenv(path, override=False)


def _credential_vars(params: dict[str, Any]) -> list[str]:
    """Return every credential variable NAME referenced by litellm_params."""
    names: list[str] = []
    for value in params.values():
        values: list[Any] = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, str) and item.startswith("os.environ/"):
                name = item.split("/", 1)[1]
                if name not in names:
                    names.append(name)
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
    by_alias: dict[str, dict[str, Any]] = {}
    for entry in config.get("model_list") or []:
        alias = entry.get("model_name")
        if alias not in TARGET_ALIASES:
            continue
        params = entry.get("litellm_params") or {}
        by_alias[alias] = {
            "alias": alias,
            "model": params.get("model"),
            "api_key_ref": params.get("api_key"),
            "api_base": params.get("api_base") or params.get("api_base_url"),
            "credential_vars": _credential_vars(params),
        }
    return [by_alias[alias] for alias in TARGET_ALIASES if alias in by_alias]


def _base_kwargs(dep: dict[str, Any]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": dep["model"],
        "timeout": CALL_TIMEOUT,
        "num_retries": 0,
    }
    if dep["api_key_ref"] is not None:
        kwargs["api_key"] = _resolve(dep["api_key_ref"])
    if dep["api_base"]:
        kwargs["api_base"] = dep["api_base"]
    return kwargs


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


def _message_of(response: Any) -> Any:
    try:
        return response.choices[0].message
    except (AttributeError, IndexError, KeyError):
        return None


def _tool_calls_of(message: Any) -> list[Any]:
    calls = getattr(message, "tool_calls", None)
    return list(calls) if isinstance(calls, (list, tuple)) else []


def _tool_name(call: Any) -> str | None:
    function = getattr(call, "function", None)
    name = getattr(function, "name", None)
    return name if isinstance(name, str) else None


def _delta_text(delta: Any) -> str:
    """Extract assistant text from one streamed delta, tolerating block lists."""
    content = getattr(delta, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text")
            else:
                text = getattr(part, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return ""


def _consume_stream(stream: Any, started: float) -> tuple[str, str | None, int, bool]:
    """Drain a stream with a wall-clock deadline; return (text, finish, chunks, timeout)."""
    parts: list[str] = []
    finish: str | None = None
    chunks = 0
    timed_out = False
    for chunk in stream:
        if time.perf_counter() - started > CALL_TIMEOUT:
            timed_out = True
            break
        chunks += 1
        try:
            choice = chunk.choices[0]
        except (AttributeError, IndexError, KeyError):
            continue
        delta = getattr(choice, "delta", None)
        if delta is not None:
            parts.append(_delta_text(delta))
        reason = getattr(choice, "finish_reason", None)
        if reason:
            finish = reason
    return "".join(parts), finish, chunks, timed_out


def _parse_json(text: str) -> tuple[bool, str]:
    """Return (ok, mode) where mode is strict, fenced, not_json, or empty.

    Only strict JSON counts as support: a caller sending
    ``response_format={"type": "json_object"}`` expects ``json.loads`` to work
    on the content as returned. A fenced reply is recorded as ``fenced`` so the
    distinction is visible, never silently upgraded.
    """
    stripped = text.strip()
    if not stripped:
        return False, "empty"
    try:
        json.loads(stripped)
    except json.JSONDecodeError:
        pass
    else:
        return True, "strict"
    fence = "```"
    if stripped.startswith(fence) and stripped.endswith(fence):
        inner = stripped[len(fence) : -len(fence)].strip()
        if inner.lower().startswith("json"):
            inner = inner[4:].strip()
        try:
            json.loads(inner)
        except json.JSONDecodeError:
            return False, "not_json"
        return False, "fenced"
    return False, "not_json"


def _error_cell(exc: Exception, requests: int) -> dict[str, Any]:
    status = getattr(exc, "status_code", None)
    if status is not None:
        outcome = f"ERROR_{status}"
    elif isinstance(exc, TimeoutError) or "timeout" in type(exc).__name__.lower():
        outcome = "ERROR_TIMEOUT"
    else:
        outcome = "ERROR_NO_STATUS"
    return {
        "outcome": outcome,
        "requests": requests,
        "status_code": status,
        "error_class": type(exc).__name__,
        "error_preview": str(exc)[:ERROR_PREVIEW_CHARS],
    }


def _probe_streaming(dep: dict[str, Any]) -> dict[str, Any]:
    import litellm

    kwargs = _base_kwargs(dep)
    kwargs.update(
        messages=[{"role": "user", "content": CHAT_PROMPT}],
        max_tokens=MAX_TOKENS,
        stream=True,
    )
    begin = time.perf_counter()
    started = begin
    requests = 0
    try:
        requests += 1
        stream = litellm.completion(**kwargs)
        content, finish, chunks, timed_out = _consume_stream(stream, started)
        escalated = False
        if not content.strip() and finish == "length" and not timed_out:
            escalated = True
            requests += 1
            kwargs["max_tokens"] = ESCALATED_MAX_TOKENS
            started = time.perf_counter()
            stream = litellm.completion(**kwargs)
            content, finish, chunks, timed_out = _consume_stream(stream, started)
        elapsed = round((time.perf_counter() - begin) * 1000, 1)
        if timed_out:
            return {
                "outcome": "ERROR_TIMEOUT",
                "requests": requests,
                "latency_ms": elapsed,
                "chunks": chunks,
                "detail": "stream did not complete inside the wall-clock cap",
            }
        return {
            "outcome": "SUPPORTED" if content.strip() else "UNSUPPORTED",
            "requests": requests,
            "latency_ms": elapsed,
            "chunks": chunks,
            "finish_reason": finish,
            "content_preview": content.strip()[:ERROR_PREVIEW_CHARS],
            "escalated_budget": escalated,
        }
    except Exception as exc:  # noqa: BLE001 - classified and reported
        return _error_cell(exc, max(requests, 1))


def _probe_json(dep: dict[str, Any]) -> dict[str, Any]:
    import litellm

    kwargs = _base_kwargs(dep)
    kwargs.update(
        messages=[
            {"role": "system", "content": "You reply with JSON only."},
            {"role": "user", "content": JSON_PROMPT},
        ],
        max_tokens=MAX_TOKENS,
        response_format={"type": "json_object"},
    )
    begin = time.perf_counter()
    requests = 0
    try:
        requests += 1
        response = litellm.completion(**kwargs)
        content = _content_of(response)
        finish = _finish_of(response)
        escalated = False
        if not content.strip() and finish == "length":
            escalated = True
            requests += 1
            kwargs["max_tokens"] = ESCALATED_MAX_TOKENS
            response = litellm.completion(**kwargs)
            content = _content_of(response)
            finish = _finish_of(response)
        elapsed = round((time.perf_counter() - begin) * 1000, 1)
        ok, mode = _parse_json(content)
        return {
            "outcome": "SUPPORTED" if ok else "UNSUPPORTED",
            "requests": requests,
            "latency_ms": elapsed,
            "json_parse": mode,
            "finish_reason": finish,
            "content_preview": content.strip()[:ERROR_PREVIEW_CHARS],
            "escalated_budget": escalated,
        }
    except Exception as exc:  # noqa: BLE001 - classified and reported
        return _error_cell(exc, max(requests, 1))


def _probe_tool_use(dep: dict[str, Any]) -> dict[str, Any]:
    import litellm

    kwargs = _base_kwargs(dep)
    kwargs.update(
        messages=[{"role": "user", "content": TOOL_PROMPT}],
        max_tokens=MAX_TOKENS,
        tools=[TOOL_SCHEMA],
        tool_choice="auto",
    )
    begin = time.perf_counter()
    requests = 0
    try:
        requests += 1
        response = litellm.completion(**kwargs)
        message = _message_of(response)
        calls = _tool_calls_of(message)
        content = _content_of(response)
        finish = _finish_of(response)
        escalated = False
        if not calls and not content.strip() and finish == "length":
            escalated = True
            requests += 1
            kwargs["max_tokens"] = ESCALATED_MAX_TOKENS
            response = litellm.completion(**kwargs)
            message = _message_of(response)
            calls = _tool_calls_of(message)
            content = _content_of(response)
            finish = _finish_of(response)
        elapsed = round((time.perf_counter() - begin) * 1000, 1)
        return {
            "outcome": "SUPPORTED" if calls else "UNSUPPORTED",
            "requests": requests,
            "latency_ms": elapsed,
            "tool_calls": len(calls),
            "tool_names": [name for name in map(_tool_name, calls) if name],
            "finish_reason": finish,
            "content_preview": content.strip()[:ERROR_PREVIEW_CHARS],
            "escalated_budget": escalated,
        }
    except Exception as exc:  # noqa: BLE001 - classified and reported
        return _error_cell(exc, max(requests, 1))


def _probe_alias(dep: dict[str, Any]) -> dict[str, Any]:
    base = {
        "alias": dep["alias"],
        "model": dep["model"],
        "credential_vars": dep["credential_vars"],
    }
    missing = [name for name in dep["credential_vars"] if not os.environ.get(name)]
    if missing:
        cell = {"outcome": "NO_CREDENTIAL", "requests": 0, "missing_vars": missing}
        return {**base, "capabilities": {cap: dict(cell) for cap in CAPABILITIES}}
    return {
        **base,
        "capabilities": {
            "streaming": _probe_streaming(dep),
            "json": _probe_json(dep),
            "tool_use": _probe_tool_use(dep),
        },
    }


def _print_matrix(results: list[dict[str, Any]]) -> None:
    headers = ("alias", "streaming", "json+structured_output", "tool_use")
    rows = [
        (
            result["alias"],
            result["capabilities"]["streaming"]["outcome"],
            result["capabilities"]["json"]["outcome"],
            result["capabilities"]["tool_use"]["outcome"],
        )
        for result in results
    ]
    table = [headers, *rows]
    widths = [max(len(row[index]) for row in table) for index in range(len(headers))]

    def render(row: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)).rstrip()

    print(render(headers), file=sys.stderr)
    print(render(tuple("-" * width for width in widths)), file=sys.stderr)
    for row in rows:
        print(render(row), file=sys.stderr)


def main() -> int:
    _load_env()
    deps = _deployments()
    if not deps:
        print(
            json.dumps(
                {
                    "verdict": "ENVIRONMENT",
                    "reason": "no target deployments found in config/config.yaml",
                }
            )
        )
        return 3

    import litellm

    litellm.suppress_debug_info = True

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        results = list(pool.map(_probe_alias, deps))

    matrix = {
        result["alias"]: {
            cap: result["capabilities"][cap]["outcome"] for cap in CAPABILITIES
        }
        for result in results
    }
    requests_made = sum(
        cell["requests"] for result in results for cell in result["capabilities"].values()
    )
    escalations = sum(
        1
        for result in results
        for cell in result["capabilities"].values()
        if cell.get("escalated_budget")
    )

    _print_matrix(results)
    print(
        json.dumps(
            {
                "verdict": "PROBED",
                "probe": "capabilities",
                "date": "2026-11-23",
                "aliases": [result["alias"] for result in results],
                "capabilities": list(CAPABILITIES),
                "cells": [
                    f"{result['alias']} x {cap}"
                    for result in results
                    for cap in CAPABILITIES
                ],
                "requests_made": requests_made,
                "escalations": escalations,
                "matrix": matrix,
                "results": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
