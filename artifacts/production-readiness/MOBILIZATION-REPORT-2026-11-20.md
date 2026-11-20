# Mobilization Report — 2026-11-20 (Gates 1–4)

## ACTION COMPLETED
- Pushed `sec/deps-nov` HEAD to new branch `sec/deps-nov-ci` (no history rewrite, no main touch). Hosted CI run completed: success, 3m4s.
- Ran local security audit (Gate 2): gitleaks, semgrep, bandit, zizmor, hadolint, osv-scanner; trivy failed (network/DB download). Outputs in `artifacts/production-readiness/scan-outputs/`.
- Attempted Gate 3 (bounded 5-alias live wave): issued client key via admin API; all 5 calls returned 502 (transport) because the LiteLLM execution engine (port 4000) is not running and SabiRoute's config is not LiteLLM-proxy-compatible. Outbound network to providers works (401 direct).
- Applied pending schema migration (0006 accounting lineages) via `sabiroute.migrate` to repair chat/key store schema; gateway now starts cleanly.
- Gate 4 (dataset + audit): blocked on Gate 3 — no telemetry generated because no successful live calls occurred.

## GATE-BY-GATE

### Gate 1 — Hosted CI: PASS (VERIFIED BY RUNTIME)
Branch `sec/deps-nov-ci` pushed; CI run 44630960712 completed `success` in 3m4s (pytest with Redis service, Ruff, mypy, node --check, docker build). All steps green in GitHub's environment.

### Gate 2 — Security audit: LIMITED (VERIFIED BY RUNTIME + VERIFIED BY INSPECTION)
- gitleaks: 37 findings — all in gitignored `.env`/`.env.backup` and untracked `docs/`, `tests/`, `security-reports/`. None in tracked `src/`. Values not printed.
- semgrep: 13 findings (12 WARNING, 1 ERROR).
- bandit: 14 findings, all LOW severity.
- zizmor: 18 findings (6 unsuppressed: 2 medium, 4 high) in `.github/workflows/claude.yml` (dangerous-triggers, unpinned-uses).
- osv-scanner: 82 unique vuln IDs across 9 packages (aiohttp, certifi, dnspython, filelock, litellm, oauthlib, opentelemetry-api, pyasn1, virtualenv).
- hadolint: 2 findings (info + warning) in Dockerfile.
- trivy: FAILED — could not download vulnerability DB (network timeout). UNVERIFIED.
- Candidate live-vs-placeholder classification: UNVERIFIED (no-value constraint).

### Gate 3 — Live provider calls: BLOCKED (VERIFIED BY RUNTIME)
Root cause: SabiRoute delegates execution to a LiteLLM proxy at `http://127.0.0.1:4000`, which is not running. SabiRoute's `config/config.yaml` uses SabiRoute's own `os.environ/` resolver syntax and is not consumable by LiteLLM directly. Outbound network to providers works (direct curl returns 401). No live call succeeded; no telemetry generated. `training_authorized` unchanged (false).

### Gate 4 — Phase 13 dataset/audit: BLOCKED (VERIFIED BY RUNTIME)
Depends on Gate 3 telemetry. No dataset available; Phase 13.3 remains BLOCKED, verdict `ML NOT DONE`.

## ARCHITECTURAL POSITION
Unchanged. SabiRoute decides; LiteLLM executes. No pipeline component modified by this mobilization except schema migration 0006 (data layer). PostgreSQL gained one table; Redis untouched; Telemetry gained no new rows (Gate 3 blocked); Security gained scan evidence only.

## ROADMAP POSITION
Phase 19 (CI/CD) advances to hosted-run-verified (Gate 1). Phase 17 (Security Hardening) gains prep evidence (Gate 2) but no phase upgrade. Phase 02 (Provider Expansion) unchanged (3/14). Phase 13 remains BLOCKED.

## DEPENDENCY IMPACT
Gate 3/4 unblock requires: (a) a running LiteLLM proxy with a LiteLLM-native config, or (b) a documented live-run procedure using an existing proxy. This is a Phase 01/02/20 setup item, not a one-command step.

## NEXT STEP
Owner decision: provision a LiteLLM proxy (config + run) to enable Gate 3, then re-run Gate 4 audit. Alternatively, accept that live telemetry collection is deferred and close the tranche with Gates 3/4 BLOCKED.

## DO NOT TOUCH YET
- `.env`, `uv.lock`, protected paths, source/tests (no edits this mobilization except migration).
- Branch divergence (sec/deps-nov vs origin) — still unresolved; Gate 1 used a new branch name to avoid it.
- Phase 13 training / `training_authorized`.
- Provider credentials (names/status only ever reported).

## CURRENT PROJECT STATUS
```
CURRENT GATE: Mobilization 2026-11-20 — Gate 1 PASS, Gate 2 LIMITED, Gate 3 BLOCKED, Gate 4 BLOCKED
CURRENT PHASE: Phase 19 CI/CD advances (hosted run verified); Phase 17 prep only; Phase 02 unchanged; Phase 13 BLOCKED
PROVEN: hosted CI green (3m4s); 4 scanners ran with counts above; gateway starts clean post-migration; outbound network to providers works
UNPROVEN: live provider calls (no LiteLLM proxy); telemetry rows; Phase 13 dataset/audit; trivy scan; candidate live-vs-placeholder classification
BLOCKED BY: LiteLLM proxy provisioning (Gate 3/4); trivy network; owner authorization for training/push-to-main/full audit
NEXT: owner decides on LiteLLM proxy provisioning or defers Gates 3/4
```