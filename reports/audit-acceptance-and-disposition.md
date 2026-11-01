# Audit Acceptance & Finding Disposition (Sprints 1–5 + 16A/16B)

Baseline: `/Users/airm2/My ML Hub/SabiRoute`,
`feat/sabiroute-routing-foundation` @ `c50a349b723633fa933e49eb2ff4619f57a198ab`
(full SHA verified), upstream in sync (0/0). 11 tracked files modified, all
untracked work preserved, `git diff --check` clean. No fixes, commits, or
behavior changes in this mission.

Source authority: the working tree decides. `reports/` working docs are
gitignored (verified) — history, not authority. Phase-gated empty files
remain empty (verified). Sprint 13/15 artifacts are self-declared
proposals/drills/assessments, not completions.

## 1. AUD-01–AUD-14 disposition

Classes: (1) confirmed open · (2) remediated w/ evidence · (3) partial ·
(4) historical/N/A · (5) unverified-needs-work · (6) owner decision needed ·
(7) disputed. Severity/confidence re-checked against the current tree; all
severities stand.

| ID | Class | Severity | Verdict |
|---|---|---|---|
| AUD-01 no per-user quotas/spend caps | 1 (+6 for billing scope) | P1 | Open. Service key still sole funder (`api/chat.py:134-155`); no budget on it. Tests pass while exposed — confirmed gap, not test artifact. |
| AUD-02 no emergency shutdown | 1 | P1 | Open. No kill-switch path exists in tree (searched). |
| AUD-03 single-process limiters | 1 | P1 | Open. `FixedWindowLimiter` in-process (`api/chat.py:100-119`); Redis Lua bucket is genuinely atomic (read in full) but only covers per-key admission. |
| AUD-04 single service key | 1 (+6 for identity design) | P1 | Open. Memory-only, re-minted per restart (verified). |
| AUD-05 managed PG/TLS, GH run, compose-up, backups policy | 1 | P1 | Open. Local PG-16 gate (19/19) and local container/CI-config evidence do not cover these; nothing since changes that. |
| AUD-06 security headers/CORS | 1 | P2 | Open. Zero header middleware in `src` (searched). Absent CORS is safe-by-default but implicit. |
| AUD-07 automated browser suite, aria-live, mobile/a11y depth | 1 | P2 | Open. Manual smoke only; no suite file exists. |
| AUD-08 2.71 GB image | 1 | P2 | Open (litellm weight; no slimming attempted). |
| AUD-09 gitignored sprint history | 1 (+6: owner must choose track vs back-up) | P2 | Open. `git check-ignore` confirms both working reports ignored. |
| AUD-10 process-local telemetry | 1 | P2 | Open (`HealthRegistry` in-memory by construction). |
| AUD-11 `ruff format` hygiene (29 files) | 1 | P3 | Open; repo convention is check-only, so cosmetic. |
| AUD-12 hardcoded `/srv/sabiroute` probe fallback | 1 | P3 | Open (`main.py:_web_dir`); works, inelegant. |
| AUD-13 deps never vulnerability-scanned | 1 | P3 | Open; no scanner available in this environment. |
| AUD-14 chat retention/export/deletion | 1 (+6: retention policy) | P2 | Open. Telemetry redacts properly (verified); conversation text persists with no policy. |

No finding meets class 2, 3, 4, 5, or 7: nothing was remediated, nothing is
stale, nothing needs more investigation to classify, nothing is disputed.
Falsifiers (what would close each): cited in the remediation backlog.

## 2. 16A/16B executor acceptance dossier

**Original problem** (`artifacts/sprint15-sync-db-p1.md`, assessed NOT
remediated): every `PostgresApiKeyStore` call is synchronous and was invoked
inline on the event loop — one slow query serializes all requests and
defeats deadline/cancellation delivery. Confirmed accurate for the
pre-16A tree.

**What changed.**
- 16A — COMMITTED at HEAD `c50a349` ("feat: offload request-path store
  operations", 438 insertions, 43 deletions, pushed, branch in sync):
  new `security/store_executor.py` (155 lines: fair loop-agnostic
  `_LoopSemaphore` + `BoundedStoreExecutor`, 32-slot default, daemon
  worker threads, slot released only on worker return, cancelled waiters
  withdraw cleanly), await-conversions in `completions.py`, `gateway.py`
  (executor field), `auth.py`; new `tests/test_store_executor.py` (210
  lines, 9 tests: overlap, exact limit, cancel-queued/running, propagation,
  deadline consistency, capacity validation, multi-loop).
- 16B — UNCOMMITTED in the working tree: `admin.py` +35/−15 (await
  conversions of issue/rotate/revoke/rate-limit/usage/budget paths only)
  plus untracked `tests/test_admin_executor.py` (5 HTTP-level tests).

**Code review (read in full).** Semaphore accounting is correct (slot
transfer on wake, done-future skipping, thread-safe via one guard;
cancellation withdraws). `run()` holds the slot across worker execution,
propagates results/exceptions, never frees early on waiter cancellation —
matching its docstring. Session discipline holds: every store method uses
short-lived `engine.begin()` blocks, and each `run()` wraps exactly one
store method, so no transaction spans threads and no new split is
introduced. No routing/selection/execution logic touched. New risks, all
bounded: thread-per-call (capped at 32, daemon); shutdown may orphan an
in-flight write (lifespan closes pools; no drain — same class as before,
narrower window); cancellation is not preemption (documented in code).

**Test evidence (fresh runs, exit 0).** `test_store_executor.py` +
`test_admin_executor.py` + `test_admin.py`: 18 passed. These cover the
assessment's required tests (overlap, cancel-during-block, deadline under
slow store) except a live-PG threaded-integrity run — unit-tested on
sqlite, consistent with the project's evidence standard for this layer.
Full suite unaffected: 308 passed / 4 skipped.

**Remaining risks / unproven.** Live-PG threaded behavior under real
latency; shutdown-drain semantics; 16B uncommitted (owner commit decision
pending — the work is reviewed-clean and isolated, but only the owner
authorizes the commit).

**Recommended owner decision.** Accept 16A as landed (already pushed; no
action needed beyond acknowledgment). Approve or defer the 16B commit on
its own: scope is adapter-only, tests green, no behavior change for
unbudgeted keys. Do not rewire the two known integration gaps
(`FallbackEngine` non-integration, unwired health checker) as part of this.
