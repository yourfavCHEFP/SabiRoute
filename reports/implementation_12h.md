# 12-Hour Product Integration Mission — Running Report

Mission: maximum safe, testable progress toward SabiChat + Free Chat + Free Pool
on the shared routing engine. Time-boxed; correctness is not negotiable.

Rule reminders: no commit/push/deploy without fresh explicit authorization;
no secrets in output; phase-gated empty files stay empty; deterministic-v1,
retry semantics, `training_authorized`, and existing response behavior unchanged.

## Baseline (verified, pre-change)

- Root `/Users/airm2/My ML Hub/SabiRoute`, branch
  `feat/sabiroute-routing-foundation`, HEAD `c50a349`, upstream in sync (0/0).
- Tracked modification preserved: `M src/sabiroute/api/admin.py` (Mission 16B,
  uncommitted). Untracked `tests/test_admin_executor.py` + artifacts preserved.
  Nothing staged. No destructive operations performed.
- Toolchain: Python 3.11.15, uv 0.11.33, ruff 0.16.8, mypy 2.3.1.
- Suite: **242 passed, 4 skipped** (Redis skips: `SABIROUTE_TEST_REDIS_URL` unset).
- `ruff check src tests scripts config`: clean. `mypy src`: clean.
  `git diff --check`: clean. (`ruff format --check` flags 29 pre-existing files;
  the repo does not enforce format — recorded, not changed.)
- Schema approach: SQLAlchemy create-all + additive helper
  (`PostgresApiKeyStore._migrate_usage_columns`); `migrations/` empty; no
  versioned framework. No frontend in tree. Compose runs LiteLLM/PG/Redis only.

## Sprint 1 — Free Pool eligibility contract: COMPLETE

Design: Free Chat is a request marker (`sabi_route_free_chat`, alongside the
existing `sabi_route_request_type`), enforced by a new pure policy module that
reuses `Router.evaluate_candidates` / `choose_deployment`. No parallel router,
no ranking duplication, no execution duplication, no formula change.

Files:
- NEW `src/sabiroute/freepool/__init__.py`, `src/sabiroute/freepool/eligibility.py`
  (`FreePoolPolicy` disabled-by-default, `evaluate_free_pool`,
  `deny_reason_for_evaluation`, 5 stable reason codes).
- `src/sabiroute/gateway.py`: `GatewayState.free_pool` + `build_gateway_state(...,
  free_pool=None)` + `_free_pool_from_env()` (`SABIROUTE_FREEPOOL_ENABLED`,
  `SABIROUTE_FREEPOOL_DEPLOYMENTS`). Default: disabled, empty allowlist.
- `src/sabiroute/api/completions.py`: marker popped with the other
  SabiRoute-owned fields (never forwarded to LiteLLM, never trips the budget
  estimator); gate runs after classification, before general eligibility,
  budget reservation, and provider execution; denial via existing `finish()`
  (usage finalization + budget reconciliation preserved); `candidates`
  narrowed to the allowlist so the attempt loop / fallback cannot escape it.
- NEW `tests/test_freepool_eligibility.py` (14 tests).

Gate semantics: marked + disabled → 503 `free_pool_unavailable` (fail closed);
unmapped → 403 `free_pool_unmapped_deployment`; allowlisted but incapable →
503 `free_pool_no_capable_deployment`; allowlisted but unhealthy → 503
`free_pool_no_healthy_deployment`; misconfigured subset → 503
`free_pool_route_configuration_error`. Unmarked requests never consult the gate.

Evidence (at Sprint 1 close; superseded by the final verification below):
- `pytest tests/test_freepool_eligibility.py`: **14 passed**.
- Full suite: **256 passed, 4 skipped** (242 baseline + 14 new; same 4 skips).
- `ruff check`, `mypy src` (40 files), `git diff --check`: all clean.
- Mid-sprint finding fixed, not hidden: the gate first sat after the general
  eligibility checks, so an unhealthy allowlisted deployment surfaced
  `no_healthy_deployment` instead of the Free-Pool-typed reason; the gate moved
  ahead of the general checks so marked requests always carry Free-Pool-typed
  reasons. Unmarked behavior byte-identical (gate skipped entirely).

Not done: catalogue↔registry mapping endpoint (data draft only), usage-source
attribution (needs Sprint 2 migrations), SabiChat identity/frontend (Sprints
3–4), containers/CI/runbooks (Sprint 5), live-provider validation.

## Sprint 2 — Versioned migrations + usage attribution: COMPLETE

Decision, recorded: **no new dependency** (no Alembic). The schema is
SabiRoute-owned, namespaced, five tables, additive-only history, with no
production deployment holding divergent versions; the tree already evolves via
`create_all` + `_migrate_usage_columns`. Sprint 2 formalizes that pattern with
an explicit ordered revision ledger instead of adding a framework.

Files:
- `src/sabiroute/security/keys.py`: `USAGE_SOURCES`
  (`unknown`/`free_pool`/`byok`/`paid`; only `free_pool` assigned today),
  `RequestUsageEvent.usage_source` (default `"unknown"`, appended last so all
  existing keyword constructions are unaffected), finalization rejects any
  other value.
- `src/sabiroute/security/store.py`: nullable `usage_source` column on
  `sabiroute_request_usage` (fresh installs via `create_all`, existing DBs via
  the extended `_migrate_usage_columns`); new `sabiroute_schema_versions`
  ledger + ordered `SCHEMA_MIGRATIONS` (`0001-usage-source`) applied
  idempotently in `__init__` via `_apply_schema_migrations()`; new
  `applied_revisions()` accessor. `_usage_values` persists the source;
  `_usage_from_row` maps NULL to `"unknown"` — legacy rows are never
  backfilled or invented.
- `src/sabiroute/api/completions.py`: admission event is always `"unknown"`.
  After the gate allows, `event = replace(event, usage_source="free_pool")`,
  so every later exit finalizes with the authoritative source. Denied requests
  (unmapped, incapable, unhealthy, disabled policy) finalize as `"unknown"` —
  the client marker alone never confers attribution. Activation is strict
  (`extras.pop(...) is True`): only the exact marker key with JSON true
  selects Free Chat; truthy strings and marker-like aliases cannot.
- `src/sabiroute/api/admin.py`: `GET .../usage` items expose `usage_source`.
- `tests/test_usage_source.py` (12 tests): fresh-DB revision + round-trip;
  raw-SQL legacy-schema upgrade preserving the row as `"unknown"`; rerun
  idempotency; finalization rejects `usage_source="free"`; allowed/denied/
  disabled/spoofed (`"yes"` string, marker-like alias) attribution outcomes;
  fallback preserves `free_pool` across 2 attempts; SQL finalize UPDATE
  carries the source per-row; simulated migration failure propagates and the
  same file recovers on re-init. Request-path + admin test reports
  `["free_pool", "unknown"]` for the two modes.
- Migration order / backup / rollback, explicit: order is `SCHEMA_MIGRATIONS`
  list order, recorded per database; before applying to any real database, take
  a PostgreSQL backup (`pg_dump`) — migrations here run only against
  disposable sqlite test databases in this mission; every revision is additive,
  so rollback is at most an ignored column, never lost rows. No BYOK/payment
  schema added.

Evidence:
- `pytest tests/test_usage_source.py tests/test_freepool_eligibility.py`:
  **26 passed**.
- Full suite: **268 passed, 4 skipped** (242 baseline + 26 new; same 4
  env-gated Redis skips).
- `ruff check`, `mypy src` (40 files), `git diff --check`: all clean.

## Migration procedure (revision 0001-usage-source)

Fresh database: start the gateway (or instantiate `PostgresApiKeyStore`) with
the target `DATABASE_URL`; `create_all` builds all six tables including
`sabiroute_schema_versions`, the column migration is a no-op, the ledger
records `0001-usage-source`. Verify with:

- `store.applied_revisions()` → `["0001-usage-source"]`
- `SELECT revision FROM sabiroute_schema_versions;` → one row
- `SELECT usage_source FROM sabiroute_request_usage LIMIT 1;` → column present

Existing database: back up first (`pg_dump "$DATABASE_URL" > backup.sql`);
start the gateway / instantiate the store — `ADD COLUMN IF NOT EXISTS` adds
`usage_source` (nullable, existing rows become NULL → read as `"unknown"`),
then the ledger records the revision. Verify row counts before/after
(`SELECT count(*) FROM sabiroute_request_usage;`) and re-run: second startup
is a no-op. Rollback limitation: revisions are additive-only; downgrade means
ignoring the column, never data loss. Validation limit, stated plainly: this
mission exercised the procedure on disposable sqlite databases only. The
PostgreSQL `IF NOT EXISTS` branch was never executed here — it is
code-inspected only, not integration-tested. A live-PostgreSQL upgrade run
(backup → apply → count check → revision check) is required before any real
database migration.

Not done: SabiChat identity/backend (Sprint 3), frontend (Sprint 4),
containers/CI/runbooks (Sprint 5), live-provider validation.

## Sprint 3 — SabiChat backend: COMPLETE (backend only, no frontend)

Design: bearer session tokens (opaque `secrets.token_urlsafe`, SHA-256 digest
persisted, 7-day absolute expiry, revocation on logout) — bearer headers match
the existing API conventions and remove any CSRF surface, so no cookie
settings exist to weaken. Passwords: stdlib PBKDF2-HMAC-SHA256, 600k
iterations, 128-bit salt, modular versioned format — no new dependency, no
custom crypto (choice documented in `chat/passwords.py`). Chat calls the
gateway's own `POST /v1/chat/completions` in-process (ASGI transport) with a
server-held service key provisioned once via `issue_api_key` and cached only
in memory; the marker is forced server-side and unknown client fields are
ignored, so attribution and Free Pool policy apply unchanged. Gateway errors
map to fixed public messages (raw text never forwarded). Auth/chat rate
limits are in-process fixed windows (single-process semantics, documented).

Files:
- NEW `src/sabiroute/chat/__init__.py`, `chat/passwords.py`, `chat/store.py`
  (`SabiChatStore`: users, sessions, conversations, messages; digest-only
  tokens; owner-scoped reads; naive-datetime normalization at the row
  boundary for sqlite).
- EDIT `security/store.py`: `sabichat_*` tables in shared metadata +
  `create_all`, revision `0002-sabichat-backend`; engine/schema/ledger logic
  factored to module functions (`_connect`, `ensure_schema`,
  `migrate_usage_columns`, `apply_schema_migrations`,
  `applied_schema_revisions`) with thin delegating methods (behavior
  identical; `SabiChatStore` runs the same `ensure_schema`, so init order
  never matters).
- NEW `src/sabiroute/api/chat.py`: `POST /v1/auth/register|login|logout`,
  `GET /v1/auth/me`, `POST|GET /v1/conversations`,
  `GET|POST /v1/conversations/{id}[/messages]`; generic 401s (login failures
  identical for unknown/wrong/disabled, with dummy-hash work); generic 400
  duplicate registration; owner-scoped 404s; bounded pagination
  (conv 1–50, messages 1–200); content 1–8000, titles ≤120, model ≤256;
  history window 20, gateway `max_tokens` capped 1024 (interim, documented).
- EDIT `gateway.py`: `GatewayState.chat_store` + `build_gateway_state(...,
  chat_store=None)`; env auto-creation only when neither store was injected
  (an injected key store signals a managed context — no surprise DB
  connections; this repaired a real regression in
  `test_injected_store_prevents_database_connection`).
- EDIT `main.py`: mount `chat_router`.
- EDIT `tests/test_usage_source.py`: revision expectations now
  `[0001, 0002]` (schema evolved; assertions updated, not weakened).
- NEW `tests/test_sabichat.py` (24 tests): register/login/logout/me,
  duplicate/invalid/disabled/generic failures, hash-not-plaintext, expiry,
  revocation, malformed credentials, auth rate limit (10+1 → 429),
  unauthenticated denial on all routes, cross-user isolation (get/post/list/
  guessed IDs), pagination bounds, chat success + message persistence,
  default-model routing, `free_pool` attribution, denial mapping + error
  message recording, provider-failure mapping without leaks, marker-spoof
  immunity, invalid content short-circuit, error-mapping unit tests,
  chat-unavailable without store, sqlite table/revision checks, session purge.
- Errors share one envelope: `{"detail": {"error": {message, type}}}` via
  `HTTPException` (admin.py convention); fixed mid-sprint from a mixed
  envelope after 5 test failures exposed it — not hidden.

Evidence:
- `pytest tests/test_sabichat.py`: **24 passed**.
- Full suite: **292 passed, 4 skipped** (268 prior + 24 new; same env-gated
  Redis skips). One real regression found and fixed (gateway auto-connect,
  above); no other failures.
- `ruff check`, `mypy src` (44 files), `git diff --check`: all clean
  (B008 Depends singletons, E501, F401 findings fixed before closing).
- sqlite-file persistence tested; live PostgreSQL NOT used; live providers
  NOT used; timeout-transport mapping code-inspected only (stub cannot raise
  transport errors through the in-process call).

Known gaps (not smuggled in): per-user gateway keys/quotas (one service key,
restart re-mints, old rows retained); Redis-backed global rate limits;
cookie+CSRF session option for production; request-size hardening beyond
field caps; monitoring/backup (Sprint 5).

## Sprint 4 — SabiChat frontend: COMPLETE (MVP, no automated browser suite)

Stack decision, recorded: zero-build vanilla HTML/CSS/JS in `web/`, served by
the app at `/app/` via `StaticFiles` (API routes and docs untouched; the same
directory deploys to static hosting unchanged). No package.json, no bundler,
no framework, no CDN dependency — the repo has no frontend toolchain and a
new one for an MVP chat UI would be pure overhead.

Files:
- NEW `web/index.html` (auth view + sidebar/chat layout, landmarks, labels,
  responsive viewport), `web/styles.css` (light/dark, responsive breakpoint at
  720px), `web/app.js` (typed API client separated from presentation;
  in-memory token only; textContent-only rendering; AbortController cancel;
  double-submit guard; conversation-switch abort + immediate clear;
  friendly error mapping incl. session-expiry return to auth).
- EDIT `src/sabiroute/main.py`: mount `/app` when `web/` exists.
- EDIT `README.md`: SabiChat section covers the UI, Free Pool status updated,
  migration/SabiChat limitation bullets current, cross-cutting roadmap note.
- NEW `tests/test_sabichat_web.py` (7 tests): serving + content types, mount
  does not shadow the API, landmark/label presence, endpoint parity against
  the live route table (every fetched `/v1/*` path resolves; no direct
  `/v1/chat/completions`, LiteLLM, host, or port references), backend error
  envelope parsing, no-secret/no-storage scan, no-innerHTML + guard markers.

Evidence:
- `pytest tests/test_sabichat_web.py tests/test_sabichat.py`: **31 passed**.
- Full suite: **299 passed, 4 skipped** (same env-gated Redis skips).
- `ruff check`, `mypy src` (44 files), `git diff --check`: all clean
  (two import-sort findings fixed before closing).
- Real-browser smoke (playwright-cli, Chromium, stub provider, disposable
  sqlite DBs, throwaway server script outside the repo): register → app view
  with user email → new conversation → send → assistant reply rendered →
  sign-out returns to auth; `localStorage`/`sessionStorage` both length 0;
  console had exactly one error (favicon 404), fixed with an inline data-URI
  icon. No provider credentials anywhere in the loop.

Known gaps: no automated browser regression suite (manual smoke only);
mobile-width CSS unexercised in a real viewport; no screen-reader pass
(no aria-live for incoming messages); token lost on reload by design
(documented trade-off).

Continued verification (second browser session, fresh disposable DBs):
register → auth UI → two conversations → message each → switch A/B with
server-DB cross-check (each view shows exactly its own messages, no leak
either direction) → synchronous double-`requestSubmit` probe yields exactly
one new pair (pending guard proven) → server-side session revocation →
next action returns the auth view with "session expired". One scare
investigated honestly: an early snapshot appeared to show A's messages in
B — server-DB inspection proved the click had re-selected A (identical
"New conversation" titles), not a leak; the retest with verified selection
is what stands. `node --check web/app.js` passes; `textContent` ×10,
zero matches for innerHTML/outerHTML/document.write/storage/cookie/
LiteLLM/direct-completions references. Console fully clean (favicon fix
confirmed — zero errors this session).

Third verification pass (fresh DBs, same stub setup): A shows only the
alpha pair, B only the beta pair, switching restores each history exactly
(server-DB row placement matches in both directions); logout returns the
auth view and an unauthenticated POST is 401; wrong password shows the
generic "Invalid email or password."; a second user sees zero conversations;
server-side revocation surfaces "session expired" on the next action. The
only console entries are the browser's own failed-fetch logs for the
expected 401s — zero JS errors. Full battery re-run: 299 passed / 4
skipped, ruff/mypy/diff-check clean, `node --check` passes. No source
changes in this pass; Sprint 4 remains VERIFIED COMPLETE.

Acceptance remediation (code inspection + slow-stub browser proofs):
1. Stale-render guard — inspection found the send continuation rendered
   unconditionally after its re-fetch, so a switch landing mid-continuation
   could paint the old conversation into the new view (usually self-healing
   on the next fetch, permanent if that fetch failed). Fixed by capturing
   session/id up front and skipping renders (and composer re-enable) when
   the selection moved on; sign-out now aborts in-flight work. Browser proof
   with an 8s stub: send in A, switch to B mid-flight → B stays empty;
   back to A → full history intact.
2. Cancel cleanup — the abort path returned early, leaving the optimistic
   "Thinking…" bubble stuck. Fixed by re-syncing from the server when the
   conversation is still active. Browser proof: cancel at 0.5s of an 8s
   request → pending bubble gone, composer re-enabled; server-side
   completion still records truthfully and appears on revisit (abort ends
   the wait, not the work — documented semantics).
3. Error recovery — server killed mid-session → visible "Couldn't reach the
   SabiChat backend…" banner; server restarted → next send succeeds and the
   banner clears. Console shows only the expected connection-refused fetch
   logs from the deliberate kill; zero JS errors throughout.

Resume-turn re-verification (identical tree, fresh DBs, 3s stub): send
handler re-read line by line — exactly one `postMessage` per submit (the
earlier "duplicate-looking" lines were the intentional double-submit probe
plus re-sync GETs, not a defect); captured session/id guards confirmed in
place, no change needed. Browser re-proved: register → A/B round trips with
unique markers → B-only and A-only views each way with server-DB row match →
mid-flight switch keeps the incoming view clean → markup renders inert
(0 img/script nodes) → logout → auth view + unauthenticated POST 401 →
second user sees 0 conversations → genuine screenshot captured
(`/tmp/sabichat-acceptance.png`, outside the repo). Battery: targeted 57
passed, full 299 passed / 4 skipped, ruff/mypy/diff-check/`node --check`
all pass. Sprint 4 remains VERIFIED COMPLETE; no source changes this turn.

Resume re-verification (identical tree, fresh DBs, 3s stub): send handler
re-read — exactly one `postMessage` call site (line 330); the four
`getConversation` sites sit in mutually exclusive paths (select / success /
abort / error), so the "duplicate-looking" log was the intentional
double-submit probe plus re-sync GETs, not a defect; no change made.
Browser re-proved: register → A/B round trips with unique markers → B-only
and A-only views each way with server-DB row match → mid-flight switch
keeps the incoming view clean → markup inert (0 em nodes) → logout → auth
view + unauthenticated POST 401 → second user sees 0 conversations. Console:
one expected 401 fetch log, zero JS errors. Battery re-run: targeted 57
passed, full 299 passed / 4 skipped, ruff/mypy/diff-check/`node --check`
all pass, exit 0 throughout. No commit; Sprint 4 remains VERIFIED COMPLETE.

## Checkpoint — Sprints 1–4 delivered (safe, coherent, tested)

Delivered: eligibility + attribution + SabiChat backend + browser UI on the
shared routing engine, migrations at 0002, full suite green. Next: Sprint 5 —
container, CI, backup/restore, runbooks, staging smoke test (see below).
No commit/push/deploy performed; all changes uncommitted in the tree
(pre-existing 16B admin work and artifacts preserved).

## Sprint 5 — Deployment foundation: COMPLETE (foundation, not production)

Baseline: branch `feat/sabiroute-routing-foundation` @ `c50a349`; Python
3.11–3.13, uv + `uv.lock`; Docker 29.6.2 available; entry point `sabiroute`
→ uvicorn `sabiroute.main:app` (HOST/PORT env-driven); DB via `DATABASE_URL`
(sqlite-compatible for smoke); Redis optional (rate limits only);
`/health/live` dependency-free, `/health/ready` checks startup+registry+store
with existing tests; lifespan closed key_store + rate_limiter but not the
chat store (fixed). Existing infra: compose for litellm/pg/redis only
(loopback ports, no public exposure); `Dockerfile`/`Makefile`/
`requirements.txt` 0-byte; CI only the Claude Action; no `.dockerignore`.
`Dockerfile` filled as Sprint 5's phase (documented); `Makefile`/
`requirements.txt`/other placeholders stay empty — not needed.

Files:
- `Dockerfile` (was 0-byte, now Sprint 5's phase): python:3.11-slim, `uv
  sync --frozen --no-dev` (deps layer cached, project installed after `src/`
  copy — an empty-wheel ordering bug found and fixed during the build),
  non-root `sabiroute` user, pinned `SABIROUTE_CONFIG_PATH/_ROUTES_PATH/
  _WEB_DIR` (wheel installs break repo-relative resolution — found via a
  failed container smoke test, fixed, re-verified), `HEALTHCHECK` on
  `/health/live`, `CMD ["sabiroute"]`.
- NEW `.dockerignore`: excludes `.env`, venvs, caches, git, sqlite files,
  artifacts, docs, tests; keeps `src/`, `config/`, `web/`, lockfile.
- `docker-compose.yml`: new `sabiroute` service (build, loopback-only port,
  env_file, container service-name overrides, healthy dependencies incl.
  litellm, liveness healthcheck). Compose validates (`docker compose
  config`, exit 0); full-stack `up` not run (needs real provider keys).
- NEW `.github/workflows/ci.yml`: locked `uv sync`, pytest (with Redis
  service so the 4 gated tests run in CI instead of skipping),
  ruff/mypy/`node --check`, `docker build`; no secrets, no deploy.
- `src/sabiroute/main.py`: lifespan also closes `chat_store`.
- `.env.example`: Free Pool template vars (disabled-shape documentation).
- NEW `tests/test_deployment.py` (9 tests): readiness ready/not-ready,
  lifespan closes chat store, chat-unavailable without persistence,
  Dockerfile/`.dockerignore`/CI-yaml/env-template contract assertions
  (incl. YAML-`on`-parses-as-True and placeholder-only-secret gotchas,
  both tripped and fixed honestly).
- `docs/deployment.md` rewritten: container build/run/smoke evidence,
  managed-PG TLS (`sslmode=require` passthrough), Redis optionality,
  startup/shutdown/rollback rules, proposed DO topology (NOT provisioned).
- `README.md`: container/CI getting-started, limitation bullets current.

Evidence:
- `docker build -t sabiroute:sprint5 .` → success (2.71 GB; litellm weight
  documented). Two genuine build/smoke failures found and fixed (empty
  wheel; installed-layout config/web resolution).
- Container smoke (sqlite `DATABASE_URL`, no provider keys): `/health/live`
  200, `/health/ready` full-ok, `/app/` 200; runs as `sabiroute`; image
  holds only runtime files; no `.env`; no secret-like env values; Docker
  health status `healthy`.
- `pytest tests/test_deployment.py`: 9 passed. Full suite: **308 passed,
  4 skipped** (same env-gated Redis skips). `ruff`, `mypy src` (44 files),
  `git diff --check`, `node --check`: all clean, exit 0.
- Free Pool stays disabled by default (no env defaults set it); no
  inference, provisioning, DNS, or paid resources touched.

Known gaps: GitHub Actions has never run this workflow (config validated
locally only); no live-PostgreSQL migration or backup/restore test; no
full-stack compose `up`; image is large; single-node, no HA claims.

## PostgreSQL migration acceptance gate: PASSED (local disposable only)

Environment: disposable `postgres:16-alpine` container (PostgreSQL 16.15),
loopback-only port, temp credentials/database, removed afterwards. No
production or managed credentials; no provider calls. Driver `psycopg`
3.3.6 via the project's `postgresql+psycopg` URL rewrite — 19/19 checks
passed using only real project code paths (`PostgresApiKeyStore`,
`SabiChatStore`, `ensure_schema`):
fresh init records `[0001-usage-source, 0002-sabichat-backend]` with all 7
tables and a nullable `VARCHAR usage_source`; usage (`free_pool`) and chat
data round-trip; second init idempotent with rows intact; pre-ledger upgrade
(raw-SQL legacy schema on a second database) records both revisions,
preserves the legacy row as `unknown` with its key intact, and leaves chat
usable; wrong password raises clear `OperationalError` (no silent success).
`pg_dump` → restore into a third database reproduced revisions, counts, and
representative data exactly (`(1, 'free_pool')`, 1 message, both revisions
on both sides). Not covered: intra-migration partial failure on PG (unit
coverage is sqlite-level), managed-PostgreSQL/TLS, and production backup
policy — all remain explicitly outstanding. No app code changed for this
gate; `docs/deployment.md` and README limitations now record the local-PG
validation boundary.

Recovery checkpoint (post-429): Dockerfile ENV block verified well-formed
(lines 13–20, proper continuations, python:3.11-slim in range); compose
password interpolations hardened with `:?` fail-fast guards (empty-password
`docker compose config` now exits 1 with "Set POSTGRES_PASSWORD in .env");
CI pins Python 3.11 to match the repo toolchain. Battery re-run: targeted
57 passed, full 308 passed / 4 skipped, ruff/mypy/diff-check/`node --check`
clean, exit 0; rebuilt image smokes green (live/ready/app 200). No source
behavior changes; Sprint 5 remains COMPLETE as a foundation.
