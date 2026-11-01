# Sprint 0.2B+ unattended work — core release progress (2026-10-18)

Branch: `feat/sabiroute-routing-foundation`. HEAD unchanged: `3030327`
(`73c963b`, 13-path core tree). No commits, no pushes, no index mutations
beyond the pre-existing staged set. All changes below are unstaged
worktree edits, verified with focused tests.

## 1. CI workflow / contract gap (structural, documented — no code change)

- Verified: the staged `.github/workflows/ci.yml` (57 lines) and the
  `test_ci_workflow_is_valid_and_secret_free` contract test (which reads
  the file from the repo root) agree with each other — no drift.
- The hosted gap is structural, not a content defect: published HEAD
  (`73c963b`, 13 paths) contains no `.github/` directory, so GitHub
  cannot trigger CI on that commit. No local edit can fix this; the fix
  is a future authorized commit that adds the workflow file (and the
  `docker build` context it needs) on top of the core tree.
- No change made. Do not claim hosted CI passes.

## 2. Identity-test separation (analysis complete, no file edits)

`tests/test_identity_propagation.py` (15 defs / 19 collected cases —
one `parametrize` expands ×5):

- 14 tests are core: gateway-only identity accept/attest, distinct
  users, concurrency isolation, forged-field/header/metadata rejection,
  unmarked-request handling, missing/invalid-field rejection,
  unauthenticated denial, retry preservation, no LiteLLM leakage,
  usage-source invariance. Result: **18 passed, 1 deselected** (core only).
- 1 test is SabiChat-product: `test_chat_round_trip_still_succeeds`
  (needs `/v1/auth/register` + `/v1/conversations`, absent by design in
  the core app — 404s as intended). Excluded from the core set;
  preserved unchanged for the SabiChat workstream.
- Recommended follow-up (separate authorization): split into
  `test_identity_propagation_core.py` (14 tests, core CI) and a product
  file holding the round-trip test. Not done here — splitting test files
  is a scope decision for the owner, and the current single file is
  coherent as staged.

## 3. F-04 docs/OpenAPI — assessed, no change (owner decision required)

- `create_app` builds `FastAPI(...)` with no `docs_url`/`redoc_url`/
  `openapi_url` overrides → docs, redoc, and openapi.json are served at
  defaults. `docs/security.md:8` documents this as intentional.
- Changing the default (disable in prod, keep in dev) is a product
  decision with routing/client implications, not a safe unattended edit.
  Left OPEN with this evidence. No code touched.

## 4. F-05 request/message size limits — assessed, partially covered

- SabiChat product surface already bounds user content:
  `MAX_CONTENT_CHARS = 8000`, `MAX_TITLE_CHARS = 120`,
  `MAX_MODEL_CHARS = 256` (`api/chat.py`), enforced via pydantic
  `Field(min_length=1, max_length=...)`; completions model requires
  non-empty `model`/`messages`.
- Core gateway `/v1/chat/completions` accepts OpenAI-compatible bodies
  with `extra="allow"` and no byte cap — by OpenAI-compat design, but no
  documented transport ceiling was found in-repo (uvicorn defaults
  apply). Setting a global cap risks breaking legitimate large-context
  requests and needs owner/product input.
- Left OPEN: product surface bounded; core transport ceiling undecided.
  No code touched.

## 5. F-06 config/API-key handling — verified sound, no change needed

- All shipped `config/config.yaml` credentials use `os.environ/NAME`
  references (verified: every `api_key:` line is an env reference);
  `_resolve_os_environ_value` raises `ConfigLoadError` on missing vars.
  `auth.py` returns generic 401 `Invalid bearer credential` with no key
  material. No literal-secret default found in code or config.
- Closed by evidence (no policy violation found). No code touched.

## 6. F-07 session expiry/cleanup — mechanism exists, no scheduler

- Enforcement present: `require_chat_session` rejects missing/expired/
  revoked sessions; `revoke_session` / `revoke_user_sessions` exist;
  `purge_expired_sessions()` (bounded `delete ... where expires_at <
  cutoff`, returns count, re-runnable) exists and is unit-tested
  (`test_purge_expired_sessions`, `test_expired_session_rejected`
  pass in the SabiChat suite context).
- Gap: no caller wires the purge into any startup/scheduler/cron path
  (grep: zero callers outside the store + tests). Wiring a scheduler is
  an ops decision (cadence, locking, observability) — documented here,
  not implemented. F-07 stays OPEN pending an owner-approved purge
  cadence. No code touched.

## 7. F-08 distributed rate limiting — documented as designed

- Core gateway: Redis Lua token bucket (`RedisTokenBucket`, server-side
  time, no client clock trust) with explicit fail-closed 503s when
  Redis/config is unavailable (`completions.py:728-743`).
- SabiChat product surface additionally documents in-process fixed
  windows as single-process (`api/chat.py:24-25`, "Redis-backed global
  limiting is a Sprint 5 concern").
- Design matches the documented constraint (single-process product
  limits + Redis-backed core limits). Multi-instance global guarantees
  remain an open deployment question, not a code defect found here.
  F-08 stays OPEN pending a deployment-topology decision. No code touched.

## 8. Salt-key rotation plan — NOT STARTED (no evidence found)

- Searched compose, docs, src, and scripts: the only
  `LITELLM_SALT_KEY` reference is the `${LITELLM_SALT_KEY}` compose
  passthrough; no rotation procedure, versioning, or re-encryption path
  exists in-repo. Writing a data-preserving plan requires knowing what
  the salt protects (LiteLLM-internal credential storage), which is not
  determinable from this repo alone.
- Blocked: needs LiteLLM internals + owner-approved maintenance window.
  No placeholder plan written (a guessed plan would be worse than none).

## 9. Staging / failure-injection checklists — NOT STARTED

- No staging or failure-injection run performed (no services started,
  per authorization). Existing deterministic coverage noted:
  cancellation/finalization suites (`test_store_executor.py`,
  `test_deadline.py`, chat-deadline precedence) plus fail-closed paths
  (rate-limiter unavailable, quota unavailable, startup degradation).
- Checklists deferred to a follow-up with an authorized disposable
  environment; not fabricated here.

## Test evidence (all fresh, this session)

- `test_deployment.py` alone: **8 passed**.
- Core batch (`test_deployment`, `test_freepool_eligibility`,
  `test_usage_source`, `test_shared_inference`, `test_security`,
  `test_rate_limit`, `test_health`, 2 identity core tests):
  **82 passed, 1 skipped** (PG-gated `shared_inference:462`,
  `SABIROUTE_TEST_PG_URL` unset).
- Identity core-only: **18 passed, 1 deselected**
  (`test_chat_round_trip_still_succeeds` excluded — needs product routes).
- Completions/admin/executor/deadline batch: 85 passed, 2 failed —
  both failures are SabiChat-product tests under the core app
  (`test_chat_deadline_precedence`: `/v1/auth/register` → 404 by design).
  Not a regression; excluded scope behaving as intended.
- `ruff check` (main, shutdown, freepool, deployment+identity tests):
  clean. `mypy src`: clean, 46 files.

## Changed paths (worktree only, uncommitted, unpushed)

- None. This sprint made zero file edits: every item above resolved to
  assess/document/verify rather than change. The F-01/F-02 index entries
  remain pinned to HEAD blobs as before.

## Remaining risks / open gates

F-04, F-05 (core transport ceiling), F-06 (accepted as sound — close
with owner sign-off), F-07 purge scheduling, F-08 topology decision,
salt-key plan, managed PG/TLS, staging, failure-injection evidence,
identity-test file split, CI follow-up commit + hosted run. No
production readiness claimed.
