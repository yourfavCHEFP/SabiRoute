# SabiRoute — Current State

**As of 2026-11-23.** This is the standing status document. Everything in it carries an
evidence tag, and every number should be re-derived before it is relied on.

Evidence tags: **[V]** verified this session by command output or file read ·
**[R]** reported by another agent or a prior session, not re-derived · **[U]** unverified.

**How to keep this honest:** update it at the end of any change to phase status, alias
evidence, or test baseline — in the same commit as the change. If a number here contradicts
the repository, the repository wins and this file is wrong. Never restate a figure without
the command that produced it.

---

## 1. Repository state

| Fact | Value | Evidence |
|---|---|---|
| `main` vs `origin/main` | `51f1dc5` on both sides, **0 ahead / 0 behind** when this was written; the commit that adds this file puts `main` 1 ahead until it is pushed | [V] `git rev-list --left-right --count` |
| Hosted CI on `main` | green — runs `45117926289` (`3d9901b`) and `45118591281` (`51f1dc5`) | [V] `gh run list` / [R] Copilot's watch |
| Test suite | **866 passed, 10 skipped** | [V] `pytest -q` on the `main` worktree |
| Skips | 9 environment-gated (`SABIROUTE_TEST_REDIS_URL` / `SABIROUTE_TEST_PG_URL`); **1 contract skip** — `tests/test_r6_registration_digest_conformance.py:570` awaits authorised ledger instantiation | [V] pytest skip report |
| Node.js | CI emits a Node 20 → 24 deprecation notice for Actions | [R] two CI runs |
| Checked-out branch | `feat/sabiroute-routing-foundation` @ `1e69ada` — the **pre-rewrite lineage**, not `main` | [V] `git branch --show-current` |

**Why the checkout is not `main`:** the 2026-11-23 co-author rewrite changed every commit SHA.
`main` carries the rewritten history; this branch still carries the originals. Expect every
non-`main` branch to *appear* diverged. That is by design, not a conflict to resolve. To build
on `main`, use the worktree at `../SabiRoute-claude-fix` (branch `main`).

## 2. Work completed this session

| Sprint | Scope | Outcome |
|---|---|---|
| 1 | Provider alias remediation | Retired provider model names corrected; proxy config regenerated. [R] |
| 2 | Phase 13 integrity + audit | Root-caused both blockers to **5 pre-instrumentation rows**, not a live defect. Gate left byte-unchanged; added an opt-in, reported scope filter. Phase 13 `BLOCKED` → `READY_FOR_HUMAN_REVIEW`. |
| 3 | Branch reconciliation + push | Landing plus a content-neutral co-author rewrite: 92/92 trees identical, 27 trailers removed, `--force-with-lease`. |
| 4 | Phase 05 fallback proof | Failure injection proved at the HTTP seam **and** through a real LiteLLM Proxy. Not Complete — no real provider failure. |

Source commits now on `main`: `e110491`, `6821ab2`, `3d9901b`, `51f1dc5`, plus the commit that
adds this file. [V]

## 3. Phase board

"Complete" is the repository's own definition: implemented **and** tested **and**
live-verified. Nothing below is Complete by that standard except where marked.

| Phase | Status | What would move it | Evidence |
|---|---|---|---|
| 00 Architecture & Environment | Complete (as recorded) | — | [R] |
| 01 Basic LiteLLM Gateway | Complete (as recorded) | — | [R] |
| 02 Provider Expansion | In progress — **1 of 14** aliases has runtime evidence | Real calls per alias; 7+ blocked on account credit | [V] 14 aliases configured; 12 marked "Configured; unverified" |
| 03 Model Registry | Complete | — | [R] |
| 04 Virtual Models | Complete | — | [R] |
| 05 Fallback Engine | **Implemented + failure-injection verified; not Complete** | One **real** provider failure through a working alias | [V] Phase 05 proof artifact |
| 06 Health Monitoring | Implemented — passive cooldown only, active checker unwired | Decide: wire it, or record passive-only as the design | [R] |
| 07 Observability | Implemented | — | [R] |
| 08 PostgreSQL | Complete (documented run) | — | [R] |
| 09 Auth & API Keys | Complete (documented run) | — | [R] |
| 10 Budgets & Rate Limits | Implemented — live rejection paths not exercised | Prove exhaustion and 429 + `Retry-After` against real PG/Redis | [R] |
| 11 Routing Intelligence | Implemented — capability evidence missing for most deployments | `docs/capabilities.md` records **11** aliases with no runtime evidence | [V] |
| 12 Model Scoring | Implemented — deterministic-v1 live, benchmarks synthetic | — | [R] |
| 13 ML Router | **`READY_FOR_HUMAN_REVIEW`** — 145 rows, 140 clean, `training_authorized: false` | Owner sign-off, then more telemetry (28-row eval split is far too thin) | [V 2026-11-22] |
| 14 Benchmarking | Planned | — | [R] |
| 15 Admin Dashboard | Planned | — | [R] |
| 16 Remote Access / Tailscale | Planned | — | [R] |
| 17 Security Hardening | Planned | — | [R] |
| 18 Testing & Regression | Planned — tests exist, not structured as a regression suite | — | [R] |
| 19 CI/CD | Implemented — hosted CI green on `main` | — | [V] |
| 20 Production Architecture | Planned | — | [R] |

## 4. Blockers

| Blocker | Detail | Kind |
|---|---|---|
| 7 provider aliases | openai 429 (no credits), minimax / cerebras / deepinfra / huggingface 402, kimi 429, together 401; gemini intermittent | **External** — money, not code |
| `docs/providers.md` vs `config/config.yaml` | The doc marks only gemini verified; the 2026-10-08 config comments name Groq and OpenRouter. One of them is wrong, and Phase 02's number depends on which | **Local** — solvable today |
| Phase 13 training | `training_authorized: false`; needs owner approval *and* a healthier sample | **Owner** |
| Docker build | Fails locally (daemon unavailable); passes in CI | [U] — not re-checked this session |

## 5. Term plan — a reconstruction, not a recovered document

The immediate / near-term / long-term split existed only in conversation and was never
persisted. What follows is rebuilt from verified state, not recalled. Expect it to differ in
emphasis from whatever was discussed earlier.

**Immediate — no external dependency**

1. Close Phase 05 with one real provider failure. Cheapest route: force a genuine 404 from
   `sabiroute-gemini` using a retired model id. No accounts, no spend, no new code.
2. Reconcile `docs/providers.md` against `config/config.yaml` comments.
3. Phase 10 live rejection paths against disposable PG + Redis.
4. Phase 06: wire the active checker or record passive-only as deliberate.

**Near term — mostly blocked on accounts**

Phase 02 per-alias remediation · Phase 11 capability evidence · Phase 18 regression structure ·
Phase 13 owner sign-off plus more telemetry.

**Long term — not started**

Phases 14, 15, 16, 17, 20. Plus the interface layer below.

## 6. Corrections to the externally kept tracker

An owner-maintained tracker was found stale in four places on 2026-11-23:

| It said | Actual |
|---|---|
| Phase 02: 3 of 14, with "4 more from a bounded wave" | `docs/providers.md` supports **1**; the bounded-wave claim is not recorded in that file |
| Phase 05: "no live failure-injection evidence" | Superseded — 10/10 direct and 7/7 through a real proxy |
| Phase 13: "33 rows, BLOCKED" | **145 rows**, 140 clean; status is `READY_FOR_HUMAN_REVIEW` |
| "`sec/deps-nov` diverged, unresolved" | No divergence: `main` = `origin/main`. Non-`main` branches appear diverged only because of the SHA rewrite |

## 7. Interface inventory

**Present** [V]: `sabiroute` console script (`sabiroute.main:main`), `/v1/chat/completions`,
`api/chat.py`, `api/admin.py`, `api/health.py`, `web/`, `.vscode/`, `migrations/`, `Dockerfile`.

**Absent** [V — no `.vsix`, `extension.ts`, or `plugin.xml` found; no root `package.json`
declaring a VS Code engine]: native VS Code extension, JetBrains plugin, IDE integration SDK,
browser extension, Slack/Teams bot. The `sabiroute` CLI starts the server; it is not an
independent client tool.

## 8. Traps — each cost a session to find

1. **`cooldown_until = None` on an unhealthy deployment is a permanent removal**, not a reset.
   Only an *expired* deadline re-enters the half-open path. Never "simplify" recovery by
   clearing it.
2. **Verify Claude attribution by parsing trailers, never by grep.** Commit `e110491`'s body
   contains a line that *begins* with `Co-Authored-By:.*Claude` as prose, so any grep matches it:
   `git log -1 --format='%(trailers:key=Co-Authored-By,valueonly)' <sha>`.
3. **Run tests in the worktree that holds the branch being pushed.** The primary checkout is on
   a different branch and yields a smaller count.
4. **`CLAUDE.md` roadmap lines are column-padded.** Match on a prefix, not equality.
5. **A shared LiteLLM Proxy carries deployment-failure state between requests** and can change
   which alias answers. Use a fresh proxy per scenario when measuring routing behaviour.

## 9. Bottom line

The gateway core is implemented and tested. Production-ready requires every phase Complete,
and 0 of 21 phases meet that bar on live evidence today. The binding constraints are not the
unstarted phases — they are Phase 05 and Phase 13, each **one real datapoint** away from being
honestly defensible, and seven aliases dark on account credit.

## Next action

Close Phase 05 with one genuine provider failure through `sabiroute-gemini`, then reconcile
`docs/providers.md` against the config comments. Both are local and cost nothing.
