"""Reproducible synthetic comparison of priority and measured routing.

This is an algorithm harness, not a provider benchmark. Synthetic outcomes and
latencies make the run repeatable without spending provider credits.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from statistics import quantiles

from sabiroute.config.loader import load_config
from sabiroute.monitoring.latency import LatencyTracker
from sabiroute.providers.registry import registry_from_config
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.router import NoHealthyDeploymentError, Router
from sabiroute.routing.scoring import ScoringSettings


def _simulate(strategy: str, request_count: int) -> dict[str, object]:
    registry = registry_from_config(load_config())
    candidates = ["sabiroute-gemini", "sabiroute-openai"]
    health = HealthRegistry()
    latency = LatencyTracker()
    router = Router(
        registry,
        health=health,
        latency=latency,
        scoring_settings=ScoringSettings(minimum_samples=5),
    )

    # Fixed synthetic historical observations create a reproducible warm start.
    for _ in range(5):
        health.mark_success(candidates[0])
        health.mark_failure(candidates[0])
        latency.record(candidates[0], 75.0)
    for _ in range(199):
        health.mark_success(candidates[1])
    health.mark_failure(candidates[1])
    for _ in range(200):
        latency.record(candidates[1], 180.0)

    attempt_counts: Counter[str] = Counter()
    first_selection_counts: Counter[str] = Counter()
    response_latencies: list[float] = []
    logical_successes = 0
    logical_timeouts = 0
    failed_attempts = 0
    timeout_attempts = 0
    requests_with_fallback = 0
    routing_seconds = 0.0
    routing_calls = 0

    for _request_index in range(request_count):
        attempted: list[str] = []
        elapsed_ms = 0.0
        request_succeeded = False
        request_timed_out = False
        for attempt_number in range(2):
            started = time.perf_counter()
            try:
                decision = router.choose_deployment(
                    candidates,
                    attempted=attempted,
                    strategy=strategy,
                )
            except NoHealthyDeploymentError:
                break
            routing_seconds += time.perf_counter() - started
            routing_calls += 1
            deployment = decision.deployment
            if attempt_number == 0:
                first_selection_counts[deployment] += 1
            attempted.append(deployment)
            attempt_counts[deployment] += 1

            if deployment == candidates[0]:
                observation_number = attempt_counts[deployment]
                latency_ms = 75.0 + (observation_number % 7)
                succeeded = observation_number % 2 == 1
                timed_out = not succeeded and observation_number % 4 == 0
            else:
                observation_number = attempt_counts[deployment]
                latency_ms = 180.0 + (observation_number % 7)
                timed_out = observation_number % 200 == 0
                succeeded = not timed_out

            elapsed_ms += latency_ms
            latency.record(deployment, latency_ms)
            if succeeded:
                health.mark_success(deployment)
                request_succeeded = True
                break

            health.mark_failure(deployment)
            failed_attempts += 1
            request_timed_out = request_timed_out or timed_out
            timeout_attempts += int(timed_out)

        if len(attempted) > 1:
            requests_with_fallback += 1
        logical_successes += int(request_succeeded)
        logical_timeouts += int(request_timed_out and not request_succeeded)
        response_latencies.append(elapsed_ms)

    percentiles = quantiles(response_latencies, n=100, method="inclusive")
    return {
        "strategy": strategy,
        "requests": request_count,
        "successful_requests": logical_successes,
        "failed_requests": request_count - logical_successes,
        "request_success_rate": logical_successes / request_count,
        "request_error_rate": (request_count - logical_successes) / request_count,
        "requests_with_timeout": logical_timeouts,
        "timeout_attempt_rate": timeout_attempts / max(sum(attempt_counts.values()), 1),
        "failed_attempts": failed_attempts,
        "fallback_frequency": requests_with_fallback / request_count,
        "response_latency_ms": {
            "p50": percentiles[49],
            "p95": percentiles[94],
            "p99": percentiles[98],
        },
        "deployment_attempt_distribution": dict(attempt_counts),
        "first_selection_distribution": dict(first_selection_counts),
        "routing_overhead_us_per_selection": (
            routing_seconds / max(routing_calls, 1) * 1_000_000
        ),
        "measured_cost": None,
        "cost_note": "unavailable: synthetic workload has no verified pricing data",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=int, default=5000)
    args = parser.parse_args()
    if args.requests < 100:
        parser.error("--requests must be at least 100 for percentile reporting")
    result = {
        "benchmark_type": "synthetic; no provider calls",
        "synthetic_profiles": {
            "sabiroute-gemini": "50% success, 50% failures; 75ms base latency",
            "sabiroute-openai": "99.5% success, 0.5% timeouts; 180ms base latency",
        },
        "scoring_settings": {
            "policy_version": "deterministic-v1",
            "reliability_weight": 0.7,
            "latency_weight": 0.3,
            "minimum_samples": 5,
        },
        "results": [
            _simulate("priority", args.requests),
            _simulate("measured", args.requests),
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
