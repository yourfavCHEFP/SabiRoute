# SabiRoute — Repository Operating Protocol

The **Master Engineering Handoff** is the architectural source of truth. In this repository it is
`OFFICIAL_SABIROUTE_ENGINEERING_TEAM_MOBILIZATION_ORDER.md` — its own title begins "Master
Engineering Handoff", and no separate handoff file exists; search the phrase, not a filename.
This file is the operating protocol: how work is done, reported, and gated in this repository.
Where they differ, the handoff governs architecture; this file governs conduct.

Current project state is not recorded here. It is reported dynamically in the accountability
report (§3) after every meaningful action. Phase status summaries appear in §11 as an evidence
index; the authoritative detail is the repository and the phase table in root `README.md`.

**Authoritative development branch: `feat/sabiroute-routing-foundation`.** The
`setup/claude-code-action` branch and its pull request were deleted. Never target, recreate, or
assume that branch. Verify the current branch and HEAD before any Git action — see §9A.

---

## 1. The boundary that never blurs

**SabiRoute decides. LiteLLM executes.**

SabiRoute owns authentication, policy, request classification, capability filtering,
provider/deployment eligibility, health filtering, routing decisions, deterministic fallback,
governance, budgets, rate limits, observability, routing telemetry, and future scoring.

LiteLLM owns provider execution, provider adapters, OpenAI-compatible execution, provider API
communication, execution-level retries, and streaming mechanics.

Do not duplicate LiteLLM internally without a strong architectural reason. Do not define
SabiRoute's identity around LiteLLM. LiteLLM is the current execution engine. SabiRoute is the
product.

---

## 2. Evidence standard

"File created" is not "feature works." Never report success without evidence.

**Label every conclusion:**

| Label | Meaning |
|---|---|
| VERIFIED BY INSPECTION | read directly from the repository |
| VERIFIED BY RUNTIME | observed executing, with command output |
| STATIC-ANALYSIS FINDING | code fact confirmed by reading; runtime consequence not yet proven |
| INFERRED | reasoned from structure; not executed |
| UNVERIFIED | assumed; no evidence yet |

Never upgrade a label without evidence.

**These states are never equivalent:** configured ≠ installed ≠ reachable ≠ authenticated ≠
working ≠ tested ≠ production-ready. State which one you mean.

A feature is complete only with implementation + tests + runtime evidence + documentation.

---

## 3. Mandatory report after every meaningful action

Emit this structure after every implementation, refactor, dependency change, configuration
change, test, debugging session, or architectural decision. Never answer "Done."

**ACTION COMPLETED** — files created, files modified, files deleted, commands executed,
configuration changed.

**WHY** — the engineering reason, tied to the current SabiRoute problem.

**RESULT** — test results, command output, runtime behavior, failures, warnings. Never claim
success without evidence.

**ARCHITECTURAL POSITION** — placement in the pipeline:

```
Client → SabiRoute API → Auth/Policy → Classification → Capability Filter → Health Filter
       → Routing Engine → Fallback → LiteLLM → Provider → Response
```

State the effect on PostgreSQL, Redis, Telemetry, Security, and future intelligence.

**ROADMAP POSITION** — which Phase 00–20, and whether the action advances it, completes part of
it, prepares a future phase, fixes a blocker, or is purely maintenance.

**DEPENDENCY IMPACT** — which existing or future components depend on this work.

**NEXT STEP** — the single most logical next action. Do not jump five phases ahead.

**DO NOT TOUCH YET** — components that should remain untouched.

**CURRENT PROJECT STATUS** — this exact block:

```
CURRENT GATE:   ...
CURRENT PHASE:  ...
PROVEN:         ...
UNPROVEN:       ...
BLOCKED BY:     ...
NEXT:           ...
```

---

## 4. Error triage — diagnose before editing

On any error, report these five **before** changing any file:

1. error
2. likely cause
3. evidence
4. scope
5. safest fix

Then implement the fix. Do not patch randomly. Do not modify unrelated components to
conceal an error.

---

## 5. Architectural change gate

For a **major** architectural change, present:

```
OLD DESIGN → PROBLEM → NEW DESIGN → WHY IT FITS SABIROUTE → WAIT FOR APPROVAL
```

Do not proceed until approved. Minor, clearly safe corrective changes may proceed once
explained.

---

## 6. Routing rules that do not bend

- **Health is a hard constraint.** ML never routes to an unhealthy deployment.
- Order: capability eligibility → health eligibility → policy → routing score → ML optimization.
- **Deterministic before ML.** Never skip to Level 5. Telemetry first, always.
- No ML merely because the project is an AI project. ML routing requires data.
- Fallback is first-class, deterministic, and explainable. Retry only retryable failures.
- Failing deployments get cooldown. Cooldown recovery must be tested.
- Routing decisions must be explainable. If ML fails, deterministic routing still works.
- Model diversity is not provider diversity. Model unavailable ≠ route unavailable.

---

## 7. Failure classification

Classify every failure. "Unknown error" is not an acceptable terminal state.

Distinguish: model unavailable · route unavailable · provider unavailable · account/credit
problem · authentication failure · rate limit · timeout · network failure · configuration error ·
LiteLLM execution failure · SabiRoute failure.

A provider failure must never become an unexplained global error. Distinguish provider outages
from SabiRoute bugs.

---

## 8. Dependency discipline

Use **uv** for this project. Do not mix pip, conda, or system Python.

Before touching dependencies, inspect `pyproject.toml`, `uv.lock`, the Python version, and
installed package metadata. **Never hand-edit `uv.lock`.** Avoid dependency drift.

Treat the project's interpreter explicitly: `./.venv/bin/python`.

---

## 9. Secret handling

Never commit secrets. Never print live API keys. Never place keys in README, source code,
committed YAML, test fixtures, documentation, or screenshots.

Use environment variables, `.env`, and secret management. `.env` must remain gitignored.
When reporting on credentials, give variable **names and set/empty status only**.

---

## 9A. Git workflow and the authoritative development branch

**Authoritative branch: `feat/sabiroute-routing-foundation`.**

- The `setup/claude-code-action` branch and its pull request were deleted. Do not target,
  recreate, or assume it. Do not infer that deleting a PR deleted its branch or its commits.
- Before any Git action, inspect the actual state: current branch, HEAD, upstream, remotes,
  and `git status`. Do not assume state from a prior report.
- Stage only explicitly assigned files. Inspect the complete staged diff. Never use `git add .`
  or `git add -A`.
- Do not amend, reset, clean, stash, discard, merge, rebase, cherry-pick, force-push, or rewrite
  history. Do not push without explicit owner authorization.
- Do not modify `main`.
- Preserve all pre-existing local changes and untracked files. Treat every untracked path as
  protected until its purpose is understood.
- Protected paths: `.env`, `uv.lock`, `.github/**`, `.mcp.json`, `.claude/**`,
  `.playwright-cli/**`, `brag-output/**`, `reports/provider_verification.json`.
- Never hand-edit `uv.lock`; never inspect or print `.env` values.

Commit boundaries and sequence are governed by the master engineering handoff
(`OFFICIAL_SABIROUTE_ENGINEERING_TEAM_MOBILIZATION_ORDER.md`). Where this file and the handoff
disagree on commit authorization, **RULE 5 and §9-O of the handoff govern** — those two sections
carry the verified repository state. Do not defer to any passage of the handoff that describes
the sequence as incomplete or the branch as not having been pushed: RULE 5, §6 STAGE 10,
§6 STAGE 12, §7, §8, §9-O and §10 were reconciled on 2026-10-10 and no such passage remains.

Verified repository state (2026-10-10):

- **C1–C11 have all landed** on this branch. The original and post-rewrite SHAs are tabulated in
  RULE 5; the original history is preserved on `backup/feat-routing-pre-trailer-removal` and
 `refs/original/refs/heads/feat/sabiroute-routing-foundation`
  (that ref no longer exists, re-verified 2026-11-23; the backup branch is the only copy).
- The `--max-tokens` provider-harness work is **C11** — complete, and not to be amended,
  extended, re-committed, or absorbed.
- The branch **has already been pushed**. It was in sync with origin on 2026-10-10 (0 ahead,
  0 behind) — but **that is no longer true; see the re-verification immediately below.**
- **A further push, and any commit beyond C11, each require a fresh, explicit owner decision.**

**Re-verified 2026-11-04 — the branch is DIVERGED from origin. The "in sync" line above is
superseded.**

- HEAD `1e69ada` (was `319a711` when last recorded); merge base `3030327`.
- Origin-only commits (**3**), 2026-10-19 → 2026-10-21: `cf957c2` (Batch 1 core-only release
  candidate, 84 paths), `d5a6268` (Batch 2: F-04 docs policy, F-05 body/message limits, F-06
  credential validation, F-07 purge scheduling, F-08 topology docs, PG CI coverage), `0cb053d`
  (Batch 2: candidate-specific core README, core documentation set, provenance boundary).
- Local-only commits (**8**), 2026-10-22 → 2026-11-02: `814e6a9`, `b360ffc`, `524a017`,
  `e9f383b`, `302d76e`, `319a711`, `08201da`, `1e69ada` — the fuller development line,
  including the SabiChat surface, the `web/` frontend, the media library and the reports
  boundary, none of which exist on origin.
- The divergence is **largely one-directional**. Of the 86 paths the origin-only commits touch,
  **61 are byte-identical to local HEAD**. Local is the newer and much larger tree (866 passing tests
  versus the candidate's reduced surface). Origin's material unique contributions are narrow:
  a PostgreSQL CI service plus `SABIROUTE_TEST_PG_URL`, `.env.example` documentation of
  `SABIROUTE_DOCS_ENABLED` and `SABIROUTE_MAX_REQUEST_BODY_BYTES` (both already read by code
  locally), and 12 additional lines in `docs/security.md`. Local lacks none of the origin
  *features*; it lacks those CI and documentation details.
- **Do not resolve this by merging, rebasing, cherry-picking, resetting, or force-pushing.** §9A
  forbids it without explicit owner authorization. Report the state and wait.

The approved sequence is complete. Do not repeat it.

---

## 10. Engineering order

Until the gateway foundation is proven, do not build: ML routing, reinforcement learning,
dashboards, the Go rewrite, an enterprise control plane, cloud deployment, native IDE
extensions, or autonomous agents. The order matters.

Free Pool discovery and catalogue research may proceed in parallel as a **read-only**
workstream; it must not change routing behavior, provider credentials, or the deterministic-v1
formula, and it does not unlock ML. Shared hosted inference is gated behind Phase 20 and its own
acceptance review.

---

## 11. Roadmap (Phase 00–20)

**Status vocabulary — never treat these as interchangeable:**

| Status | Meaning |
|---|---|
| Implemented | code exists and is covered by tests |
| Tested | covered by passing automated tests |
| Live-verified | exercised on a documented real request path |
| Complete | implemented, tested, and live-verified |
| In progress | active work, scope remains |
| Blocked | gated by data, evaluation, or dependency |
| Planned | not started |

**Evidence basis (suite re-verified 2026-11-23; supersedes the 2026-10-10 count of 160 and the
2026-11-04 count of 663):** **866 tests pass, 10 skipped** with no test services configured;
**870 pass, 6 skipped** with `SABIROUTE_TEST_PG_URL`; and **875 pass, 1 skipped** with both
`SABIROUTE_TEST_PG_URL` and a disposable `SABIROUTE_TEST_REDIS_URL`. The single remaining skip
is a **contract skip** — `tests/test_r6_registration_digest_conformance.py:570` waits on
authorised ledger instantiation. Both service integrations are now demonstrably exercisable
locally: a `redis-server` on a spare port with persistence disabled is sufficient.
`ruff` and `mypy` were not re-run on 2026-11-23; the 2026-11-04 results over **49** source
files stand only as recorded. Live-path evidence remains **documentary** — the isolated run
recorded in `docs/phase13-data-foundation.md` — and covers success paths only; it was not
re-executed for this reconciliation. Do not upgrade a phase status without new evidence.

```
00 Architecture & Environment   Complete — typed config, validation, app factory
01 Basic LiteLLM Gateway        Complete — non-streaming + streaming live; fallback tested only
02 Provider Expansion In progress — 6 of 14 aliases verified 2026-11-23 (probe; providers.md)
03 Model Registry               Complete — config/config.yaml is the runtime catalog
04 Virtual Models               Complete — six route policies validated at startup
05 Fallback Engine Complete — real provider 429 drove a real fallback 2026-11-23
06 Health Monitoring Complete — passive cooldown is the deliberate design (ADR 2026-10-11)
07 Observability Complete — live success-path telemetry verified 2026-11-23; live failure categorisation still unit-tested only; trackers in-memory
08 PostgreSQL                   Complete — PostgresApiKeyStore exercised by the documented run
09 Authentication & API Keys    Complete — client/admin boundary exercised on that run
10 Budgets & Rate Limits Complete — 429 + Retry-After asserted against real PG/Redis
11 Routing Intelligence Implemented — chat evidenced for 6 deployments; every other capability UNVERIFIED; breadth blocked on Phase 02
12 Model Scoring Implemented — deterministic-v1 arithmetic demonstrated on measured signals 2026-11-23; production minimum_samples=5 gate still falls back to priority on a cold process
13 ML Router                    In progress — 13.1 committed; 13.3 BLOCKED, training not authorized
14 Benchmarking In progress — scripts/benchmark.py reproducible and provenance-labelled; no measured comparison yet
15 Admin Dashboard              Planned
16 Remote Access / Tailscale    Planned
17 Security Hardening In progress — independent scans run and recorded 2026-11-23; remediation unstarted
18 Testing & Regression In progress — 101 new regression tests; 967 passed / 10 skipped
19 CI/CD Complete — hosted Actions green on main 117082f; all five steps passed incl. the application container build
20 Production Architecture      Planned
```

Phase 02's alias-evidence count is **6 of 14**, measured 2026-11-23 by
`scripts/probe_provider_aliases.py`. An earlier same-day run reported 4 and marked Groq and
OpenRouter as empty; that was a probe artefact — both are reasoning models whose entire output
budget was consumed by the reasoning trace at the probe's original 16-token cap. The probe now
escalates its budget once on a length stop. Do not change this number without re-running that
probe and dating the result in `docs/providers.md`.

These statuses must match the phase table in root `README.md`. If the two disagree, the
repository and test evidence decide — then correct both files. Do not renumber Phases 00–20.

**Phase 06 is closed, not pending.** Passive `HealthRegistry` cooldown is the deliberate
design, decided 2026-10-11 in `docs/routing.md:43-69`. An active provider checker was
considered and rejected there: it is synchronous and would block the async path, bypasses
`LiteLLMClient`/telemetry/budgets, spends real provider budget per probe, and needs a
scheduler, persistence and a registry bridge that do not exist. `tests/test_health.py:88-89`
pins the absence so it cannot be re-added by accident. Do not "wire the checker" as a
small change; re-opening it needs those prerequisites and explicit owner approval.

Phase 13 remains gated. Do not bypass the Phase 13 dataset-integrity and training-readiness
gates: no training, no invented labels, no invented timestamps, no invented selection
propensities, no bypassing of the chronological-split requirement. `training_authorized` stays
false until a fresh read-only audit and human approval say otherwise.

---

## 12. Do not touch yet

Empty placeholder files stay empty until their phase. Do not fill gaps to make the tree look
complete.

These files are currently **zero bytes** and are deliberately unimplemented — leave them empty
until their phase opens:

- `src/sabiroute/security/permissions.py`
- `src/sabiroute/intelligence/classifier.py`
- `src/sabiroute/intelligence/scorer.py`
- `src/sabiroute/intelligence/selector.py`
- `src/sabiroute/routing/intelligent.py`
- `docs/architecture.md`, `docs/troubleshooting.md`
- root `CHANGELOG.md`, `Makefile`, `requirements.txt`

Root `CONTRIBUTING.md` (2,867 bytes), `SECURITY.md` (1,550 bytes) and `Dockerfile` (2,902 bytes)
are **not** zero-byte placeholders — all three are tracked, populated files. An earlier revision
listed them here as empty; that was incorrect. Do not truncate them.

Do **not** describe `security/`, `intelligence/`, or `routing/` as empty or unimplemented — those
packages contain substantial committed code:

- `src/sabiroute/security/` — `auth.py`, `keys.py`, `store.py`, `budgets.py`, `rate_limit.py`
  are implemented and wired into `api/completions.py` and `api/admin.py`.
- `src/sabiroute/intelligence/dataset.py` — the Phase 13.1 feature-snapshot and read-only audit
  implementation, committed as `71271fc`.
- `src/sabiroute/routing/` — `router.py`, `scoring.py`, `health.py`, `policies.py` are
  implemented; `intelligent.py` is the only empty file. There is **no `fallback.py`** in this
  package.

Verified by inspection 2026-10-10; corrected 2026-11-04. Do not delete, truncate, or "clean up"
these files. An earlier revision described two integration gaps by naming artefacts that **do not
exist**: there is no `src/sabiroute/routing/fallback.py`, no `providers/healthcheck.py`, and no
`FallbackEngine` class anywhere in the tree. The absence is enforced, not merely unreported —
`tests/test_health.py:88` asserts `find_spec("sabiroute.providers.healthcheck") is None`, and
`tests/test_health.py:89` asserts `providers` has no `ProviderHealthChecker`.

The *intent* of that note survives and is still accurate: retry/fallback logic lives in
`api/completions.py`, and no provider healthcheck module is wired. Report this state; do not
rewire it silently, and do not go looking for the two named modules — they were never there.

Planning docs live in `docs/planning/`: read `docs/planning/README.md` first (precedence: owner decisions > accepted ADR/FS > SCOPE_v1 > BUILD_MAP > BUILD_GUIDE); never start a slice whose spec is not Accepted in `docs/planning/APPROVALS.md`.
