# R6-FAST-03 — Settlement Integrity Audit

**Audit date:** 2026-11-05
**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711`
**Mission type:** read-only audit. No production source, test, schema, migration, or configuration was modified. No test was executed.
**Remediation status (2026-11-05):** **HELD** by owner decision pending `B5`. No fix applied to any defect in §1. `F1` remains live in the pilot cohort; see §2.4 for its scope condition.
**Method:** every claim below was re-derived from the current tree by direct source read. Prior reports (`docs/r6-c01-…`, `docs/r6-independent-review-…`, `docs/r6-close-final-01-…`) were treated as *claims to verify*, not as evidence.

Labels per `CLAUDE.md` §2: **VERIFIED BY INSPECTION** · **VERIFIED BY RUNTIME** (quoted from a prior run at this HEAD, not re-executed here) · **STATIC-ANALYSIS FINDING** · **INFERRED** · **UNVERIFIED**.

---

## 0. Why no test was run

The mission forbids re-running tests until the test authority and the B5 contract are reconciled. They are not reconciled:

- `B5` (settlement basis) is `PENDING` / `NOT APPROVED` (`docs/r6-t16-r6-decision-option-register.md:71, :529`).
- `D1` (landing policy for failing tests) is `PENDING` / `NOT APPROVED` (`:80, :538`).
- The U0 test artefact's own header calls B5 "the approved contract" (`tests/test_r6_settlement_integrity.py:17`), which the register contradicts.

Running the suite now would produce a red baseline whose meaning is undecided. All runtime figures quoted below are from the prior runs recorded in `docs/r6-c01-…` §3 and `docs/r6-independent-review-…` §3, at the same HEAD, and are labelled as such.

---

## 1. Defect matrix

| ID | Defect | Severity | Label | Primary source |
|---|---|---|---|---|
| **F1** | `finish()` reads closure variable `attempted` before it is bound → `NameError` → masked as `quota_unavailable` → quota reservation stranded | **Critical** | STATIC-ANALYSIS FINDING (mechanism) + VERIFIED BY RUNTIME (consequence, prior run) | `completions.py:602` vs `:1311`; eight call sites |
| **F2** | Quota settlement ignores both `release_budget` and the unknown-usage signal; recomputes from raw parts | **High** | STATIC-ANALYSIS FINDING | `completions.py:596–632`, esp. `:603` |
| **F3** | `provider_usage_unknown` is budget-gated at every assignment except one; a quota-only request can never set it | **High** | STATIC-ANALYSIS FINDING | `completions.py:1574, 1628, 1693, 1812` |
| **F4** | No success path (buffered or streamed) ever sets `provider_usage_unknown`; `_sum_actual_tokens` conflates *absent* with *unknown* | **High** | STATIC-ANALYSIS FINDING + VERIFIED BY RUNTIME (prior run) | `completions.py:1897–1954`, `:1795–1810`, `:253–264` |
| **F5** | `snapshot_persistence_failure()` releases budget **and** quota unconditionally, and is reachable on attempt ≥ 2 after a provider attempt already consumed tokens | **High** | STATIC-ANALYSIS FINDING | `completions.py:786–832`, called `:1499`, `:1502`, before `attempted.append` `:1505` |
| **F6** | `finish()` reconcile path never clears `budget_reserved`; `reserved_tokens` is recorded in the final event after settlement | **Medium** | STATIC-ANALYSIS FINDING | `completions.py:563–583` (release clears at `:573`, reconcile does not), `:642` |
| **F7** | The documented request-local `ledger` is write-only; comments describe a ledger-based compensation model that `finish()` does not use | **Low** | STATIC-ANALYSIS FINDING | `completions.py:393–412`, `:403`, `:1163`, `:1309` |
| **F8** | U0 test artefact overstates B5's authority and misdescribes its own failing set; landing policy undecided | **Medium (governance)** | VERIFIED BY INSPECTION | `tests/test_r6_settlement_integrity.py:8–17`; register `:71, :80, :529, :538` |
| **F9** | Coverage gaps: no cross-governor divergence test, no streamed-success-usage test, no post-attempt snapshot-failure test, no quota-only flag test | **Medium** | VERIFIED BY INSPECTION | `tests/test_r6_settlement_integrity.py` (5 tests) |

**Non-defect, verified:** duplicate settlement and release are safe at the store layer. See §7.

---

## 2. F1 — C-05: `attempted` scope and the pre-loop `NameError`

### 2.1 Mechanism — STATIC-ANALYSIS FINDING

`finish()` is a nested function defined at `completions.py:542`. It reads `attempted` at `:602`:

```python
if quota_reserved and quota_user_id is not None:
    try:
        if attempted:                                   # :602
            quota_total = _sum_actual_tokens(actual_usage_parts)[2]
            ... store.settle_quota ...
        else:
            ... store.release_quota ...
```

`attempted` is assigned **once**, at `:1311` (`attempted: list[str] = []`). Grep over the module confirms `:1311` is the only assignment; every other occurrence is a read (`:602, :1321, :1383, :1391, :1397, :1465, :1494, :1505, :1724, :1877, :1952, :1963, :1970, :1979, :1987`).

Because `finish()` references it, the compiler makes `attempted` a cell variable of the enclosing `chat_completions`. Before `:1311` executes the cell is empty, so `:602` raises:

```
NameError: cannot access free variable 'attempted' where it is not associated with a value in enclosing scope
```

The `except Exception` at `:623` catches it, logs, appends `"quota_cleanup_failed"`, and **replaces the caller's response** with `503 / quota_unavailable` (`:628–632`). `release_quota` is never called.

### 2.2 Reachable sites — eight, not six

`quota_reserved = True` is set at `:1161`. `attempted` is bound at `:1311`. Every `finish()` call in that window is a defect site:

| Site | Trigger | Original error destroyed |
|---|---|---|
| `:1171` | `evaluate_candidates` raises `KeyError`/`ValueError` | `route_configuration_error` |
| `:1180` | no capability-eligible deployment | `no_capable_deployment` |
| `:1189` | no healthy deployment | `no_healthy_deployment` |
| `:1205` | pricing metadata missing for a cost budget | `budget_pricing_unavailable` |
| `:1272` | `reserve_budget` raised | `budget_reservation_unavailable` |
| `:1282` | `reserve_budget` returned `budget_changed` | `budget_config_changed` |
| `:1291` | `reserve_budget` returned `*_pricing_unknown` | `budget_pricing_unavailable` |
| `:1299` | `reserve_budget` returned `*_exceeded` | `budget_exceeded` (429 → 503) |

**Discrepancy recorded:** `docs/r6-c01-…` §5 lists six sites (`:1171, :1180, :1189, :1205, :1291, :1299`), omitting `:1272` and `:1282`. `docs/r6-close-final-01-…` TB-3 lists eight and is correct. This audit confirms **eight**.

### 2.3 Consequence — VERIFIED BY RUNTIME (prior run, same HEAD)

```
AssertionError: E-01: the pre-attempt route-configuration failure was replaced by
'quota_unavailable' (status 503). Expected the original 'route_configuration_error'.
Observed quota reservation {'estimate': 71, 'status': 'reserved',
'reserved_tokens': 71, 'consumed_tokens': 0}
ERROR sabiroute.api.completions:completions.py:624 Quota reservation could not be
reconciled: cannot access free variable 'attempted' where it is not associated
with a value in enclosing scope
```

Three harms, all present: wrong error class to the client; reservation stranded at `reserved`; durable usage row records `reserved_tokens=None` (`:642`, because `budget_reserved` is `False`) while the quota store holds 71 — the two records cannot be reconciled from the durable row alone.

### 2.4 Scope condition

F1 only fires when the quota gate ran, i.e. `sabi_user_id is not None and state.quota_policy.covers(sabi_user_id)` (`:1073`). Non-pilot requests are unaffected. This is why the defect is invisible outside the pilot cohort.

---

## 3. F2 — C-07: budget and quota settlement divergence

### 3.1 The two governors do not share a path — STATIC-ANALYSIS FINDING

Inside `finish()`:

- **Budget** (`:563–595`) is driven by the caller's `release_budget` argument. Release → `store.release_budget` (`:566–572`). Otherwise → `store.reconcile_budget(key_id, request_id, tokens[2], actual_cost)` (`:575–583`). The caller computes `tokens = (None, None, None) if provider_usage_unknown else _sum_actual_tokens(...)`, so the budget governor **honours the flag**.
- **Quota** (`:596–632`) is driven by the closure variable `attempted`, and settles with `_sum_actual_tokens(actual_usage_parts)[2]` (`:603`). It **ignores** `release_budget`, `tokens`, and `provider_usage_unknown`. `finish()` has no unknown-usage parameter (`:542–550`).

### 3.2 Divergence cases

| Case | Budget | Quota | Agree? |
|---|---|---|---|
| `attempted` empty, `release_budget=True` | releases | releases | yes |
| `attempted` non-empty, `release_budget=False`, flag False | reconciles to `tokens[2]` | settles to summed parts | yes (same value) |
| `attempted` non-empty, flag True, `tokens=(None,None,None)` | holds estimate | settles to summed **known** parts | **no** |
| Streamed success after a failed attempt with known usage | reconciles to **last** `usage` (`:1874`) | settles to **sum** of parts | **no** |
| Any caller passing `release_budget=True` with `attempted` non-empty | releases | settles | **no** (latent) |

The third row is the canonical C-07 disagreement. It is **VERIFIED BY RUNTIME** in the independent review §6.3 (known-then-unknown, budget live): budget 71, quota 7, same response.

The fourth row is a distinct multi-attempt divergence not previously recorded: `:1874` passes `usage or _sum_actual_tokens(actual_usage_parts)` — the *last* attempt's usage when present — while `:603` always sums. On a streamed retry where attempt 1 failed with known usage and attempt 2 succeeded with known usage, budget reconciles to attempt 2's tokens and quota settles to attempt 1 + attempt 2. **STATIC-ANALYSIS FINDING; no test covers it.**

The fifth row is latent: no current caller passes `release_budget=True` with `attempted` non-empty, but the two governors are driven by different signals, so any future caller that sets `release_budget` explicitly will desynchronise them.

### 3.3 Store semantics — both implementations agree

- `settle_quota(actual_tokens)`: `settled = actual_tokens if actual_tokens is not None else estimate` (`store.py:1369`; `conftest.py` in-memory equivalent). `None` → holds the estimate.
- `reconcile_budget(actual_tokens, actual_cost)`: each field updated only when not `None` (`store.py:1233–1236`). `None` → keeps the reserved amount.

So the store layer already implements "unknown holds the estimate". The defect is entirely in what the request path hands it.

---

## 4. F3 — `provider_usage_unknown` propagation

### 4.1 Every assignment except one is budget-gated — STATIC-ANALYSIS FINDING

| Line | Assignment | Gate |
|---|---|---|
| `:1316` | `= False` | initial |
| `:1572` | `= True` | failure reported a `usage` object whose total is `None` — **ungated** |
| `:1574` | `= True` | `elif budget_reserved` — **budget-gated** |
| `:1628` | `= True` | `if budget_reserved` (deadline) — **budget-gated** |
| `:1693` | `= budget_reserved or provider_usage_unknown` | **budget-gated** |
| `:1812` | `= budget_reserved or provider_usage_unknown` | **budget-gated** |

Consequence: for a **quota-only** request (`budget is None`), a provider failure that reports *no* `usage` object at all never sets the flag (`:1573`'s `elif budget_reserved` is False). Only a failure that reports a `usage` object with an unknowable total sets it (`:1572`).

This is sharper than the register's C-07 annotation. C-07 says the quota governor "structurally cannot" honour the flag because `finish()` has no parameter. That is true — but even if `finish()` were given the flag, **a quota-only request would pass `False`**, because the flag is scoped to the budget governor by construction. Any remediation that only adds a `usage_unknown` parameter to `finish()` will not fix quota-only requests.

### 4.2 No success path sets the flag — STATIC-ANALYSIS FINDING

- Buffered success: `:1897–1954`. No assignment. `success_usage = _actual_tokens(body)` (`:1903`); if `None`, nothing marks the request unknown.
- Streamed success: `:1795–1810`. No assignment. Only the *non-completed* branch sets it (`:1812`).

So a successful provider response that omits `usage` is treated as an *empty* contribution, not an *unknown* one.

### 4.3 `_sum_actual_tokens` conflates absent with unknown — STATIC-ANALYSIS FINDING

`:253–264` filters `None` contributions and sums the rest. An unknown turn and a turn that never happened are indistinguishable. With parts `[(3, 4, 7)]` the result is `(3, 4, 7)`; with parts `[]` it is `(None, None, None)`. The first is a partial sum presented as a total.

---

## 5. F4 — Unknown usage and full original-estimate handling

The contract under test (B5, proposed): unknown usage settles at the **full original estimate**, never a partial sum, in **both** governors.

| Observation | Required settlement | Current behaviour |
|---|---|---|
| Usage reported as `0` | `0` (known) | correct — `_actual_tokens` returns `(0,0,0)`, not `None` |
| Usage absent on the only attempt | full estimate | correct by accident — `_sum_actual_tokens([])` is `None` |
| Usage absent on a **successful** attempt after a known failure | full estimate | **wrong** — settles at the known partial sum (F4) |
| Usage unknown on one attempt, known on another | full estimate | **wrong** — quota settles at the known sum (F2/F3) |

The third row is **VERIFIED BY RUNTIME** (prior run): quota consumed 7, budget accounted 7, against an estimate of 71.

The known-zero guard (`test_e02_known_zero_usage_settles_zero_not_estimate`) passes and must keep passing. It is the only thing preventing a remediation from collapsing known-zero into unknown.

---

## 6. F5 — Reservation release on a post-attempt snapshot failure

### 6.1 Mechanism — STATIC-ANALYSIS FINDING

`snapshot_persistence_failure()` (`:786–832`) releases **both** the budget reservation (`:788–805`) and the quota reservation (`:806–825`) unconditionally, then returns `503 telemetry_store_unavailable`.

It is called at `:1499` (`except Exception` on the snapshot write) and `:1502` (`snapshot_persisted` falsy). Both calls sit **inside the attempt loop**, before `attempted.append(route_decision.deployment)` at `:1505`.

On attempt 1, `attempted` is empty and the release is correct. On **attempt ≥ 2**, `attempted` already contains the earlier deployment(s), and a provider attempt has already executed and consumed tokens. A snapshot write failure on that retry therefore **frees the entire reservation for a request that already consumed provider capacity** — an under-charge and a quota bypass.

### 6.2 Inconsistency with the adjacent cancellation path

The cancellation path for the *same* operation is explicitly attempt-aware (`:1476–1480`):

> "when no upstream attempt has run yet, compensate held reservations and finalize as an unattempted cancelled request; when an earlier attempt already executed, reconcile/settle and finalize with that attempt's attribution."

The exception path at `:1497–1502` does not apply that distinction. The `except UsageEventValidationError` branch at `:1481–1496` *does* (`release_budget=not attempted`). So within one `try` block, one failure branch is attempt-aware and the other is not.

### 6.3 Evidence status

**STATIC-ANALYSIS FINDING. No runtime evidence exists.** No test drives a snapshot-write failure on attempt 2. This is a new finding, not present in C-01, the independent review, or the closure package.

---

## 7. Reservation release and duplicate settlement

### 7.1 Store-layer idempotency — VERIFIED BY INSPECTION

| Operation | Guard | Repeat behaviour |
|---|---|---|
| `settle_quota` (`store.py:1343–1391`) | selects `status == "reserved"`, sets `"settled"` | second call is a no-op |
| `release_quota` (`:1392–1424`) | selects `status == "reserved"`, sets `"released"` | after settle, no-op; after release, no-op |
| `release_budget` (`:1249–1256`) | `DELETE` | idempotent |
| `reconcile_budget` (`:1213–1247`) | `UPDATE` with the same values | idempotent |
| `check_and_reserve_quota` (`:1258–1341`) | existing `request_id` → `return True` (`:1314–1317`) | no double-reserve |

Settle and release are mutually exclusive because both filter on `status == "reserved"`. A settle racing a release cannot erase consumed usage. **No duplicate-settlement defect at the store layer.**

### 7.2 Caller-layer single-settlement — VERIFIED BY INSPECTION

`chat_completions` has no outer `try/finally` that finalizes (`:301–370`; the `try` at `:834` is the rate-limit read only). Each exit path calls `finish()` or `_cancelled_finish()` exactly once. The streaming path finalizes inside `stream_body` (`:1869`). No path double-settles.

### 7.3 F6 — reconcile does not clear `budget_reserved`

`finish()` clears `budget_reserved` only on the release branch (`:573`). The reconcile branch (`:575–583`) leaves it `True`. Consequences:

1. `reserved_tokens=reserved_tokens if budget_reserved else None` (`:642`) records the reservation amount in the final event **after** it has been reconciled — the durable row claims tokens are still held.
2. A second `finish()` on the same request would re-run `reconcile_budget` (harmless, same values) but would also re-run the quota branch only if `quota_reserved` were still `True` — it is cleared at `:620`, so quota is safe.

Severity Medium: telemetry/contract inaccuracy, no double-charge.

---

## 8. Multi-attempt accounting

| Aspect | Behaviour | Assessment |
|---|---|---|
| `attempted` append timing | `:1505`, before the provider call | correct — an attempt that starts is recorded even if it never returns |
| Usage accumulation | `actual_usage_parts` appended on failure (`:1569`) and success (`:1905`, `:1802`) | correct |
| Cost accumulation | `cost_usage_parts` appended alongside | correct |
| Retry gating | `:1601` breaks when `budget_reserved and provider_usage_unknown` | correct for budget; quota-only requests retry past unknown usage |
| Budget headroom shrink | `:1603–1608` reduces `max_tokens` by consumed tokens | correct |
| Settlement basis | budget uses `tokens[2]`; quota uses summed parts | **divergent** (F2) |
| Streamed success basis | `:1874` uses last `usage` if present, else the sum | **divergent** from quota (F2, row 4) |
| Post-attempt snapshot failure | releases everything (F5) | **wrong** |

---

## 9. F8 — U0 test artefact authority and disposition

### 9.1 What the artefact is

`tests/test_r6_settlement_integrity.py` — 487 lines, 5 tests, untracked. It is the U0 deliverable.

### 9.2 Authority defects — VERIFIED BY INSPECTION

| Claim in the artefact | Repository fact | Verdict |
|---|---|---|
| `:17` "written against the **approved** contract" | B5 is `PENDING` / `NOT APPROVED` (`register:71, :529`) | **overstated** |
| `:8` "`test_e01_*` and both `test_e02_unknown_*` cases are expected to FAIL" | only **one** test matches `test_e02_unknown_*`; the failing set is **four** tests, not three | **wrong** |
| `:24` "Owner decision B5" | B5 is a proposal awaiting decision | **overstated** |

The two `test_e02_spec5_*` tests — which cover the most important scenario, unknown usage on a *successful* attempt — are not matched by the header's stated pattern. A reader triaging from the header would misread their red result as a regression.

### 9.3 Disposition

The artefact is **unauthorised evidence**. It cannot land until:

- **B5** is decided (defines the settlement target the tests encode);
- **D1** is decided (defines whether four red tests may enter the suite — no `xfail` marker exists anywhere in the module or pytest config);
- **D2** authorises U0 separately;
- **D3** names `tests/` inside the G7 write boundary.

Its *technical* content is sound: expectations are read back from the reservation row, prohibited values are named in failure messages, the stub refuses unexpected attempts, and the known-zero guard is correctly constructed. The defects are in its authority claims and its self-description, not its assertions.

### 9.4 Conditions still open

| Condition | Status at `319a711` |
|---|---|
| C1 — header must not call B5 "approved" | **OPEN** (`:17`) |
| C2 — D1 decided before landing | **OPEN** |
| C3 — failing-set description corrected | **OPEN** (`:8`) |
| C4 — add the cross-governor divergence test | **OPEN** |
| C5 — E-01 must not forbid a reorder-based fix | **OPEN** (`_quota_snapshot` requires exactly one reservation) |

---

## 10. F9 — Existing settlement and quota regression coverage

### 10.1 What exists

| File | Coverage | Would it catch F1–F5? |
|---|---|---|
| `tests/test_r6_settlement_integrity.py` | E-01 (F1), E-02 spec5 (F4), E-02 unknown-then-known (F2/F3), known-zero guard | F1 yes; F4 yes; F2/F3 partially; **F5 no**; **F6 no** |
| `tests/test_user_quotas.py` | store-level settle/release, request-path provider failure | **no** — `test_provider_failure_holds_estimate` asserts only `consumed_tokens > 0`, which every positive settlement satisfies; `test_unknown_usage_holds_estimate` calls `settle_quota(..., None)` directly and proves the store layer, not the request path |
| `tests/test_phase10.py` | budget/quota API surface | no settlement-basis assertions |
| `tests/test_lineage_admission_concurrency.py` | admission concurrency | no settlement-basis assertions |
| `tests/test_r3_real_service_controls.py` | real-service controls | no settlement-basis assertions |

### 10.2 Gaps, ranked

1. **Cross-governor divergence** (known-then-unknown, budget live). The only scenario that proves C-07's "can disagree on the same response". Independent-review condition C4.
2. **Post-attempt snapshot failure** (F5). No test drives a snapshot-write failure on attempt 2.
3. **Streamed success without usage** (`:1800`, `:1829`). Separate path, uncovered.
4. **Quota-only failure with no usage object** (F3). No test proves the flag is never set when `budget is None`.
5. **Streamed multi-attempt settlement basis** (F2 row 4). No test compares budget's last-usage basis against quota's summed basis.
6. **`reserved_tokens` after reconcile** (F6). No test asserts the final event's `reserved_tokens` is `None` after settlement.
7. **E-01 reorder tolerance** (C5). The test forbids a legitimate reorder-based fix.

---

## 11. Runtime verification gaps

| Finding | Runtime evidence | Gap |
|---|---|---|
| F1 | Yes (prior run, same HEAD) | none |
| F2 | Yes (prior run, independent review §6.3) | streamed variant unproven |
| F3 | Partial (test 4 proves quota ignores the flag) | no test proves the flag is budget-gated for quota-only requests |
| F4 | Yes (prior run) | streamed success unproven |
| F5 | **None** | entirely static |
| F6 | **None** | entirely static |
| F7 | N/A (documentation) | — |
| F8 | Yes (prior run: 4 failed, 1 passed) | — |
| F9 | N/A (coverage) | — |

**No finding in this report is claimed fixed.** F5 and F6 have no runtime evidence at all and should be treated as unproven until a test exercises them.

---

## 12. Remediation dependency graph

```
OWNER DECISIONS (all PENDING / NOT APPROVED)
├── B5  Settlement basis: unknown wins at the full original estimate?
│        gates: F2, F3, F4 — the target semantics are undefined until B5 is decided
│        must be stated for BOTH governors (C-07 annotation)
│
├── D1  Landing policy for failing tests: strict-xfail / land-with-U1 / skip?
│        gates: whether the U0 artefact (and any new failing test) may enter the suite
│
├── D2  Authorise U0 separately, ahead of U1–U12?
│        gates: sequencing of the test-only deliverable
│
└── D3  Define G7 scope as U0–U11, naming tests/ explicitly?
         gates: whether tests/ is inside the authorised write boundary

ENGINEERING (each behind CLAUDE.md §5)
├── F1  bind `attempted` before the reservation window, or make :602 tolerant
│        independent of B5 — a defect under either settlement option
│        needs D1 to land; needs C5 resolved so the test permits the chosen shape
│
├── F3  un-gate `provider_usage_unknown` from `budget_reserved`
│        prerequisite for F2 — without it, a quota-only request passes False
│
├── F2  give `finish()` an unknown-usage parameter; quota branch honours it
│        depends on F3 (flag must be set) and B5 (target semantics)
│
├── F4  set the flag on buffered and streamed success when usage is absent
│        depends on B5; independent of F2's plumbing
│
├── F5  make `snapshot_persistence_failure()` attempt-aware
│        independent of B5 — releasing a consumed reservation is wrong under either option
│        needs a new test (gap 2)
│
├── F6  clear `budget_reserved` after reconcile
│        independent; low risk
│
└── F7  correct the ledger comments (or implement the ledger)
         documentation only
```

**Critical ordering constraint:** F2 must not be implemented before F3. A `finish(usage_unknown=...)` parameter that receives `False` for every quota-only request is a no-op that will look like a fix.

**Second constraint:** F4 and F2 are independent defects with a shared symptom. Fixing one and declaring E-02 closed is the single most likely remediation error.

---

## 13. Safest implementation sequence

1. **Owner: decide B5** (Option A recommended by the register), stated for both governors.
2. **Owner: decide D1, D2, D3.**
3. **Correct the U0 artefact header** (C1, C3): "approved" → "proposed"; failing set three → four; "both `test_e02_unknown_*`" → one.
4. **Add the cross-governor divergence test** (C4) — known-then-unknown, budget live.
5. **Add tests for F5 and F6** before touching their code, so the fix has evidence.
6. **Split E-02** into E-02a (flag never set on success) and E-02b (quota block ignores the flag).
7. **Resolve C5** — record the permitted E-01 repair shapes (bind-before-window vs reorder).
8. **Remediate F1** — independent of B5; lowest semantic risk; highest severity.
9. **Remediate F3** — un-gate the flag.
10. **Remediate F2** — quota branch honours the flag.
11. **Remediate F4** — set the flag on success paths.
12. **Remediate F5** — attempt-aware snapshot failure.
13. **Remediate F6, F7** — telemetry and documentation.
14. **Re-run the full suite** only after steps 1–2 are decided and the new tests exist.

Steps 1–2 are owner decisions and are not delegable to an implementer.

---

## 14. Explicit non-actions

- No file under `src/**` was modified.
- No file under `tests/**` was modified.
- No test was executed.
- Nothing was staged, committed, or pushed.
- The origin divergence recorded in `CLAUDE.md` §9A was not touched.

---

## 15. Corrections to prior reports

| Prior claim | Correction |
|---|---|
| `docs/r6-c01-…` §5 lists six F1 sites | **Eight** sites: add `:1272` and `:1282`. The closure package TB-3 is correct. |
| C-07 says the quota governor "structurally cannot" honour the flag | True, but incomplete: the flag is also **budget-gated at every assignment except `:1572`**, so a quota-only request would pass `False` even with a new parameter. |
| No prior report records F5 | `snapshot_persistence_failure()` releases reservations unconditionally and is reachable after a provider attempt. New finding. |
| No prior report records F6 | `finish()` reconcile does not clear `budget_reserved`; `reserved_tokens` is recorded post-settlement. New finding. |
| No prior report records the streamed multi-attempt basis divergence | `:1874` uses last `usage`; `:603` sums. New finding. |
