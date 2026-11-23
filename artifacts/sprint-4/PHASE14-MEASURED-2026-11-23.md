# Phase 14 — first measured benchmark run

**Date:** 2026-11-23 · **Verdict:** measured comparison produced, but degenerate ·
**Phase 14 status after this run:** still **not Complete** (now has one recorded
measured run; see "Verdict" at the end).

This closes the gap the previous Phase 14 evidence left open in principle — a
`--measured` run over real provider observations — and records exactly what it
produced. It does not fabricate or simulate anything: the outcome and latency
values are the real results of one minimal completion per configured alias.

---

## Step 1 — the probe (real provider calls)

One call per configured alias, through LiteLLM, using the repository's own
`scripts/probe_provider_aliases.py` unchanged. Budget: 14 aliases, one
`litellm.completion` each at `max_tokens=64`, `timeout=25`, `num_retries=0`,
escalating to 512 only if a response came back empty with
`finish_reason == "length"`. No retries, no loops.

```bash
cd "/Users/airm2/My ML Hub/SabiRoute-claude-fix"
PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
  "/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
  scripts/probe_provider_aliases.py > /tmp/phase14-probe.json 2>/tmp/phase14-probe.err
```

```
PROBE_EXIT=0
stderr: `max_retries` is not supported. It will be ignored.
sha256(/tmp/phase14-probe.json) = c17f253e877cd2dac1a5fde35b28e4cb4554a2a183ce96184a2ac230083a81e5
```

**Stream contamination, handled without re-running.** LiteLLM writes coloured
log/error noise to **stdout**, so the redirected file contained that noise before
the JSON object. The JSON the script emitted with its final `print()` was
extracted byte-for-byte (from the `{\n  "verdict": "PROBED"` marker to the end of
the object; one trailing newline dropped) and written to
`/tmp/phase14-probe.clean.json`. No observation was edited, added, removed, or
reordered; only third-party log lines that preceded the JSON were separated out.
Re-running the probe to get a clean stream was **not** done, because that would
spend provider credits a second time.

```
sha256(/tmp/phase14-probe.clean.json) = a05ea8233c6402d24fb99c25f19222a45835df6cd9faa3050b1fee2e24855b82
```

### Real probe observations [VERIFIED BY RUNTIME]

`verdict: PROBED · total_aliases: 14 · working: 6`

| alias | outcome | latency_ms | HTTP status |
|---|---|---:|---:|
| `sabiroute-openai` | ERROR | 2245.3 | 429 |
| `sabiroute-gemini` | ERROR | 2301.1 | 503 |
| `sabiroute-groq` | **OK** | 1500.8 | — |
| `sabiroute-together` | ERROR | 2058.5 | 401 |
| `sabiroute-deepinfra` | ERROR | 1486.8 | 402 |
| `sabiroute-kimi` | ERROR | 2137.1 | 429 |
| `sabiroute-minimax` | ERROR | 1242.3 | 402 |
| `sabiroute-cloudflare` | **OK** | 5177.4 | — |
| `sabiroute-openrouter` | **OK** | 4617.3 | — |
| `sabiroute-huggingface` | ERROR | 2984.4 | 402 |
| `sabiroute-cerebras` | ERROR | 4437.9 | 402 |
| `sabiroute-nvidia` | **OK** | 1868.5 | — |
| `sabiroute-cohere` | **OK** | 4701.9 | — |
| `sabiroute-pollinations` | **OK** | 3499.8 | — |

Six aliases returned real non-empty completions (`finish_reason: "stop"`). Eight
are blocked on **account state**, not on SabiRoute: 401 (auth), 402 (payment
required), 429 (rate/quota), 503 (provider unavailable). This is the documented
reality for this key set, and it is a legitimate finding: SabiRoute did not
invent an answer, and the probe correctly reports each failure with its status.

---

## Step 2 — the harness over those observations

```bash
cd "/Users/airm2/My ML Hub/SabiRoute-claude-fix"
PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
  "/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
  scripts/benchmark.py --measured /tmp/phase14-probe.clean.json
# exit 0
```

### Real output [VERIFIED BY RUNTIME]

```
SabiRoute routing benchmark — Phase 14
======================================

DATA PROVENANCE: MEASURED
  Outcome and latency values are real provider observations, replayed from the
  file named below. Routing decisions are simulated. This run made no provider
  calls and spent no credits; the observations were produced earlier by a
  separate probe.

Baseline (unchanged): deterministic-v1 reliability_weight=0.7 latency_weight=0.3 minimum_samples=5
  source: config/config.yaml (routing_scoring); matches the Phase 12 baseline constants

Measured source: /tmp/phase14-probe.clean.json
  sha256: a05ea8233c6402d24fb99c25f19222a45835df6cd9faa3050b1fee2e24855b82
  distinct observations: sabiroute-openai=1, sabiroute-gemini=1, sabiroute-groq=1, sabiroute-together=1, sabiroute-deepinfra=1, sabiroute-kimi=1, sabiroute-minimax=1, sabiroute-cloudflare=1, sabiroute-openrouter=1, sabiroute-huggingface=1, sabiroute-cerebras=1, sabiroute-nvidia=1, sabiroute-cohere=1, sabiroute-pollinations=1
  note: observations are cycled to fill the request count; N replayed requests are not N independent measurements
Workload: 200 requests x 2 attempts, 5 warm-up observations per deployment
Candidates (14): sabiroute-openai, sabiroute-gemini, sabiroute-groq, sabiroute-together, sabiroute-deepinfra, sabiroute-kimi, sabiroute-minimax, sabiroute-cloudflare, sabiroute-openrouter, sabiroute-huggingface, sabiroute-cerebras, sabiroute-nvidia, sabiroute-cohere, sabiroute-pollinations

Headline comparison (latency over successful requests)
strategy requests success fallback unroutable mean_ms p50_ms p95_ms
-------- -------- ------- -------- ---------- ------- ------ ------
priority 200 100.0% 0.0% 0.0% 1500.8 1500.8 1500.8
measured 200 100.0% 0.0% 0.0% 1500.8 1500.8 1500.8

First-selection distribution
strategy deployment count share
-------- -------------- ----- ------
priority sabiroute-groq 200 100.0%
measured sabiroute-groq 200 100.0%

Deterministic scores after the run
strategy deployment score success_rate mean_latency_ms samples
-------- ---------------------- ------ ------------ --------------- -------
priority sabiroute-openai 0.2235 0.0% 2245.3 5
priority sabiroute-gemini 0.2193 0.0% 2301.1 5
priority sabiroute-groq 0.9803 100.0% 1500.8 205
priority sabiroute-together 0.2378 0.0% 2058.5 5
priority sabiroute-deepinfra 0.2814 0.0% 1486.8 5
priority sabiroute-kimi 0.2318 0.0% 2137.1 5
priority sabiroute-minimax 0.3000 0.0% 1242.3 5
priority sabiroute-cloudflare 0.7000 100.0% 5177.4 5
priority sabiroute-openrouter 0.7427 100.0% 4617.3 5
priority sabiroute-huggingface 0.1672 0.0% 2984.4 5
priority sabiroute-cerebras 0.0564 0.0% 4437.9 5
priority sabiroute-nvidia 0.9523 100.0% 1868.5 5
priority sabiroute-cohere 0.7363 100.0% 4701.9 5
priority sabiroute-pollinations 0.8279 100.0% 3499.8 5
measured sabiroute-openai 0.2235 0.0% 2245.3 5
measured sabiroute-gemini 0.2193 0.0% 2301.1 5
measured sabiroute-groq 0.9803 100.0% 1500.8 205
measured sabiroute-together 0.2378 0.0% 2058.5 5
measured sabiroute-deepinfra 0.2814 0.0% 1486.8 5
measured sabiroute-kimi 0.2318 0.0% 2137.1 5
measured sabiroute-minimax 0.3000 0.0% 1242.3 5
measured sabiroute-cloudflare 0.7000 100.0% 5177.4 5
measured sabiroute-openrouter 0.7427 100.0% 4617.3 5
measured sabiroute-huggingface 0.1672 0.0% 2984.4 5
measured sabiroute-cerebras 0.0564 0.0% 4437.9 5
measured sabiroute-nvidia 0.9523 100.0% 1868.5 5
measured sabiroute-cohere 0.7363 100.0% 4701.9 5
measured sabiroute-pollinations 0.8279 100.0% 3499.8 5

REMINDER: outcome and latency values are MEASURED provider observations; routing decisions are simulated.
```

The same run with `--json` (exit 0) reports, per strategy:
`success_rate 1.0 · fallback_rate 0.0 · unroutable_requests 0 · failed_attempts 0
· attempts 200`, `first_selection_reasons {"priority_strategy": 200}` for
`priority` and `{"none": 200}` for `measured`, `deterministic_scoring_engaged
true` for `measured`. `data_provenance.source` is `MEASURED`,
`spends_provider_credits` is `false`, `sha256` is the clean-file digest above,
`excluded_no_observation` is empty, and `seed` is `null` with the note "not used:
the measured workload is replayed, not generated".

---

## What this proves [VERIFIED BY RUNTIME]

1. **The harness consumes real provider observations and labels them correctly.**
   `DATA PROVENANCE: MEASURED`, the file's SHA-256, and the per-alias distinct
   counts all appear in the output. No provider was called by `benchmark.py`
   (`spends_provider_credits: false`); the observations came from Step 1.

2. **The health hard constraint worked.** Eight deployments returned
   401/402/429/503 in the probe. In the benchmark they were **never attempted**:
   `failed_attempts 0`, `attempt_distribution` contains only `sabiroute-groq`, and
   each failing alias shows `samples 5` (warm-up only, no routed request). Their
   warm-up failures tripped passive cooldown and the router refused to route to
   them. This is the behaviour `CLAUDE.md §6` requires — the engine declining to
   send traffic to deployments that just failed — observed, not asserted.

3. **Deterministic-v1 scoring engaged on the measured strategy.** Its
   `first_selection_reasons` is `{"none": 200}` (score actually ranked, not a
   cold-start fallback); the priority strategy reports
   `{"priority_strategy": 200}`. The baseline constants were asserted, not
   assumed (`matches_phase12_baseline: true`).

4. **The run is deterministic and reproducible from the same file.** The report
   contains no timestamps or wall-clock values.

## What this does NOT prove

* **That `measured` scoring beats `priority`.** The two rows are identical. This
  is a **degenerate comparison**: both strategies selected `sabiroute-groq` 200
  times because groq is simultaneously (a) the first *healthy* deployment in
  configured priority order — openai and gemini ahead of it both failed — and
  (b) the highest deterministic-v1 score (0.9803, driven by the lowest healthy
  latency, 1500.8 ms). When "first healthy" and "best score" coincide, the two
  policies cannot diverge. This run cannot be quoted as evidence that either
  strategy is better.
* **Provider reliability or latency distributions.** Each alias has **one**
  observation. The 200 replayed requests per strategy are one measurement per
  alias cycled 205 times, not 205 measurements — the report says so. Every
  returned latency is a single real sample; p50 and p95 equal the mean because
  the value is constant under replay.
* **Coverage of 8 of the 14 aliases.** They are blocked on account state
  (401/402/429/503). No routing evidence exists for them until their accounts
  are funded/authorised.
* **Provider execution, streaming, cost, or answer quality.** Routing is
  simulated over recorded outcomes; `benchmark.py` executes nothing.
* **Behaviour of the five other reachable aliases under load.** Only `groq` was
  ever selected; `cloudflare`, `openrouter`, `nvidia`, `cohere` and
  `pollinations` contributed warm-up samples only.

---

## Verdict — does this close Phase 14?

**No, not on its own.** What it closes is the specific gap "no measured run has
ever been executed": there is now one recorded, reproducible, real-observation
run. What it does **not** do is produce a comparison with any discriminating
power — the two strategies are identical because the data makes them identical,
and each alias carries a single observation.

Phase 14's acceptance is "compare against the unchanged deterministic baseline".
This run performs that comparison over real observations but on a degenerate
workload, so it is methodology-plus-one-data-point, not a finished benchmark. The
honest status is **In progress** with a recorded measured run — not **Complete**.

### What would make it meaningful (concrete)

1. **More than one observation per alias.** Run the probe several times, spaced
   over time, and concatenate the per-alias records into one measured file. This
   gives reliability and latency variance so the score can move between
   observations, and lets the report's distinct-count and percentile logic do
   real work. (This spends credits per run; it is a budgeted decision, not a
   free rerun — hence not done here.)
2. **A case where "first healthy in priority order" ≠ "highest score".** With
   varying per-alias latency, e.g. groq's mean rising above nvidia's, `priority`
   would keep picking the earlier deployment while `measured` switched to the
   better-scoring one — the only way the comparison discriminates.
3. **A documented scope decision for the 8 blocked aliases** — either fund/authorise
   them, or explicitly scope the Phase 14 benchmark to the reachable set and say
   so in the acceptance record.

Until at least (1) and (2) exist, do not upgrade Phase 14 to Complete.

---

## Reproduce (with the two traps)

```bash
# Trap 1: PYTHONPATH must point at the tree being measured, or the venv imports
# the OLD primary checkout's sabiroute.  Trap 2: SABIROUTE_ENV_FILE must point
# at the credential file; no .env value is read or printed by this record.
cd "/Users/airm2/My ML Hub/SabiRoute-claude-fix"
PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
  "/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
  scripts/probe_provider_aliases.py    # one call per alias; spends credits
# then extract the JSON object from stdout into /tmp/phase14-probe.clean.json
PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
  "/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
  scripts/benchmark.py --measured /tmp/phase14-probe.clean.json
```

The benchmark replay itself makes **no** provider calls and spends **no**
credits; only Step 1 does.
