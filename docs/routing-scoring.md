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
bad score to a new deployment. By default telemetry is process-local and resets
on restart; configuring Redis persists it across restarts (see *Cross-restart
signal persistence* below). The durable routing-attempt records preserve
decision evidence but are not read back into the request path. No database query
is issued for a routing decision.

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

Two harnesses exist, and they answer different questions.

Run `./.venv/bin/python scripts/benchmark_routing.py --requests 5000` for a
repeatable synthetic comparison of `priority` and `measured`. The harness uses
fixed synthetic reliability and latency profiles, performs no provider calls, and
reports logical success/error/timeout rates, latency percentiles, fallback
frequency, deployment distribution, and selection overhead. Its output is a
methodology check only; it is not provider performance evidence. Cost is reported
as unavailable because the synthetic fixtures contain no verified pricing data.

Run `./.venv/bin/python scripts/phase12_measured_scoring.py` for the measured
counterpart described below. It makes one real completion per runtime-working
alias, records the measured latency and outcome in `LatencyTracker` and
`HealthRegistry`, and asks the real `Router(strategy="measured")` for a ranking.

## Measured evidence (2026-11-23)

`scripts/phase12_measured_scoring.py` replaced synthetic profiles with measured
signals for the six aliases that had runtime evidence on this date. Each alias
received exactly one minimal completion (`max_tokens=64`, `timeout=25`,
`num_retries=0`; escalation to `max_tokens=512` only for empty content with
`finish_reason == "length"`). Six calls were made, all answered, none escalated,
and every credential variable was set. Measured attempt latency and the measured
outcome were recorded into the production `LatencyTracker` and `HealthRegistry`;
no number was invented.

| alias | outcome | measured mean latency | latency samples | reliability outcomes |
|---|---|---|---|---|
| `sabiroute-cohere` | success | 707.5 ms | 1 | 1 success / 0 failure |
| `sabiroute-nvidia` | success | 721.6 ms | 1 | 1 success / 0 failure |
| `sabiroute-pollinations` | success | 1488.8 ms | 1 | 1 success / 0 failure |
| `sabiroute-cloudflare` | success | 4647.6 ms | 1 | 1 success / 0 failure |
| `sabiroute-groq` | success | 4695.3 ms | 1 | 1 success / 0 failure |
| `sabiroute-openrouter` | success | 7599.0 ms | 1 | 1 success / 0 failure |

### The production gate did not engage, and that is the honest result

With `minimum_samples: 5`, the production policy fell back to configured priority
order with `fallback_reason` `insufficient_latency_samples,insufficient_reliability_samples`.
The scorer requires every eligible candidate to hold at least five reliability
outcomes **and** five latency samples. Six single calls cannot satisfy that — five
samples per alias would cost 30 provider calls — so a cold process cannot engage
`measured` routing at all. Because the gate is all-or-nothing across the eligible
set, one newly added deployment also forces the whole set back to configured
order. Freshness was satisfiable and was not the cause: every observation was
0.0–15.2 s old against `max_signal_age_seconds: 3600`. Telemetry is process-local,
so this cold start recurs after every restart.

### The scoring path on the same measured data

To show the arithmetic on measured values without inventing samples, the harness
re-ran the scorer with `minimum_samples=1`; weights, policy version, freshness
window and every measured value are the production ones. Latency bounds:
fastest 707.5 ms, slowest 7599.0 ms, range 6891.5 ms.

| alias | success rate | mean ms | latency normalized | score = 0.7·reliability + 0.3·latency |
|---|---|---|---|---|
| `sabiroute-cohere` | 1.000 | 707.5 | 1.000000 | 0.700000 + 0.300000 = 1.000000 |
| `sabiroute-nvidia` | 1.000 | 721.6 | 0.997954 | 0.700000 + 0.299386 = 0.999386 |
| `sabiroute-pollinations` | 1.000 | 1488.8 | 0.886628 | 0.700000 + 0.265989 = 0.965989 |
| `sabiroute-cloudflare` | 1.000 | 4647.6 | 0.428267 | 0.700000 + 0.128480 = 0.828480 |
| `sabiroute-groq` | 1.000 | 4695.3 | 0.421345 | 0.700000 + 0.126404 = 0.826404 |
| `sabiroute-openrouter` | 1.000 | 7599.0 | 0.000000 | 0.700000 + 0.000000 = 0.700000 |

Measured ranking: `cohere`, `nvidia`, `pollinations`, `cloudflare`, `groq`,
`openrouter`. Configured order was `groq`, `cloudflare`, `openrouter`, `nvidia`,
`cohere`, `pollinations`, so measured latency alone reordered the set. The harness
recomputes every score from the printed terms and asserts equality with the
scorer's own output.

Reliability did **not** reorder this run: all six calls succeeded, so success rate
was a flat 1.0 for every candidate and the 0.7 term was identical throughout. The
latency-only ranking of the same data equals the 0.7/0.3 ranking. A measured
reliability-driven ordering has therefore not been observed yet; it needs a real
failed attempt among the measured aliases.

### Rank flips are constructed, not measured

Two transparent perturbations were applied to copies of the measured table, and
both flip the ordering:

- **Reliability:** change the measured leader `sabiroute-cohere` from 1 success to
  1 failure. Its score drops 1.000 → 0.300 (the 0.7 term goes to zero) and it
  falls from first to last.
- **Latency:** change `sabiroute-cohere` from 707.5 ms to 7599.0 ms. Its score
  drops 1.000 → 0.700 (its latency term goes to zero) and it falls from first to
  last.

These demonstrate that the ordering responds to the signals that feed it. They
are labelled constructed in the JSON and are **not** additional measurements.

### Still synthetic or unverified

- `scripts/benchmark_routing.py` remains the synthetic methodology harness; its
  profiles are invented and are not evidence.
- Only one sample per alias exists, so no multi-attempt reliability rate has been
  measured and the production `minimum_samples=5` path has never been exercised
  live.
- No measured failure was injected into the scorer ranking; the reliability flip
  is constructed.
- The measured run covers success paths at one moment, not provider stability
  over time.

### Reproduction

```bash
PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
scripts/phase12_measured_scoring.py
```

The harness prints one JSON document to stdout (measured calls, both rankings, the
per-candidate arithmetic, the flip demonstrations, and the policy findings) and a
compact ranking table to stderr. It spends six provider calls; it never writes a
report file and prints credential variable names with their set/empty state only.

## Cross-restart signal persistence

### The defect this closes

`HealthRegistry` and `LatencyTracker` originally held their observations only in
process memory. A cold process therefore could not satisfy
`routing_scoring.minimum_samples` (default 5) within its first requests for any
deployment, so `DeterministicScorer` fell back to configured priority order and
every restart reset the measurement. The six reachable aliases would need 30
calls per process lifetime before measured routing could engage. Persisting the
signals — not lowering the threshold — is what lets measured routing engage in
production.

### Backends

`src/sabiroute/monitoring/signals_store.py` defines the narrow `SignalsBackend`
protocol with two implementations:

- **`InMemoryBackend`** (default): process-local and identical to the
  pre-persistence behaviour. A fresh instance starts empty, so a registry that
  receives no backend behaves exactly as it did before this change.
- **`RedisBackend`**: writes outcomes and latency samples to Redis sorted sets
  keyed `sabiroute:signals:v1:{health|latency}:<deployment>`. Each key's TTL is
  `routing_scoring.max_signal_age_seconds`, so stale observations expire without
  a sweeper, and each set keeps at most 1000 members.

`build_gateway_state` selects the backend with the same Redis detection as
request admission: `REDIS_URL` first, then `REDIS_HOST` with `REDIS_PORT`,
`REDIS_DB` and `REDIS_PASSWORD` (blank means unset). No Redis configuration
selects `InMemoryBackend`.

### Hydration and what is not restored

`HealthRegistry` and `LatencyTracker` read the backend when they are constructed,
so a restarted process inherits observations that are still inside the freshness
window. Reliability totals, last success/failure, latency samples and means are
restored.

Cooldown state (`healthy`, `consecutive_failures`, `cooldown_until`) is
deliberately **not** restored: a restart grants one fresh failure budget, exactly
as before. Persisting a tripped cooldown would change the health contract and is
out of scope for this fix.

Hydrated observations are attributed to the new process's `state_scope_id`. The
scope identifies the live registry instance that served the decision; it does not
identify the process that originally observed each sample.

### Failure behaviour

The store is telemetry. Writes are queued to a bounded background writer, so a
slow or unavailable Redis never blocks a request; reads return an empty result.
A failure sets `RedisBackend.degraded`, records a redacted `last_error`, and the
process continues with in-process behaviour. Observations dropped because the
writer queue was full are counted in `dropped_observations`. Nothing in the
routing path raises because the signal store failed.

The writer is a daemon thread: a graceful shutdown drains it, while an abrupt
`SIGKILL` can lose the last queued observations. Losing a tail of telemetry is
acceptable; losing routing is not.

### Evidence

`tests/test_phase12_persistence_inmemory.py` needs no service and proves
in-process behaviour is unchanged, that observations survive a simulated
restart, that a failing store degrades without raising, and that the scorer
produces a measured ranking after restart where a cold registry still falls back
to priority. `tests/test_phase12_persistence_redis.py` repeats the restart and
scorer proofs against a disposable Redis (opt-in via
`SABIROUTE_TEST_REDIS_URL`, loopback-only) and additionally proves TTL expiry,
stale-window pruning, and gateway backend selection.
