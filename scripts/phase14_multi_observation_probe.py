#!/usr/bin/env python3
"""Phase 14 multi-observation probe: several real completions per working alias.

The single-observation probe (``scripts/probe_provider_aliases.py``) makes one
call per configured alias. That is enough to prove an alias answers, but it
cannot produce a latency or reliability *distribution*: one sample per alias
makes every percentile a constant. This probe exists to collect a small, real
sample set per alias so ``scripts/benchmark.py --measured`` can rank on genuine
observations instead of a single replicated value.

Scope is deliberately narrow and budgeted:

* only the aliases already known to answer (the six the 2026-11-23 probe
  reached); the eight account-blocked aliases are not touched, because calling
  them spends budget and returns the same 401/402/429/503;
* ``--samples`` real completions per alias (default 5), so the default run is
  ``6 x 5 = 30`` provider calls and nothing more;
* **no retries** and **no budget escalation** -- one call is one observation,
  whatever its outcome. A failure is recorded as a failure, never backfilled;
* calls are paced (``--delay``) so a free tier's per-minute limit is not
  mistaken for provider unreliability;
* credentials are read from the environment and never printed -- only the
  variable *name* appears in the output.

Output is written as clean JSON to ``--output`` (default
``/tmp/phase14_multi_observation.json``) with an atomic replace, because LiteLLM
writes coloured log noise to stdout. The file is the authoritative record; the
stdout summary is for humans. The JSON is shaped for ``benchmark.py
--measured``: an object with an ``observations`` list of records carrying
``alias``, ``outcome`` and ``latency_ms``.

Usage:
    SABIROUTE_ENV_FILE=/path/to/.env \\
    PYTHONPATH=src python scripts/phase14_multi_observation_probe.py \\
        [--samples 5] [--output /tmp/phase14_multi_observation.json] [--dry-run]

Exit codes: 0 every call answered, 1 some call did not, 3 environment problem.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# The six aliases the 2026-11-23 single-observation probe reached with a real
# completion. The other eight returned account-state failures (401/402/429/503)
# and are intentionally excluded: calling them again spends budget and yields
# no new routing evidence.
KNOWN_WORKING_ALIASES: tuple[str, ...] = (
    "sabiroute-groq",
    "sabiroute-cloudflare",
    "sabiroute-openrouter",
    "sabiroute-nvidia",
    "sabiroute-cohere",
    "sabiroute-pollinations",
)

DEFAULT_SAMPLES = 5
DEFAULT_MAX_TOKENS = 64
DEFAULT_TIMEOUT = 30
DEFAULT_DELAY_SECONDS = 1.0
DEFAULT_OUTPUT = Path("/tmp/phase14_multi_observation.json")

# A per-call nonce keeps a provider's prompt cache from making later samples
# artificially fast; the instruction itself is unchanged.
PROMPT_TEMPLATE = "Reply with the single word OK. (sample {index})"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--aliases",
        nargs="+",
        default=list(KNOWN_WORKING_ALIASES),
        help="aliases to probe (default: the six known-working aliases)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=DEFAULT_SAMPLES,
        help=f"real completions per alias (default: {DEFAULT_SAMPLES})",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"max_tokens per call (default: {DEFAULT_MAX_TOKENS})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"per-call timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=(
            "seconds to wait between calls, to avoid tripping a free tier's "
            f"per-minute limit (default: {DEFAULT_DELAY_SECONDS})"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"clean JSON output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the call plan and exit without contacting any provider",
    )
    args = parser.parse_args(argv)
    if args.samples < 1:
        parser.error("--samples must be at least 1")
    if args.max_tokens < 1:
        parser.error("--max-tokens must be at least 1")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.delay < 0:
        parser.error("--delay cannot be negative")
    return args


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dotenv is a runtime dependency
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


def _deployments() -> dict[str, dict[str, Any]]:
    import yaml

    config = yaml.safe_load((REPO_ROOT / "config" / "config.yaml").read_text())
    out: dict[str, dict[str, Any]] = {}
    for entry in config.get("model_list") or []:
        params = entry.get("litellm_params") or {}
        alias = entry.get("model_name")
        if not isinstance(alias, str):
            continue
        out[alias] = {
            "alias": alias,
            "model": params.get("model"),
            "api_key_ref": params.get("api_key"),
            "api_base": params.get("api_base") or params.get("api_base_url"),
            "credential_vars": _credential_vars(params.get("api_key")),
        }
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


def _one_call(dep: dict[str, Any], index: int, args: argparse.Namespace) -> dict[str, Any]:
    """Make exactly one completion. No retry, no escalation."""
    import litellm

    base: dict[str, Any] = {
        "alias": dep["alias"],
        "model": dep["model"],
        "sample_index": index,
        "credential_vars": dep["credential_vars"],
    }
    missing = [name for name in dep["credential_vars"] if not os.environ.get(name)]
    if missing:
        return {**base, "outcome": "NO_CREDENTIAL", "missing_vars": missing}

    kwargs: dict[str, Any] = {
        "model": dep["model"],
        "messages": [
            {"role": "user", "content": PROMPT_TEMPLATE.format(index=index)}
        ],
        "max_tokens": args.max_tokens,
        "timeout": args.timeout,
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
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        return {
            **base,
            "outcome": "OK" if content.strip() else "EMPTY_CONTENT",
            "latency_ms": elapsed,
            "content_preview": content.strip()[:80],
            "finish_reason": finish,
        }
    except Exception as exc:  # noqa: BLE001 - classified and reported, never retried
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


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _load_env()
    deployments = _deployments()
    if not deployments:
        print(json.dumps({"verdict": "ENVIRONMENT", "reason": "no model_list"}))
        return 3

    unknown = [alias for alias in args.aliases if alias not in deployments]
    if unknown:
        print(
            json.dumps(
                {
                    "verdict": "ENVIRONMENT",
                    "reason": "aliases not present in config/config.yaml",
                    "unknown_aliases": unknown,
                }
            )
        )
        return 3

    plan = [(alias, index) for alias in args.aliases for index in range(args.samples)]
    if args.dry_run:
        print(
            json.dumps(
                {
                    "verdict": "DRY_RUN",
                    "aliases": args.aliases,
                    "samples_per_alias": args.samples,
                    "total_calls": len(plan),
                    "max_tokens": args.max_tokens,
                    "timeout_seconds": args.timeout,
                    "delay_seconds": args.delay,
                    "retries": 0,
                    "output": str(args.output),
                },
                indent=2,
            )
        )
        return 0

    started_at = datetime.now(UTC).isoformat()
    observations: list[dict[str, Any]] = []
    for position, (alias, index) in enumerate(plan):
        if position > 0 and args.delay:
            time.sleep(args.delay)
        record = _one_call(deployments[alias], index, args)
        observations.append(record)
        status = record.get("status_code")
        detail = f" status={status}" if status is not None else ""
        print(
            f"[{position + 1:02d}/{len(plan)}] {alias} sample={index} "
            f"{record['outcome']} {record.get('latency_ms', 'n/a')}ms{detail}",
            flush=True,
        )

    finished_at = datetime.now(UTC).isoformat()
    working = [r for r in observations if r["outcome"] == "OK"]
    payload: dict[str, Any] = {
        "verdict": "PROBED",
        "probe": "scripts/phase14_multi_observation_probe.py",
        "started_at": started_at,
        "finished_at": finished_at,
        "aliases": args.aliases,
        "samples_per_alias": args.samples,
        "total_calls": len(observations),
        "working_calls": len(working),
        "max_tokens": args.max_tokens,
        "timeout_seconds": args.timeout,
        "delay_seconds": args.delay,
        "retries": 0,
        "prompt_template": PROMPT_TEMPLATE,
        "observations": observations,
    }
    _write_atomic(args.output, payload)

    per_alias: dict[str, dict[str, int]] = {}
    for record in observations:
        bucket = per_alias.setdefault(record["alias"], {"ok": 0, "total": 0})
        bucket["total"] += 1
        if record["outcome"] == "OK":
            bucket["ok"] += 1
    print(
        json.dumps(
            {
                "verdict": "PROBED",
                "total_calls": len(observations),
                "working_calls": len(working),
                "per_alias": per_alias,
                "output": str(args.output),
            },
            indent=2,
        )
    )
    return 0 if len(working) == len(observations) else 1


if __name__ == "__main__":
    raise SystemExit(main())
