# Phase 14 — multi-observation measured benchmark

**Date:** 2026-11-23 · **Verdict:** 30 real observations collected, harness now
consumes genuine samples, **no genuine divergence** was produced ·
**Phase 14 status after this run:** still **not Complete** (now has a
multi-sample measured run; see "Verdict").

This closes the *methodological* gap the first measured run left open: each
alias now carries five **real** observations, and `scripts/benchmark.py
--measured` computes reliability and latency from those distinct samples rather
than replicating a single value. It does **not** close Phase 14, because the
real data did not make `priority` and `measured` diverge. That is the finding,
and it is reported plainly rather than engineered away.

Nothing here is simulated, injected, or hand-edited. Every latency and outcome
below is the result of one real completion through LiteLLM.

---

## Step 0 — harness change: multiple observations become genuine samples

`scripts/benchmark.py` already appended repeated records per alias, but it
reported them only as a replay stream and the score was driven by whatever the
tracker accumulated. Two additive changes make the multi-sample case honest:

1. **Per-alias distinct-sample statistics.** `_measured_sample_stats()` summarises
   every alias from its **distinct** observations — count, successes, failures,
   success rate, and latency mean/p50/p95 over the real samples — and flags
   `percentiles_meaningful` (false for a single sample).
2. **Explicit observation mode.** The report now states
   `observation mode: multi_observation` when any alias has more than one
   distinct record, or `single_observation` otherwise, and adapts the replay
   note to match. The human table gains a "Measured per-deployment samples
   (distinct real observations)" section; the JSON carries
   `data_provenance.observation_mode` and `data_provenance.measured_samples`.

Single-observation files behave exactly as before. [VERIFIED BY RUNTIME] — the
2026-11-23 single-observation file (`/tmp/phase14-probe.clean.json`) still
renders `observation mode: single_observation`, the same headline rows
(`priority 1500.8 / measured 1500.8`, both `sabiroute-groq 50/50` at
`--requests 50`), and the same deterministic scores.

---

## Step 1 — the probe: 5 real completions per working alias

`scripts/phase14_multi_observation_probe.py` (new) hits **only** the six aliases
the first probe reached, makes `--samples` real completions per alias, and has
**no retry and no budget escalation** so the run is capped at exactly
`6 x 5 = 30` calls. Calls are paced (1.0 s apart) so a free tier's per-minute
limit is not mistaken for provider unreliability. Credentials are read from the
environment; only the variable *name* (`GROQ_API_KEY`, …) appears in the output,
never a value.

Plan, verified before spending [VERIFIED BY RUNTIME]:

```bash
PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
scripts/phase14_multi_observation_probe.py --dry-run
```
```
{"verdict":"DRY_RUN","aliases":["sabiroute-groq","sabiroute-cloudflare","sabiroute-openrouter","sabiroute-nvidia","sabiroute-cohere","sabiroute-pollinations"],"samples_per_alias":5,"total_calls":30,"max_tokens":64,"timeout_seconds":30,"delay_seconds":1,"retries":0,"output":"/tmp/phase14_multi_observation.json"}
```

The run [VERIFIED BY RUNTIME] (exit 1: not every call answered):

```bash
PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
scripts/phase14_multi_observation_probe.py --samples 5 --delay 1.0 \
  --output /tmp/phase14_multi_observation.json
```
```
{"verdict":"PROBED","total_calls":30,"working_calls":26,"per_alias":{"sabiroute-groq":{"ok":5,"total":5},"sabiroute-cloudflare":{"ok":5,"total":5},"sabiroute-openrouter":{"ok":1,"total":5},"sabiroute-nvidia":{"ok":5,"total":5},"sabiroute-cohere":{"ok":5,"total":5},"sabiroute-pollinations":{"ok":5,"total":5}},"output":"/tmp/phase14_multi_observation.json"}
```

### The 30 real observations [VERIFIED BY RUNTIME]

| # | alias | sample | outcome | latency_ms | finish_reason |
|---:|---|---:|---|---:|---|
| 1 | `sabiroute-groq` | 0 | OK | 1187.5 | stop |
| 2 | `sabiroute-groq` | 1 | OK | 491.7 | stop |
| 3 | `sabiroute-groq` | 2 | OK | 407.0 | stop |
| 4 | `sabiroute-groq` | 3 | OK | 393.0 | stop |
| 5 | `sabiroute-groq` | 4 | OK | 671.9 | stop |
| 6 | `sabiroute-cloudflare` | 0 | OK | 1460.3 | stop |
| 7 | `sabiroute-cloudflare` | 1 | OK | 759.8 | stop |
| 8 | `sabiroute-cloudflare` | 2 | OK | 560.5 | stop |
| 9 | `sabiroute-cloudflare` | 3 | OK | 622.4 | stop |
| 10 | `sabiroute-cloudflare` | 4 | OK | 644.1 | stop |
| 11 | `sabiroute-openrouter` | 0 | OK | 2371.5 | stop |
| 12 | `sabiroute-openrouter` | 1 | EMPTY_CONTENT | 2565.5 | length |
| 13 | `sabiroute-openrouter` | 2 | EMPTY_CONTENT | 2575.4 | length |
| 14 | `sabiroute-openrouter` | 3 | EMPTY_CONTENT | 2810.0 | length |
| 15 | `sabiroute-openrouter` | 4 | EMPTY_CONTENT | 2176.3 | length |
| 16 | `sabiroute-nvidia` | 0 | OK | 3659.7 | stop |
| 17 | `sabiroute-nvidia` | 1 | OK | 582.9 | stop |
| 18 | `sabiroute-nvidia` | 2 | OK | 584.7 | stop |
| 19 | `sabiroute-nvidia` | 3 | OK | 632.7 | stop |
| 20 | `sabiroute-nvidia` | 4 | OK | 442.8 | stop |
| 21 | `sabiroute-cohere` | 0 | OK | 3836.1 | stop |
| 22 | `sabiroute-cohere` | 1 | OK | 473.4 | stop |
| 23 | `sabiroute-cohere` | 2 | OK | 478.6 | stop |
| 24 | `sabiroute-cohere` | 3 | OK | 533.1 | stop |
| 25 | `sabiroute-cohere` | 4 | OK | 873.2 | stop |
| 26 | `sabiroute-pollinations` | 0 | OK | 3468.9 | stop |
| 27 | `sabiroute-pollinations` | 1 | OK | 3452.1 | stop |
| 28 | `sabiroute-pollinations` | 2 | OK | 3302.7 | stop |
| 29 | `sabiroute-pollinations` | 3 | OK | 4010.2 | stop |
| 30 | `sabiroute-pollinations` | 4 | OK | 3349.5 | stop |

Probe file SHA-256: `fd7180734349070bb1634dd420dcf77e5aef46ab78ea1b6beeaf620fac6ade7a`.

Two real effects are visible in the data and are not artefacts:

* **Cold-connection first samples.** The first call to nvidia (3659.7 ms), cohere
  (3836.1 ms) and pollinations (3468.9 ms) — and, less sharply, cloudflare and
  groq — is much slower than the following warm calls (400–900 ms). That is a
  real TLS/connection warm-up cost per alias, now captured as latency variance
  instead of a single constant.
* **OpenRouter's four `EMPTY_CONTENT` are a budget artefact, not unreliability.**
  All four returned `finish_reason: "length"` with empty `content`: the model
  spent the entire 64-token output budget on its reasoning trace and emitted no
  answer. This probe deliberately does **not** escalate the budget (that would
  exceed the 30-call cap), so these four records must **not** be read as a 20 %
  reliability rate for OpenRouter. They are inconclusive-under-a-64-token-budget,
  and OpenRouter is excluded from reliability conclusions below.

---

## Step 2 — the harness over the 30 observations

```bash
PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
scripts/benchmark.py --measured /tmp/phase14_multi_observation.json
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

Measured source: /tmp/phase14_multi_observation.json
  sha256: fd7180734349070bb1634dd420dcf77e5aef46ab78ea1b6beeaf620fac6ade7a
  distinct observations: sabiroute-groq=5, sabiroute-cloudflare=5, sabiroute-openrouter=5, sabiroute-nvidia=5, sabiroute-cohere=5, sabiroute-pollinations=5
  observation mode: multi_observation
  note: each alias carries multiple distinct observations; they are cycled to fill the request count so N replayed requests are not N independent measurements. The per-deployment reliability and latency below are computed from the distinct real samples; the headline table is over replayed requests
Workload: 200 requests x 2 attempts, 5 warm-up observations per deployment
Candidates (6): sabiroute-groq, sabiroute-cloudflare, sabiroute-openrouter, sabiroute-nvidia, sabiroute-cohere, sabiroute-pollinations

Measured per-deployment samples (distinct real observations)
deployment             samples ok/total success_rate mean_ms p50_ms p95_ms
---------------------- ------- -------- ------------ ------- ------ ------
sabiroute-groq         5       5/5      100.0%       630.2   491.7  1084.4
sabiroute-cloudflare   5       5/5      100.0%       809.4   644.1  1320.2
sabiroute-openrouter   5       1/5      20.0%        2499.7  2565.5 2763.1
sabiroute-nvidia       5       5/5      100.0%       1180.6  584.7  3054.3
sabiroute-cohere       5       5/5      100.0%       1238.9  533.1  3243.5
sabiroute-pollinations 5       5/5      100.0%       3516.7  3452.1 3901.9

Headline comparison (latency over successful requests)
strategy requests success fallback unroutable mean_ms p50_ms p95_ms
-------- -------- ------- -------- ---------- ------- ------ ------
priority 200      100.0%  0.0%     0.0%       630.2   491.7  1187.5
measured 200      100.0%  0.0%     0.0%       630.2   491.7  1187.5

First-selection distribution
strategy deployment         count share
-------- -------------- ----- ------
priority sabiroute-groq    200   100.0%
measured sabiroute-groq    200   100.0%

Deterministic scores after the run
strategy deployment            score  success_rate mean_latency_ms samples
-------- ---------------------- ------ ------------ --------------- -------
priority sabiroute-groq        1.0000 100.0%       630.2           205
priority sabiroute-cloudflare  0.9814 100.0%       809.4           5
priority sabiroute-openrouter  0.2457 20.0%        2499.7          5
priority sabiroute-nvidia      0.9428 100.0%       1180.6          5
priority sabiroute-cohere      0.9367 100.0%       1238.9          5
priority sabiroute-pollinations 0.7000 100.0%      3516.7          5
measured sabiroute-groq        1.0000 100.0%       630.2           205
measured sabiroute-cloudflare  0.9814 100.0%       809.4           5
measured sabiroute-openrouter  0.2457 20.0%        2499.7          5
measured sabiroute-nvidia      0.9428 100.0%       1180.6          5
measured sabiroute-cohere      0.9367 100.0%       1238.9          5
measured sabiroute-pollinations 0.7000 100.0%      3516.7          5

REMINDER: outcome and latency values are MEASURED provider observations; routing decisions are simulated.
```

The JSON variant (`--json`, exit 0) confirms the routing reasons:
`priority` → `first_selection_reasons {"priority_strategy": 200}`,
`deterministic_scoring_engaged false`; `measured` →
`first_selection_reasons {"none": 200}`,
`deterministic_scoring_engaged true`; both `failed_attempts 0`,
`attempt_distribution [("sabiroute-groq", 200)]`.

What the harness now does correctly with real samples [VERIFIED BY RUNTIME]:

* **Percentiles are real, not constant.** `sabiroute-groq` p50 491.7 / p95
  1084.4; `pollinations` p50 3452.1 / p95 3901.9 — distributions over five real
  measurements, not one value repeated.
* **Reliability is a real fraction.** Five aliases are 5/5; OpenRouter is 1/5
  (but see the budget-artefact caveat above).
* **The health hard constraint still works.** OpenRouter's four consecutive
  `length` failures (records 12–15) trip the passive cooldown during warm-up, so
  the router never selects it; `attempt_distribution` contains only `sabiroute-groq`.
* **Deterministic scoring engaged** on the `measured` strategy
  (`{"none": 200}`, not a cold-start fallback), and the baseline constants were
  asserted, not assumed.

---

## Step 3 — did a genuine divergence occur?

**No. The real measurements did not diverge.** `priority` and `measured` both
selected `sabiroute-groq` 200/200 and produced identical headline rows.

The numbers that show why [VERIFIED BY RUNTIME]:

| deployment | success (5 samples) | mean latency (ms) | deterministic score | configured index |
|---|---|---:|---:|---:|
| `sabiroute-groq` | 5/5 | **630.2** (lowest) | **1.0000** (highest) | 2 (first among the six measured) |
| `sabiroute-cloudflare` | 5/5 | 809.4 | 0.9814 | 7 |
| `sabiroute-openrouter` | 1/5 (budget artefact) | 2499.7 | 0.2457 | 8 |
| `sabiroute-nvidia` | 5/5 | 1180.6 | 0.9428 | 11 |
| `sabiroute-cohere` | 5/5 | 1238.9 | 0.9367 | 12 |
| `sabiroute-pollinations` | 5/5 | 3516.7 | 0.7000 | 13 |

Groq is simultaneously (a) the first *healthy* deployment in configured order
among the measured set and (b) the highest `deterministic-v1` score — 100 %
reliable **and** the lowest mean latency (630.2 ms, ~180 ms faster than
cloudflare and ~550 ms faster than nvidia). The scoring formula gives a perfect
0.7·1.0 + 0.3·1.0 = 1.0000. When "first healthy" and "highest score" are the
same deployment, `priority` and `measured` cannot choose differently, so the
comparison has no discriminating power **on this data**.

This is not a defect in the harness. The synthetic parser-test fixture used to
validate the code path (three observations per alias, with a failure injected
*only as a parser test*) does diverge — `priority → groq`, `measured → nvidia`
— which proves the multi-observation logic *can* discriminate. But that divergence
is synthetic and is **not** Phase 14 evidence; it is reported here only to show
the code is not structurally stuck.

### Why the real data is monotone, not adversarial

Configured priority order and score order happen to agree for the reachable
set. The two deployments configured *ahead* of groq — `sabiroute-openai`
(index 0) and `sabiroute-gemini` (index 1) — are account-blocked and therefore
absent from this probe. If either were reachable and scored below groq, priority
would select it (first healthy) while measured selected groq (top score): a
genuine divergence. That is the one realistic path, and it is unavailable today.

---

## Verdict — does this close Phase 14?

**No.** It advances Phase 14 and fixes a real weakness in the first measured
run, but it does not close it.

What this run establishes:

1. **Multi-sample measured benchmarking now exists and is honest.** 30 real
   observations across six aliases; the harness reports genuine per-alias
   reliability and latency distributions and labels the mode
   (`multi_observation`). [VERIFIED BY RUNTIME]
2. **The replication weakness is gone.** Reliability and latency are no longer a
   single value cycled 200 times — the percentiles are real sample percentiles.
3. **The health hard constraint and deterministic scoring still behave correctly
   on real outcomes.**

What it does not establish:

* **That `measured` beats `priority`.** On this data they are identical, because
  the best-scoring deployment is also the earliest healthy one. This run cannot
  be quoted as evidence that either strategy is better.
* **OpenRouter's reliability.** Its four `length` outcomes are a 64-token budget
  artefact, not provider failure, and must not be counted as 20 % uptime.
* **Coverage of the eight blocked aliases** (401/402/429/503), or of the two
  aliases configured ahead of groq.

### Exactly what evidence would close Phase 14

A real measured dataset in which **the earliest healthy deployment in configured
order is not the highest deterministic-v1 score**, so the two strategies select
different deployments. Concretely, at least one of:

1. `sabiroute-openai` (index 0) or `sabiroute-gemini` (index 1) becomes reachable
   (funded/authorised) and, measured alongside the six, scores **below** groq —
   priority picks it first, measured picks groq. This is the cleanest closure and
   is blocked on account state today.
2. A later alias (`cloudflare`, `nvidia`, `cohere`, `pollinations`) is measured
   to be **faster and/or more reliable than groq** over enough samples that its
   score exceeds 1.0000-equivalent, so measured leaves groq while priority does
   not. The current five-sample means (groq 630.2 ms vs the next-best 809.4 ms)
   are far apart, so this would need many more observations or a real
   performance change.
3. Multi-round observations spaced over time (not a burst) so cooldown and
   reliability variance across minutes are exercised — the current run completes
   in milliseconds, well inside the 30-second cooldown, so recovery is untested.

Until at least one exists, Phase 14 stays **In progress**, not Complete.

---

## Reproduce (with the two traps)

```bash
# Trap 1: PYTHONPATH must point at the tree being measured, or the venv imports
# the OLD primary checkout's sabiroute. Trap 2: SABIROUTE_ENV_FILE must point at
# the credential file; no .env value is read or printed by this record.
cd "/Users/airm2/My ML Hub/SabiRoute-claude-fix"
PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
scripts/phase14_multi_observation_probe.py --samples 5 --delay 1.0 \
  --output /tmp/phase14_multi_observation.json       # 30 calls; spends credits

PYTHONPATH="/Users/airm2/My ML Hub/SabiRoute-claude-fix/src" \
"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
scripts/benchmark.py --measured /tmp/phase14_multi_observation.json
```

The benchmark replay makes **no** provider calls and spends **no** credits; only
the probe does, and it is capped at `6 x --samples` calls by construction.
