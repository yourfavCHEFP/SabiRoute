# Local Incident-Response Runbook

**Status:** local-only triage guide. This is **not production verification**. It
does not prove managed PostgreSQL/TLS, managed backup/restore, hosted CI, staging
deployment, live provider behavior, or rollback under production load. It changes
no code, configuration, credentials, or acceptance gate.

**Anchors:** `docs/deployment.md:26-43,57-143`;
`src/sabiroute/api/health.py:21-87`; `src/sabiroute/main.py:87-132`;
`src/sabiroute/security/auth.py:18-123`; `src/sabiroute/api/completions.py:198-207,864-903,2010-2040`;
`src/sabiroute/security/redaction.py:1-23`;
`docs/failure-injection-runbook.md:62-87`. `[VERIFIED BY INSPECTION]`

## 1. Readiness 503

1. Identify the topology first: host-run versus Compose addresses differ
   (`docs/deployment.md:1-24`).
2. Probe the readiness endpoint, for example
   `curl -sS -i http://127.0.0.1:8000/health/ready` with the host port replaced
   as needed.
3. `GET /health/ready` returns HTTP 200 with `status: ready` only when startup,
   registry, and key-store checks pass. On failure it returns HTTP 503 with
   `status: not_ready`, a `failing` list, and `components` for `startup`,
   `registry`, `key_store`, and `rate_limiter`. When a chat store is configured,
 a post-startup chat-store schema recheck failure also adds `chat_store` to
 both `failing` and `components`.
4. Do not route traffic to a `not_ready` instance. `GET /health/live` only proves
   the process is alive and is not a deployment gate. `rate_limiter: absent` is
   informational when no per-key limiter is configured; readiness does not probe
   Redis on every call. `[VERIFIED BY INSPECTION]`

## 2. Startup and schema failure

- Schema changes are never performed by startup or a store constructor. They are
  applied by the explicit migration `./.venv/bin/python -m sabiroute.migrate`,
  using `DATABASE_URL` or `SABIROUTE_DATABASE_URL`.
- Migration exit statuses: `0` schema present and valid; `1` migration failed and
  rolled back; `2` no database URL configured. Confirm the database target before
  running any migration; never run it against an unidentified target.
- In Compose, the one-shot migration service must complete successfully before
  the API starts. For a host process or standalone container, migrate first.
- Startup construction failure (including the startup-time schema check): the
  exception is passed through `redact_secrets`, stored as `startup_error`, and
  the key/chat stores are set to `None`. Liveness may remain up while readiness
  reports 503 and completions fail closed with the startup error. This state is
 sticky by design: treat it as a real startup/schema/connectivity failure, not
  a transient ready state to retry around.
- Post-startup defensive read-only schema recheck failure: `GET /health/ready`
 performs this check on each probe. A failure is response-local only; it does
 not set `startup_error` and does not null the stores. A key-store recheck
 failure adds `key_store` to `failing`/`components`; a configured chat-store
 recheck failure adds `chat_store` to both. The current probe returns
 HTTP 503, but a later probe may return 200 once the checks pass. A persistent
 failure fails every readiness probe and must be triaged rather than routed
 around.
- Managed-PostgreSQL upgrade and backup validation remain outstanding. Do not
  infer them from a local disposable-database result. `[VERIFIED BY INSPECTION]`

## 3. Authentication and store 503

- `401` with `type: authentication_error` means an invalid bearer credential.
- `503` with `type: authentication_unavailable` means the client key store is
  absent or a store lookup faulted; the auth path fails closed. For the admin
  boundary it also covers an unconfigured or disallowed administrative secret.
- In the completion path, distinguish store-outage responses such as
  `usage_store_unavailable`, `budget_store_unavailable`, and
  `telemetry_store_unavailable` from invalid credentials. They are accounting
  failures, not evidence that the caller's key is wrong.
- Do not rotate keys, edit `.env`, or infer a live credential value during triage.
  Report only variable names and set/empty status. `[VERIFIED BY INSPECTION]`

## 4. Redis / rate-limit 503

- With no configured per-key rate limit, the gateway can serve without a limiter
  and readiness reports `rate_limiter: absent`.
- With a configured limit but no limiter, or an exception from `admit`, the
  completion path returns HTTP 503 `rate_limiter_unavailable` and records
  `failure_category: redis_unavailable`. This is fail-closed admission, not
  silent allowance.
- HTTP 429 `rate_limit_exceeded` with `Retry-After` means the limit was actually
  exceeded; it is not a Redis outage.
- Durable state lives in PostgreSQL, not Redis. Do not convert Redis loss into a
  claim of data loss. `[VERIFIED BY INSPECTION]`

## 5. Provider-failure classification

- Classify before changing anything: model unavailable, route unavailable,
  provider unavailable, account/credit problem, authentication failure, rate
  limit, timeout, network failure, configuration error, LiteLLM execution
  failure, or SabiRoute failure.
- The completion path maps a provider exception without a status to `timeout`
  or `transport`; `401`/`403` to `auth`; `429` to `rate_limit`; `>=500` to
  `server`; and other statuses to `client`.
- Exhausted attempts return HTTP 502 `sabiroute_upstream_error` with the last
  classified `failure_category`; a processing-deadline expiry returns HTTP 503
  `deadline_exceeded`. A provider failure must not become an unexplained global
  error. Do not label a classified client/auth error as an outage.
- Cooldown is passive and lives in `routing/health.py`; no active provider health
  checker is wired. Live failure-injection evidence is absent. Use
  `docs/failure-injection-runbook.md` for the local stub procedure and keep its
  `UNVERIFIED` status intact. `[VERIFIED BY INSPECTION]`

## 6. Rollback

- Rollback is image-tag based: run the previously verified image while retaining
  its tag until the new revision is verified against `/health/ready`.
- Schema revisions are additive-only; do not migrate down or delete columns to
  force a rollback. A previous image is expected to ignore newer nullable
  columns.
- Restore local configuration only from an identified, pre-existing local source.
  Do not amend, reset, rebase, cherry-pick, or force-push to effect a rollback.
  `[VERIFIED BY INSPECTION]`

## 7. Evidence capture

Capture, with timestamps and the applicable evidence label:

- exact command, topology, and environment variable **names**, never values;
- the full sanitized `/health/ready` JSON and the HTTP status;
- `X-SabiRoute-Request-ID` from the response, plus correlated decision, attempt,
  and final-outcome records where available;
- migration exit code, failing component list, and classified `failure_category`;
- pass/fail per triage step and any command output needed to reproduce it.

Do not retain prompt contents in routine telemetry. If a payload snapshot is
genuinely needed, sanitize it first and record why. Local replay records are not
live-provider or production evidence. `[VERIFIED BY INSPECTION]`

## 8. Secret redaction

- `redact_secrets` masks recognized carriers: URI userinfo passwords, `Bearer`
  tokens, `sr_live_`/`sr_test_` client keys, and `sk-` provider key shapes.
- It is pattern-based. A secret in another shape, such as a bare password quoted
  in prose, is not masked. When a zero-leak guarantee is required, log only the
  exception class name.
- Never paste `.env` contents, authorization headers, DSNs, API keys, or live
  provider responses into evidence. Credential reporting is limited to variable
  names and set/empty status. `[VERIFIED BY INSPECTION]`

## 9. Gate boundary

This runbook supports local triage only. It does not close S6, S9, S13, S17, or
S18; does not authorize live provider calls, spend, managed services, staging, or
production deployment; and does not change dataset integrity, training readiness,
or any registration decision. `[VERIFIED BY INSPECTION]`
