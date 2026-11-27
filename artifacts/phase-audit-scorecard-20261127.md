# Phase Audit Scorecard — phases 00–20

Recorded 2026-11-27 on `feat/sabiroute-routing-foundation` (HEAD `80bb83c`).

**Provenance:** authored by `orch-chef-p@factory` directly from the repository, after
`orch-lead@factory` claimed the audit row and returned
`Incomplete response returned, reason: max_output_tokens` without writing an artifact.
Every status below is derived from the tree and commands cited, not from the README's claim.

**Verification basis run for this audit:**
- `./.venv/bin/python -m pytest -q` → **1123 passed, 9 skipped** (27.53s). The 9 skips are all
  environment-gated on `SABIROUTE_TEST_REDIS_URL` / `SABIROUTE_TEST_PG_URL`.
- `curl -m 3 http://127.0.0.1:8000/health` → `000` (no gateway running).
- `docker ps` → no containers running.
- Redis and PostgreSQL paths are therefore **unverified in this run**.

**Vocabulary (strict, from README legend):** Complete · Live-verified · Tested · Implemented ·
In progress · Blocked · Planned. *Implemented* is not *Complete*; a green unit suite is not
live evidence.

---

## Scorecard

| Phase | Status | Evidence | Gap | Next action |
|---:|---|---|---|---|
| 00 | Complete | `gateway.py`, `main.py`, `config/{loader,models,validation}.py`; full suite green (1123 pass) | none blocking | maintain |
| 01 | Complete | `api/completions.py` (streaming + non-streaming), `providers/litellm_client.py`; `tests/test_completions*.py` (12 files) | documented live path is success-only and not re-run; nothing listening on `:8000` now | bring the stack up and re-run one completion to re-establish a live path |
| 02 | In progress | 3 of 14 aliases have runtime evidence — `gemini`, `groq`, `openrouter` (`docs/capabilities.md`); 11 marked unknown | 11/14 deployments have zero runtime evidence; Together auth failure recorded 2026-10-10 | run `scripts/test_providers.py` against the next unverified deployment |
| 03 | Complete | `providers/registry.py`; `config/config.yaml` is the runtime catalog; `tests/test_registry.py` | none blocking | maintain |
| 04 | Complete | `routing/policies.py`; six route policies validated at startup; `tests/test_policies*.py` | `research` policy is the only one exercised live | exercise a second policy on the live path |
| 05 | Complete | retry/fallback loop in `api/completions.py` routes every attempt through `Router.choose_deployment`; `tests/test_fallback_injection.py`, `tests/test_proxy_attempt_census.py`; live real-provider failover **PASS** re-verified 2026-11-27 (`artifacts/phase05-live-fallback-reverify-20261127.md`) | failover is proven on a harness-supplied `primary`/`secondary` topology; the shipped catalog gives **every alias exactly one deployment**, so no configured alias has a second target | add a second deployment to at least one alias, or record the single-target constraint as accepted design |
| 06 | Complete | passive success/failure + cooldown registry in `routing/health.py`; `tests/test_health*.py`, `tests/test_router_and_health_guards.py`; live cooldown → recovery **PASS** re-verified 2026-11-27 (`artifacts/phase06-live-reverify-20261127.md`) | active `ProviderHealthChecker` was removed by design, not neglect (`docs/routing.md`, amendment 2026-11-23, owner accepted passive-only) | maintain; re-open only under the routing.md re-opening conditions |
| 07 | Complete | `monitoring/{metrics,latency,errors,usage}.py` wired into gateway state; `/admin/{metrics,latency,errors,usage}`; success path live-verified 2026-11-23 (`artifacts/sprint-4/PHASE07-LIVE-TELEMETRY-2026-11-23.md`); **failure path live-verified 2026-11-27** (`artifacts/phase07-metrics-under-failure-20261127.md`) | trackers remain in-process and still reset on restart; `signals_store.py` persists health/latency signals, **not** these counters | make the counters durable, or record the restart-reset as accepted design |
| 08 | Complete | `security/store.py` `PostgresApiKeyStore`; `docs/phase13-data-foundation.md` documents the live run | **PostgreSQL integration tests skipped locally** (`SABIROUTE_TEST_PG_URL` unset); never validated on managed PG | set `SABIROUTE_TEST_PG_URL` and run the gated PG tests |
| 09 | Complete | `security/{auth,keys}.py`; client/admin boundary; `tests/test_api_key_validation.py`, `test_auth_dependencies.py`, `test_admin.py` | key issuance/revocation rests on the same documentary run as 08 | re-issue and revoke a key against a live stack |
| 10 | **Implemented** | `security/{budgets,rate_limit}.py`; `tests/test_phase10.py`, `test_rate_limit*.py`, `scripts/verify_phase10.py` | **all 4 Redis rate-limit tests skipped locally**; rejection paths never exercised live; token estimator is text-only | run with `SABIROUTE_TEST_REDIS_URL` set, then force a real 429 |
| 11 | **Implemented** | `capabilities.py`; unknown never counts as support; `tests/test_capabilities*.py` | capability evidence exists for only 3/14 deployments — blocked on Phase 02 | collect capability evidence for the next deployment |
| 12 | **Implemented** | `routing/scoring.py` (`deterministic-v1`); `scripts/benchmark_routing.py` | benchmark is **synthetic only**; no warm live-routing telemetry | run the harness with real provider outcomes |
| 13 | In progress | 13.1 `intelligence/dataset.py` = **1560 lines, implemented**; `training_authorized: false` enforced in code (3 sites); `docs/phase13-data-foundation.md` | **13.2 aggregate closure pending**; 13.3 training **blocked**; `intelligence/{classifier,scorer,selector}.py` and `routing/intelligent.py` are **0-line stubs**; live-path evidence is success-only | stay blocked — resolve 13.2 aggregate integrity and chronological split first; do not train |
| 14 | **Implemented** | `scripts/benchmark_routing.py` — reproducible synthetic `priority` vs `measured` comparison, imports real `Router`/`HealthRegistry`/`ScoringSettings` | synthetic outcomes only; no real-provider benchmark | promote to a provider-backed benchmark run |
| 15 | Planned | `api/admin.py` is an admin **API**, not a dashboard; `web/` is the SabiChat client, not admin UI — no dashboard exists | whole dashboard | build it after the operator loop it serves is stable |
| 16 | Planned | no Tailscale or remote-access code in `src/`, `config/`, or `.github/` (grep clean) | whole phase | defer |
| 17 | In progress | `security/redaction.py` (64 lines), `api/body_limit.py` (121 lines), `api/deadline.py`, `security/auth.py` operate throughout | `security/permissions.py` is a **0-line stub**; no formal hardening review | finish `permissions.py` and run a security pass |
| 18 | **Implemented** | `docs/phase18-testing-evidence.md` records 1123 passed / 100% coverage / ruff+mypy clean — **re-verified this audit: 1123 passed, 9 skipped** | 9 environment-gated skips; no regression baseline pinned in CI | set Redis+PG in CI so the skips execute |
| 19 | Implemented (definition + local execution) | `.github/workflows/ci.yml`: locked `uv sync --frozen`, pytest w/ Redis service, ruff, mypy, `node --check`, container build; `tests/test_deployment.py` | **no hosted Actions run verified**; `gh` not authenticated locally so runs could not be listed | push and confirm one green hosted run |
| 20 | **Implemented** | `Dockerfile` (63), `docker-compose.yml` (278), `src/sabiroute/migrate.py` (66), `docs/deployment.md` (173); one-shot migration gated before API start | no staging deployment; no managed-PostgreSQL validation; Phase 20 review still gates public exposure | run the Compose stack end-to-end, then schedule the Phase 20 review |

---

## Summary

1. **Complete: 10 phases** — 00, 01, 03, 04, 05, 06, 07, 08, 09, and no others. Of these, 01 and
   04 rest on a documented live path that is **success-only and not currently running**; 06 was
   re-verified live on 2026-11-27, including the failure and recovery transitions; 05 was
   re-verified live on 2026-11-27 against real providers, under a real upstream failure; 07 was
   live-verified on both the success path (2026-11-23) and the failure path (2026-11-27).
2. **Implemented but not live: 5 phases** — 10, 11, 12, 14, 18 (plus 20 as a
   deployment foundation). All have code and tests; none has exercised its failure path
   against real providers. Phases 05, 06 and 07 left this group on 2026-11-27.
3. **Highest-leverage next phase by the constitution's engineering order: Phase 02**
   (provider expansion). It is the earliest non-Complete phase, and it is the direct
   upstream blocker for 11 (capability evidence), 12 (real telemetry) and 13 (dataset
   coverage). Finishing 02 converts three "Implemented" phases into promotable ones at once.

---

## README-vs-tree disagreements

Four rows in the README phase table understate what the tree actually contains. None
overstates — the README errs conservative, which is the right direction for this project.

| Phase | README says | Tree shows | Assessment |
|---:|---|---|---|
| 14 | `Planned` | `scripts/benchmark_routing.py` — working synthetic harness importing the real router | README understates; should read *Implemented (synthetic)* |
| 17 | `Planned` | `security/redaction.py`, `api/body_limit.py`, `api/deadline.py` all active on the request path | README understates; should read *In progress* |
| 18 | `Planned` | `docs/phase18-testing-evidence.md` + 1123 passing tests + 100% coverage claim, re-verified today | README materially understates; should read *Implemented* |
| 20 | `Planned` | `Dockerfile`, 278-line `docker-compose.yml`, `migrate.py`, `docs/deployment.md`, `tests/test_deployment.py` | README understates; should read *Implemented (deployment foundation)* — the limitations section already says this, contradicting the table |

Additional correction: an incoming handoff asserted "full suite 1474 pass". The measured
figure on this branch is **1123 passed, 9 skipped** — consistent with
`docs/phase18-testing-evidence.md`. The 1474 figure is not reproducible here and should not
be quoted.

## Two 0-line stubs worth naming

`src/sabiroute/security/permissions.py` and `src/sabiroute/intelligence/{classifier,scorer,selector}.py`
plus `src/sabiroute/routing/intelligent.py` exist as empty files. They inflate an apparent
module count without carrying behaviour. Phase 13's stubs are correctly gated; Phase 17's stub
is an unowned hole.

## Safety state

- `training_authorized` remains **`false`**, enforced at `intelligence/dataset.py:657`, `:698`, `:1106`.
- **Phase 13 stays gated and blocked.** No model has been trained or deployed.
