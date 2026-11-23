#!/usr/bin/env python3
"""Phase 12 — drive the deterministic scorer from MEASURED provider signals.

Why this exists
---------------
``scripts/benchmark_routing.py`` exercises the same scorer on synthetic
reliability and latency profiles. That proves the arithmetic is wired, not
that the ranking responds to evidence. Phase 12's remaining gap was exactly
that word: *synthetic*.

This harness makes one minimal real completion per runtime-working alias
(six calls total), measures wall-clock attempt latency and the real
success/failure outcome, records both into the production registries
(``LatencyTracker``, ``HealthRegistry``), and then asks the real
``Router(strategy="measured")`` for a ranking. Every number used by the
scorer is therefore a measurement, and the printed arithmetic can be checked
by hand.

Budget, deliberately conservative
---------------------------------
* one call per alias, ``max_tokens=64``;
* escalation to ``max_tokens=512`` only when the first response was empty
  *and* ``finish_reason == "length"`` (a reasoning model spending the whole
  budget on its trace is a budget artefact, not a failure — see
  ``scripts/probe_provider_aliases.py``);
* ``timeout=25`` seconds per HTTP call, ``num_retries=0`` so LiteLLM cannot
  spend extra calls behind the harness's back;
* calls are sequential, not concurrent, so one alias's network contention
  cannot be recorded as another alias's latency;
* credentials are read from the environment and never printed — only the
  variable *name* and its set/empty state appear in the output.

What is measured vs constructed
-------------------------------
* MEASURED: latency_ms, success/failure, finish_reason, error class.
* MEASURED DATA, OVERRIDDEN GATE: the scoring run with ``minimum_samples=1``
  reuses those same measurements; the production gate of 5 cannot be met by
  one sample per alias, so the production-policy run is reported separately
  as a fallback. Nothing is imitated.
* CONSTRUCTED: the rank-flip demonstrations. They perturb one measured
  signal in a copy of the measured table and are labelled "constructed".
  They are not presented as additional provider calls.

Exit codes: 0 measured ranking produced and arithmetic self-check passed,
1 no usable measurement or a self-check failed, 3 environment problem.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# The six aliases with runtime evidence as of 2026-11-23.
ALIASES: tuple[str, ...] = (
    "sabiroute-groq",
    "sabiroute-cloudflare",
    "sabiroute-openrouter",
    "sabiroute-nvidia",
    "sabiroute-cohere",
    "sabiroute-pollinations",
)

MAX_TOKENS = 64
ESCALATED_MAX_TOKENS = 512
CALL_TIMEOUT = 25
NUM_RETRIES = 0
PROMPT = "Reply with the single word OK."


def _load_env() -> None:
    """Load credentials from SABIROUTE_ENV_FILE or the repo-root .env.

    Values are never read by this module: ``load_dotenv`` sets them in the
    process environment and LiteLLM consumes them at the call boundary.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover
        return
    explicit = os.environ.get("SABIROUTE_ENV_FILE")
    path = Path(explicit) if explicit else REPO_ROOT / ".env"
    if path.exists():
        load_dotenv(path, override=False)


def _scrub(text: str, credential_names: list[str]) -> str:
    """Remove any live credential value from diagnostic text."""
    for name in credential_names:
        value = os.environ.get(name)
        if value:
            text = text.replace(value, "[REDACTED]")
    return text


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


def _measure(deployment: Any) -> dict[str, Any]:
    """Make one real, minimal completion and measure it. Never prints secrets."""
    import litellm

    alias = deployment.name
    credential_names = [deployment.api_key_env] if deployment.api_key_env else []
    missing = [name for name in credential_names if not os.environ.get(name)]
    base: dict[str, Any] = {
        "alias": alias,
        "model": deployment.model,
        "credential_variables": credential_names,
        "credential_state": "empty" if missing else "set",
    }
    if missing:
        return {
            **base,
            "outcome": "NO_CREDENTIAL",
            "success": False,
            "calls": 0,
            "latency_ms": None,
            "measured": False,
        }

    params = deployment.as_litellm_params()
    params["messages"] = [{"role": "user", "content": PROMPT}]
    params["max_tokens"] = MAX_TOKENS
    params["timeout"] = CALL_TIMEOUT
    # The config sets num_retries: 1. The measurement budget is explicit:
    # one attempt per alias, no hidden retries.
    params["num_retries"] = NUM_RETRIES

    calls = 1
    started = time.perf_counter()
    try:
        response = litellm.completion(**params)
        content = _content_of(response)
        finish = _finish_of(response)
        escalated = False
        if not content.strip() and finish == "length":
            escalated = True
            calls = 2
            params["max_tokens"] = ESCALATED_MAX_TOKENS
            response = litellm.completion(**params)
            content = _content_of(response)
            finish = _finish_of(response)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        outcome = "OK" if content.strip() else "EMPTY_CONTENT"
        return {
            **base,
            "outcome": outcome,
            "success": outcome == "OK",
            "calls": calls,
            "latency_ms": elapsed_ms,
            "finish_reason": finish,
            "escalated_budget": escalated,
            "content_preview": _scrub(content.strip()[:80], credential_names),
            "measured": True,
        }
    except Exception as exc:  # noqa: BLE001 - classified and reported
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            **base,
            "outcome": "ERROR",
            "success": False,
            "calls": calls,
            "latency_ms": elapsed_ms,
            "status_code": getattr(exc, "status_code", None),
            "error_class": type(exc).__name__,
            "error_preview": _scrub(str(exc)[:200], credential_names),
            "measured": True,
        }


class _FixedReliability:
    """ReliabilitySource over a frozen snapshot of measured outcomes."""

    def __init__(self, observations: dict[str, tuple[int, int, datetime | None]]) -> None:
        self.observations = observations
        self.state_scope_id = "phase12-measured-reliability"

    def scoring_observation(
        self, deployment: str, as_of: datetime | None = None
    ) -> tuple[int, int, datetime | None]:
        return self.observations.get(deployment, (0, 0, None))


class _FixedLatency:
    """LatencySource over a frozen snapshot of measured attempt latencies."""

    def __init__(self, observations: dict[str, tuple[int, float | None, datetime | None]]) -> None:
        self.observations = observations
        self.state_scope_id = "phase12-measured-latency"

    def scoring_observation(
        self, deployment: str, as_of: datetime | None = None
    ) -> tuple[int, float | None, datetime | None]:
        return self.observations.get(deployment, (0, None, None))


@dataclass(frozen=True, slots=True)
class _Arithmetic:
    rows: list[dict[str, Any]]
    fastest_ms: float
    slowest_ms: float
    range_ms: float


def _arithmetic(ranking: Any, settings: Any) -> _Arithmetic:
    """Recompute and expose every term the scorer used."""
    scores = list(ranking.candidate_scores)
    averages = [item.average_latency_ms for item in scores if item.average_latency_ms is not None]
    fastest = min(averages)
    slowest = max(averages)
    span = slowest - fastest
    rows: list[dict[str, Any]] = []
    for item in scores:
        if item.average_latency_ms is None or item.latency_normalized is None:
            rows.append(
                {
                    "deployment": item.deployment,
                    "scored": False,
                    "reason": "no measured latency sample",
                }
            )
            continue
        if span == 0:
            normalization = (
                f"all means equal ({item.average_latency_ms:.1f} ms) -> latency_normalized = 1.0"
            )
            expected_normalized = 1.0
        else:
            normalization = (
                f"({slowest:.1f} - {item.average_latency_ms:.1f}) / "
                f"({slowest:.1f} - {fastest:.1f}) = {item.latency_normalized:.6f}"
            )
            expected_normalized = (slowest - item.average_latency_ms) / span
        reliability_term = settings.reliability_weight * (item.success_rate or 0.0)
        latency_term = settings.latency_weight * expected_normalized
        recomputed = reliability_term + latency_term
        rows.append(
            {
                "deployment": item.deployment,
                "scored": True,
                "success_rate": item.success_rate,
                "reliability_samples": item.reliability_samples,
                "average_latency_ms": item.average_latency_ms,
                "latency_samples": item.latency_samples,
                "latency_normalization": normalization,
                "latency_normalized": expected_normalized,
                "reliability_term": (
                    f"{settings.reliability_weight:.2f} * {item.success_rate:.4f} = "
                    f"{reliability_term:.6f}"
                ),
                "latency_term": (
                    f"{settings.latency_weight:.2f} * {expected_normalized:.4f} = "
                    f"{latency_term:.6f}"
                ),
                "expression": (f"{reliability_term:.6f} + {latency_term:.6f} = {recomputed:.6f}"),
                "scorer_score": item.score,
                "recomputed_score": recomputed,
                "matches_scorer": item.score is not None and abs(item.score - recomputed) <= 1e-12,
            }
        )
    return _Arithmetic(rows=rows, fastest_ms=fastest, slowest_ms=slowest, range_ms=span)


def _rank(
    candidates: list[str],
    reliability: _FixedReliability,
    latency: _FixedLatency,
    settings: Any,
    as_of: datetime,
) -> tuple[list[str], dict[str, Any]]:
    from sabiroute.routing.scoring import DeterministicScorer

    ranking = DeterministicScorer(settings).rank(
        candidates, reliability=reliability, latency=latency, now=as_of
    )
    scored = {item.deployment: item for item in ranking.candidate_scores}
    return list(ranking.ranked_candidates), {
        "fallback_reason": ranking.fallback_reason,
        "scores": {
            name: {
                "score": item.score,
                "success_rate": item.success_rate,
                "average_latency_ms": item.average_latency_ms,
                "latency_normalized": item.latency_normalized,
            }
            for name, item in scored.items()
        },
    }


def _flip_demonstration(
    candidates: list[str],
    reliability_snapshot: dict[str, tuple[int, int, datetime | None]],
    latency_snapshot: dict[str, tuple[int, float | None, datetime | None]],
    settings: Any,
    as_of: datetime,
    observed_at: datetime,
) -> dict[str, Any]:
    """Construct a transparent signal change on one measured candidate."""
    baseline, baseline_detail = _rank(
        candidates,
        _FixedReliability(dict(reliability_snapshot)),
        _FixedLatency(dict(latency_snapshot)),
        settings,
        as_of,
    )
    leader = baseline[0]
    successes, failures, _ = reliability_snapshot[leader]

    # Reliability flip: degrade the current leader's measured outcome.
    reliability_flip: dict[str, Any] = {"applicable": False}
    if successes > 0:
        perturbed = dict(reliability_snapshot)
        perturbed[leader] = (0, 1, observed_at)
        flipped_rank, flipped_detail = _rank(
            candidates,
            _FixedReliability(perturbed),
            _FixedLatency(dict(latency_snapshot)),
            settings,
            as_of,
        )
        reliability_flip = {
            "applicable": True,
            "evidence": "constructed",
            "changed": leader,
            "change": (
                f"measured outcome {successes} success / {failures} failure "
                f"-> 0 success / 1 failure (success_rate 1.0 -> 0.0)"
            ),
            "ranked_before": baseline,
            "ranked_after": flipped_rank,
            "flipped": flipped_rank != baseline,
            "before": baseline_detail["scores"][leader],
            "after": flipped_detail["scores"][leader],
        }
    else:
        reliability_flip["reason"] = (
            "leader has no measured success to degrade; a synthetic success "
            "would not demonstrate a reliability-driven rank change"
        )

    # Latency flip: make the current leader the slowest measured candidate.
    means = [value[1] for value in latency_snapshot.values() if value[1] is not None]
    latency_flip: dict[str, Any] = {"applicable": False}
    if means:
        slowest = max(means)
        leader_mean = latency_snapshot[leader][1] or 0.0
        target = slowest if leader_mean < slowest else leader_mean * 2.0
        perturbed_latency = dict(latency_snapshot)
        perturbed_latency[leader] = (1, target, observed_at)
        flipped_rank, flipped_detail = _rank(
            candidates,
            _FixedReliability(dict(reliability_snapshot)),
            _FixedLatency(perturbed_latency),
            settings,
            as_of,
        )
        latency_flip = {
            "applicable": True,
            "evidence": "constructed",
            "changed": leader,
            "change": (
                f"measured mean latency {leader_mean:.1f} ms -> {target:.1f} ms "
                "(now the slowest of the measured set)"
            ),
            "ranked_before": baseline,
            "ranked_after": flipped_rank,
            "flipped": flipped_rank != baseline,
            "before": baseline_detail["scores"][leader],
            "after": flipped_detail["scores"][leader],
        }

    return {
        "evidence": "constructed",
        "baseline_ranked": baseline,
        "reliability_flip": reliability_flip,
        "latency_flip": latency_flip,
    }


def main() -> int:
    _load_env()

    from sabiroute.config.loader import load_config
    from sabiroute.monitoring.latency import LatencyTracker
    from sabiroute.providers.registry import registry_from_config
    from sabiroute.routing.health import HealthRegistry
    from sabiroute.routing.router import Router
    from sabiroute.routing.scoring import ScoringSettings

    config = load_config()
    registry = registry_from_config(config)
    scoring_config = config.routing_scoring

    health = HealthRegistry()
    latency = LatencyTracker()

    measurements: list[dict[str, Any]] = []
    for alias in ALIASES:
        deployment = registry.get(alias)
        result = _measure(deployment)
        measurements.append(result)
        if not result["measured"]:
            continue
        # A failed attempt still consumed real wall-clock time; record the
        # measured attempt latency and the measured outcome independently.
        latency.record(alias, float(result["latency_ms"]))
        if result["success"]:
            health.mark_success(alias)
        else:
            health.mark_failure(alias)

    measured_aliases = [item["alias"] for item in measurements if item["measured"]]
    if not measured_aliases:
        print(
            json.dumps(
                {
                    "verdict": "ENVIRONMENT",
                    "reason": "no alias produced a measured attempt",
                    "measurements": measurements,
                },
                indent=2,
                default=str,
            )
        )
        return 3

    production_settings = ScoringSettings(
        policy_version=scoring_config.policy_version,
        reliability_weight=scoring_config.reliability_weight,
        latency_weight=scoring_config.latency_weight,
        minimum_samples=scoring_config.minimum_samples,
        max_signal_age_seconds=scoring_config.max_signal_age_seconds,
    )
    measured_settings = ScoringSettings(
        policy_version=scoring_config.policy_version,
        reliability_weight=scoring_config.reliability_weight,
        latency_weight=scoring_config.latency_weight,
        # Explicit, documented override: one measured sample per alias cannot
        # satisfy the production minimum of 5. Everything else is unchanged.
        minimum_samples=1,
        max_signal_age_seconds=scoring_config.max_signal_age_seconds,
    )

    production_router = Router(
        registry,
        health=health,
        latency=latency,
        scoring_settings=production_settings,
    )
    production_decision = production_router.choose_deployment(measured_aliases, strategy="measured")
    assert production_decision.explanation is not None

    measured_router = Router(
        registry,
        health=health,
        latency=latency,
        scoring_settings=measured_settings,
    )
    scored_at = datetime.now(UTC)
    measured_decision = measured_router.choose_deployment(
        measured_aliases, strategy="measured", scoring_as_of=scored_at
    )
    explanation = measured_decision.explanation
    assert explanation is not None

    ranking = measured_router.scorer.rank(
        measured_aliases,
        reliability=health,
        latency=latency,
        now=scored_at,
    )
    arithmetic = _arithmetic(ranking, measured_settings)

    observed_at_by_alias: dict[str, datetime] = {}
    for item in measurements:
        if item["measured"]:
            _, _, observed_at_by_alias[item["alias"]] = health.scoring_observation(item["alias"])
    fallback_now = datetime.now(UTC)
    reliability_snapshot = {
        alias: (*health.scoring_observation(alias, fallback_now)[:2], observed_at_by_alias[alias])
        for alias in measured_aliases
    }
    latency_snapshot = {
        alias: (
            1,
            float(next(m["latency_ms"] for m in measurements if m["alias"] == alias)),
            observed_at_by_alias[alias],
        )
        for alias in measured_aliases
    }

    # The frozen adapter must reproduce the live registry's ranking exactly;
    # otherwise the flip demonstration would be built on different numbers.
    baseline_ranked, _ = _rank(
        measured_aliases,
        _FixedReliability(dict(reliability_snapshot)),
        _FixedLatency(dict(latency_snapshot)),
        measured_settings,
        fallback_now,
    )
    snapshot_matches_registry = baseline_ranked == list(explanation.ranked_candidates)

    flips = _flip_demonstration(
        measured_aliases,
        reliability_snapshot,
        latency_snapshot,
        measured_settings,
        fallback_now,
        observed_at_by_alias[measured_aliases[0]],
    )
    flips["baseline_matches_live_registry"] = snapshot_matches_registry

    # Did measured reliability change the order at all? Compare the policy's
    # 0.7/0.3 ranking against a latency-only ranking of the same measurements.
    latency_only_settings = ScoringSettings(
        policy_version=scoring_config.policy_version,
        reliability_weight=0.0,
        latency_weight=1.0,
        minimum_samples=1,
        max_signal_age_seconds=scoring_config.max_signal_age_seconds,
    )
    latency_only_ranked, _ = _rank(
        measured_aliases,
        _FixedReliability(dict(reliability_snapshot)),
        _FixedLatency(dict(latency_snapshot)),
        latency_only_settings,
        fallback_now,
    )

    configured_order = list(measured_aliases)
    measured_order = list(explanation.ranked_candidates)
    latencies_by_alias = {
        item["alias"]: item["latency_ms"] for item in measurements if item["measured"]
    }
    table = [
        {
            "alias": alias,
            "mean_latency_ms": latencies_by_alias[alias],
            "latency_samples": 1,
            "successes": reliability_snapshot[alias][0],
            "failures": reliability_snapshot[alias][1],
            "age_seconds": round((fallback_now - observed_at_by_alias[alias]).total_seconds(), 1),
        }
        for alias in measured_aliases
    ]

    arithmetic_ok = all(row.get("matches_scorer", True) for row in arithmetic.rows)
    production_fallback = production_decision.explanation.scoring_fallback_reason
    findings = [
        (
            f"Production policy (minimum_samples={production_settings.minimum_samples}) "
            f"did not engage: fallback_reason={production_fallback!r}. "
            "The scorer requires every eligible candidate to carry at least "
            f"{production_settings.minimum_samples} reliability outcomes AND "
            f"{production_settings.minimum_samples} latency samples, so six single "
            "calls (one per alias) cannot satisfy it; five samples per alias would "
            f"cost {5 * len(measured_aliases)} provider calls."
        ),
        (
            "The gate is all-or-nothing across the eligible set: one cold "
            "deployment forces the entire ranking back to configured priority "
            "order, not just that deployment."
        ),
        (
            f"Freshness was satisfiable: every observation was measured "
            f"{min(row['age_seconds'] for row in table):.1f}-"
            f"{max(row['age_seconds'] for row in table):.1f} s before scoring, "
            f"inside max_signal_age_seconds={production_settings.max_signal_age_seconds}."
        ),
    ]
    if measured_order != configured_order:
        findings.append(
            "Measured signals alone changed the order: "
            f"configured {configured_order} -> measured {measured_order}."
        )
    else:
        findings.append(
            "Measured signals did not change the order relative to configured "
            f"priority: {measured_order}."
        )
    if latency_only_ranked != measured_order:
        findings.append(
            "Measured reliability changed the order relative to a latency-only "
            f"ranking: latency-only {latency_only_ranked} vs 0.7/0.3 {measured_order}."
        )
    else:
        findings.append(
            "Measured reliability did not change the order relative to a "
            "latency-only ranking of the same measurements."
        )
    findings.append(
        "Telemetry is process-local: these observations reset on restart, so "
        "the production gate re-opens as a cold start after every restart."
    )
    findings.append(
        f"Calls made: {sum(item['calls'] for item in measurements)} "
        f"({len(measured_aliases)} aliases; escalation counts are included)."
    )

    verdict = (
        "MEASURED"
        if arithmetic_ok
        and snapshot_matches_registry
        and any(item["success"] for item in measurements)
        else "CHECK_FAILED"
    )

    payload = {
        "harness": "phase12_measured_scoring",
        "generated_at": datetime.now(UTC).isoformat(),
        "verdict": verdict,
        "budget": {
            "aliases": len(ALIASES),
            "calls_made": sum(item["calls"] for item in measurements),
            "max_tokens": MAX_TOKENS,
            "escalated_max_tokens": ESCALATED_MAX_TOKENS,
            "timeout_seconds": CALL_TIMEOUT,
            "num_retries": NUM_RETRIES,
        },
        "scoring_policy": {
            "policy_version": scoring_config.policy_version,
            "reliability_weight": scoring_config.reliability_weight,
            "latency_weight": scoring_config.latency_weight,
            "minimum_samples": scoring_config.minimum_samples,
            "max_signal_age_seconds": scoring_config.max_signal_age_seconds,
        },
        "measured_calls": measurements,
        "measured_latency_table": table,
        "production_policy_run": {
            "evidence": "VERIFIED BY RUNTIME",
            "engaged": production_decision.explanation.scoring_fallback_reason is None,
            "fallback_reason": production_decision.explanation.scoring_fallback_reason,
            "ranked_candidates": list(production_decision.explanation.ranked_candidates),
            "selected_deployment": production_decision.deployment,
            "selection_reason": production_decision.explanation.selection_reason,
            "scores": [
                {
                    "deployment": item.deployment,
                    "score": item.score,
                    "success_rate": item.success_rate,
                    "reliability_samples": item.reliability_samples,
                    "latency_samples": item.latency_samples,
                }
                for item in production_decision.explanation.candidate_scores
            ],
        },
        "measured_ranking_minimum_samples_1": {
            "evidence": "VERIFIED BY RUNTIME (measured data; sample-count gate overridden)",
            "override": (
                "ScoringSettings.minimum_samples=1 instead of 5. The measured "
                "values, weights, policy version and freshness window are the "
                "production ones."
            ),
            "eligible": measured_aliases,
            "configured_order": configured_order,
            "ranked_candidates": measured_order,
            "selected_deployment": measured_decision.deployment,
            "ineligible_for_scoring": [
                item["alias"] for item in measurements if not item["measured"]
            ],
            "latency_bounds": {
                "fastest_ms": arithmetic.fastest_ms,
                "slowest_ms": arithmetic.slowest_ms,
                "range_ms": arithmetic.range_ms,
            },
            "arithmetic": arithmetic.rows,
            "self_check": {
                "all_scores_recomputed_from_printed_terms": arithmetic_ok,
                "frozen_snapshot_matches_live_registry": snapshot_matches_registry,
            },
            "latency_only_ranking": latency_only_ranked,
        },
        "flip_demonstrations": flips,
        "findings": findings,
        "reproduction": (
            'PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" '
            'SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" '
            '"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" '
            "scripts/phase12_measured_scoring.py"
        ),
    }

    print(json.dumps(payload, indent=2, default=str))

    # Human-readable mirror of the ranking so the arithmetic is visible
    # without parsing JSON.
    print("", file=sys.stderr)
    print("alias                          success  mean_ms    n   norm   score", file=sys.stderr)
    for row in arithmetic.rows:
        if not row.get("scored"):
            print(f"{row['deployment']:<30} unscored", file=sys.stderr)
            continue
        print(
            f"{row['deployment']:<30} {row['success_rate']:>6.3f} "
            f"{row['average_latency_ms']:>8.1f} {row['reliability_samples']:>3} "
            f"{row['latency_normalized']:>6.3f} {row['scorer_score']:>6.3f}"
            f"   [{row['expression']}]",
            file=sys.stderr,
        )
    print(f"ranked: {measured_order}", file=sys.stderr)
    print(
        f"production gate: {production_decision.explanation.scoring_fallback_reason}",
        file=sys.stderr,
    )

    return 0 if verdict == "MEASURED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
