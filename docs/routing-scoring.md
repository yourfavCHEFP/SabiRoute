# Phase 12 measured deterministic routing

Virtual routes may set `strategy: measured` to rank the deployments that have
already passed policy candidate discovery, capability filtering, and health
filtering. `strategy: priority` retains configured order. The production route
YAML uses `measured`; direct deployment aliases remain priority-routed because
they contain one candidate.

## Signals and formula

The scorer uses only these preselection signals already collected by SabiRoute:

- **Operational reliability:** successful provider attempts divided by all
  successful and failed attempts for that deployment in the current process.
  A successful HTTP/API completion is an operational success, not an answer
  quality label.
- **Mean observed attempt latency:** `LatencyTracker` measurements for that
  deployment in the current process.

For fresh, sufficiently sampled eligible candidates:

```text
latency_normalized = (slowest_eligible_mean - candidate_mean)
                    / (slowest_eligible_mean - fastest_eligible_mean)
score = reliability_weight * success_rate
      + latency_weight * latency_normalized
```

When all eligible candidates have equal measured latency, their normalized
latency is `1.0`; configured order breaks equal-score ties. The default weights
are 0.7 for reliability and 0.3 for latency. This is a transparent baseline
policy preference for avoiding failed attempts; it is configurable and has not
been tuned against production benchmark data. Weights must be non-negative and
sum to 1.

`config/config.yaml` contains `routing_scoring.policy_version`, the two weights,
`minimum_samples`, and `max_signal_age_seconds`. Change `policy_version` when a
formula or scoring semantics change materially.

## Cold start and stale telemetry

If any currently eligible deployment has fewer than the configured minimum
reliability outcomes or latency samples, has missing measurements, or has no
observation within `max_signal_age_seconds`, the scorer falls back to the
configured route order for the entire eligible set. The scorer does not assign a
bad score to a new deployment. Telemetry is process-local and resets on restart;
the durable routing-attempt records preserve decision evidence but are not read
back into the request path. No database query is issued for a routing decision.

## Scope and excluded signals

- Measured historical cost is excluded: current per-deployment cost fields are
  pricing metadata, while durable request costs are not a bounded, low-cost
  aggregate suitable for request-path scoring.
- Answer quality is excluded: SabiRoute has no defensible quality label.
- Request type and capability fit are recorded in each decision but do not add
  score points. Capability eligibility is a hard pre-scoring filter, and no
  evidence supports request-specific performance weights yet.
- Usage from the current attempt, its outcome, and its latency are never used to
  select that same attempt. They update health/latency observations for later
  decisions only.

## Decision records and fallback

Each logical request's durable usage record contains one internal routing
decision entry per provider attempt, including candidate and eligible sets,
request type, selected deployment, policy version, weights, score breakdown,
decision time, fallback attempt, outcome, latency, provider-reported usage, and
actual cost only when it can be calculated from returned usage and explicit
pricing metadata. The record is available through the existing admin-only usage
inspection path; it is not returned to ordinary clients.

Each fallback attempt reruns eligibility against the same policy candidate set
and excludes attempted or unhealthy deployments before ranking. A candidate
rejected by policy, capability, or health cannot be reintroduced by the scorer.

## Streaming lifecycle

Streaming requests use the same authentication, durable admission, budget,
request classification, capability and health filters, and deterministic
scorer as non-streaming requests. SabiRoute opens the selected LiteLLM stream
and reads its first SSE frame before returning the response, so HTTP/provider
errors before any frame can still follow the normal fallback loop. Once the
first SSE frame is committed to the client, SabiRoute never replays that request
against another deployment. A mid-stream failure emits a generic SSE error and
`[DONE]`, records a failed attempt, and updates health/latency. Provider-reported
usage is captured from the final usage event when present; missing usage remains
unknown. The upstream connection is closed when the client stream ends or is
cancelled.

## Benchmarking

Run `./.venv/bin/python scripts/benchmark_routing.py --requests 5000` for a
repeatable synthetic comparison of `priority` and `measured`. The harness uses
fixed synthetic reliability and latency profiles, performs no provider calls, and
reports logical success/error/timeout rates, latency percentiles, fallback
frequency, deployment distribution, and selection overhead. Its output is a
methodology check only; it is not provider performance evidence. Cost is reported
as unavailable because the synthetic fixtures contain no verified pricing data.
