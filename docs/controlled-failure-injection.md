# Controlled failure injection — operational evidence (2026-10-11)

Scope: local, deterministic failure injection against the real SabiRoute
request path (`POST /v1/chat/completions`) using in-process ASGI tests and
stubbed provider doubles. No real provider calls, no provider spend, no
external services, no database mutation, no synthetic historical telemetry.

Evidence level: gateway-path simulation. A mocked provider failure proves
simulated handling, not real-provider behavior. Live-provider drills remain a
separate, owner-authorized activity.

Mechanism: `StubLiteLLMClient` (`tests/conftest.py`) fails the first N calls
per deployment with a configurable `failure_status`; selected tests raise
`LiteLLMClientError` (including `status_code=None` for timeouts,
`status_code=200` with a non-dict `response_body` for malformed upstream
responses) or `asyncio.CancelledError` directly. Failing stores
(`fail_usage_writes`, `fail_finalize_usage_writes`, `FailedRedis`) simulate
backend outages.

Execution-attempt accounting: SabiRoute's `LiteLLMClient` issues exactly one
raw httpx request per execution attempt (no client retries, no backoff, no
`num_retries` payload). One SabiRoute attempt therefore equals one
SabiRoute-to-proxy HTTP request. It does NOT necessarily equal one provider
attempt: the downstream LiteLLM proxy may apply its own retries/fallback per
its deployment configuration, which is invisible to SabiRoute telemetry. No
proxy retry configuration was found in this repository, and proxy-side
behavior is unverified.

Reproduce: `./.venv/bin/python -m pytest tests/test_completions.py
tests/test_phase10.py tests/test_capabilities.py tests/test_health.py
tests/test_router.py -q`

## Scenario matrix

| Scenario | Status | Evidence (test names) | Limits |
|---|---|---|---|
| Upstream HTTP 500 → fallback, then success | Covered, passing | `test_policy_request_falls_back_to_next_deployment`, `test_measured_policy_scores_and_persists_each_fallback_decision` | Simulated only |
| Upstream timeout (`status None`) → retry next | Covered, passing | `test_upstream_timeout_retries_next_deployment` (Sprint 4) | Simulated only |
| Upstream 429 → fallback, attempt recorded as `rate_limit` | Covered, passing | `test_upstream_rate_limit_falls_back_and_records_attempt` (Sprint 4) | Simulated only |
| Upstream 401/403 → fail over (provider-denied, not client-denied) | Covered, passing | `test_upstream_auth_failure_fails_over_without_client_denial` (Sprint 4) | Simulated only; failover is the documented contract (`completions.py` retry comment) |
| Client denied at SabiRoute boundary (no attempt) | Covered, passing | `test_authenticated_request_without_trusted_identity_fails_closed` | — |
| Non-retryable 400 stops the sequence | Covered, passing | `test_non_retryable_client_error_stops_retrying` | — |
| Malformed upstream 200, text body | Covered, passing | `test_malformed_upstream_text_body_fails_closed_without_retry` (Sprint 5) | 502, one attempt, `client` category, usage/cost null |
| Malformed upstream 200, list body | Covered, passing | `test_malformed_upstream_list_body_fails_closed_without_retry` (Sprint 5) | Same no-retry contract; dict-shape responses still trusted to LiteLLM normalization |
| Budget denial (missing cap, overage, store failure) | Covered, passing | `test_budget_rejects_missing_cap_multimodal_and_daily_overage`, `test_budget_reservation_store_failure_fails_before_provider_execution`, `test_token_budget_reserves_once_for_fallback_and_reconciles_actual` | Denials assert `stub.calls == []` |
| SabiRoute rate-limit denial + Redis/store outage | Covered, passing | `test_one_client_request_consumes_one_bucket_token_across_fallback`, `test_configured_rate_limit_fails_closed_when_redis_is_unavailable`, `test_usage_store_failure_rejects_before_provider_execution` | Redis atomicity is code-inspected, not integration-tested |
| No capable / no healthy deployment → 503, zero attempts | Covered, passing | `test_current_unannotated_config_stays_unknown_and_fails_explicitly`, `test_all_unhealthy_candidates_rejected_before_provider_execution` (Sprint 4) | Simulated only |
| Fallback exhaustion → 502, finalized history | Covered, passing | `test_policy_exhaustion_fails_closed_with_finalized_telemetry` (must keep passing) | Simulated only |
| Client cancellation (non-stream + streaming) | Covered, passing | `test_non_stream_cancellation_finalizes_an_interrupted_attempt`, `test_stream_cancellation_before_first_frame_finalizes_attempt`, `test_stream_cancellation_after_partial_delivery_is_recorded_as_client_cancel` | 499 + `client_cancelled`, distinct from provider failure |
| Streaming failure before/after first chunk | Covered, passing | `test_streaming_falls_back_only_before_first_event`, `test_streaming_failure_after_first_event_is_not_replayed` | — |
| Telemetry finalization failure | Covered, passing | `test_stream_finalization_failure_is_logged_and_remains_unfinalized`, `test_non_stream_finalization_failure_returns_unavailable_and_stays_unfinalized` | Unfinalized stays auditable (`final_status is None`), never fabricated |
| Concurrent/distributed rate-limit correctness | Not covered — infrastructure-gated | `RedisTokenBucket` is a server-side Lua script (atomic by design); no local Redis here | Requires Redis + owner approval; in-memory tests must not claim distributed safety |
| Real-provider failure drills | Blocked — owner authorization | Needs spend scope, credentials, and explicit approval | See Handoff: no live failure-injection evidence to date |

## Confirmed defects and fixes (Sprint 4)

No production-code defect was confirmed. Three new gateway-path tests plus one
eligibility test were added for genuine coverage gaps; two test-authoring
errors during the sprint (wrong attempt-event key `deployment` vs
`selected_deployment`; wrong assumption that policy `fast` spans only
primary/secondary) were diagnosed against the implementation and corrected in
the tests — production behavior was correct in both cases.

## Unresolved risks

- Upstream 401/403 failover is intended but masks per-provider credential
  rot: a globally misconfigured credential burns all attempts (bounded by
  `max_attempts`) before surfacing; alerting on repeated attempt-level `auth`
  failures is operational future work.
- Attempt-level `rate_limit` (upstream) vs request-level `rate_limited`
  (SabiRoute) share a naming family; they are distinct values on distinct
  records, but dashboards must not conflate them.
- Malformed-200 handling (fail-closed, no retry) awaits an owner contract
  decision.
