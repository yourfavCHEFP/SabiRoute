#!/usr/bin/env python3
"""Reproducible SabiRoute routing benchmark (Phase 14).

Compares the unchanged deterministic-v1 routing baseline against itself under
two routing strategies -- ``priority`` (configured order) and ``measured``
(deterministic-v1 scoring) -- on an identical, reproducible workload.

Two workload sources, never conflated:

* **synthetic** (default) -- seeded fixtures derived from the seed and the
  deployment name. No provider is contacted and no credits are spent.
* **measured** (``--measured PATH``) -- replays real provider observations
  from a probe JSON file. This tool still makes no provider calls; it only
  reads observations that another tool produced.

Every report states which of the two it is. Synthetic output must never be
mistaken for measured provider performance.

Note the two different uses of the word "measured":

* ``--strategy measured`` selects the deterministic-v1 *routing policy*.
* ``--measured PATH`` selects the *data source* (real observations).

They are independent; ``--strategy priority --measured probe.json`` is valid.

Usage:
    PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py
    PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py --requests 500 --json
    PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py --measured probe.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import textwrap
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, quantiles
from typing import Any

import yaml

from sabiroute.config.loader import load_config
from sabiroute.monitoring.latency import LatencyTracker
from sabiroute.providers.registry import ProviderRegistry, registry_from_config
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.router import (
    NoHealthyDeploymentError,
    NoRemainingDeploymentError,
    Router,
)
from sabiroute.routing.scoring import ScoringSettings

# The Phase 12 baseline. Phase 14 compares against this unchanged; the tool
# refuses to run if config/config.yaml has drifted away from it, because a
# benchmark against a silently retuned baseline proves nothing.
BASELINE: dict[str, Any] = {
    "policy_version": "deterministic-v1",
    "reliability_weight": 0.7,
    "latency_weight": 0.3,
    "minimum_samples": 5,
}

# Synthetic fixture ranges. Deliberately wide and derived from a hash of the
# seed and the deployment name, so no deployment is favoured by construction
# and both strategies face exactly the same ground truth.
SYNTHETIC_SUCCESS_RANGE = (0.90, 0.995)
SYNTHETIC_LATENCY_RANGE_MS = (150.0, 1500.0)
SYNTHETIC_JITTER_RANGE_MS = (10.0, 250.0)

# Record keys that identify the deployment. Both the probe harness
# (``alias``) and the persisted verification report (``model_name``) are
# accepted; an unknown key is an error, never a guess.
MEASURED_NAME_KEYS = ("alias", "deployment", "model_name")

# Outcome vocabulary accepted from a measured probe file. ``OK`` and friends
# come from scripts/probe_provider_aliases.py; ``PASS``/``FAIL`` come from
# reports/provider_verification.json.
MEASURED_SUCCESS_OUTCOMES = frozenset({"OK", "SUCCESS", "SUCCEEDED", "PASS"})
MEASURED_FAILURE_OUTCOMES = frozenset(
    {"EMPTY_CONTENT", "ERROR", "FAILED", "FAILURE", "TIMEOUT", "FAIL"}
)
# No provider was contacted for these, so there is no observation to replay.
MEASURED_EXCLUDED_OUTCOMES = frozenset({"NO_CREDENTIAL", "SKIPPED"})
# The persisted report also carries a coarse ``status`` field.
MEASURED_STATUS_AS_OUTCOME = {"PASS": "PASS", "FAIL": "FAIL"}


class BenchmarkError(RuntimeError):
    """A benchmark input or baseline problem that must stop the run."""


@dataclass(frozen=True, slots=True)
class Observation:
    """One ground-truth outcome for one deployment on one request."""

    succeeded: bool
    latency_ms: float


@dataclass(frozen=True, slots=True)
class Workload:
    """A labelled, reproducible ground truth shared by every strategy."""

    provenance: dict[str, Any]
    candidates: tuple[str, ...]
    # Per deployment, one observation per (warm-up + measured) request index.
    observations: dict[str, tuple[Observation, ...]]
    profiles: dict[str, dict[str, float]] | None


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=200,
        help="logical requests per strategy (default: 200)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20261123,
        help="seed for the synthetic workload (default: 20261123)",
    )
    parser.add_argument(
        "--strategy",
        choices=("priority", "measured", "both"),
        default="both",
        help="routing strategy to benchmark (default: both)",
    )
    parser.add_argument(
        "--measured",
        metavar="PATH",
        default=None,
        help=(
            "replay real provider observations from a probe JSON file "
            "instead of synthetic fixtures"
        ),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=2,
        help="attempts per logical request (default: 2)",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help="config file (default: config/config.yaml)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON instead of a human-readable table",
    )
    args = parser.parse_args(argv)
    if args.requests < 1:
        parser.error("--requests must be at least 1")
    if args.max_attempts < 1:
        parser.error("--max-attempts must be at least 1")
    return args


def _settings_from_config(config: Any) -> ScoringSettings:
    scoring = config.routing_scoring
    return ScoringSettings(
        policy_version=scoring.policy_version,
        reliability_weight=scoring.reliability_weight,
        latency_weight=scoring.latency_weight,
        minimum_samples=scoring.minimum_samples,
        max_signal_age_seconds=scoring.max_signal_age_seconds,
    )


def _assert_baseline(settings: ScoringSettings) -> None:
    drift = {
        key: {"expected": expected, "actual": getattr(settings, key)}
        for key, expected in BASELINE.items()
        if getattr(settings, key) != expected
    }
    if drift:
        raise BenchmarkError(
            "routing baseline has drifted from the Phase 12 constants; "
            f"refusing to benchmark against a changed baseline: {drift}"
        )


def _synthetic_workload(
    candidates: tuple[str, ...],
    requests: int,
    warmup: int,
    seed: int,
) -> Workload:
    observations: dict[str, tuple[Observation, ...]] = {}
    profiles: dict[str, dict[str, float]] = {}
    for name in candidates:
        # random.Random(str) seeds from a SHA-512 of the string, so these
        # profiles are stable across runs, processes and platforms.
        profile_rng = random.Random(f"sabiroute-phase14-profile|{seed}|{name}")
        success_rate = round(profile_rng.uniform(*SYNTHETIC_SUCCESS_RANGE), 4)
        base_latency = round(profile_rng.uniform(*SYNTHETIC_LATENCY_RANGE_MS), 1)
        jitter = round(profile_rng.uniform(*SYNTHETIC_JITTER_RANGE_MS), 1)
        profiles[name] = {
            "success_rate": success_rate,
            "base_latency_ms": base_latency,
            "jitter_ms": jitter,
        }
        draw_rng = random.Random(f"sabiroute-phase14-draw|{seed}|{name}")
        draws: list[Observation] = []
        for _ in range(warmup + requests):
            succeeded = draw_rng.random() < success_rate
            latency = round(base_latency + draw_rng.uniform(0.0, jitter), 3)
            draws.append(Observation(succeeded=succeeded, latency_ms=latency))
        observations[name] = tuple(draws)

    provenance = {
        "source": "SYNTHETIC",
        "statement": (
            "No provider was contacted and no credits were spent. Outcome and "
            "latency values are seeded fixtures, not provider measurements. "
            "These numbers describe the deterministic-v1 routing POLICY on a "
            "fixed workload; they are not provider performance evidence."
        ),
        "spends_provider_credits": False,
        "seed": seed,
        "fixture_ranges": {
            "success_rate": list(SYNTHETIC_SUCCESS_RANGE),
            "base_latency_ms": list(SYNTHETIC_LATENCY_RANGE_MS),
            "jitter_ms": list(SYNTHETIC_JITTER_RANGE_MS),
        },
        "derivation": (
            "per-deployment profile and per-request draws are seeded from "
            "sha512(seed|deployment); both strategies consume the same matrix"
        ),
    }
    return Workload(
        provenance=provenance,
        candidates=candidates,
        observations=observations,
        profiles=profiles,
    )


def _measured_records(payload: Any, path: Path) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("results", "observations"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise BenchmarkError(
        f"{path}: expected a JSON list of observations, or an object with a "
        "'results' or 'observations' list"
    )


def _measured_outcome(record: dict[str, Any]) -> str | None:
    """Normalise the outcome token, or return None when only 'succeeded' is set."""
    outcome = record.get("outcome")
    if outcome is None:
        status = record.get("status")
        if isinstance(status, str):
            outcome = MEASURED_STATUS_AS_OUTCOME.get(status.strip().upper(), status)
    if isinstance(outcome, str):
        return outcome.strip().upper()
    return None


def _measured_success(
    record: dict[str, Any],
    index: int,
    path: Path,
    outcome: str | None,
) -> bool:
    if "succeeded" in record:
        value = record["succeeded"]
        if not isinstance(value, bool):
            raise BenchmarkError(
                f"{path}: record {index} has a non-boolean 'succeeded'"
            )
        return value
    if outcome is None:
        raise BenchmarkError(
            f"{path}: record {index} has none of 'succeeded', 'outcome' or "
            "'status'"
        )
    if outcome in MEASURED_SUCCESS_OUTCOMES:
        return True
    if outcome in MEASURED_FAILURE_OUTCOMES:
        return False
    raise BenchmarkError(
        f"{path}: record {index} has unrecognised outcome {outcome!r}"
    )


def _measured_workload(
    path: Path,
    requests: int,
    warmup: int,
    known_deployments: frozenset[str],
) -> Workload:
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise BenchmarkError(f"{path}: cannot read measured file ({exc})") from exc
    digest = hashlib.sha256(raw_bytes).hexdigest()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BenchmarkError(f"{path}: not valid UTF-8 JSON ({exc})") from exc

    records = _measured_records(payload, path)
    by_deployment: dict[str, list[Observation]] = {}
    excluded: dict[str, str] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise BenchmarkError(f"{path}: record {index} is not an object")
        name = next(
            (
                record[key]
                for key in MEASURED_NAME_KEYS
                if isinstance(record.get(key), str) and record[key].strip()
            ),
            None,
        )
        if name is None:
            raise BenchmarkError(
                f"{path}: record {index} has none of {', '.join(MEASURED_NAME_KEYS)}"
            )
        name = name.strip()
        if name not in known_deployments:
            raise BenchmarkError(
                f"{path}: record {index} names {name!r}, which is not a "
                "configured deployment"
            )
        outcome = _measured_outcome(record)
        if outcome is not None and outcome in MEASURED_EXCLUDED_OUTCOMES:
            excluded[name] = outcome
            continue
        succeeded = _measured_success(record, index, path, outcome)
        latency = record.get("latency_ms")
        if (
            isinstance(latency, bool)
            or not isinstance(latency, (int, float))
            or latency < 0
        ):
            raise BenchmarkError(
                f"{path}: record {index} ({name}) has no non-negative numeric "
                "'latency_ms'"
            )
        by_deployment.setdefault(name, []).append(
            Observation(succeeded=succeeded, latency_ms=float(latency))
        )

    if not by_deployment:
        raise BenchmarkError(
            f"{path}: no replayable observations (every record was excluded)"
        )

    observations: dict[str, tuple[Observation, ...]] = {}
    distinct: dict[str, int] = {}
    for name, items in by_deployment.items():
        distinct[name] = len(items)
        observations[name] = tuple(
            items[index % len(items)] for index in range(warmup + requests)
        )

    provenance = {
        "source": "MEASURED",
        "statement": (
            "Outcome and latency values are real provider observations, "
            "replayed from the file named below. Routing decisions are "
            "simulated. This run made no provider calls and spent no credits; "
            "the observations were produced earlier by a separate probe."
        ),
        "spends_provider_credits": False,
        "path": str(path),
        "sha256": digest,
        "distinct_observations": distinct,
        "replayed_requests": requests,
        "replay_note": (
            "observations are cycled to fill the request count; N replayed "
            "requests are not N independent measurements"
        ),
        "excluded_no_observation": dict(sorted(excluded.items())),
    }
    return Workload(
        provenance=provenance,
        candidates=tuple(by_deployment),
        observations=observations,
        profiles=None,
    )


def _latency_stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "mean": None,
            "p50": None,
            "p95": None,
            "note": "no observations",
        }
    ordered = sorted(values)
    if len(ordered) < 2:
        # statistics.quantiles requires at least two data points.
        return {
            "count": 1,
            "mean": round(ordered[0], 3),
            "p50": round(ordered[0], 3),
            "p95": round(ordered[0], 3),
            "note": (
                "single observation; percentiles need at least 2 points, so "
                "p50/p95 repeat the one value"
            ),
        }
    percentiles = quantiles(ordered, n=100, method="inclusive")
    return {
        "count": len(ordered),
        "mean": round(fmean(ordered), 3),
        "p50": round(percentiles[49], 3),
        "p95": round(percentiles[94], 3),
        "note": None,
    }


def _distribution(counter: Counter[str], total: int) -> list[dict[str, Any]]:
    return [
        {
            "deployment": name,
            "count": count,
            "share": round(count / total, 6) if total else 0.0,
        }
        for name, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def _final_scores(router: Router, candidates: list[str]) -> dict[str, Any]:
    ranking = router.scorer.rank(
        tuple(candidates),
        reliability=router.health,
        latency=router.latency,
    )
    return {
        "policy_version": ranking.policy_version,
        "fallback_reason": ranking.fallback_reason,
        "candidates": [
            {
                "deployment": score.deployment,
                "score": None if score.score is None else round(score.score, 6),
                "success_rate": (
                    None
                    if score.success_rate is None
                    else round(score.success_rate, 6)
                ),
                "average_latency_ms": (
                    None
                    if score.average_latency_ms is None
                    else round(score.average_latency_ms, 3)
                ),
                "reliability_samples": score.reliability_samples,
                "latency_samples": score.latency_samples,
            }
            for score in ranking.candidate_scores
        ],
    }


def _run_strategy(
    *,
    strategy: str,
    registry: ProviderRegistry,
    settings: ScoringSettings,
    workload: Workload,
    requests: int,
    warmup: int,
    max_attempts: int,
) -> dict[str, Any]:
    health = HealthRegistry()
    latency = LatencyTracker()
    router = Router(
        registry,
        health=health,
        latency=latency,
        scoring_settings=settings,
    )
    candidates = list(workload.candidates)

    # Warm start from the first `warmup` ground-truth observations of each
    # deployment. This is not invented data: it is the same matrix the
    # measured requests consume, and both strategies get the identical start.
    for name in candidates:
        for observation in workload.observations[name][:warmup]:
            latency.record(name, observation.latency_ms)
            if observation.succeeded:
                health.mark_success(name)
            else:
                health.mark_failure(name)

    first_selection: Counter[str] = Counter()
    attempt_counts: Counter[str] = Counter()
    first_reasons: Counter[str] = Counter()
    successful_latencies: list[float] = []
    attempted_latencies: list[float] = []
    successes = 0
    fallbacks = 0
    unroutable = 0
    failed_attempts = 0

    for index in range(requests):
        attempted: list[str] = []
        elapsed_ms = 0.0
        succeeded = False
        for attempt in range(max_attempts):
            try:
                decision = router.choose_deployment(
                    candidates,
                    attempted=attempted,
                    strategy=strategy,
                )
            except (NoHealthyDeploymentError, NoRemainingDeploymentError):
                break
            deployment = decision.deployment
            if attempt == 0:
                first_selection[deployment] += 1
                explanation = decision.explanation
                reason = (
                    explanation.scoring_fallback_reason
                    if explanation is not None
                    else None
                )
                first_reasons[reason or "none"] += 1
            attempted.append(deployment)
            attempt_counts[deployment] += 1
            observation = workload.observations[deployment][warmup + index]
            elapsed_ms += observation.latency_ms
            latency.record(deployment, observation.latency_ms)
            if observation.succeeded:
                health.mark_success(deployment)
                succeeded = True
                break
            health.mark_failure(deployment)
            failed_attempts += 1

        if not attempted:
            unroutable += 1
        else:
            attempted_latencies.append(elapsed_ms)
        if succeeded:
            successes += 1
            successful_latencies.append(elapsed_ms)
        if len(attempted) > 1:
            fallbacks += 1

    return {
        "strategy": strategy,
        "requests": requests,
        "successful_requests": successes,
        "failed_requests": requests - successes,
        "success_rate": round(successes / requests, 6),
        "fallback_requests": fallbacks,
        "fallback_rate": round(fallbacks / requests, 6),
        "unroutable_requests": unroutable,
        "failed_attempts": failed_attempts,
        "attempts": sum(attempt_counts.values()),
        "latency_ms": {
            "successful_requests": _latency_stats(successful_latencies),
            "all_attempted_requests": _latency_stats(attempted_latencies),
        },
        "first_selection_distribution": _distribution(first_selection, requests),
        "attempt_distribution": _distribution(
            attempt_counts, sum(attempt_counts.values())
        ),
        "first_selection_reasons": dict(sorted(first_reasons.items())),
        "deterministic_scoring_engaged": "none" in first_reasons,
        "final_scores": _final_scores(router, candidates),
    }


def _build_report(
    args: argparse.Namespace,
    settings: ScoringSettings,
    workload: Workload,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "tool": "scripts/benchmark.py",
        "benchmark": "sabiroute-routing",
        "schema_version": 1,
        "phase": "14",
        "seed": args.seed if workload.provenance["source"] == "SYNTHETIC" else None,
        "seed_note": (
            None
            if workload.provenance["source"] == "SYNTHETIC"
            else "not used: the measured workload is replayed, not generated"
        ),
        "requests": args.requests,
        "max_attempts": args.max_attempts,
        "warmup_observations_per_deployment": settings.minimum_samples,
        "data_provenance": workload.provenance,
        "baseline": {
            "policy_version": settings.policy_version,
            "reliability_weight": settings.reliability_weight,
            "latency_weight": settings.latency_weight,
            "minimum_samples": settings.minimum_samples,
            "max_signal_age_seconds": settings.max_signal_age_seconds,
            "source": "config/config.yaml (routing_scoring)",
            "expected": BASELINE,
            "matches_phase12_baseline": True,
        },
        "candidates": list(workload.candidates),
        "workload_profiles": workload.profiles,
        "results": results,
    }


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def render(row: list[str]) -> str:
        return "  ".join(
            cell.ljust(widths[index]) for index, cell in enumerate(row)
        ).rstrip()

    lines = [render(headers), "  ".join("-" * width for width in widths)]
    lines.extend(render(row) for row in rows)
    return lines


def _fmt(value: Any, spec: str) -> str:
    return "n/a" if value is None else format(value, spec)


def _render(report: dict[str, Any]) -> str:
    provenance = report["data_provenance"]
    baseline = report["baseline"]
    lines: list[str] = [
        "SabiRoute routing benchmark — Phase 14",
        "=" * 38,
        "",
        f"DATA PROVENANCE: {provenance['source']}",
        textwrap.fill(
            provenance["statement"],
            width=78,
            initial_indent="  ",
            subsequent_indent="  ",
        ),
        "",
        (
            "Baseline (unchanged): "
            f"{baseline['policy_version']}  "
            f"reliability_weight={baseline['reliability_weight']}  "
            f"latency_weight={baseline['latency_weight']}  "
            f"minimum_samples={baseline['minimum_samples']}"
        ),
        f"  source: {baseline['source']}; matches the Phase 12 baseline constants",
        "",
    ]

    if provenance["source"] == "MEASURED":
        lines.append(f"Measured source: {provenance['path']}")
        lines.append(f"  sha256: {provenance['sha256']}")
        lines.append(
            "  distinct observations: "
            + ", ".join(
                f"{name}={count}"
                for name, count in provenance["distinct_observations"].items()
            )
        )
        if provenance["excluded_no_observation"]:
            lines.append(
                "  excluded (no provider observation): "
                + ", ".join(
                    f"{name}={outcome}"
                    for name, outcome in provenance[
                        "excluded_no_observation"
                    ].items()
                )
            )
        lines.append(f"  note: {provenance['replay_note']}")
    else:
        lines.append(
            f"Seed: {report['seed']}  (same seed reproduces these numbers exactly)"
        )

    lines.append(
        f"Workload: {report['requests']} requests x {report['max_attempts']} "
        f"attempts, {report['warmup_observations_per_deployment']} warm-up "
        "observations per deployment"
    )
    lines.append(f"Candidates ({len(report['candidates'])}): "
                 + ", ".join(report["candidates"]))
    lines.append("")

    lines.append("Headline comparison (latency over successful requests)")
    rows = []
    for result in report["results"]:
        stats = result["latency_ms"]["successful_requests"]
        rows.append(
            [
                result["strategy"],
                str(result["requests"]),
                _fmt(result["success_rate"], ".1%"),
                _fmt(result["fallback_rate"], ".1%"),
                _fmt(result["unroutable_requests"] / result["requests"], ".1%"),
                _fmt(stats["mean"], ".1f"),
                _fmt(stats["p50"], ".1f"),
                _fmt(stats["p95"], ".1f"),
            ]
        )
    lines.extend(
        _table(
            [
                "strategy",
                "requests",
                "success",
                "fallback",
                "unroutable",
                "mean_ms",
                "p50_ms",
                "p95_ms",
            ],
            rows,
        )
    )
    lines.append("")

    lines.append("First-selection distribution")
    rows = []
    for result in report["results"]:
        for entry in result["first_selection_distribution"]:
            rows.append(
                [
                    result["strategy"],
                    entry["deployment"],
                    str(entry["count"]),
                    _fmt(entry["share"], ".1%"),
                ]
            )
    lines.extend(_table(["strategy", "deployment", "count", "share"], rows))
    lines.append("")

    lines.append("Deterministic scores after the run")
    rows = []
    for result in report["results"]:
        for entry in result["final_scores"]["candidates"]:
            rows.append(
                [
                    result["strategy"],
                    entry["deployment"],
                    _fmt(entry["score"], ".4f"),
                    _fmt(entry["success_rate"], ".1%"),
                    _fmt(entry["average_latency_ms"], ".1f"),
                    str(entry["reliability_samples"]),
                ]
            )
    lines.extend(
        _table(
            [
                "strategy",
                "deployment",
                "score",
                "success_rate",
                "mean_latency_ms",
                "samples",
            ],
            rows,
        )
    )
    lines.append("")

    if provenance["source"] == "SYNTHETIC":
        lines.append(
            "REMINDER: these numbers are SYNTHETIC fixtures. They are not "
            "provider measurements."
        )
    else:
        lines.append(
            "REMINDER: outcome and latency values are MEASURED provider "
            "observations; routing decisions are simulated."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        config = load_config(args.config)
        settings = _settings_from_config(config)
        _assert_baseline(settings)
        registry = registry_from_config(config)
        configured = tuple(
            deployment.name for deployment in registry.list_deployments()
        )
        warmup = settings.minimum_samples
        if args.measured is not None:
            workload = _measured_workload(
                Path(args.measured),
                args.requests,
                warmup,
                frozenset(configured),
            )
        else:
            workload = _synthetic_workload(
                configured, args.requests, warmup, args.seed
            )
        strategies = (
            ["priority", "measured"]
            if args.strategy == "both"
            else [args.strategy]
        )
        results = [
            _run_strategy(
                strategy=strategy,
                registry=registry,
                settings=settings,
                workload=workload,
                requests=args.requests,
                warmup=warmup,
                max_attempts=args.max_attempts,
            )
            for strategy in strategies
        ]
        report = _build_report(args, settings, workload, results)
    except (BenchmarkError, ValueError, yaml.YAMLError) as exc:
        # ValueError covers ConfigLoadError, ConfigValidationError and pydantic
        # validation; yaml.YAMLError covers a config file that is mid-write.
        # load_config() wraps none of them, so report cleanly instead of
        # dumping a traceback.
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
