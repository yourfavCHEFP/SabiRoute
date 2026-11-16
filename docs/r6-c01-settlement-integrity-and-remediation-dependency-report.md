# R6 C-01 — Settlement Integrity and Remediation Dependency Report

**Audit date:** 2026-11-05 (UTC)
**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711`
**Mission type:** read-only audit. No production source, test, schema, migration, or configuration was modified.
**Overall verdict:** **SETTLEMENT INTEGRITY IS BROKEN AT HEAD — 4 failing tests, 3 distinct production defects, all remediation blocked on owner decisions `B5` and `D1`.**

---

## 1. Mission authority and scope

C-01 is a *reporting* mission. Its authorised scope is:

- read the repository, its decision register, and its test suite;
- run the existing test suite to obtain runtime evidence;
- state what is broken, how it is broken, and what each repair depends on.

Explicitly **out of scope, and not done**: editing `src/**`, editing `tests/**`, editing `docs/r6-t16-*`, staging, committing, pushing, or resolving the origin divergence described in `CLAUDE.md` §9A.

Evidence labels follow `CLAUDE.md` §2 and are applied to every conclusion below.

---

## 2. Repository baseline and working-tree status

| Fact | Value | Label |
|---|---|---|
| Branch | `feat/sabiroute-routing-foundation` | VERIFIED BY INSPECTION |
| HEAD | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` (committed 2026-11-02) | VERIFIED BY INSPECTION |
| Upstream | `origin/feat/sabiroute-routing-foundation`, merge base `3030327` | VERIFIED BY INSPECTION |
| Divergence | 6 local-only / 3 origin-only commits | VERIFIED BY INSPECTION |
| Tracked modifications | **0** | VERIFIED BY INSPECTION |
| Untracked entries | 116 | VERIFIED BY INSPECTION |

The zero tracked-modification count is the load-bearing fact in this table: **every result in this report is a property of committed HEAD `319a711`, not of uncommitted work in the tree.** The origin divergence is reported here only because `CLAUDE.md` §9A requires it to be stated, and because it is a live hazard for any future remediation commit (see §11.3).

---

## 3. Runtime evidence — full suite

```
$ python3 -m pytest -q --no-header -p no:randomly
4 failed, 664 passed, 9 skipped in 21.01s
```

677 tests collected. **The only failing tests in the entire repository are the four R6 settlement-integrity tests.** Label: VERIFIED BY RUNTIME.

The 9 skips are environment-gated integration tests (`SABIROUTE_TEST_REDIS_URL`, `SABIROUTE_TEST_PG_URL` unset) and are unrelated to settlement.

---

## 4. Executive summary

Three production defects sit behind four failing tests:

1. **C-01-F1 — masked error + stranded quota reservation.** `finish()` reads the closure variable `attempted` before it is bound. The resulting `NameError` is swallowed by a broad `except Exception`, which replaces the caller's real error with `quota_unavailable` and leaves the quota reservation held. This is the most severe finding: it produces a **wrong answer to the client plus an unreconcilable accounting leak.**
2. **C-01-F2 — unknown usage settles at a partial sum (both governors).** A successful provider response that omits `usage` is not recorded as *unknown*; it is silently treated as an *empty* contribution, so settlement uses only the known turns.
3. **C-01-F3 — quota settlement can never honour unknown usage.** `finish()` has no `usage_unknown` parameter, so the quota branch recomputes settlement from raw parts. The budget governor honours the flag; the quota governor structurally cannot. The two governors therefore disagree on the same response.

Two of the decision register's entries — `B5` (settlement basis) and `D1` (landing policy for failing tests) — are unresolved owner decisions. **No remediation can be ratified until they are taken.** A repair written today would be implementing an unapproved contract and landing it against an undecided policy.

---

## 5. Findings

### C-01-F1 — `finish()` reads `attempted` before it is bound; the `NameError` is masked and strands the reservation

**Severity: Critical. Labels: STATIC-ANALYSIS FINDING (mechanism) + VERIFIED BY RUNTIME (consequence).**

| Element | Location |
|---|---|
| `attempted` referenced | `src/sabiroute/api/completions.py:602` (`if attempted:`), inside `finish()` defined at `:542` |
| `attempted` bound | `src/sabiroute/api/completions.py:1311` (`attempted: list[str] = []`) |
| Quota reservation taken | `:1161` (`quota_reserved = True`), `:1162` (`quota_user_id = sabi_user_id`) |
| `finish()` reachable in the window | `:1171`, `:1180`, `:1189`, `:1205`, `:1291`, `:1299` |
| Failure swallowed | `:623`–`:632`; log line `:624`; response replaced `:628`–`:632` |

**Mechanism.** `finish()` is a nested function closing over `chat_completions`'s locals. Static scope analysis confirms `attempted` is a **free** variable inside `finish`, assigned only in the enclosing scope, and the enclosing assignment at `:1311` executes *after* six `finish()` call sites. On every path that reserves quota at `:1161` and then denies before `:1311` runs, line `:602` is reached with no binding and raises:

```
cannot access free variable 'attempted' where it is not associated with a value in enclosing scope
```

The `except Exception` at `:623` catches it, logs it, appends `"quota_cleanup_failed"`, and **replaces the caller's response** with a fabricated `503 quota_unavailable`.

**Runtime evidence (verbatim).**

```
E  AssertionError: E-01: the pre-attempt route-configuration failure was replaced by
   'quota_unavailable' (status 503). Expected the original 'route_configuration_error'.
   Observed quota reservation {'estimate': 71, 'status': 'reserved',
   'reserved_tokens': 71, 'consumed_tokens': 0}
ERROR sabiroute.api.completions:completions.py:624 Quota reservation could not be
   reconciled: cannot access free variable 'attempted' where it is not associated
   with a value in enclosing scope
```

**Three distinct harms, all proven:**

1. **Error masking.** A misconfigured route (`route_configuration_error`, `:1171`), an ineligible route (`no_capable_deployment`, `:1180`), an unhealthy route (`no_healthy_deployment`, `:1189`), a pricing gap (`:1205`, `:1291`), and a budget denial (`:1299`) are **all** reported to the client as `quota_unavailable`. An operator debugging a Free Pool denial is pointed at the quota store, which is not the fault.
2. **Stranded reservation.** `status='reserved'` with `reserved_tokens=71` persists after the request has terminated. The window is not settled and not released.
3. **Unreconcilable durable record.** Finalisation at `:633`–`:659` records `reserved_tokens = reserved_tokens if budget_reserved else None` (`:642`). On this path `budget_reserved` is `False`, so the durable usage row states **nothing was reserved** while the quota store simultaneously states **71 tokens are held**. No reconciler can detect the discrepancy from the durable row alone — this is precisely why it is a settlement-integrity defect and not merely a lost reservation.

**Note on repair shape.** A reorder-based fix (bind `attempted` before the reservation window) and a defence-based fix (make `:602` tolerant of an unbound/empty list) are both viable and have different failure modes. The independent review's condition **C5** records that the E-01 test must not silently forbid the reorder shape.

---

### C-01-F2 — A successful response without `usage` is treated as empty, not unknown

**Severity: High. Labels: STATIC-ANALYSIS FINDING (mechanism) + VERIFIED BY RUNTIME (consequence).**

`_sum_actual_tokens` (`:253`–`:264`) filters out `None` contributions:

```python
total_values = [part[2] for part in parts if part[2] is not None]
...
total = sum(total_values) if total_values else None
```

An *unknown* usage turn is therefore indistinguishable from a turn that *did not occur*. The success path never marks the attempt unknown, so settlement proceeds on the known subset.

**Runtime evidence (verbatim), two governors, same scenario:**

```
E  AssertionError: E-02 (quota governor): unknown usage from the successful attempt
   must settle at the full original estimate, but quota consumed 7 against an estimate of 71
E  AssertionError: E-02 (budget governor): unknown usage from the successful attempt
   must hold the full original estimate, but budget accounted 7 against an estimate of 71
```

Both governors under-settle by ~91% of the reservation. The caller is accounted 7 tokens for a request that reserved 71 and whose true consumption is unknown.

**Why this is not "conservative billing".** Under-settling on unknown usage is an *under-charge*, which in a governed Free Pool is a quota bypass: a caller whose provider omits `usage` pays a fraction of the cost of every request.

---

### C-01-F3 — The quota governor structurally cannot honour unknown usage

**Severity: High. Label: STATIC-ANALYSIS FINDING.**

`finish()`'s signature (`:542`–`:550`) has no unknown-usage parameter. Its quota branch recomputes settlement from raw parts at `:603`:

```python
quota_total = _sum_actual_tokens(actual_usage_parts)[2]
```

The budget governor, by contrast, receives the flag through `_actual_cost(..., has_unknown_usage)`, which returns `None` when the flag is set (verified: `_actual_cost` returns `None` when `has_unknown_usage or not parts`). The budget path can therefore hold the estimate **when the flag is set** — which F2 shows it is not, on the success path.

**Runtime evidence (verbatim), multi-attempt, known-then-known:**

```
E  AssertionError: E-02 (quota governor): a request containing an attempt whose usage
   is unknown must settle at the full original estimate, but quota consumed 20 against
   an estimate of 71
```

**Consequence.** F2 and F3 are independent defects with a shared symptom. Repairing F2 alone leaves the quota governor unable to consume the flag it would then set; repairing F3 alone leaves the flag unset on the success path. **A remediation that fixes one and reports "E-02 fixed" will be wrong.** The independent review recommends splitting E-02 into `E-02a` (flag never set on the success path) and `E-02b` (quota block ignores the flag, `:603`) for exactly this reason.

This matches the register's own `C-07` annotation (`docs/r6-t16-…` §5 B5), which already records that the budget governor honours the flag while the quota governor cannot, and that B5 must cover **both** governors.

---

### C-01-F4 — The governors' disagreement is asserted, not yet proven by a dedicated test

**Severity: Medium (test-coverage gap). Label: VERIFIED BY INSPECTION (gap), INFERRED (divergence not fully exercised).**

The C-07 divergence requires a request that contains a **known-usage** turn and an **unknown-usage** turn, so that the two governors produce different answers on the *same* response. The module contains no such test:

- `test_e02_spec5_quota_governor_holds_estimate` and `test_e02_spec5_budget_governor_holds_estimate` are the same scenario run against each governor separately.
- `test_e02_unknown_usage_on_earlier_attempt_holds_estimate_for_quota` covers the quota governor only.
- `test_e02_known_zero_usage_settles_zero_not_estimate` passes and is the essential guard: it proves a repair must not collapse **known-zero** into **unknown**.

This is independent-review condition **C4**, and it remains open.

---

### C-01-F5 — The documented accounting `ledger` is write-only

**Severity: Low (no functional impact; documentation/observability divergence). Label: VERIFIED BY INSPECTION.**

`:393`–`:403` documents a request-local ledger as *the* compensation mechanism, and `:410` states that `finish()` "waits for it before inspecting the ledger". In fact:

- `ledger` is declared at `:403`;
- appended at `:1163` and `:1309`;
- **never read anywhere in the module**;
- `finish()`'s compensation decisions actually read the boolean flags `budget_reserved` (`:563`) and `quota_reserved` / `quota_user_id` (`:596`).

A reader — or a future remediation author — is told the accounting model is ledger-based when it is flag-based. This is not cosmetic: F1 and F3 are both *within* the region this comment describes, and the comment's claim that `finish()` inspects a ledger is false as written.

---

## 6. Why the known-zero guard matters

`test_e02_known_zero_usage_settles_zero_not_estimate` **passes** at HEAD. It exists so that a repair cannot satisfy F2/F3 by treating every zero as unknown. Any remediation must preserve this distinction:

| Observation | Must settle at |
|---|---|
| Usage reported as `0` | `0` (known) |
| Usage absent / unknown | full original estimate |
| Usage absent from **some** attempt, known from others | full original estimate |

The third row is the one currently violated.

---

## 7. Remediation dependency graph

Remediation is **blocked**, not pending effort. Each line names the decision that gates it.

```
OWNER DECISIONS (all currently PENDING / NOT APPROVED)
├── B5  Settlement basis: unknown wins at the full original estimate?
│        register: docs/r6-t16-… §5 B5   status: OUTSTANDING (index :71), NOT APPROVED (:529)
│        gates:   F2, F3  — the *target semantics* of any settlement repair are undefined
│                 until B5 is decided (Option B would ratify the current behaviour as correct)
│        notes:   must be stated for BOTH governors (C-07 annotation)
│
├── D1  Landing policy for failing tests: strict-xfail / land-with-U1 / skip?
│        register: docs/r6-t16-… §6.2 D1  status: OUTSTANDING (:80), NOT APPROVED (:538)
│        gates:   whether 4 red tests may enter the suite at all
│        notes:   no xfail marker exists in the module or pytest config (verified)
│
├── D2  Authorise U0 separately, ahead of U1–U12?
│        register: §6.2 D2                status: OUTSTANDING (:81), NOT APPROVED (:539)
│        gates:   sequencing of the test-only deliverable relative to U1
│
└── D3  Define G7 scope as U0–U11, naming tests/ explicitly?
         register: §6.2 D3                status: OUTSTANDING (:82), NOT APPROVED (:540)
         gates:   whether tests/ is inside the authorised write boundary at all
```

**Two consequences worth stating plainly:**

1. **The failing tests cannot be landed.** Four red tests in a 677-test suite is not a stable baseline. Without `D1`, the only options are (a) an unapproved `xfail` edit to `tests/`, or (b) shipping a red suite. Both are the owner's call, not the implementer's.
2. **The repair cannot be specified.** `B5`'s Option B is literally "partial-sum settlement" — the register annotates it: *"partial-sum settlement **is** the confirmed defect; choosing it ratifies the bug."* So F2/F3 are not defects until B5 selects Option A. Writing the fix first inverts the authority chain.

**F1 is the exception.** `C-01-F1` does not semantically depend on `B5`: an unbound variable masking an error and stranding a reservation is a defect under either settlement option. It still requires `D1` to land, and it touches the settlement core, so `CLAUDE.md` §5 (architectural change gate) applies.

---

## 8. Independent-review condition status

`docs/r6-independent-review-r6-settlement-integrity-tests.md` returned **ACCEPT WITH CONDITIONS** and five conditions. Re-checked at HEAD:

| Condition | Requirement | Status at `319a711` | Label |
|---|---|---|---|
| **C1** | Header must not call B5 "the approved contract" | **OPEN** — `tests/test_r6_settlement_integrity.py:17` still reads "written against the approved contract"; B5 is `NOT APPROVED` | VERIFIED BY INSPECTION |
| **C2** | `D1` must be decided before landing | **OPEN** — `D1` is `PENDING`; no `xfail` marker exists | VERIFIED BY INSPECTION |
| **C3** | Failing-test description must be corrected | **OPEN** — `:9` still says "both ``test_e02_unknown_*`` cases"; only **one** test matches that prefix (`test_e02_unknown_usage_on_earlier_attempt_holds_estimate_for_quota`); the failing set is **four** tests | VERIFIED BY RUNTIME |
| **C4** | Add the C-07 divergence scenario | **OPEN** — no known-then-unknown cross-governor test exists | VERIFIED BY INSPECTION |
| **C5** | E-01 must not forbid a reorder-based fix | **OPEN** — not yet addressed | VERIFIED BY INSPECTION |

The review's verdict is corroborated: its E-01 mechanism description, its "stranded at 71", and its split of E-02 into `E-02a`/`E-02b` all reproduce exactly at HEAD.

---

## 9. Blast radius and severity

| Finding | Client-visible | Accounting-visible | Data loss | Blast radius |
|---|---|---|---|---|
| F1 | Yes — wrong error type for 5 denial classes | Yes — reservation stranded; durable row denies it | No | All Free Pool requests denied in the `:1161`→`:1311` window |
| F2 | No | Yes — under-settlement, under-charge | No | Any request whose provider omits `usage` |
| F3 | No | Yes — quota governor cannot hold estimate | No | Every quota settlement |
| F4 | No | N/A (coverage gap) | No | Test evidence only |
| F5 | No | No (documentation) | No | Reader comprehension of the settlement core |

**Not affected.** 664 tests pass, including routing, capability eligibility, health filtering, BYOK-0 credential rejection, rate limiting, and the rest of the completion surface. The defects are confined to the settlement path. This is a **narrow but deep** failure: the settlement layer is exactly where wrongness is silent.

---

## 10. Recommended sequence

No code change is proposed by this report. The ordered sequence, reconciled with the independent review §11:

1. **Resolve `B5`** — owner decision; the register recommends Option A, stated for both governors. Unblocks the *target* of F2/F3.
2. **Resolve `D1`, `D2`, `D3`** — unblocks whether and how failing tests may land, and whether `tests/` is in the write boundary.
3. **Correct the module header** (`C1`, `C3`) — "approved" → "proposed", and the failing set from three to four.
4. **Add the C-07 divergence test** (`C4`).
5. **Split E-02** into `E-02a` (flag never set on success path) and `E-02b` (quota block ignores flag, `:603`).
6. **Address `C5`** — record the permitted E-01 repair shapes.
7. **Then** remediate, in the review's order: F3/C-07 → F2 → F1, each behind `CLAUDE.md` §5.

Steps 1–2 are owner decisions and are not delegable to an implementer.

---

## 11. Risk notes for whoever acts next

1. **Do not "fix" F2 alone and declare E-02 closed.** F2 and F3 are independent; the quota governor will remain unable to honour the flag. This is the single most likely remediation error.
2. **Do not weaken the known-zero guard.** It passes today and is the only thing preventing a repair from collapsing known-zero into unknown.
3. **The origin divergence is a live hazard.** `CLAUDE.md` §9A records 6 local-only / 3 origin-only commits and forbids merge/rebase/cherry-pick/reset without explicit owner authorisation. Any remediation commit lands on the divergent local line; do not resolve the divergence as a side effect of it.
4. **F1 will hide itself in staging.** Because the `NameError` is caught and converted to a 503, it produces no traceback and no 500 in logs — only a single `ERROR … cannot access free variable 'attempted'` line. An operator looking at dashboards sees "quota unavailable", which is a plausible, wrong explanation.

---

## 12. Explicit non-actions

- No file under `src/**` was modified.
- No file under `tests/**` was modified.
- `docs/r6-t16-r6-decision-option-register.md` was read, not modified.
- Nothing was staged, committed, pushed, or reformatted.
- No `xfail` marker, skip, or assertion relaxation was applied to make the suite green.
- The only file created is this report.

---

## 13. Current project status

```
CURRENT GATE:   R6.1 — settlement integrity. BLOCKED on owner decisions B5, D1, D2, D3.
CURRENT PHASE:  R6 (settlement integrity audit, mission C-01).
PROVEN:         4 settlement tests fail at HEAD 319a711; 664 pass; 9 skipped.
                F1: finish() reads unbound 'attempted' (:602 before :1311) -> NameError
                    swallowed at :623-:632 -> route_configuration_error masked as
                    quota_unavailable -> 71 tokens stranded as 'reserved' while the
                    durable row records reserved_tokens=None.
                F2: unknown usage settles at the partial sum (7 vs estimate 71) in both
                    governors; known-zero guard passes.
                F3: finish() has no unknown-usage parameter (:542-:550); quota recomputes
                    at :603 — the quota governor structurally cannot honour the flag.
                F5: the documented 'ledger' (:403) is appended at :1163/:1309 and never read.
                Independent-review conditions C1-C5 are all still open.
UNPROVEN:       Whether any production traffic has exercised F1 (no runtime traffic data
                was collected; evidence is the test harness only).
                The C-07 cross-governor divergence on a single response (no such test exists).
                Behaviour under the environment-gated Redis/PostgreSQL integration tests.
BLOCKED BY:     Owner decisions B5 (settlement basis), D1 (landing policy), D2, D3.
NEXT:           Owner decides B5 and D1. No code change is authorised before that.
```
