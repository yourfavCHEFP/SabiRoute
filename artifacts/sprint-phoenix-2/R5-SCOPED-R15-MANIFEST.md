# R5 — Scoped R15 Manifest

**Reconstructed:** 2026-11-18 on `sec/deps-nov` @ `fb7583b` (verified by `git branch --show-current` and `git rev-parse --short HEAD`).
**Purpose:** replace the scorecard note at `reports/my_scorecard.md:90` — "scoped-R15 manifest still to reconstruct" — with an exact, evidence-labelled manifest.
**Authority:** documentation/reconstruction only. No production code, tests, scorecard, configuration, dependencies, protected paths, commits, pushes, or live provider calls were changed or made.
**Scope discipline:** one new file only. This report supersedes no existing document; the parent is expected to reference it from `reports/my_scorecard.md`. A new file was required because no scoped-R15 manifest existed in `docs/`, `reports/`, or `artifacts/` (repository-wide `rg -n -i 'R15|scoped-R15' docs reports artifacts --glob '*.md' --glob '*.txt'` returned only the two source statements listed below).

Evidence labels used here are those required by `CLAUDE.md` §2: **VERIFIED BY INSPECTION**, **VERIFIED BY RUNTIME**, **STATIC-ANALYSIS FINDING**, **INFERRED**, **UNVERIFIED**.

---

## 1. Claim under reconstruction

| Source | Exact location | Text / status |
|---|---|---|
| R6 decision campaign | `docs/r6-decision-resolution-and-approval-campaign.md:83` | R15: "Provider boundary is OpenAI chat-completions only, so the Anthropic path is never exercised"; source class "Assumption — `litellm_client.py` posts to `/v1/chat/completions`"; status "**Assumed, not proven** for every future client path" |
| Scorecard | `reports/my_scorecard.md:90` | R5 row: "Live failure-injection (env-gated); scoped-R15 manifest still to reconstruct" |
| Controlled-injection evidence | `docs/controlled-failure-injection.md:3–10` | Scope is local in-process ASGI + stub doubles; "A mocked provider failure proves simulated handling, not real-provider behavior. Live-provider drills remain a separate, owner-authorized activity." |
| Runbook | `docs/failure-injection-runbook.md:71–76` | "Live failure-injection evidence is **not** yet captured in this repository"; execution requires an injectable provider/stub and is gated on environment availability |

**VERIFIED BY INSPECTION:** both source statements are present exactly at the cited lines in the current tree.
**STATIC-ANALYSIS FINDING:** `docs/failure-injection-runbook.md` is stale in two places: `:10` names `src/sabiroute/routing/fallback.py` / `FallbackEngine`, and `:79` names `providers/healthcheck.py`; neither artefact exists in this repository. `CLAUDE.md` §12 explicitly records their absence. Do not use those two references as current-code evidence. The runbook's limitation at `:71–76` remains accurate and is retained as the live-evidence blocker.

---

## 2. Scoped R15 statement

**VERIFIED BY INSPECTION (current code path only):** SabiRoute's sole execution boundary to LiteLLM is an OpenAI-compatible HTTP `POST {base_url}/v1/chat/completions`. There is no SabiRoute-side Anthropic client branch, no Anthropic Messages endpoint call, and no Anthropic-specific transform/bypass branch in the runtime request path. The R15 phrase "so the Anthropic path is never exercised" is true only in this narrow sense: no Anthropic-specific *SabiRoute client path* exists today.

**UNVERIFIED / ASSUMED (future-client-path universality):** the stronger claim — that every future client path will remain OpenAI-chat-completions-only, therefore an Anthropic path can never be exercised — is **not proven**. R15 itself labels this "Assumed, not proven for every future client path" (`docs/r6-decision-resolution-and-approval-campaign.md:83`). This manifest does not upgrade it.

**INFERRED:** downstream LiteLLM may still route an OpenAI-compatible request to an Anthropic provider adapter inside the proxy. That downstream execution is outside SabiRoute's code boundary and was not observed here. Model/provider diversity in `config/config.yaml` does not create a second SabiRoute client path.

---

## 3. Current code path — exact files and lines

### 3.1 The client

**VERIFIED BY INSPECTION:**

| Location | Fact |
|---|---|
| `src/sabiroute/providers/litellm_client.py:53–59` | `LiteLLMClient` describes itself as the SabiRoute → LiteLLM boundary; LiteLLM owns provider execution, retries, cooldowns, load balancing and fallbacks |
| `src/sabiroute/providers/litellm_client.py:63–69` | `base_url` defaults to `http://127.0.0.1:4000`; optional API key and `httpx.Timeout` are stored |
| `src/sabiroute/providers/litellm_client.py:71–90` | Non-streaming payload: `{"model": decision.deployment, "messages": list(messages), **extra}`, plus optional `temperature` / `max_tokens` |
| `src/sabiroute/providers/litellm_client.py:92–103` | Headers and `POST` to `f"{self.base_url}/v1/chat/completions"` |
| `src/sabiroute/providers/litellm_client.py:104–131` | Timeout/transport/HTTP-status/non-dict-body failures normalized to `LiteLLMClientError` |
| `src/sabiroute/providers/litellm_client.py:133–162` | Streaming payload and `client.build_request("POST", f"{self.base_url}/v1/chat/completions", ...)`; `stream=True` |
| `src/sabiroute/providers/litellm_client.py:163–195` | Streaming error normalization, event-stream content-type check, cleanup paths |
| `src/sabiroute/gateway.py:150–159` | Real client is constructed from `SABIROUTE_LITELLM_URL` (blank → default proxy URL), `LITELLM_MASTER_KEY`, and `litellm_settings.request_timeout` |
| `src/sabiroute/gateway.py:283` | `empty_gateway_state()` uses `LiteLLMClient()` with the same default path when no client is injected |

**VERIFIED BY INSPECTION:** repository-wide search for direct Anthropic markers over `src/sabiroute` and `config` (`rg -n -i 'anthropic|/v1/messages|chat/completions|LITELLM|base_url'`) found no Anthropic API client and no `/v1/messages` call in runtime source. The only `anthropic` hits outside configuration comments were descriptive comments in `src/sabiroute/request_transform/compression.py:3,8` (stub/retrieval rationale and `cache_control` preservation).

### 3.2 Invocation sites

**VERIFIED BY INSPECTION:** `rg -n '\.chat_completion\(|\.start_chat_completion_stream\(' src/sabiroute` returned exactly two production call sites:

- `src/sabiroute/api/completions.py:1559–1565` — streaming path: `state.client.start_chat_completion_stream(route_decision, attempt_messages, ...)`.
- `src/sabiroute/api/completions.py:1578–1584` — non-streaming path: `state.client.chat_completion(route_decision, attempt_messages, ...)`.

`src/sabiroute/api/chat.py:195–199` calls SabiRoute's own in-process `/v1/chat/completions` ASGI path; it does not open a second LiteLLM or Anthropic client.

### 3.3 Config wiring

**VERIFIED BY INSPECTION:**

| Location | Fact |
|---|---|
| `config/config.yaml:1–14` | Config rules: credentials come from environment variables; `model_name` is SabiRoute's public alias; `litellm_params.model` is the actual LiteLLM provider route |
| `config/config.yaml:16,22–25` | Runtime `model_list` begins with public alias `sabiroute-openai` → `openai/gpt-6-luna`; credentials are `os.environ/...` references |
| `config/config.yaml:257–267` | `litellm_settings.request_timeout: 120`, `drop_params: true`, `set_verbose: false` |
| `config/config.yaml:277–281` | `general_settings.master_key: os.environ/LITELLM_MASTER_KEY` — variable reference only, no key value |
| `config/models/anthropic.yaml:1` | The Anthropic catalogue file contains only `model_list: []`; it is not a runtime SabiRoute client and declares no deployment. `src/sabiroute/config/loader.py:16` sets the default runtime config to `config/config.yaml`, not `config/models/*.yaml` |
| `config/config.yaml:242–252` | Qoder is explicitly on HOLD; the "Anthropic-compatible endpoint" text is a future integration note, not a wired route |
| `tests/conftest.py:328–371` | Offline `make_config()` builds an in-memory config with `openai/gpt-4o-mini`, `groq/llama-3.1-8b-instant`, `cloudflare/...`, `together/...` deployments |

**STATIC-ANALYSIS FINDING:** changing `litellm_params.model` to an `anthropic/...` route would not change the SabiRoute-side URL — it would still be the single OpenAI-compatible proxy endpoint — but no such runtime route was executed or verified here. This is exactly why the universal form of R15 remains assumed.

### 3.4 Transform placement relative to the boundary

**VERIFIED BY INSPECTION:** `src/sabiroute/api/completions.py:1368–1382` places `run_transform(...)` after admission and before the retry loop; `:1384` begins `for attempt in range(1, policy.max_attempts + 1)`; the two provider invocations are at `:1559` and `:1578`. Failures in the transform degrade to the original messages before any provider call.

**INFERRED:** because the transformed list is computed once before the loop and both provider call sites consume `attempt_messages`, a fallback attempt reuses the same effective request. This is separately pinned by `tests/test_r6_request_transform.py:850–890`.

---

## 4. Offline failure-injection and recovery coverage

All tests below use `StubLiteLLMClient` (`tests/conftest.py:374–440`) or in-memory/disposable stores; they exercise SabiRoute orchestration, not a live provider.

### 4.1 Fallback injection — `tests/test_fallback_injection.py`

**VERIFIED BY RUNTIME (this manifest's run):** 6 tests passed, 0 failed, 0 skipped.

| Test (line) | Offline fact covered |
|---|---|
| `test_retryable_primary_failure_falls_back` (`:21`) | first-call 500 on `primary` → success on `secondary`; both deployments recorded |
| `test_non_retryable_400_does_not_fallback` (`:36`) | 400 stops retry; only `primary` invoked |
| `test_all_deployments_fail_terminal_error` (`:49`) | all candidates fail → 502 with both attempts in the error body |
| `test_deadline_expired_prevents_invocation` (`:63`) | expired deadline → 503, zero provider calls |
| `test_cancellation_propagates_no_fallback` (`:80`) | `CancelledError` → one attempt, no health poisoning, `client_cancelled` telemetry |
| `test_cooldown_excludes_failed_deployment` (`:119`) | after three failures, `primary` is excluded from the fourth request |

### 4.2 Recovery / shutdown — `tests/test_recovery_shutdown.py`

**VERIFIED BY RUNTIME (this manifest's run):** 4 tests passed, 0 failed, 0 skipped.

| Test (line) | Offline fact covered |
|---|---|
| `test_persistence_failure_fails_closed_without_success` (`:30`) | finalize-store failure → 503, no fabricated success |
| `test_feature_snapshot_failure_blocks_before_provider_call` (`:42`) | snapshot-write failure → 503 and `stub.calls == []` |
| `test_startup_shutdown_purge_failure_does_not_break_lifespan` (`:53`) | purge failure does not break lifespan |
| `test_executor_capacity_recovers_after_failures` (`:91`) | executor slot restored after worker exception; subsequent work succeeds |

### 4.3 Request-transform bypass / error path — `tests/test_r6_request_transform.py`

**VERIFIED BY RUNTIME (this manifest's run):** 65 tests passed, 0 failed, 0 skipped. Directly relevant anchors:

- `:351` `test_i9_returns_the_original_on_exception`; `:363` `test_i9_does_not_swallow_cancelled_error`.
- `:376–433` R6.4 protection tests for system/last-user/last-assistant, cache breakpoint, tool spans, cached prefix and JSON validity.
- `:510` expanding transform degrades to original; `:531` byte-budget gate is wired into the pipeline; `:558` I9 call-site window; `:584` and `:605` latency-budget degradation including bypass/freeze.
- `:647` disabled policy sends byte-identical messages; `:694` capability loss degrades to original; `:717` compressor exception leaves the original intact with `fallback_reason == "transform_error"`.
- `:792` call site reached with disabled default and identical bytes; `:815` enabled policy reaches the provider with fewer messages; `:850` transform runs once across a fallback.

**STATIC-ANALYSIS FINDING:** these tests stub `LiteLLMClient`; they prove the request path and degrade/bypass behaviour locally. They do not prove a real proxy request or a real provider response.

---

## 5. Executed local commands and exact outputs

All commands were run from `/Users/airm2/My ML Hub/SabiRoute` with `./.venv/bin/python`. No live provider calls, managed services, credentials, or protected paths were used. Timings are the observed run values and may vary.

### 5.1 Focused fallback + recovery

```
$ ./.venv/bin/python -m pytest tests/test_fallback_injection.py tests/test_recovery_shutdown.py -q; echo "EXIT=$?"
.......... [100%]
10 passed in 0.45s
EXIT=0
```

**VERIFIED BY RUNTIME:** exit 0; 10 passed, 0 failed, 0 skipped.

### 5.2 Request-transform suite

```
$ ./.venv/bin/python -m pytest tests/test_r6_request_transform.py -q; echo "EXIT=$?"
................................................................. [100%]
65 passed in 0.67s
EXIT=0
```

**VERIFIED BY RUNTIME:** exit 0; 65 passed, 0 failed, 0 skipped.

### 5.3 Combined deterministic local gate

```
$ ./.venv/bin/python -m pytest tests/test_fallback_injection.py tests/test_recovery_shutdown.py tests/test_r6_request_transform.py -q; echo "EXIT=$?"
........................................................................ [ 96%]
... [100%]
75 passed in 0.54s
EXIT=0
```

**VERIFIED BY RUNTIME:** exit 0; 75 passed, 0 failed, 0 skipped.

### 5.4 Reproduction command published in `docs/controlled-failure-injection.md:29–31`

```
$ ./.venv/bin/python -m pytest tests/test_completions.py tests/test_phase10.py tests/test_capabilities.py tests/test_health.py tests/test_router.py -q; echo "EXIT=$?"
........................................................................ [ 74%]
......................... [100%]
97 passed in 0.83s
EXIT=0
```

**VERIFIED BY RUNTIME:** exit 0; 97 passed, 0 failed, 0 skipped.

---

## 6. Status and residual blockers

| Item | Status | Evidence label / reason |
|---|---|---|
| Scoped R15 manifest reconstructed | **DONE — local scope** | VERIFIED BY RUNTIME (four commands above) + VERIFIED BY INSPECTION (code/config lines above) |
| Current SabiRoute client boundary is OpenAI-compatible `/v1/chat/completions` | **DONE for current code** | VERIFIED BY INSPECTION (`litellm_client.py:96,159`; two production call sites only) |
| Offline fallback / recovery / transform degradation | **DONE — unit-tested** | VERIFIED BY RUNTIME (75/75 combined) |
| Live failure injection against real providers | **NOT DONE — BLOCKED** | `docs/controlled-failure-injection.md:8–10,53`; `docs/failure-injection-runbook.md:71–76`; `reports/my_scorecard.md:90`. Requires owner authorization, spend scope and credentials; no live call was made here |
| R15 universality for all future client paths | **ASSUMED, NOT PROVEN** | `docs/r6-decision-resolution-and-approval-campaign.md:83`; no code test can prove a future path that does not exist |
| Real HTTP URL / real proxy response observed | **NOT DONE** | STATIC-ANALYSIS FINDING only; offline suites use `StubLiteLLMClient` (`tests/conftest.py:374–440`) |
| Redis/PG/env-gated live persistence paths | **NOT DONE in this run** | No services were started; no `SABIROUTE_TEST_REDIS_URL` / `SABIROUTE_TEST_PG_URL` evidence was captured |
| Multi-worker / downstream proxy retries | **UNVERIFIED** | `docs/controlled-failure-injection.md:20–27` records proxy retry behaviour as invisible to SabiRoute telemetry |
| Stale runbook artefact names | **DOCUMENTATION DEBT — reported, not edited** | `docs/failure-injection-runbook.md:10,77–79`; `CLAUDE.md` §12 governs current code facts; this manifest changes no other file |

**Explicit non-upgrade:** live failure injection remains **BLOCKED / NOT DONE**. This manifest reconstructs the scoped local evidence only; it does not close R5's live-provider row, does not authorize provider calls, and does not mark R15 complete beyond the current code path.

---

## 7. Architectural position

`Client → SabiRoute API → Auth/Policy → Classification → Capability Filter → Health Filter → Routing Engine → Fallback → LiteLLM → Provider → Response`

**VERIFIED BY INSPECTION:** this manifest documents the `Fallback → LiteLLM` seam and the transform step immediately before it. It does not add code to any stage. PostgreSQL, Redis, telemetry and security behaviour are unchanged; the only observed effects are local test executions using in-memory stores and stub clients. Future intelligence is unaffected — no ML routing or dataset change is implied.

**ROADMAP POSITION (INFERRED):** maintenance/evidence reconstruction for R5 within the R1–R8 integration lane; it prepares a future live matrix but does not advance R9–R20 and does not unlock any gated phase.

**DO NOT TOUCH YET (per `CLAUDE.md`):** zero-byte placeholder modules, `uv.lock`, `.env`, `.github/**`, `.mcp.json`, `.claude/**`, `reports/provider_verification.json`; no commit, push, branch switch, merge, rebase, reset or history rewrite was performed.
