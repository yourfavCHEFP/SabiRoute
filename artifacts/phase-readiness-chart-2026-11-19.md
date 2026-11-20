# SabiRoute phase readiness — 2026-11-19

**Verdict: NOT PRODUCTION READY.** 6 of 21 phases carry the README's `Complete` label; 7 have code + tests but lack required verification; 2 remain open; 6 are not started. Phase 13 is explicitly **in progress with a blocked 13.3 training gate**. No model has been trained or deployed.

Source: `README.md:322-344` (phase table), `README.md:352-376` (Phase 13), T0–T6 reports in `artifacts/production-readiness/`, `.superpowers/sdd/2026-11-18-s1-s18-local-gap-closure/progress.md:81-85` (SDD ledger). Verification below was re-run at current HEAD `13d0377`, branch `sec/deps-nov`; T7 reconciles T0–T6 evidence without upgrading any phase label.

## Verification bands — one block = one phase

```
VERIFIED ON DOCUMENTED LIVE PATH  ██████     6 / 21   00 01 03 04 08 09
CODE + TESTS ONLY                 ███████    7 / 21   05 06 07 10 11 12 19
ACTIVE / OPEN GATE                ██         2 / 21   02 13
NOT STARTED                       ██████     6 / 21   14 15 16 17 18 20
```

`Complete` in this repository means implemented, tested, and exercised on a **documented live path**. The README warns that this evidence is success-only and was not re-run as part of the last documentation update. It is not a production-verified label.

## Phase matrix

Status glyphs: `✓` Complete · `~` Implemented · `•` In progress · `–` Planned · `⛔` blocked sub-gate. Glyphs and words carry the status; no categorical color palette is used.

| Phase | Focus | Status | Gate evidence / open constraint |
|---:|---|---|---|
| 00 | Architecture and environment | ✓ COMPLETE | Typed config, validation, app factory; full suite green |
| 01 | Basic LiteLLM gateway | ✓ COMPLETE | Non-streaming + streaming documented live; fallback tested only |
| 02 | Provider expansion | • IN PROGRESS | 3 of 14 aliases have runtime evidence; Together auth failure recorded |
| 03 | Model registry | ✓ COMPLETE | `config/config.yaml` is the runtime catalog |
| 04 | Virtual models / policies | ✓ COMPLETE | Six policies validated at startup; `research` exercised live |
| 05 | Fallback engine | ~ IMPLEMENTED | Retry/fallback in `api/completions.py`; local stub retry/fallback/cooldown tests re-executed (T2); no live-provider failure injection |
| 06 | Health monitoring | ~ IMPLEMENTED | Passive cooldown/recovery tested; no active checker wired |
| 07 | Observability | ~ IMPLEMENTED | Trackers wired; local stored-record success/failure linkage and rejection of unlinked outcomes verified (T3); live-provider telemetry UNVERIFIED |
| 08 | PostgreSQL | ✓ COMPLETE | `PostgresApiKeyStore` exercised on documented live run; real PostgreSQL tenant-isolation control passed on disposable infrastructure (T1) |
| 09 | Authentication and API keys | ✓ COMPLETE | Client/admin boundary; key issued and revoked on that run |
| 10 | Budgets and rate limits | ~ IMPLEMENTED | Unit/API tested; disposable-service Redis/PostgreSQL integration tests passed (T1); live rejection paths not exercised on documented live provider path |
| 11 | Capability-aware deterministic routing | ~ IMPLEMENTED | Capability evidence missing for most deployments |
| 12 | Measured deterministic scoring | ~ IMPLEMENTED | `deterministic-v1` live; benchmark evidence synthetic only |
| 13 | ML-assisted routing | • IN PROGRESS + ⛔ 13.3 BLOCKED | Historical integrity failure, no outcome variation, no chronological split; fresh re-audit found no dataset and failed before querying, leaving all five checks UNVERIFIED; ML NOT DONE (T4) |
| 14 | Benchmarking | – PLANNED | Compare against unchanged deterministic baseline |
| 15 | Admin dashboard | – PLANNED | Not started |
| 16 | Private remote access / Tailscale | – PLANNED | Not started |
| 17 | Security hardening | – PLANNED | Baseline controls maintained; preparation-only evidence recorded (T6); live/placeholder classification, external scanners, Git history, deployed probes, and full audit UNVERIFIED |
| 18 | Testing and regression | – PLANNED | Tests required throughout earlier phases |
| 19 | CI/CD | ~ IMPLEMENTED | Five check steps; local pytest with disposable services, Ruff, mypy, node --check passed (T5); local docker build failed (Docker daemon unavailable); hosted Actions UNVERIFIED |
| 20 | Production architecture | – PLANNED | Not started |

## Phase 13 sub-gate detail — ML is not done

| Sub-gate | Status | Evidence |
|---|---|---|
| 13.1 Data foundation | IMPLEMENTED | Schema `1.1` feature snapshots + read-only audit tool, committed as `71271fc` |
| 13.2 Targets / labels / provenance / audit | IN PROGRESS | Documentary live sub-gate passed; aggregate closure pending; fresh re-audit produced no numeric result (T4) |
| 13.3 Training and evaluation | **BLOCKED** | Historical no outcome variation and no defensible chronological split; fresh checks UNVERIFIED; training unauthorized |
| 13.4 Guarded inference | BLOCKED | Pending a valid trained artifact |
| 13.5 ML selector integration | BLOCKED | Pending validated inference |

Historical documentary audit (not a fresh run): 7 logical requests, 6 provider attempts, 5 feature snapshots, 6 labeled outcomes; all attempts successful; 1 feature/outcome count mismatch; 1 outcome without a feature snapshot; only 2 attempts with verified temporal provenance; no usable chronological evaluation split. The 2026-11-19 fresh re-audit found no dataset on disposable PostgreSQL and failed during SQLAlchemy dialect initialization before querying; pair integrity, temporal provenance, outcome variation, chronological-split feasibility, and live-row exclusions are all UNVERIFIED. Verdict: ML NOT DONE; training_authorized unchanged; no model has been trained or deployed (T4).

## Current global gates — VERIFIED BY RUNTIME at HEAD `13d0377`

```
no-service baseline: pytest 866 passed, 10 skipped exit 0
disposable-service run: pytest 875 passed, 1 skipped exit 0
ruff src/tests/scripts/config exit 0, all checks passed
mypy src no issues in 61 files exit 0
node --check web/app.js no output exit 0
REPORTS-MANIFEST.sha256 13 OK exit 0
git diff --check exit 0
docker build -t sabiroute:ci . exit 1 (local Docker daemon unavailable)
pytest tests/test_r3_secret_leakage.py 33 passed exit 0 (T6)
```

Baseline skips: 5 Redis-gated, 4 PostgreSQL-gated, 1 registration-ledger authorization; with disposable services only the registration-ledger authorization skip remains. Real Redis/PostgreSQL controls and teardown were verified on disposable loopback infrastructure (T1/T5); owner/default services were not used. Local stub fallback/cooldown (T2) and local stored-record telemetry linkage (T3) were verified; live-provider failure injection and live-provider telemetry remain UNVERIFIED. Container build and hosted Actions are UNVERIFIED; security preparation is count-only with candidate live-vs-placeholder classification, external scanners, Git-history scan, deployed probes, and full audit UNVERIFIED (T6). Production rollout remains UNVERIFIED.
## Chart method note

Form: status strip + table, because 21 ordered phases with four distinct states read better as a table than as >7 colored categories. Status is encoded by glyph and label, never color alone. The reserved status palette was checked with the dataviz validator; its failures are expected because that validator's categorical checks do not apply to status colors, which ship with icon + label by design.
