# Benchmarking (Phase 14)

`scripts/benchmark.py` is the Phase 14 benchmarking entry point. It answers one
question:

> Under an identical workload, how does the unchanged `deterministic-v1`
> routing baseline behave with `priority` selection versus `measured` scoring?

Acceptance for Phase 14 is "compare against the unchanged deterministic
baseline". This tool performs that comparison and labels its evidence. It does
not tune the baseline, and it refuses to run if the baseline has been retuned.

## Relationship to `scripts/benchmark_routing.py`

**`scripts/benchmark.py` supersedes `scripts/benchmark_routing.py` as the
benchmarking entry point.** Run `benchmark.py`; do not reach for
`benchmark_routing.py` for new work.

`benchmark_routing.py` is kept in the tree unchanged as the Phase 12
methodology record. It compares the same two strategies, but it is narrowly
scoped:

| | `benchmark_routing.py` | `benchmark.py` |
|---|---|---|
| Candidate set | two hardcoded aliases | every deployment in `config/config.yaml` |
| Workload | hardcoded synthetic profile | seeded fixtures, or `--measured` replay |
| Provenance label | partial (`benchmark_type` string) | explicit `data_provenance` block |
| Release guard | none | refuses to run if the baseline drifted |
| Reproducibility | not byte-exact: reports wall-clock `routing_overhead_us_per_selection` | byte-exact for a given seed and input |
| CLI | `--requests` only | `--requests`, `--seed`, `--strategy`, `--measured`, `--json`, ... |

`benchmark.py` also drops `routing_overhead_us_per_selection` deliberately. It
was the only field in the older harness that changed between two runs with
identical inputs, so it made "same seed, same numbers" unverifiable. Routing
CPU cost is not a Phase 14 acceptance criterion.

The older harness is still referenced by `docs/routing-scoring.md` (§
Benchmarking) and the Phase 12 note in `README.md`. Those references are owned
by other edits and still point at `benchmark_routing.py`; when they are next
touched they should point here.

## Two meanings of "measured"

They are independent, and the report distinguishes them:

* `--strategy measured` — selects the **routing policy** (deterministic-v1
  scoring). The alternative is `priority`.
* `--measured PATH` — selects the **data source** (real provider observations
  replayed from a file). The default is synthetic fixtures.

`--strategy priority --measured probe.json` is valid: priority routing over
measured observations.

## Commands

The runtime incantation in this repository must point `PYTHONPATH` at the tree
you mean to measure, or the venv silently imports an older `sabiroute`.

A checkout without its own `.venv` (a worktree, for example) can use
`uv run python` or any interpreter that can import this tree; `PYTHONPATH` is
what selects the tree, not the interpreter path.

```bash
# 1. Default: synthetic, both strategies, human table. Zero provider credits.
PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py

# 2. Machine-readable, byte-reproducible for a given seed.
PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py --json

# 3. Reproduce exactly, twice.
PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py > a.txt
PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py > b.txt
diff a.txt b.txt          # no output

# 4. One strategy only.
PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py --strategy priority

# 5. Replay real observations produced earlier by a probe.
PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py --measured probe.json

# 6. Pin a different config, or a larger run.
PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py --config config/config.yaml \
    --requests 2000 --seed 7
```

Exit codes: `0` success, `2` argument, config, baseline-drift, or measured-file
problem (the message names the file and record).

## What it measures

Per strategy, over `--requests` logical requests:

| Metric | Definition |
|---|---|
| `success_rate` | logical requests that ended in a successful attempt |
| `fallback_rate` | logical requests that needed more than one attempt |
| `unroutable_requests` | requests where no candidate was eligible before any attempt (typically every deployment cooling down) |
| `latency_ms.successful_requests` | mean / p50 / p95 over requests that succeeded — "how fast is a served request" |
| `latency_ms.all_attempted_requests` | mean / p50 / p95 including failed attempts — "what a client waits, success or not" |
| `first_selection_distribution` | which deployment the router chose first, and how often |
| `attempt_distribution` | which deployments were attempted at all, including fallback attempts |
| `first_selection_reasons` | why each first selection happened (`priority_strategy`, or `none` meaning deterministic scoring actually ranked) |
| `final_scores` | each deployment's `success_rate`, mean latency, sample counts and `deterministic-v1` score after the run |

Percentiles use `statistics.quantiles(..., n=100, method="inclusive")`, which
requires at least two data points. With one point the tool reports the single
value for p50 and p95 and sets `note`, rather than crashing or inventing a
distribution.

Both strategies are built from **separate** `HealthRegistry`, `LatencyTracker`
and `Router` instances, and they consume the **same** pre-generated ground-truth
matrix. The only thing that differs between the two rows of the headline table
is the routing policy.

## What it does NOT measure

* **Real provider reliability or latency.** In synthetic mode every outcome is a
  fixture. A synthetic `success_rate` is not a claim about a provider.
* **Provider cost.** No pricing is applied and no tokens are counted.
* **Answer quality.** SabiRoute has no defensible quality label.
* **LiteLLM execution.** No request is executed, in any mode.
* **Streaming, concurrency, load, token throughput.**
* **Durable telemetry.** PostgreSQL, Redis, usage records and routing-decision
  records are not written or read.
* **Independent measurements in `--measured` mode.** Observations are cycled to
  fill `--requests`. Two hundred replayed requests over two observations are two
  measurements, not two hundred. The report prints the distinct counts and says
  so.

## Synthetic versus measured

Every report leads with `DATA PROVENANCE`:

* `SYNTHETIC` — "No provider was contacted and no credits were spent. Outcome
  and latency values are seeded fixtures, not provider measurements."
* `MEASURED` — "Outcome and latency values are real provider observations,
  replayed from the file named below. Routing decisions are simulated."

The JSON carries the same text in `data_provenance.statement`, plus the measured
file's SHA-256. The human table ends with a matching reminder line. This is the
distinction the phase exists to protect: synthetic output must never be mistaken
for measured provider performance.

**Neither mode spends provider credits.** `benchmark.py` never imports
`litellm`, `openai`, `httpx`, `requests` or `aiohttp`, and constructs no client.
`--measured` only reads a file that some other tool wrote.

### Synthetic fixture derivation

For each deployment, a profile is derived from
`sha512(seed | deployment)` over fixed ranges: success rate 0.90–0.995, base
latency 150–1500 ms, jitter 10–250 ms. Per-request outcomes are drawn from
`sha512(seed | deployment)` again, independently of the routing strategy. The
derivation is reported in `data_provenance.derivation` and every profile appears
in `workload_profiles`.

Deriving the profile from a hash rather than hand-picking it is deliberate: no
deployment is favoured by construction, and no result was tuned to make either
strategy look better.

### Accepted measured input shapes

The file may be a JSON list of records, or an object with a `results` or
`observations` list. Two record shapes are accepted:

```jsonc
// scripts/probe_provider_aliases.py (stdout)
{"alias": "sabiroute-nvidia", "outcome": "OK", "latency_ms": 1032.4}

// reports/provider_verification.json (persisted)
{"model_name": "sabiroute-together", "status": "FAIL", "latency_ms": 3168.15}
```

* Deployment key: `alias`, `deployment`, or `model_name`.
* Outcome: `succeeded` (boolean), or an outcome token from `outcome`, or
  `status`.
* `OK`, `SUCCESS`, `SUCCEEDED`, `PASS` → success.
* `EMPTY_CONTENT`, `ERROR`, `FAILED`, `FAILURE`, `TIMEOUT`, `FAIL` → failure.
* `NO_CREDENTIAL`, `SKIPPED` → excluded: no provider was contacted, so there is
  no observation to replay. Excluded aliases are listed in the report.
* `latency_ms` must be a non-negative number.

An unknown deployment name, an unrecognised outcome, or a missing latency is an
error that names the record — never a silent guess. Only deployments present in
`config/config.yaml` are accepted, so a stale probe file cannot invent routes.

Example, using the only measured file currently persisted in the repository (it
is stale, from 2026-10-10, and holds a single failing alias):

```bash
PYTHONPATH=src ./.venv/bin/python scripts/benchmark.py \
    --measured reports/provider_verification.json --requests 10
```

That run reports `MEASURED`, one distinct observation for `sabiroute-together`,
and every request `unroutable` — five consecutive failures trip the passive
cooldown, and a single always-failing deployment has no fallback. That is the
health hard constraint working, not a benchmark failure.

## Baseline is asserted, not assumed

At startup the tool loads `config/config.yaml`, builds `ScoringSettings` from
`routing_scoring`, and compares it with the Phase 12 constants:

```
policy_version      deterministic-v1
reliability_weight  0.7
latency_weight      0.3
minimum_samples     5
```

If any of those changed, the run stops with exit code 2 and names the drifted
values. A benchmark against a silently retuned baseline proves nothing, so the
tool refuses rather than reports a favourable number. `max_signal_age_seconds`
is reported alongside but is not part of the acceptance constants.

## Reproducibility

Two runs with the same `--seed`, `--requests`, `--max-attempts` and config
produce byte-identical output, in both table and `--json` form. The report
contains no timestamps, durations, UUIDs or wall-clock measurements. Warm-up is
deterministic too: the first `minimum_samples` observations of each deployment
seed the health and latency trackers before request 0, and both strategies
receive the identical warm start.

`--seed` is ignored in `--measured` mode, and the report says so
(`seed: null`, `seed_note`); a measured run is reproducible because the file is,
not because of a seed. Changing `--seed` changes the synthetic fixtures.

### Recorded synthetic result (2026-11-23, seed 20261123, 200 requests)

Synthetic, on the 14 configured aliases, `deterministic-v1` unchanged:

| strategy | success | fallback | unroutable | mean_ms | p50_ms | p95_ms | first selection |
|---|---:|---:|---:|---:|---:|---:|---|
| `priority` | 100.0% | 14.5% | 0.0% | 1508.9 | 1308.6 | 2736.6 | `sabiroute-openai` 200/200 |
| `measured` | 100.0% | 0.0% | 0.0% | 364.2 | 363.8 | 369.9 | `sabiroute-huggingface` 200/200 |

Both rows faced the same fixtures. `priority` never left configured order
(`first_selection_reasons` = `{"priority_strategy": 200}`); `measured` ranked
(`{"none": 200}`, i.e. no cold-start or stale-telemetry fallback), and the
best-scoring deployment under this seed was also the fastest and most reliable
one. These numbers describe the routing policy on fixtures. They are not
provider measurements and must not be quoted as such.

## Limitations

* A synthetic comparison cannot show that `measured` beats `priority` against
  real providers. That requires observations from real calls, replayed with
  `--measured`, and enough distinct observations to be meaningful.
* A measured file with one observation per alias makes percentile and
  distribution figures descriptive only. The report prints the distinct counts
  next to them for exactly this reason.
* The workload has no request-type or capability mix: every request is an
  untyped chat request with no required capabilities, so capability and policy
  filtering are exercised only in their "everything eligible" form.
* Process-local telemetry only, matching the request path: health and latency
  reset per run. Cooldown is the passive 30-second rule; a run finishing inside
  30 seconds cannot observe cooldown recovery.

## Phase 14 evidence status

This tool provides the comparison mechanism and reproducible synthetic
baseline-versus-baseline evidence. It does **not**, on its own, establish live
provider benchmarking: that requires a `--measured` run over a probe file with
real observations, and the Phase 14 status should stay `Planned` or move to
`In progress` until such a run is recorded. Synthetic output is a methodology
result, in the same sense as `docs/routing-scoring.md` describes
`benchmark_routing.py`.
