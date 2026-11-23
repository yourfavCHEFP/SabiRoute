# Phase 17 — Security Hardening: Independent Scan Record (2026-11-23)

**Status of this document:** read-and-report. No code was changed. No fix was applied.
Every claim below carries an evidence label from §5.

**Repository state at scan time**

| Fact | Value | Label |
|---|---|---|
| Worktree | `/Users/airm2/My ML Hub/SabiRoute-claude-fix` | VERIFIED BY INSPECTION |
| Branch | `main` | VERIFIED BY RUNTIME (`git rev-parse --abbrev-ref HEAD`) |
| HEAD | `be10ab97b820a85d7d656dc95254d57d1e211733` (2026-11-23 10:34:06 +0100) | VERIFIED BY RUNTIME |
| Working tree | clean (`git status --porcelain` empty) | VERIFIED BY RUNTIME |
| Tracked files | 1,360 | VERIFIED BY RUNTIME |
| `src/` Python | 61 files, 12,429 lines | VERIFIED BY RUNTIME |
| `tests/` Python | 55 files | VERIFIED BY RUNTIME |

This document exists because `README.md` currently records Phase 17 as
"preparation-only security evidence … external scanners, Git history, deployed probes, and full
audit UNVERIFIED." The scans below were run to replace that statement with measured results.
They do not close Phase 17; §4 says exactly what remains open.

---

## 1. Scope

### 1.1 What was scanned

| Target | Coverage |
|---|---|
| Tracked working tree | full directory scan (22.22 MB) |
| Git history, all refs | 231 commits, 264.40 MB, `--all` |
| `src/` (61 files) | Semgrep `p/python` + `p/security-audit` (346 rules), Bandit |
| `uv.lock` | 177 resolved packages, OSV advisory database |
| `Dockerfile` | Hadolint |
| `Dockerfile`, `.github/workflows/**` | Checkov (70 checks) |
| `.github/workflows/**` | zizmor |
| `src/sabiroute/security/` | manual review: `auth.py`, `keys.py`, `store.py`, `budgets.py`, `rate_limit.py`, `redaction.py`, `store_executor.py` |
| `src/sabiroute/api/` | manual review of the client/admin boundary: `admin.py`, `completions.py`, `chat.py`, `health.py`, `shutdown.py` |
| `web/` (518 lines JS, 74 lines HTML) | manual review for DOM sinks and token storage |
| `.env.example` | value-shape classification (names and lengths only; no value printed) |

### 1.2 Tools that ran, with versions

| Tool | Version | Result |
|---|---|---|
| gitleaks | 8.30.1 | worktree: 6 hits · history: 129 hits |
| Semgrep | 1.184.0 | 346 rules loaded, 1 result |
| Bandit | 1.9.4 (runner Python 3.15.2) | 14 results, all LOW |
| osv-scanner | 2.7.0 (osv-scalibr 0.5.3) | 177 packages, 0 advisories |
| Hadolint | 2.15.1 | 2 results (1 info, 1 warning) |
| Checkov | 3.4.3 | 70 passed, 0 failed |
| zizmor | 1.32.0 | 6 findings |

### 1.3 Tools that were UNAVAILABLE

| Tool | Status | Reason |
|---|---|---|
| Trivy 0.76.2 | **UNAVAILABLE — network refused** | `failed to download vulnerability DB … mirror.gcr.io … connection reset by peer`. Trivy's vuln/misconfig/secret scanners therefore produced **no** result. This is not a clean result. |
| pip-audit | **UNAVAILABLE — not installed** | Not present on PATH. Dependency coverage came from osv-scanner against `uv.lock` instead. |
| ZAP / Strix | **NOT RUN** | Both require a running, owned target. No deployed instance was probed (see §4). |
| npm audit | **NOT APPLICABLE** | `web/` is zero-build vanilla JS; there is no `package.json` and no JS dependency tree. |
| picklescan | **NOT APPLICABLE** | No pickle artefacts in the tree; no `pickle`/`dill`/`marshal` import anywhere in `src/`. |

### 1.4 Deliberately excluded

- `/Users/airm2/My ML Hub/SabiRoute/.env` — outside this worktree, gitignored, **not read, not
  scanned, not reported**. No `.env` exists inside this worktree; only `.env.example`.
- The full test suite was not run (out of scope for a read-and-report pass).
- No provider was contacted. No database was mutated. No repository code was executed.

---

## 2. Findings

Severity is assigned by reachability and exploitability in this deployment, not by raw tool
score. `CONFIRMED` = reproduced by a tool or read directly in source. `NEEDS-VALIDATION` = the
material is present but its liveness cannot be established without an action this pass forbids.

| ID | Severity | Location | Classification | Evidence |
|---|---|---|---|---|
| **F-01** | **CRITICAL** | `artifacts/production-readiness/scan-outputs/gitleaks.json` @ commit `195dad20df` | **NEEDS-VALIDATION** | Credential material present at that path. The committed gitleaks report embeds the values it scanned from `.env` (lines 10, 11, 23, 26, 29, 35, 38, 40, 50, 53, 57, 60, 63, 69, 72, 86, 98, 101) and `.env.backup` (lines 10, 11, 23, 26, 29, 35, 38, 50, 53, 57, 60, 63, 69), including one `openai-api-key` and one `huggingface-access-token` match per file. Values are not reproduced here. |
| **F-02** | **HIGH** | `.github/workflows/ci.yml:32`, `ci.yml:35`, `.github/workflows/claude.yml:24` | CONFIRMED | zizmor `unpinned-uses` (High/High): actions referenced by mutable tag (`actions/checkout@v4`, `astral-sh/setup-uv@v5`, and the Claude action) rather than by commit SHA. A retagged or compromised upstream action executes with the workflow's token. |
| **F-03** | **MEDIUM** | `.github/workflows/claude.yml:2` | CONFIRMED | zizmor `dangerous-triggers` (High/Medium): `issue_comment` + `pull_request_review_comment` triggers combined with `id-token: write` and `issues: write` / `pull-requests: write`. Partially mitigated — the job is gated on `author_association` ∈ {OWNER, MEMBER}. |
| **F-04** | **MEDIUM** | `.github/workflows/ci.yml:14` | CONFIRMED | zizmor `excessive-permissions` (Medium/Medium): no `permissions:` block, so the workflow token carries the repository default rather than least privilege. |
| **F-05** | **MEDIUM** | `.github/workflows/ci.yml:32` | CONFIRMED | zizmor `artipacked` (Medium/Low): `actions/checkout` without `persist-credentials: false`; the token stays in `.git/config` and can be captured by a later artifact upload. |
| **F-06** | **MEDIUM** | `security-reports/**`, `artifacts/production-readiness/scan-outputs/**` | CONFIRMED | Raw scanner JSON is committed. All 6 worktree gitleaks hits and all 129 history hits resolve to these artefacts or to a canary fixture — i.e. the committed reports are themselves the recurring source of secret-scanner noise, and F-01 shows they can carry real material. |
| **F-07** | **LOW** | `src/sabiroute/security/redaction.py:43-44` | CONFIRMED | Redaction covers `sr_live_`/`sr_test_`, `sk-`, `Bearer`, and URI userinfo only. `hf_…`, `AIza…`, `sk-ant-…` (partially, via the `sk-` rule), and bare JWTs are not masked. `src/sabiroute/api/completions.py:1621-1622` persists provider error text after this redaction, so an unmasked shape reaches the error tracker. |
| **F-08** | **LOW** | `src/sabiroute/api/health.py:79-86` | CONFIRMED | Unauthenticated `/health/ready` returns component names and whether `rate_limiter` is `configured` or `absent` — tells an unauthenticated caller whether throttling is in force. |
| **F-09** | **LOW** | `src/sabiroute/api/health.py:46-55` | CONFIRMED | Unauthenticated `/health/ready` performs up to three database schema checks per request, with no rate limit on the health router. Cheap unauthenticated DB load amplification. |
| **F-10** | **LOW** | `src/sabiroute/api/chat.py:389-391` | CONFIRMED | Auth and chat rate limiting key on `request.client.host`. No `X-Forwarded-For` handling exists, so behind a reverse proxy every client shares one bucket (collateral lockout), and if a proxy header were trusted later without care the key becomes spoofable. |
| **F-11** | **LOW** | `src/sabiroute/api/chat.py:139-165` | CONFIRMED | The SabiChat service API key is minted on first use, cached in process memory, and never revoked or expired. It is a permanent `sr_live_` credential for project `sabichat-service`. |
| **F-12** | **LOW** | `src/sabiroute/security/store_executor.py:173-175` | CONFIRMED | One OS thread is spawned per store call (bounded at 32 concurrent). Correct, but thread churn rather than a pool; a burst creates and destroys threads continuously. |
| **F-13** | **LOW** | `src/sabiroute/main.py:149-179` | CONFIRMED | No security-header middleware: no CSP, no `X-Content-Type-Options`, no HSTS, no `Referrer-Policy`. The static UI is served from `/app`. No CORS middleware is registered either — that is the safe default, not a defect. |
| **F-14** | INFO | `src/sabiroute/migrate.py:48` | FALSE-POSITIVE | Semgrep `avoid-sqlalchemy-text`: the f-string interpolates `LOCK_TIMEOUT_SECONDS`, a module-level integer constant. No user input reaches the statement. |
| **F-15** | INFO | `src/sabiroute/security/rate_limit.py:13` | FALSE-POSITIVE | Bandit B105 "hardcoded password" matched the Redis Lua token-bucket script literal. Not a credential. |
| **F-16** | INFO | `src/sabiroute/security/keys.py:253-256` | FALSE-POSITIVE | Bandit B101 asserts are type-narrowing after an explicit `raise` on the same condition. No security check depends on them. |
| **F-17** | INFO | `src/sabiroute/api/completions.py:1610`, `:1685` | FALSE-POSITIVE | Bandit B110 `try/except/pass` is documented best-effort stream cleanup that deliberately preserves the provider failure outcome. |
| **F-18** | INFO | `tests/test_r3_byok_boundary.py:37` | FALSE-POSITIVE | A self-labelled canary sentinel used to prove redaction works. Not a credential. |
| **F-19** | INFO | `docs/r6-t9-capability-recovery-review.md:349` | FALSE-POSITIVE | gitleaks `generic-api-key` matched prose in a design document. |
| **F-20** | INFO | `security-reports/osv.json:4797`, `security-reports/bandit.json:35829` | FALSE-POSITIVE | Advisory prose and Bandit's own echo of F-18, both inside committed scan artefacts. |

### 2.1 Dependency audit result

**0 advisories** across 177 resolved packages in `uv.lock` (osv-scanner 2.7.0, exit 0).
VERIFIED BY RUNTIME. Caveat: this is a **lockfile** audit, not an installed-environment audit —
no `.venv` exists in this worktree — and the advisory set is whatever osv.dev served at scan
time. `pip-audit` was unavailable, so there is no second opinion.

### 2.2 Secrets scan result

- **Worktree:** 6 hits, all resolved to F-18/F-19/F-20. No live credential in the tracked tree.
- **History:** 129 hits across 16 commits, all resolving to the committed scan artefacts
  (F-06) or the canary fixture — **except** the material described in F-01, which is the one
  item that is not explained by a fixture.
- `.env` and `.env.backup` were **never tracked** (`git log --all -- .env` and
  `-- .env.backup` both empty). The exposure is the committed *report*, not the file.
- `.env.example` values are placeholders (each non-empty credential value contains
  `change`/`password`/`secret`). Not a finding.

### 2.3 Static analysis result

- **No** `subprocess`, `os.system`, `eval`, `exec`, or `__import__` anywhere in `src/`.
- **No** `pickle`, `yaml.load`, `marshal`, or `dill` anywhere in `src/`.
- **No** user-controlled `api_base`/`base_url`: the only base URL is
  `SABIROUTE_LITELLM_URL` from the environment (`src/sabiroute/gateway.py:155`). No SSRF
  surface was found on the request path.
- **SQL:** `src/sabiroute/security/store.py` contains exactly two `text()` calls, both
  parameterised or constant (`:401`, `:403`). Everything else is SQLAlchemy Core. No
  string-built SQL.
- **Frontend:** `web/app.js` has no `innerHTML`, `outerHTML`, `insertAdjacentHTML`,
  `document.write`, or `eval`. The session token is held in memory only and never written to
  `localStorage`/`sessionStorage`; path segments are `encodeURIComponent`-escaped.

### 2.4 Client/admin authorization boundary

Reviewed `auth.py`, `keys.py`, `store.py`, `budgets.py`, `rate_limit.py`, `redaction.py`,
`store_executor.py`, plus `admin.py`, `completions.py`, `chat.py`, `health.py`, `shutdown.py`.

**No authorization-boundary defect was found.** Specifically:

- The admin router carries `dependencies=[Depends(require_admin_key)]` at router level
  (`admin.py:27`), so every admin route — including `/health`, `/metrics`, `/latency`,
  `/errors`, `/usage` — is admin-gated. `shutdown.py:32` does the same.
- The completions router carries `dependencies=[Depends(require_client_key)]` at router level
  (`completions.py:57`).
- `require_admin_key` (`auth.py:103-123`) fails closed when `SABIROUTE_ADMIN_KEY` is unset,
  refuses an admin secret that is itself a client key (`sr_live_` prefix) or the LiteLLM master
  key, and compares with `hmac.compare_digest`.
- `require_client_key` (`auth.py:66-100`) fails closed on any store fault with a typed 503 and
  `from None`, so a driver exception carrying the DSN cannot reach the log.
- Client keys are 96-bit random identifiers plus 256-bit random secrets, stored only as
  SHA-256 digests, compared with `hmac.compare_digest` (`keys.py:377-448`). Format is validated
  before any store access.
- The trusted SabiChat identity field is honoured **only** when the presented key ID equals the
  server-recorded service key ID (`completions.py:1030-1044`); an ordinary API-key caller
  echoing the field is ignored.
- SabiChat sessions are validated on digest, revocation, expiry, and user-disabled state, with
  a single generic 401 for every failure mode (`chat.py:285-306`). Passwords use PBKDF2-HMAC-SHA256
  at 600,000 iterations with a 128-bit salt and a dummy-verify path for unknown accounts
  (`chat/passwords.py`).
- Admin usage listing is bounded (`limit ≤ 100`, `offset ≤ 1,000,000`, `admin.py:314-315`).

---

## 3. Prioritised remediation

Highest first. Each item names the file and the smallest change that closes it. **None was
applied** — this pass is report-only.

1. **F-01 — Treat the historical credential material as compromised.** Rotate the OpenAI and
   HuggingFace credentials that were present in `.env` at the time of commit `195dad20df`,
   whether or not they still work. Then remove the committed report from history. Rotation
   first, history rewrite second: rewriting without rotating protects nothing. The commit is
   reachable only from `refs/original/refs/heads/main` and `refs/original/refs/stash`, so it
   will not travel on a normal `git push` — but it will travel on `git push --mirror`, and it
   is present in every clone that has fetched those refs.
2. **F-02 — Pin every action to a commit SHA** in `ci.yml` and `claude.yml`. Highest
   exploitability of the CI findings: a mutable tag is an upstream-controlled code path into a
   workflow that holds `id-token: write`.
3. **F-03 — Narrow `claude.yml`.** Keep the `author_association` guard, add an explicit
   `permissions:` block granting only what the job uses, and drop `id-token: write` unless the
   action genuinely needs OIDC.
4. **F-04 / F-05 — Add `permissions: contents: read` to `ci.yml`** and
   `persist-credentials: false` to its checkout step.
5. **F-06 — Stop committing raw scanner output.** Add `security-reports/` and
   `artifacts/**/scan-outputs/` to `.gitignore`, or commit only redacted summaries. This is
   what makes F-01 possible and what generates every false positive in §2.2.
6. **F-07 — Extend `redaction.py`** with `hf_`, `AIza`, and JWT shapes, and add a regression
   test per shape. Cheap, and it hardens the one path that persists provider error text.
7. **F-08 / F-09 — Reduce `/health/ready` disclosure and cost.** Return `ready`/`not_ready`
   without component names on the unauthenticated route, and either cache the schema check or
   move the detailed variant behind the admin key.
8. **F-10 — Decide the proxy contract.** Either document that SabiRoute must be the edge, or
   implement an explicit trusted-proxy list before reading `X-Forwarded-For`. Do not add
   header trust without a trusted-proxy allowlist.
9. **F-11 — Give the SabiChat service key a lifecycle.** Rotate it on a schedule, or mint it
   per process start and revoke on shutdown.
10. **F-12 / F-13 — Lower priority.** A thread pool for the store executor, and a
    security-header middleware (CSP, `X-Content-Type-Options`, HSTS behind TLS).

---

## 4. What this does NOT prove

Stated explicitly, because a scan record that overstates itself is worse than no record.

- **No deployed probe was run.** Nothing was exercised against a running instance. Every
  runtime claim here is about a scanner process, not about SabiRoute serving traffic.
- **No penetration test was performed.** No authentication bypass, privilege escalation,
  injection, or business-logic attack was attempted against a live target.
- **Hosted CI is unverified.** The workflow findings (F-02…F-05) are static reads of the YAML.
  Whether the hosted run behaves as the YAML says was not observed.
- **Git history was scanned, not exhaustively rewritten or audited.** gitleaks covered 231
  commits across all refs. It cannot prove the absence of a secret in a shape it has no rule
  for, and it says nothing about material that was force-pushed away and is now unreachable.
- **F-01's liveness is unknown.** Confirming whether those credentials still authenticate would
  require contacting the provider, which this pass forbids. They must be treated as live.
- **Trivy produced no result** (network refused). Container-image and filesystem vulnerability
  coverage is therefore absent, not clean.
- **The dependency audit is lockfile-based**, not environment-based, and rests on a single
  source (osv.dev) at a single point in time.
- **No dynamic analysis of the SabiChat surface.** Session fixation, CSRF, and browser-side
  behaviour were not tested; the frontend review was a source read.
- **No load, DoS, or resource-exhaustion testing.** F-09 and F-12 are reasoned from source, not
  measured.
- **No review of `litellm-test.yaml`, `docker-compose.yml` runtime secrets, or deployment
  topology.** Checkov covered the Dockerfile and workflows only.
- **Phase 17 is not closed by this document.** It converts "no independent scan has been run"
  into "these scans were run, and here is what they found". The remediation list is unstarted.

---

## 5. Evidence labels

| Label | Used for |
|---|---|
| **VERIFIED BY RUNTIME** | Scanner executions with exit codes and counts; `git` state; file and line counts. |
| **VERIFIED BY INSPECTION** | Facts read directly from the repository — router dependencies, key format, hashing parameters, absence of `subprocess`/`pickle`. |
| **STATIC-ANALYSIS FINDING** | A code fact confirmed by reading whose runtime consequence is not proven — F-07 through F-13. |
| **INFERRED** | Reasoning from structure without execution — the proxy-collateral consequence in F-10, the thread-churn consequence in F-12. |
| **UNVERIFIED** | F-01's liveness; hosted CI behaviour; anything in §4. |

No label in this document was upgraded without evidence. Where a tool was unavailable, the
result is recorded as unavailable, never as clean.

---

## 6. Remediation — F-07, F-08, F-09, F-13 (2026-11-23)

This section supersedes the report-only status of §2 and §3 **for these four findings only**.
F-01…F-06, F-10, F-11 and F-12 remain open exactly as recorded above.

### 6.1 F-07 — redaction gaps (CLOSED)

`src/sabiroute/security/redaction.py` now masks three additional carriers:

| Carrier | Pattern | Replacement |
|---|---|---|
| HuggingFace access token | `\bhf_[A-Za-z0-9]{8,}` | `hf_***` |
| Google API key | `\bAIza[0-9A-Za-z_\-]{20,}` | `AIza***` |
| Bare JWT | `\beyJ[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{6,}` | `***` |

The JWT rule runs **before** the `sk-` rule: base64url segments may contain `sk-`, and masking
that fragment first would destroy the JWT shape. No existing pattern was changed or removed.

Proof: `tests/test_phase17_redaction.py` (12 tests) — each new shape is masked, ordinary prose
(`hf_` as a word, `AIza` as a prefix, `sk-learn`, a bare `JWT` mention) is untouched, the four
pre-existing carriers still mask, and the new rules are idempotent.

Residual, unchanged: redaction is pattern-based. A secret in none of these shapes is still not
masked; callers that must guarantee zero leak log the exception class name only.

### 6.2 F-08 — unauthenticated disclosure (CLOSED; public response shape changed)

`GET /health/ready` now returns a bare verdict:

- `200 {"status": "ready"}`
- `503 {"status": "not_ready"}`

The `components` map (component names, `rate_limiter: configured|absent`) and the `failing` list
are no longer returned to any caller. This is a **public API response shape change**, stated
explicitly rather than shipped silently. The Docker `HEALTHCHECK` reads only the HTTP status, so
it is unaffected. Operators keep the authenticated detail surface at `/admin/health`; startup
diagnosis remains in `gateway.startup_error` and the startup log line.

**Consequence for existing tests (reported, not edited).** Six existing tests pin the removed
body and now fail with `KeyError: 'components'` / `KeyError: 'failing'`:

- `tests/test_admin.py::test_readiness_reports_ready_when_request_path_is_servable`
- `tests/test_admin.py::test_readiness_recovers_after_transient_schema_check_failure`
- `tests/test_admin.py::test_readiness_fails_when_startup_is_degraded`
- `tests/test_deployment.py::test_readiness_reports_ready_without_providers`
- `tests/test_deployment.py::test_readiness_fails_without_request_accounting`
- `tests/test_deployment_migration_contract.py::test_unmigrated_database_cannot_report_healthy`

They were left untouched because the remediation brief forbids editing existing test files. Their
status assertions (200/503, `status` value) still hold; only the disclosure assertions fail. They
need an owner-authorized update to the new shape.

Proof: `tests/test_phase17_health_disclosure.py` — the ready and not-ready bodies are exactly the
bare verdicts, and none of `components`, `startup`, `registry`, `key_store`, `chat_store`,
`rate_limiter`, `configured`, `absent` or `failing` appears in the response text.

### 6.3 F-09 — unauthenticated database work (CLOSED)

`src/sabiroute/api/health.py` adds `SchemaCheckCache`, a per-application, 5-second TTL cache
(`READINESS_SCHEMA_CACHE_SECONDS`) around the schema re-checks. A successful check is cached; a
failed check is **not** cached, so a transient database fault cannot hold readiness down for the
TTL and the next probe can recover immediately. The amplification F-09 names is the healthy
steady state, where every unauthenticated request would otherwise run three schema queries.

Proof: `tests/test_phase17_health_disclosure.py::test_repeated_readiness_calls_do_not_repeat_schema_work`
asserts one schema call across three probes, then exactly one more after the cache clock passes
the TTL; `test_failed_schema_check_is_not_cached` asserts a failed probe is re-checked and
recovers on the next request.

### 6.4 F-13 — security headers (CLOSED)

`src/sabiroute/main.py` adds `SecurityHeadersMiddleware` (pure ASGI, outermost user middleware) and
emits on every HTTP response:

- `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'`
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security: max-age=31536000`

CSP compatibility was verified against the shipped assets, not assumed:

- `web/index.html` loads `./styles.css` and `./app.js`; `web/dashboard/index.html` loads
  `./dashboard.css` and `./dashboard.js` — same-origin, permitted by `script-src`/`style-src 'self'`.
- Neither page has an inline `<script>`, `<style>`, `style=` attribute, or `on*=` handler.
- Neither JS file uses `eval`, `new Function`, `innerHTML`, or `document.write`; the only style
  write is CSSOM (`web/app.js:189`), which CSP does not govern.
- Both pages declare `href="data:,"` favicons, which `img-src 'self' data:` permits.
- All `fetch` targets are same-origin, permitted by `connect-src 'self'`.

`/docs` and `/redoc` are exempt from the CSP: the opt-in developer docs bootstrap Swagger UI and
ReDoc from a CDN with an inline script, which the strict policy would block. The baseline headers
still apply there. HSTS is emitted unconditionally; browsers ignore STS received over plain HTTP
(RFC 6797 §8.1), and `includeSubDomains` is deliberately omitted for a local-first gateway.

Proof: `tests/test_phase17_security_headers.py` (7 tests) — headers on a normal response and on a
503, the policy permits same-origin script/style and contains no `'unsafe-inline'`, `'unsafe-eval'`
or `*`, both served UIs carry the policy, the asset graph is same-origin and free of blocked
constructs, and the docs exemption holds.

### 6.5 Not remediated — design items

- **F-10** — rate limiting keyed on `client.host` remains proxy-blind. Needs a trusted-proxy
  configuration decision; no header trust was added.
- **F-11** — the SabiChat service key is still minted once and never revoked or expired. Needs a
  key lifecycle design.
- **F-12** — thread-per-call in `store_executor.py` is a performance item, not a security defect.
- **F-01…F-06** — untouched: F-01 needs credential rotation and history work; F-02…F-06 live in
  `.github/**`, a protected path.

### 6.6 Verification (2026-11-23)

| Command | Result |
|---|---|
| `pytest tests/test_phase17_redaction.py tests/test_phase17_health_disclosure.py tests/test_phase17_security_headers.py -q` | **24 passed** |
| `pytest tests/test_admin.py tests/test_sabichat_web.py tests/test_deployment.py tests/test_health.py tests/test_r3_secret_leakage.py tests/test_deployment_migration_contract.py tests/test_chat_session_hygiene.py tests/test_phase15_dashboard_serving.py -q` | **78 passed, 6 failed** — all six are the F-08 shape assertions listed in §6.2 |
| `ruff check src tests` | clean |
| `mypy src` | clean, 63 source files |

Labels: header emission, redaction behaviour, readiness bodies and the cache are **VERIFIED BY
RUNTIME** (pytest). CSP compatibility with the UIs is **VERIFIED BY INSPECTION** of the asset graph
and policy; no browser was executed, so browser-side enforcement is **UNVERIFIED**.

### 6.7 Phase 17 status after this pass

**Not Complete.** F-07, F-08, F-09 and F-13 are closed with tests. F-01 (CRITICAL, needs
credential rotation), F-02…F-06 (CI), F-10, F-11 and F-12 remain open, and no deployed probe or
penetration test has been run.
