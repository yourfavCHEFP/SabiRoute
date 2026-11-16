# R6 T14 — Independent Audit of T13 and R6.0 Decision-Readiness Verification

**Status:** audit only. **This report approves nothing, adopts no ADR, grants no G7, and authorises no implementation, test, or U0/U1/R6.1 work.**
**Mode:** read-only. Exactly one file was created — this report. No source, test, config, migration, dataset, dependency, or predecessor report was modified.
**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`.
**Audited artefact:** `docs/r6-t13-documentation-correction-and-owner-decision-preparation.md` (58,863 B, 803 lines, untracked).

**Evidence labels used throughout:**

| Label | Meaning |
|---|---|
| `VERIFIED` | Read directly from the working tree at HEAD `319a711`; exact anchor cited. |
| `STATIC-ANALYSIS FINDING` | Reachable by control-flow inspection; runtime consequence **not executed**. |
| `Unexecuted runtime hypothesis` | A behavioural outcome reasoned from code, never observed. Always labelled as such. |
| `CONTRADICTED` | Source or document evidence contradicts the T13 statement. |
| `PARTIALLY VERIFIED` | The conclusion holds; a supporting statement, mechanism, or scope does not. |
| `UNRESOLVED` | Evidence insufficient to decide. |

**Independence note.** Every anchor below was re-derived from source at HEAD. No line number or conclusion was carried forward from T13 on T13's authority. Where this audit's number differs from T13's, the difference is stated.

---

## 1. Mission Scope and Authority

T14 answers one question: **is T13 accurate and internally consistent enough to be the decision basis for the R6.0 owner session?**

It does **not** re-open settled architecture, produce new architecture, or convert recommendations into decisions. It re-reads source for the five highest-consequence T13 claims, re-counts the decision register, and re-checks the ADR and gate boundaries.

**Authority boundaries honoured:** no ADR adopted; no gate granted; no decision marked approved; no test run; no provider contacted; no Git mutation; no predecessor touched.

---

## 2. Actual Repository Baseline

`VERIFIED` by direct command at mission start.

| Fact | Value | Method |
|---|---|---|
| Repository root | `<repo-root>` | `pwd` |
| Branch | `feat/sabiroute-routing-foundation` | `git rev-parse --abbrev-ref HEAD` |
| HEAD | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` | `git rev-parse HEAD` |
| Upstream | `origin/feat/sabiroute-routing-foundation` | `git rev-parse @{upstream}` |
| Divergence | **ahead 6, behind 3** | `git rev-list --left-right --count` |
| Staged tracked changes | none | `git diff --cached --stat` (empty) |
| Unstaged tracked changes | none | `git diff --stat` (empty) |
| Untracked entries | 110 | `git status --porcelain=v1 \| wc -l` |
| Ignored entries | 35 | `git status --porcelain=v1 --ignored` |
| Worktrees | 6 registered, 2 `prunable`, none touched | `git worktree list` |

**Baseline verdict: MATCHES the mission's expected HEAD and branch exactly.** T13's own baseline table (§3) also matches, with one reconciled difference in untracked count (below).

**Divergence caveat.** Local HEAD is six ahead of and three behind origin. Every anchor here is against **local** `319a711`. A reviewer working from a remote ref must re-anchor. T14 did not fetch, pull, or reconcile.

---

## 3. T13 Artefact Integrity and Git-Status Discrepancy Reconciliation

`VERIFIED` — the discrepancy is fully resolved, not merely noted.

| Check | Result |
|---|---|
| File exists | **Yes** — `docs/r6-t13-documentation-correction-and-owner-decision-preparation.md` |
| Size / lines | **58,863 bytes / 803 lines** |
| `git ls-files` | **empty** — not tracked |
| `git check-ignore -v` | **rc=1** — no ignore rule applies |
| `git status --porcelain` | **`??`** — untracked |
| Present in any commit | **No** — `git log --all -- <path>` returns nothing |
| Present in index | **No** — `git ls-files --error-unmatch` reports "did not match any file(s) known to git" |

**Reconciliation of the transcript contradiction ("created one new report" vs "nothing new was introduced").** Both statements are true and non-conflicting:

- *"Created one new report"* is a **working-tree** fact — the file now exists on disk.
- *"Nothing new was introduced"* is a **Git-history** fact — no commit, no index entry, no tracked change. `git diff` and `git diff --cached` are both empty.

An untracked file is neither "new in Git" nor "absent". T13's own §22.1 ("Exactly one file created") and its mission's "no commit" rule are therefore mutually consistent. **No contradiction remains.**

**Untracked-count reconciliation (109 → 110).** T13 §3 records 109 untracked entries; T14 observes 110. The difference is exactly T13 itself, which did not exist when T13 measured its own baseline (T13's table states "T13 target before this file: absent"). The current count is the pre-T13 count plus T13. **Reconciled; not an error.**

**Finding AF-01 — `VERIFIED`.** T13 is a genuine, complete, untracked, un-ignored working-tree artefact; the transcript discrepancy is a working-tree-vs-history artefact, not a governance breach.

---

## 4. Predecessor Corpus Integrity

`VERIFIED` — all six predecessors present, none modified.

| Report | Bytes |
|---|---:|
| `docs/r6-architecture-decision-pack.md` | 35,947 |
| `docs/r6-decision-resolution-and-approval-campaign.md` | 50,154 |
| `docs/r6-t9-capability-recovery-review.md` | 96,860 |
| `docs/r6-t10-decision-consolidation-and-freeze-preparation.md` | 54,604 |
| `docs/r6-t11-r6-readiness-and-implementation-preparation.md` | 69,543 |
| `docs/r6-t12-accounting-integrity-and-gate-closure.md` | 88,581 |

All are untracked working-tree files (same `??` status as T13). Sizes match T13 §3's recorded values exactly. **Finding AF-02 — `VERIFIED`.**

---

## 5. Five Critical Technical Claim Audits

### 5.1 U0 Spec 5 — known-failure then no-usage success

**Finding AF-03 — `VERIFIED` (source fact + static-analysis).**

The complete control flow was re-derived, in order, from source:

| # | Step | Anchor | Observed |
|---|---|---|---|
| 1 | Flag initialised | `completions.py:1316` | `provider_usage_unknown = False` |
| 2 | Attempt 1 failure usage extracted | `:1567` | `failure_usage = _actual_tokens(exc.response_body)` |
| 3 | `_actual_tokens` returns `None` when no usage object | `:239–242` | `usage is None → return None` |
| 4 | Outer branch entered only if usage present | `:1568` (12-space indent) | `if failure_usage is not None:` |
| 5 | Flag set only when **total is unknown** | `:1571–1572` (16-space indent) | inner `if failure_usage[2] is None:` |
| 6 | `elif` attaches to the **outer** `if` | `:1573–1574` (12-space indent) | `elif budget_reserved:` — fires **only** when no usage object at all |
| 7 | Retry eligibility | `:1599–1601` | `retryable = status is None or status >= 500 or status in RETRYABLE_STATUS_CODES` (`{401,403,429}` at `:59`); break if `not retryable or (budget_reserved and provider_usage_unknown)` |
| 8 | Narrowing before retry | `:1603–1608` | `remaining = reserved_tokens - used`; break if `remaining <= estimated_input`; else narrow `max_tokens` |
| 9 | Success with no usage | `:1903` | `success_usage = _actual_tokens(body)` → `None` |
| 10 | Success path never sets the flag | `:1904–1906` | `if success_usage is not None:` — appends only; flag untouched |
| 11 | Settlement argument | `:1945–1953` | `tokens = (None,None,None) if provider_usage_unknown else _sum_actual_tokens(actual_usage_parts)` → flag `False` ⇒ **partial sum** |
| 12 | Budget settlement | `finish()` `:563–583` → `store.reconcile_budget` `:1213–1247` | `accounted_tokens = actual_tokens` when not `None` ⇒ settled at attempt-1 total only |
| 13 | HTTP response | `:1940–1944` | `JSONResponse(status_code=200, …)` |

**Confirming detail:** `_sum_actual_tokens` (`:253–264`) sums only the known parts across attempts, so with only attempt 1's usage present the "sum" is attempt 1's total — a genuine partial sum, not the original estimate. `reconcile_budget` initialises `accounted_tokens=estimated_tokens` at `:1201–1202` and overwrites it only when given a non-`None` value (`:1233–1234`).

**T13's conclusion is correct.** On a **budgeted** request whose first attempt fails **retryably with known total usage** and whose second attempt **succeeds with no usage object**, the flag is never set, and settlement uses the attempt-1 partial sum rather than holding the estimate. The exact misreading T13 attributes to T12 — treating `:1573` as firing "whenever budgeted" rather than only "when no usage object" — is confirmed at `:1568`/`:1573`.

**Is `xfail(strict=True)` technically justified?** Yes. The case **fails at baseline** for the stated defect and will **pass after a correct fix**; `strict=True` additionally catches a silent fix that fails to flip the marker. It must not be skipped or omitted.

**Fixture conditions required for a non-inconclusive test.** T13 §13.5 pins (a) retryable first failure, (b) known usage on the failure, (c) `remaining > estimated_input`. These are necessary and correct. T14 adds three conditions T13 leaves implicit, without which the test can pass or fail for the wrong reason:

- **(d)** No/oversized quota, so the **budget** path — not the quota governor — is the one under test.
- **(e)** The second attempt carries **no usage object at all**, not merely a missing `total`; otherwise `_actual_tokens` may synthesise a total from prompt + completion (`:246–247`).
- **(f)** The primary assertion must target the **budget reservation row** (`accounted_tokens == original estimate`) and the usage event (`total_tokens is None`), not only the HTTP status — status alone cannot distinguish held-estimate from partial-sum.

T13 §14.4's template asks for "the assertions"; it does not enumerate them. See correction **C-04**.

### 5.2 Pre-loop `finish()` NameError

**Finding AF-04 — `VERIFIED`, with the defect window broader than T13 states.**

- `finish()` is defined at `:542–550`. Its signature has **no `attempted` parameter** — `attempted` is a free variable read at `:602` (`if attempted:`).
- `finish()` declares `nonlocal budget_reserved, quota_reserved` (`:551`) but **not** `attempted`; `attempted` is read-only inside `finish()`.
- `attempted` is bound at `:1311` (`attempted: list[str] = []`).
- Quota is reserved at `:1161` (`quota_reserved = True`) with `quota_user_id` set at `:1162`.
- **Eight** pre-loop `finish()` call sites execute **after** the quota reservation and **before** `attempted` is bound: `:1171`, `:1180`, `:1189` (eligibility denials), `:1205` (budget pricing), `:1272` (budget reservation unavailable), `:1282` (budget changed), `:1291` (budget pricing), `:1299` (budget exceeded, a **429**).

Static consequence: when a quota is held and any of these calls reaches `:602`, the empty closure cell raises `NameError`. That `NameError` is an `Exception`, so it is caught by `except Exception as exc:` at `:623`, which:

1. logs and appends `quota_cleanup_failed`;
2. **replaces the intended response** with `_error_response(503, "Quota reservation could not be reconciled.", QUOTA_UNAVAILABLE)`;
3. **skips** `quota_reserved = False` at `:620`, so the reservation is never released on this path.

Therefore a pre-execution denial can surface as a **503 `QUOTA_UNAVAILABLE`** instead of its true status — including turning a **429 `budget_exceeded`** into a 503 quota outage — and the quota hold can leak. This is a **static-analysis conclusion**; no test was run and no runtime reproduction is claimed.

**Correction to T13 scope:** T13 §14.2 X6 frames the trigger as "budget-denied". The reachable window is all **eight** pre-loop denial sites, not only budget denial. The consequence class is identical; the trigger set is wider. See **C-05**.

### 5.3 Mixed known/unknown usage settlement

**Finding AF-05 — `PARTIALLY VERIFIED` (outcome correct; mechanism and consistency misstated).**

Two sequences were checked against the flag (`provider_usage_unknown`, all use sites enumerated: `1316, 1328, 1332, 1378, 1381, 1462, 1464, 1491, 1493, 1572, 1574, 1601, 1628, 1693, 1719, 1722, 1742, 1812, 1873, 1876, 1949, 1951, 1967, 1969, 1984, 1986`):

- **Known → unknown (X1).** Attempt 1 appends a known part and does not set the flag; attempt 2 (no usage) appends nothing and does not set the flag. Flag `False`. The budget path would settle the partial sum; the **quota path** (`:603`) computes `_sum_actual_tokens(actual_usage_parts)[2]` = attempt-1 total → `settle_quota(partial)`. Under-charge. **T13's mechanism description is correct here.**
- **Unknown → known (X2).** If attempt 1's failure body carries a usage object whose `total` is absent, `:1572` sets the flag **True** and appends a part with `total=None`. Attempt 2 appends a known total. On the **budget** path the flag now forces `(None,None,None)`, so `reconcile_budget` holds the estimate — correct. On the **quota** path, `:603` **ignores the flag entirely** and sums only the known totals → `settle_quota(attempt-2 total)` — a partial sum. Under-charge.

**The substantive finding T13 under-describes: the unknown-usage signal is applied asymmetrically.** Budget settlement honours `provider_usage_unknown` (`:1948–1951`, `:1966–1968`, `:1983–1985`), but **quota settlement at `:602–603` recomputes from raw parts and never consults the flag.** `settle_quota`'s own docstring (`store.py:1346–1352`) states unknown usage must hold the estimate; the caller can violate that intent whenever any part carries a known total.

Consequences for the owner:

- T13 §14.2 X2's stated cause ("Flag `False` ⇒ partial sum charged") is **wrong for the sub-case where attempt 1 carries a usage object with a missing total** — the flag is `True`; quota still charges the partial sum. The **outcome T13 predicts is right**; the **reason is not**.
- The settlement contract in B5 ("unknown wins at the full original estimate, never a partial sum") requires a fix in **both** governors. T7's settlement row should name the quota governor explicitly, or B5's scope understates the work.

### 5.4 Rollout apparatus

**Finding AF-06 — `VERIFIED`, with one nuance.**

- `grep` for `optimization_enabled | optimization_flag | feature_flag | kill_switch | killswitch | default_off | rollout` over `src/` → **zero hits**; over `config/` → **zero hits**.
- **Nuance:** a *different*, implemented switch exists — the Free Chat / shared-inference kill-switch (`store.py:1019 get_shared_inference`, `:1039 set_shared_inference`, policy table at `:111`/`:140`), re-checked **per attempt** at `completions.py:1351–1368` (`SHARED_INFERENCE_DISABLED`). This is a **general kill-switch precedent**, not the R6 optimisation rollout apparatus.

**Accurate status: the R6 optimisation rollout is SPECIFIED, UNBUILT.** T13's correction of T11 §19 criterion 17 (graded `PASS` at `r6-t11:418`) to **SPECIFIED, UNBUILT** is correct. The nuance strengthens, not weakens, the correction: a reusable per-attempt switch pattern already exists, but no optimisation flag, default-off path, or kill-switch for the new stage is built.

### 5.5 Capability declarations

**Finding AF-07 — `VERIFIED` exactly.**

| Fact | Value | Anchor |
|---|---|---|
| Configured aliases | **14** | `model_name` at `config.yaml:22,46,72,98,110,122,134,147,160,185,197,209,221,233` |
| Shared anchor | `&unverified_capabilities` at `:27`, referenced by `*unverified_capabilities` at `:103,115,127,140,153,190,202,214,226,239` (10 refs) + the first alias's inline block = **11 aliases UNKNOWN** |
| Explicit capability blocks | `:53` (gemini), `:79` (groq), `:166` (openrouter) = **3 BOUNDED `chat`** |
| `chat: true` | `:54, :80, :167` |
| `streaming: true` | `:88` (groq only) = **1** |
| `tool_use` / `structured_output` | `unknown` at `:33–34, 59–60, 85–86, 172–173` — **all 14 UNKNOWN** |
| CALIBRATED | **none** |

X-5's corrected figures — 11 UNKNOWN, 3 BOUNDED `chat`, 1 also `streaming`, zero `tool_use`/`structured_output` evidence, zero CALIBRATED — are exact. **No promotion follows from any C decision.**

---

## 6. X-1 through X-6 Verification

| Item | Finding | Verdict | Evidence | Consequence |
|---|---|---|---|---|
| **X-1** | AF-08 | `VERIFIED` | `docs/compression-discovery-packet.md` exists, **8,645 B**; names `src/sabiroute/compression/` with seven modes `off/lite/standard/aggressive/ultra/rtk/stacked` (`:64–66`) | BL-26's evidence sentence is false; its substance survives. The packet's package conflicts with ADR-2's proposed `request_transform/`. |
| **X-2** | AF-09 | `PARTIALLY VERIFIED` | R6 G4/G5/G7 defined verbatim at `r6-t9:417` and campaign `:332` | The defect is real; the "three colliding namespaces" framing **overstates** it — see below. |
| **X-3** | AF-10 | `VERIFIED` | T11 §15 `T7` = "D23 settlement fix + reconciler", `T8` = Tier-1 estimator; campaign §15 `T7` = "No dataset/migration change in v1"; T10 lists `T1–T7` plus an **unnamed** Tier-1 estimator row (`r6-t10:359`) | `T7` genuinely means two different things; BL-21 cannot issue until one numbering is fixed. |
| **X-4** | AF-11 | `VERIFIED` | T11 `:33` states "decide **12** questions"; T11 §18 enumerates A1–A4 (4) + B1–B5 (5) + C1–C3 (3) + D1–D3 (3) = **15** (`r6-t11:371–393`); two rulings unenumerated → **17** | T11's internal count is wrong by 3 (12 vs 15). T13's Group B additions B6/B7 are justified. |
| **X-5** | AF-07 | `VERIFIED` | See §5.5 | "All 14 UNKNOWN" is false; BL-10 is a repeat procedure, not a research programme. |
| **X-6** | AF-06 | `VERIFIED` | See §5.4 | T11's `PASS` is an overclaim; correct status is SPECIFIED, UNBUILT. |

**X-2 nuance (AF-09).** T13 §4.3's table lists three "colliding namespaces", but only **two** actually collide on the G-identifiers G4/G5/G7:

- **R6** scale: G4 = benchmark, G5 = red-team, G7 = implementation authorisation (`r6-t9:417`, campaign `:332`).
- **Developer Workflow Overhaul** scale: G4 = deadline/retries, G5 = async lifecycle, G7 = deployment/security (`SabiRoute_Developer_Workflow_Overhaul_Plan.md:239–247`). **Genuine collision.**
- **Repository remediation** uses letters **A–E**, with no G4/G5/G7 (`reports/remediation-roadmap-and-gates.md:56–68`). T13's own table leaves its G columns as "—". This is a **third gate vocabulary**, not a G-number collision.

The recommendation (a disambiguating gate register) stands; "three colliding namespaces" should be restated as "two colliding G-scales plus a separate lettered gate scale". See **C-01**.

**X-4 renumbering note — `VERIFIED`.** T11 B5 (Class-1 gating) → T13 C3; T11 C3 (reconciler) → T13 B9; T11 D1 (Track A engagement) → T13 D4. T13's new D1/D2/D5 are genuinely new. Reconcilers must map by content, not identifier — confirmed.

---

## 7. CLAUDE.md §12 Verification

**Finding AF-12 — `VERIFIED`: CLAUDE.md §12 is stale on all three named artefacts.** CLAUDE.md was **not** edited.

| CLAUDE.md §12 claim | Verified position at HEAD |
|---|---|
| `routing/fallback.py` is implemented | **File does not exist.** `src/sabiroute/routing/` contains only `health.py`, `intelligent.py` (0 B), `policies.py`, `router.py`, `scoring.py`. |
| `FallbackEngine` methods are never called | **No class of that name exists** — `rg "class FallbackEngine" src/` returns nothing. True only vacuously. |
| `providers/healthcheck.py` is referenced by nothing | **Module does not exist** (`providers/` = `base.py`, `litellm_client.py`, `registry.py`). Its absence is **enforced by test**: `tests/test_health.py:88` asserts `importlib.util.find_spec("sabiroute.providers.healthcheck") is None`. |

The *intended* meaning survives — retry/fallback logic lives in `api/completions.py`, and no provider healthcheck module is wired. The *description* names artefacts that never existed. Correction belongs in a separately authorised change; T14 does not make it.

---

## 8. Owner Decision Count and Consistency Audit

**Finding AF-13 — `VERIFIED`: the inventory is 23, correctly partitioned.**

| Group | Register | Count |
|---|---|---:|
| A | §7 A1–A4 | 4 |
| B | §8 B1–B9 | 9 |
| C | §9 C1–C4 | 4 |
| D | §10 D1–D6 | 6 |
| **Total** | | **23** |

Checks performed:

1. **Each appears once in its primary register.** Confirmed — no identifier repeats across §7–§10.
2. **All `OUTSTANDING`.** Confirmed — every row and §20 states no decision is approved.
3. **Recommendation ≠ decision.** Preserved — every recommendation is labelled as T12's recommendation, not an owner ruling.
4. **Group A + B as R6.0 conditions.** A1–A4 and B1 are marked "Blocks R6.0". Consistent with §19.1 conditions 1–3.
5. **Group C not an R6.0 blocker.** §9 states "informs; does not gate R6.0". C3 is marked "Partial R6.1". Confirmed.
6. **Group D not an R6.0 approval.** D1–D5 block R6.1; D6 blocks Release. No R6.0 claim. Confirmed.
7. **Signature not a 24th decision.** §20 item 24 ("Sign BL-22") is explicitly non-Group. Confirmed.
8. **CLAUDE.md correction not an R6 decision.** §20 item 25 is explicitly "a T13 finding, not an R6 gate". Confirmed.
9. **T1–T8 mapping stays a proposal until D5.** §6 and §6.1(4) both mark it `PROPOSED`, pending D5. Confirmed.
10. **T11/T12/T13 identifiers mapped by meaning.** §4's renumbering note matches source (see §6). Confirmed.

**Count correction:** none. The 23-decision inventory is accurate.

**Two precision issues (findings AF-14, AF-15):**

- **AF-14 — `PARTIALLY VERIFIED` (internal tension).** §8 marks only **B1** as blocking R6.0 (B2–B8 block R6.1; B9 blocks Release), but §19.1 condition 3 reads "Record **Group A + Group B** decisions, then sign BL-22." As written, that makes B2–B9 R6.0 conditions, contradicting the tables. It is resolvable — recording B2–B9 at the same session is harmless — but the condition text and the tables should agree. See **C-02**.
- **AF-15 — `PARTIALLY VERIFIED` (composite/incomplete decisions).** Two decisions bundle independently consequential choices or lack complete alternatives:
  - **D3** combines three choices — G7 scope = U0–U11, explicit `tests/` naming, and U12 placement in R6.7. Each is separately consequential.
  - **C1** is a genuine open conversation with **no recommendation and no listed alternatives** ("—"), unlike every other row.
  - **B1** ("adopt ADR-2 **with** C-1 name resolution") couples adoption to one of ADR-2's own unresolved conflicts; if C-1 is not settled, B1 is not cleanly decidable.
  - See **C-03**.

---

## 9. ADR-1 and ADR-2 Audit

### ADR-1 (Telemetry) — `VERIFIED` as a brief; `PROPOSED`, not adopted

| Element | Verified |
|---|---|
| Proposed target: separate content-free table `sabiroute_optimization_records`, PK `(request_id, attempt_number)` | **Absent from `src/` and `config/`** (`grep` returns nothing) — genuinely unimplemented. |
| Existing inline synchronous **fail-closed** telemetry on the accounting row | **Confirmed.** `finish()` awaits `store.finalize_usage_event` inline (`:650–656`); non-persistence returns **500** (validation) or **503** (`:666–677`). Row shape `_REQUEST_USAGE` at `store.py:65–88`. |
| P2 tenant guard precedent | **Confirmed** — `finalize_usage_event` scopes by `request_id` **and** `key_id`, and requires `final_status IS NULL` (`store.py:1516–1518`). |
| P3 additive migration via `_SCHEMA_VERSIONS` | **Present** — `store.py:89–95`. |
| P4 `_REQUIRED_COLUMNS` startup validation | **Present** — `store.py:703`, consumed at `:746`. |
| Adoption **freezes a target, implements nothing** | Correctly stated as a brief (§11). |

**Finding AF-16 — `VERIFIED`.** ADR-1 accurately distinguishes the proposed target from the live interim behaviour and lists unmet prerequisites. Adopting it would freeze a *target*, not build it.

### ADR-2 (R6.1 Foundation Contract) — `VERIFIED` as a brief; `PROPOSED`, not adopted

| Element | Verified |
|---|---|
| I1–I9 contract | **Nine contracts present** in `r6-t11` §8 (`I1…I9`, rows `:379–387` of that section). |
| Monotone-shrink, no per-attempt re-derivation | I3 states "one per logical request — re-derivation per attempt forbidden" and "Monotone-shrink: output ≤ original". |
| Fail-to-original, `CancelledError` propagates | I9 states it explicitly. |
| Phase-13 keep-out | I4 states "R6.1 must emit no snapshot fields". |
| One construction point before loop entry `:1345` | Loop entry confirmed at `completions.py:1345`; no `request_transform` package exists in `src/`. |
| Unresolved 250 ms / 2× budget (I2) and I5 schema | I2: "**250 ms / 2× bytes budget must be specified**"; I5: `OptimizationPolicy` described, not written. Correctly carried as unresolved. |
| Naming conflict C-1 | **Confirmed** — packet proposes `src/sabiroute/compression/` (7 modes); ADR-2 proposes `src/sabiroute/request_transform/`. One name must win. |
| Insertion-point conflict C-2 | ADR-2 supersedes the packet's "after final deployment selection" because selection is inside the loop — consistent with `choose_deployment` being per-attempt. |

**Finding AF-17 — `VERIFIED`.** ADR-2 accurately identifies the package, contract, insertion point, invariants, fail-to-original behaviour, Phase-13 keep-out, and the two unresolved quantitative items, and records the packet conflict as a decision rather than assuming a winner. **Adopting ADR-2 authorises no code.**

---

## 10. R6.0 / R6.1 / U0 / G7 Gate-Boundary Audit

**Finding AF-18 — `VERIFIED`; all required distinctions are preserved.**

| Gate | T13 status | T14 verdict | Note |
|---|---|---|---|
| **R6.0** architecture freeze | `CONDITIONALLY READY` | **Accurate** | A prepared package is not a freeze. |
| **R6.1** overall | `NOT READY` | **Accurate** | Nine §6 conditions stand; accounting is binding. |
| **U0** | `READY FOR SEPARATE OWNER AUTHORIZATION` | **Accurate**, with a wording caveat below | Ready ≠ authorised; §19.2 states U0 is not authorised. |
| **U1** | `NOT READY` | **Accurate** | Depends on U0, B5/B6/B7, Track A, G7. |
| **G7** | `NOT GRANTED` | **Accurate** | Never requested; not implied by R6.0 readiness. |
| **Track A** | `NOT OBTAINED` | **Accurate** | No reviewer contacted. |
| **Terminal B/C/D/E** | `NOT OBTAINED` | **Accurate** | Packets drafted, none issued. |

**Required distinctions — all held:** READY ≠ AUTHORISED; CONDITIONALLY READY ≠ FROZEN; proposed ADR ≠ adopted; drafted packet ≠ obtained review; recommendation ≠ decision; approval to engage reviewers ≠ reviewer sign-off; G7 ≠ implied by R6.0.

**U0 wording caveat (AF-19).** T13 §14.6 says U0's remaining conditions are "two, not three: D1 and D3". That counts **readiness** conditions correctly (the spec-5 re-derivation is discharged). But **execution** of U0 also requires **D2** (the separate G7 authorisation). T13 §19 correctly separates "ready" from "authorised", so this is internally consistent — but "remaining conditions are two" can be misread as "two steps to running U0". State it as "two readiness conditions (D1, D3); D2 is the authorisation act". See **C-06**.

**R6.0 condition-3 tension** is recorded at AF-14 above.

---

## 11. Corrections Required

None invalidates a technical verdict or changes a gate. All are precision corrections the owner should see before signing. Ordered by consequence.

| ID | Location in T13 | Correction | Severity |
|---|---|---|---|
| **C-01** | §4.3 (X-2) | Restate "three colliding namespaces" as **two colliding G-scales** (R6, Developer Workflow Overhaul) **plus a separate lettered A–E gate scale** (remediation roadmap). Only the G-number collision is a true collision. | Low (precision) |
| **C-02** | §19.1 condition 3 vs §8 table | Reconcile: either mark B2–B9 as R6.0-adjacent or change condition 3 to "Record the Group A decisions **and B1**, then sign BL-22." | Medium (governance clarity) |
| **C-03** | §10 D3; §9 C1; §8 B1 | Split or annotate composite decisions. **D3** bundles scope + `tests/` naming + U12 placement; **C1** has no recommendation and no alternatives; **B1** couples adoption to C-1 resolution. | Medium (decision quality) |
| **C-04** | §13.5 / §14.2 X5 | Add three fixture conditions: (d) quota absent/oversized so the budget path is under test; (e) second attempt carries **no usage object at all**; (f) assert the **reservation row** and **usage-event `total_tokens`**, not only HTTP 200. | Medium (test soundness) |
| **C-05** | §14.2 X6 | Widen the trigger from "budget-denied" to **all eight pre-loop `finish()` sites** (`api/completions.py:1171, :1180, :1189, :1205, :1272, :1282, :1291, :1299`), noting that a **429** can be masked as a 503. | Medium (defect scope) |
| **C-06** | §14.6 | State U0 as "**two readiness conditions (D1, D3); D2 is the authorisation act**", so "two" is not read as "two steps to running U0". | Low (wording) |
| **C-07** | §14.2 X2 | Correct the stated mechanism: with a usage object whose `total` is absent, the flag is **True**, not `False`; the defect is that **quota settlement (`api/completions.py:603`) ignores the flag**. Record the budget/quota asymmetry as its own finding. | **High (technical)** |
| **C-08** | §19.3 / §11.2 | Note that a per-attempt kill-switch **precedent exists** (`shared_inference`, `completions.py:1351–1368`) even though the **R6 optimisation** apparatus is unbuilt. Strengthens X-6; does not change it. | Low (precision) |

**C-07 is the only correction with technical weight beyond T13.** It means the settlement fix (T7) must address **both** governors, and B5's contract wording must name the quota path explicitly. Left uncorrected, the owner could approve a contract whose scope the code does not yet match.

---

## 12. Final Owner-Session Readiness Verdict

### `READY WITH CORRECTIONS`

The owner **can** begin the R6.0 decision session using T13, provided the corrections above are appended or annotated first. T13's five highest-consequence technical findings are substantively correct; its documentation corrections (X-1, X-3, X-4, X-5, X-6) and its CLAUDE.md §12 finding are verified; the 23-decision register is accurate and correctly partitioned; both ADRs are honest briefs; and every gate boundary preserves its mandatory distinctions.

The corrections are precision and scope refinements, not reversals. **C-07** is the one substantive addition: the unknown-usage signal is applied to budget settlement but **not** to quota settlement, which widens the settlement fix and must be visible when B5 and T7 are decided.

**Recommended first owner decisions (recommendations only — not decisions):**

1. **Read C-07 first** — before B5/T7, because it changes what "fixed" means.
2. **A3 (adopt ADR-1)** and **B1 (adopt ADR-2)** — they gate the R6.0 signature (§19.1 conditions 1–2).
3. **A1, A2, A4** — the remaining Group A freeze decisions.
4. **B5, B6, B7** — the settlement-identity contract that U1 cannot be written without.
5. **D1, D3** (and note **D2**) — the U0 readiness path, independent of the architecture questions.

Dependencies: A3/B1 → signature; B5/B6/B7 → U1; D1/D3 → U0 readiness; D2 → U0 execution; C and D-lane release items need not block R6.0.

**T14 does not answer any decision above.**

---

## 13. Explicit Limitations and Non-Authority Statement

### 13.1 What T14 did not establish

- **No runtime confirmation.** Every behavioural finding (Spec 5, the `NameError`, the settlement asymmetry) is **static**. No test, request, or provider call was executed.
- **No code written.** No test, source, config, migration, or dataset was authored.
- **No decision taken.** All 23 remain `OUTSTANDING`; no ADR adopted; no gate granted.
- **No fetch or reconciliation** of the divergent branch; all anchors are local to `319a711`.
- **No reviewer contacted**; Track A and Terminals B/C/D/E remain `NOT OBTAINED`.

### 13.2 Evidence-class honesty

- Spec-5 failure, the pre-loop `NameError`/503 path, and the quota/budget settlement asymmetry are **`STATIC-ANALYSIS FINDING` / unexecuted runtime hypotheses** — not observed behaviour. They are **not** `VERIFIED`.
- `VERIFIED` is used only for facts read directly from the working tree at `319a711` — anchors, config, SQL table shapes, document citations, and Git metadata.

### 13.3 Residual unknowns

- Whether the `NameError` path is currently reachable in production depends on quota enforcement being active for the requesting user (not instrumented here).
- Whether an existing test already exercises a pre-loop, quota-held denial was not searched exhaustively; T13 §14.2 proposes X6 as an absent case.
- The streaming path's flag handling (`:1812`) was noted but not expanded, per the instruction not to broaden the accounting investigation.

### 13.4 Non-authority statement

This report is **audit support only**. It approves nothing, adopts no ADR, grants no G7, authorises no U0/U1/R6.1 work, records no owner decision, and issues no external request. Silence from any reviewer is **not** approval. A recommendation is not a decision; a prepared decision is not a taken one; a verified anchor is not a verified runtime behaviour.

---

**FINAL STATUS: T14 COMPLETE — T13 INDEPENDENTLY AUDITED; READY WITH CORRECTIONS; NO GATE GRANTED.**

**Next action belongs to the owner:** apply or acknowledge corrections C-01…C-08 (C-07 before B5/T7), then adjudicate the 23 decisions beginning with A3 and B1. T14's job was to verify the decision basis, not to make a decision.
