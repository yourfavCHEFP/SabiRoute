# Phase 05 — real-provider fallback proof

**Date:** 2026-11-23 · **Verdict:** PASS · **Phase 05 status:** Complete

This closes the one gap the previous Phase 05 evidence left open. The earlier
harness (`scripts/phase05_fallback_injection.py`) proved the fallback state
machine by driving a controllable stub — real code, real sockets, real proxy,
but a provider that was told to fail. That established *the code branches
correctly*. It could not establish *a real provider's real failure produces a
real fallback*, because nothing real ever failed.

This run has no stub anywhere in the path.

```
SabiRoute  ->  LiteLLM Proxy  ->  primary    openai/gpt-6-luna
                              ->  secondary  nvidia_nim/nvidia/nemotron-3.5-bolt-e4b
```

Both legs are real HTTPS calls to real providers carrying real credentials.

## Reproduce

```
SABIROUTE_ENV_FILE=/Users/airm2/My ML Hub/SabiRoute/.env \
PYTHONPATH=/Users/airm2/My ML Hub/SabiRoute-claude-fix/src \
  /Users/airm2/My ML Hub/SabiRoute/.venv/bin/python \
  scripts/phase05_real_provider_failure.py
```

The `PYTHONPATH` pin is not cosmetic. The venv resolves `sabiroute` to the
**primary checkout**, which sits on `feat/sabiroute-routing-foundation` — the
pre-rewrite lineage. Without the pin this harness would silently measure a
different codebase than the one being pushed.

## Result [VERIFIED BY RUNTIME]

```
verdict            PASS
status             200
elapsed_ms         2483.9
content_preview    "OK"

checks
  status_200                  true
  non_empty_text              true
  primary_recorded_failure    true
  secondary_recorded_success  true
  primary_never_succeeded     true

health.primary    total_failures 1   total_successes 0
health.secondary  total_successes 1  total_failures 0
```

`primary_never_succeeded` is the load-bearing check. It rules out the reading
"the answer came from the primary and the log is decoration." The successful
content can only have come from the secondary.

## The premise check, and why it exists

A "fallback worked" claim is worthless if nothing failed. The harness therefore
refuses to pass on a run where the primary answered, and says so:

| Verdict | Meaning | Exit |
|---|---|---|
| `PASS` | primary failed, failover happened, secondary answered | 0 |
| `PREMISE_NOT_MET` | primary answered — no failure, so no fallback claim is warranted | 2 |
| `PREMISE_UNREACHABLE` | neither failure nor success recorded against primary | 3 |
| `ENVIRONMENT` | credentials absent or the proxy never started | 3 |

`PREMISE_NOT_MET` is deliberately not exit 0. A green result that means
"nothing was tested" is how false confidence enters a project.

## What it took — six iterations, five falsified hypotheses

Each of these is a real behaviour, not a setup mistake, and each cost a run.

**1. An invalid API key cannot be used as a retryable fault.** [VERIFIED BY
RUNTIME] Gemini answers a deliberately invalid key with **HTTP 400**
`INVALID_ARGUMENT`, not 401. SabiRoute's `RETRYABLE_STATUS_CODES` is
`{401, 403, 429}` plus anything `>= 500`, so a 400 would have produced *no
fallback* — a test that looks like a failure and proves nothing.

**2. A retired model id cannot be used either.** A 404 is likewise outside the
retryable set. This was already known from the stub matrix (scenario
`D_non_retryable_404_stops`) and is why the original plan named it.

**3. A proxy-side timeout is `408`, which is NOT retryable.** [VERIFIED BY
RUNTIME] With `gemini` as primary and a 60s proxy `request_timeout`, the request
took 60.6s and produced `attempts: ["primary"]` — the engine stopped without
trying the secondary. SabiRoute was correct to stop; `408` is not in the
retryable set. **This is a real trap: a slow provider consumes the budget and
suppresses failover, and it presents as "fallback is broken."** It is not.
Recording it here so the next person does not diagnose it from scratch.

**4. Deployment names and proxy model names share one namespace.** When
SabiRoute's deployment name did not match the proxy's `model_name`, the request
failed in **79 ms** with the primary marked failed and the secondary never
attempted. A 79ms failure is the tell: no provider was ever reached.

**5. `docs/providers.md` carried a stale nvidia model id.** The document said
`nvidia_nim/meta/llama3-70b-instruct`; the config actually loads
`nvidia_nim/nvidia/nemotron-3.5-bolt-e4b`. The documented value returns a real
provider 404. Corrected in that file today.

**6. OpenRouter is not a usable secondary.** It returns 200 with **empty
assistant text** at small `max_tokens`, and **HTTP 402** once a request asks for
a real completion. HTTP 200 with empty content is not a working alias, and
SabiRoute rightly counts it as a failed attempt.

## What this does and does not prove

**Proved:** a genuine provider-returned retryable failure (HTTP 429 from OpenAI)
on the primary deployment caused SabiRoute to attempt the secondary deployment,
which answered through a real provider with real non-empty content, and the
health registry recorded exactly that.

**Not proved, and not claimed:**

- That fallback recovers from a *provider outage* (5xx) rather than a quota
  rejection. 429 and 5xx are both in the retryable set, so the branch is the
  same, but this run exercised 429 only. The stub matrix covers 500, and that is
  stub evidence.
- That fallback works when *every* candidate is unhealthy. The stub matrix
  covers it (`F_all_candidates_fail_is_classified`); no real run does.
- That streaming fallback works against a real provider. Stub only
  (`G_streaming_failure_falls_back`).
- Anything about cooldown or half-open recovery against a real provider. The
  stub runs cover it, and the `cooldown_until = None` permanence trap recorded
  in the current-state document still stands.

Phase 05's own definition of Complete is implemented + tested + live-verified.
Implementation and tests were already in place; this run supplies the live leg.
