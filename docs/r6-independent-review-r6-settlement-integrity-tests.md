# Independent Review — `tests/test_r6_settlement_integrity.py`

**Status:** Review artifact. Untracked, unstaged, uncommitted.
**Basis:** direct source read + narrowly scoped runtime execution at HEAD `319a711`.
**Verdict:** **ACCEPT WITH CONDITIONS** — see §10.

Labels used throughout, per the repository evidence standard:

- **VERIFIED (source)** — read directly from the repository at HEAD `319a711`.
- **VERIFIED (runtime)** — observed by executing, with command output.
- **INFERRED** — reasoned from structure; not executed.
- **UNVERIFIED** — assumed; no evidence.

---

## 1. Repository baseline and working-tree status

VERIFIED (runtime):

| Item | Value |
|---|---|
| Path | `<repo-root>` |
| Branch | `feat/sabiroute-routing-foundation` |
| HEAD | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` |
| HEAD subject | `docs(reports): regenerate manifest attestation for committed scorecard` |
| Upstream | `origin/feat/sabiroute-routing-foundation` |
| Divergence | 3 origin-only / 6 local-only |
| Merge base | `303032756aa0b195fc57b3ed630a1cbef2a96398` |

This matches the state recorded in `CLAUDE.md` §9A (re-verified 2026-11-04). No drift. The branch
remains **diverged**; per §9A no merge, rebase, cherry-pick, reset, or force-push was performed or
contemplated.

No Git write operation of any kind was executed during this review. Nothing was staged.

## 2. Target file integrity

| Check | Before review | After review |
|---|---|---|
| SHA-256 | `71952664fd9885cda04508ca8d98696040fcd8c71fbac5b6e8d90d86e065561e` | `71952664fd9885cda04508ca8d98696040fcd8c71fbac5b6e8d90d86e065561e` |
| Size | 19,392 bytes | 19,392 bytes |
| mtime | Nov 4 18:43 | Nov 4 18:43 (unchanged) |
| Git state | `??` (untracked) | `??` (untracked) |

Byte-identical and still untracked. The file was never opened for write.

## 3. Five-row test review matrix

VERIFIED (runtime): `pytest tests/test_r6_settlement_integrity.py` → **4 failed, 1 passed in 0.33s**.

| # | Test | Scenario | Result at HEAD | Failure observed | Reproduces intended defect? |
|---|---|---|---|---|---|
| 1 | `test_e01_pre_attempt_failure_keeps_original_error_and_releases_quota` | Post-reservation, pre-attempt `KeyError` | **FAIL** | error type `quota_unavailable`, not `route_configuration_error`; reservation `reserved`, 71 tokens held | **Yes** — masking + stranding both present (§4) |
| 2 | `test_e02_spec5_quota_governor_holds_estimate` | Attempt 1 known usage (7), attempt 2 success with no usage | **FAIL** | quota consumed 7 vs estimate 71 | **Yes** — partial-sum settlement |
| 3 | `test_e02_spec5_budget_governor_holds_estimate` | Same scenario, budget governor | **FAIL** | budget accounted 7 vs estimate 71 | **Yes** — partial-sum settlement |
| 4 | `test_e02_unknown_usage_on_earlier_attempt_holds_estimate_for_quota` | Attempt 1 prompt-only usage, attempt 2 known (20), budget removed | **FAIL** | quota consumed 20 vs estimate 71 | **Yes** — quota ignores the unknown-usage flag |
| 5 | `test_e02_known_zero_usage_settles_zero_not_estimate` | Single success reporting explicit zeros | **PASS** | — | Guard behaves correctly |

## 4. E-01 findings

### 4.1 The mechanism is real and correctly located — VERIFIED (source + runtime)

`finish()` is a closure defined at `api/completions.py:542`. It reads `attempted` at `:602`:

```python
if quota_reserved and quota_user_id is not None:
    try:
        if attempted:                      # :602
            quota_total = _sum_actual_tokens(actual_usage_parts)[2]
            ...settle_quota...
        else:
            ...release_quota...
```

`attempted` is bound only at `:1311` (`attempted: list[str] = []`). Grep confirms that is the **only**
assignment in the function; every other occurrence is a read.

The failing path is:

1. `:1035` — first `evaluate_candidates` (Free Pool eligibility) succeeds.
2. `:1161` — `quota_reserved = True`; reservation committed with estimate 71.
3. `:1166` — second `evaluate_candidates` raises `KeyError`.
4. `:1170` — `except (KeyError, ValueError)` catches it and calls `finish(...)` at `:1171`.
5. `:1311` is **never reached**, so `attempted` is unbound.
6. Inside `finish()`, `:602` raises `NameError` (unbound free variable) — inside the `try` opened at `:601`.
7. `:623` `except Exception` catches it, logs, appends `quota_cleanup_failed`, and **replaces the
   response** with `503 / quota_unavailable`.
8. `release_quota` is never called, so the reservation stays `reserved` and the 71 reserved tokens
   stay in the window.

VERIFIED (runtime) — the first assertion's own message:

```
AssertionError: E-01: the pre-attempt route-configuration failure was replaced by
'quota_unavailable' (status 503). Expected the original 'route_configuration_error'.
Observed quota reservation {'estimate': 71, 'status': 'reserved',
'reserved_tokens': 71, 'consumed_tokens': 0}
```

Every element of the reported defect is present: reservation taken → early configuration failure →
settlement path raises a *different* exception → original error masked → reservation stranded.

The test's fault injection is legitimate: it raises on the **second** `evaluate_candidates` call,
which is exactly the documented window between `:1161` and `:1311`. The production `except (KeyError,
ValueError)` at `:1170` exists because this failure mode is anticipated.

### 4.2 The test under-reports its own assertions — reviewer observation

The test asserts five things, but the first fails, so **assertions 2–5 never execute** at HEAD. The
stranded-reservation evidence appears only inside the assertion *message*, not as an evaluated
assertion.

Consequence: at HEAD the test proves **only** the error-type masking. It does **not** currently prove
release-failure as an assertion. It will begin doing so once the type assertion turns green. This is
fail-fast design and is defensible, but the module header does not warn that the current red result
exercises one assertion of five.

Additionally, assertion 2 (`status_code == 503`) is **non-discriminating** at HEAD: the masking path
also returns 503. It adds detection power only after remediation.

### 4.3 False-negative risk: the test pins reservation ordering — reviewer finding

`_quota_snapshot()` asserts exactly one quota reservation exists, and the test then requires
`status == "released"`. This forces the implementation to keep the current ordering
(reserve quota → then evaluate route config → then fail → then release).

A perfectly sound fix would move the route-configuration evaluation **before** the quota reservation.
That would leave no reservation to strand, satisfy the stated contract, and then **fail this test** at
`_quota_snapshot`'s `len(...) == 1` assertion — with a misleading message.

INFERRED: the test tacitly presumes remediation option (b) — repair the `attempted` binding — and
excludes option (a) — reorder to fail before reserving. That is an implementation-detail coupling, not
a contract assertion. It should either be documented as an explicit expectation or relaxed to
"at most one reservation, and if one exists it is released".

## 5. E-02 multi-attempt reconstruction

All figures below are VERIFIED (runtime). The reservation estimate is **71** in every scenario:
`estimate_input_tokens(["hello"]) = 55`, plus `max_tokens = 16`.

### 5.1 Spec 5 — known-failure then success-without-usage (tests 2 and 3)

| Step | Attempt | Outcome | Usage reported | Known? | `provider_usage_unknown` |
|---|---|---|---|---|---|
| reserve | — | quota + budget reserved | — | — | `False` (`:1316`) |
| 1 | `primary` | `LiteLLMClientError` 500 | prompt 3, completion 4, total 7 | **known** | stays `False` (`:1571` guard passes) |
| 2 | `secondary` | success, no `usage` key | none | **unknown** | **stays `False`** ← defect |
| settle | — | — | — | — | — |

**Budget:** `finish()` receives `tokens = _sum_actual_tokens(...)` = `(3, 4, 7)` → `tokens[2] = 7`
→ `reconcile_budget(..., 7, ...)` → **accounted 7**.
**Quota:** `:603` recomputes `quota_total = _sum_actual_tokens(...)[2] = 7` → `settle_quota(..., 7)`
→ **consumed 7**.
**Expected under B5:** both = 71 (full estimate).

**Root cause (distinct from C-07):** the success path at `:1897–1954` never sets
`provider_usage_unknown` when `success_usage is None`. The failure path does (`:1573–1574`), and so do
the cancellation paths (`:1628`, `:1693`, `:1812`). Grep confirms no assignment on the success path.
Because the flag stays `False`, `:1948` passes the partial sum instead of `(None, None, None)`.

### 5.2 C-07 — unknown-usage then known-usage failure (test 4)

| Step | Attempt | Outcome | Usage reported | Known? | `provider_usage_unknown` |
|---|---|---|---|---|---|
| reserve | — | quota only (budget removed by test) | — | — | `False` |
| 1 | `primary` | `LiteLLMClientError` 500 | prompt 3 only | **unknown** | → `True` (`:1572`) |
| 2 | `secondary` | `LiteLLMClientError` 502 | 12 / 8 / 20 | known | stays `True` |
| settle | — | 502 `sabiroute_upstream_error` | — | — | — |

**Budget:** absent in this test.
**Quota:** `:603` recomputes `_sum_actual_tokens([(3,None,None), (12,8,20)])[2] = 20` → **consumed 20**.
**Expected under B5:** 71.

VERIFIED (runtime): `quota consumed 20 against an estimate of 71`.

The test's own note is accurate — with a budget retained the loop breaks at `:1601` after the
unknown-usage attempt, so a budgeted variant cannot reach attempt 2 on this shape. I confirmed this
empirically (§6.3): the budgeted run made **1** attempt.

### 5.3 Known-zero guard (test 5)

Single success reporting `prompt_tokens: 0, completion_tokens: 0, total_tokens: 0`.
`_actual_tokens` returns `(0, 0, 0)` — a tuple, **not** `None`. Both governors therefore settle at a
known zero. Quota consumed 0, budget accounted 0. **PASSES**, as designed.

This guard is well constructed: it distinguishes `0` from `None` by relying on tuple identity rather
than truthiness, and it asserts `estimate > 0` first so the guard cannot pass vacuously on a
zero-estimate reservation.

## 6. Separate budget and quota settlement analysis

### 6.1 They do not share a path — VERIFIED (source)

Inside `finish()`:

- **Budget** (`:563–595`) uses the caller's `tokens[2]` directly:
  `store.reconcile_budget(identity.key_id, request_id, tokens[2], actual_cost)`. The caller computes
  `tokens = (None, None, None) if provider_usage_unknown else _sum_actual_tokens(...)`. So the budget
  governor **honours the flag**.
- **Quota** (`:596–632`) **ignores both** `tokens` and `provider_usage_unknown`:
  `quota_total = _sum_actual_tokens(actual_usage_parts)[2]` at `:603`. `finish()` has no
  `usage_unknown` parameter in its signature (`:542–550`).

Both store implementations hold the estimate **only** when handed `None`:
`settle_quota`: `settled = actual_tokens if actual_tokens is not None else estimate`;
`reconcile_budget`: `actual_tokens if actual_tokens is not None else old[0]`.
VERIFIED (source) in both the SQL store (`store.py:1343–1391`, `:1213–1247`) and
`InMemoryApiKeyStore` (`conftest.py:141–166`, `:234–247`) — the two agree.

### 6.2 This is exactly what C-07 records — VERIFIED (source)

`docs/r6-t16-r6-decision-option-register.md:221–225` states it precisely:

> The **budget** governor honours the unknown-usage flag (`completions.py:1944–1955`, `:1961–1972`;
> `_actual_cost` returns `None` at `:1997–1998`). The **quota** governor does **not**: `finish()` has
> no `usage_unknown` parameter (`:542–550`), so the quota block recomputes `quota_total` from raw
> parts at `:603` and never receives the flag.

Every citation in that annotation checks out against the source at HEAD. C-07 is an accurate document.

### 6.3 The governors genuinely disagree — VERIFIED (runtime), and untested

C-07 says the two paths "can disagree on the same response". The test file never demonstrates it.
I exercised the ordering the file omits — **known-usage attempt first, unknown-usage attempt second,
budget live** — with no file modification:

```
HTTP status      : 502
attempts         : 2
estimate         : 71
budget accounted : 71      <- correct (flag honoured)
quota consumed   : 7       <- wrong (partial sum)
GOVERNORS AGREE? : False
```

This is the C-07 divergence at runtime: on one response the budget governor holds the full estimate
while the quota governor settles at a partial sum. Under B5 both should be 71.

Note the contrast with the file's own C-07 test, which removes the budget and therefore cannot observe
the budget side at all.

## 7. B5 compatibility assessment

### 7.1 The asserted rules match the recommended contract — VERIFIED (source)

| B5 invariant | Test behaviour |
|---|---|
| Known usage reconciled as actuals | test 5 settles 0 from explicit zeros ✔ |
| Unknown usage never treated as zero | test 1 asserts `consumed_tokens == 0` **only** for an unattempted request; no E-02 test claims unknown→0 ✔ |
| Unknown usage never replaced by a partial sum | tests 2, 3, 4 all assert `!=` the prohibited value ✔ |
| Original estimate remains the conservative anchor when unknown | tests 2, 3, 4 assert `== estimate` ✔ |
| Both governors examined | tests 2 and 3 separate them explicitly ✔ |
| Known zero distinguishable from unknown | test 5 asserts `estimate > 0` and `consumed == 0` ✔ |

No assertion **weakens** a B5 invariant. The expectations are correctly derived from the reservation
row rather than computed by the test, which is the right construction.

### 7.2 But B5 is NOT approved — this is the material finding

`docs/r6-t16-r6-decision-option-register.md` records B5 as:

- `:207–208` — **Owner response: `PENDING`**, **Approval record: `NOT APPROVED`**
- `:219` — "Evidence status: proposal per T13; unresolved. **Not implemented.**"
- `:226–227` — `PENDING` / `NOT APPROVED`
- `:529` — status table: `B5 | PENDING | ... | NOT APPROVED`
- `:225` — "This register does **not** … claim the proposed contract has been implemented — it has not."
- `:560` — "B5 scope. … recorded in §5. **Not implemented.**"

The test module header, by contrast, states:

> `E-02  Owner decision B5, with its C-07 annotation`

and

> "each test is written against the **approved** contract, not against the observed behaviour"

**This overstates B5's authority.** B5 is an owner **proposal awaiting decision**, not an approved
owner decision. The label "approved" is not supported by the document the test cites.

The underlying defect is independently confirmed regardless — the register itself calls partial-sum
settlement "the confirmed defect" and says choosing it "ratifies the bug" (`:215`). So the tests are
detecting a real, acknowledged defect. What is unapproved is the **settlement contract wording** they
encode, and by extension whether Option A is the owner's choice.

Relatedly, `D1` — the decision governing how failing tests are to be landed (strict-xfail / land-with-U1
/ skip, `:341–352`) — is also `PENDING` / `NOT APPROVED`. **There is currently no approved policy for
admitting four failing tests to the suite.** That is a precondition for landing this module, not a
detail of it.

## 8. Documentation inconsistency (exact discrepancy)

The header claims (`test_r6_settlement_integrity.py:8`):

> `test_e01_*` and both `test_e02_unknown_*` cases are expected to FAIL

The module contains **five** tests. Their real names and results:

| Actual test name | Matches `test_e02_unknown_*`? | Fails at HEAD? |
|---|---|---|
| `test_e01_pre_attempt_failure_keeps_original_error_and_releases_quota` | n/a (`test_e01_*`) | yes |
| `test_e02_spec5_quota_governor_holds_estimate` | **no** (`test_e02_spec5_*`) | yes |
| `test_e02_spec5_budget_governor_holds_estimate` | **no** (`test_e02_spec5_*`) | yes |
| `test_e02_unknown_usage_on_earlier_attempt_holds_estimate_for_quota` | **yes** | yes |
| `test_e02_known_zero_usage_settles_zero_not_estimate` | n/a (guard) | no |

Two defects in one sentence:

1. **The word "both" is wrong.** Exactly **one** test matches `test_e02_unknown_*`, not two.
2. **The failing set is under-described.** The header describes **3** expected failures
   (`test_e01_*` + "both" `test_e02_unknown_*`); the module actually has **4** failures. The two
   `test_e02_spec5_*` tests — which cover the single most important scenario, unknown usage on a
   *successful* attempt — are not matched by the stated pattern at all.

Practical consequence: a reader triaging from the header would conclude the two `spec5` tests were
expected to **pass**, and would misread their red result as a genuine regression rather than the
intended evidence. This is the inconsistency previously reported during the Terminal E work,
confirmed here and stated exactly.

**Not corrected** — per mission scope. Recorded only.

Secondary documentation notes (not inconsistencies, but worth correcting when the file is next
touched):

- §7.2 above — "approved contract" should be "proposed contract (B5, pending owner decision)".
- The header's `E-01` citation of `api/completions.py:596-600` is accurate; the quoted sentence about
  a request "denied before any attempt releases its reservation" sits at `:600`. ✔
- Test 4's `:1601` and `:239-250` citations are accurate. ✔
- Test 1's `:1166` / `:1171` / `:1161` / `:1311` citations are accurate. ✔

## 9. False positives, false negatives, and coverage gaps

### False positives (passes for the wrong reason)

**None found.** Each failing test fails on the assertion that names the defect, and each
`!= partial` assertion is paired with an `== estimate` assertion so neither can pass vacuously.
Test 5's `estimate > 0` precondition prevents a vacuous guard. The `_ScriptedStub` raises
`AssertionError` on an unexpected extra attempt, so a scenario cannot silently drift.

One fragility, not a false positive: **the budget test anchors on the quota estimate.**
`test_e02_spec5_budget_governor_holds_estimate` compares `budget_tokens == snapshot["estimate"]`,
where `snapshot["estimate"]` is read from the **quota** reservation row. It happens to be correct
here because `estimated_input` (`:943`) and `quota_input` (`:1088`) are both
`estimate_input_tokens(payload.messages)` and `max_tokens` is unchanged at both reservation points —
verified: both are 71. But a test written to keep the governors independent should read the **budget**
reservation's own reserved amount. If those two seeds ever diverge, this assertion silently checks the
wrong anchor. (In `InMemoryApiKeyStore` the pre-reconcile budget amount is overwritten in place, so
the budget's own reserved figure is not recoverable after settlement — the harness would need a
recorded reservation to fix this properly.)

### False negatives (would not fail for the intended defect)

**One, material:** the C-07 disagreement scenario in §6.3 is **not covered**. Reordering to
known-then-unknown with a budget live yields budget 71 / quota 7. Under B5 both should be 71; under
C-07 this is the canonical disagreement. No test in the module exercises it, and the module's existing
C-07 test (budget removed) is structurally incapable of it.

**One, conditional:** §4.3 — the E-01 test would fail a legitimate reorder-based fix.

### Coverage gaps, ranked

1. **Known-then-unknown with budget live** (§6.3). The only scenario that demonstrates C-07's
   "can disagree on the same response", and the only one that isolates the quota defect with a
   correct budget governor as the control.
2. **No test separates E-02's two distinct root causes.** The `spec5` tests fail because
   `provider_usage_unknown` is never set on the success path (`:1897–1954`). Test 4 fails because the
   quota block ignores the flag (`:603`). These are different defects with different fixes; the module
   groups them under one label, so a fix for one may appear to satisfy the other.
3. **Missing usage on a *streamed* success** (`:1800`, `:1829`). Streaming success takes a separate
   path; not covered.
4. **No budget-side C-07 control.** Because budget is removed in test 4, nothing proves the budget
   governor is *correct* on unknown-then-known — the claim on which C-07 rests.
5. **No assertion that the E-01 reservation was actually created with a positive estimate** beyond
   `_quota_snapshot`'s existence check (minor; the snapshot surfaces estimate 71).

## 10. Overall verdict

**ACCEPT WITH CONDITIONS.**

The five tests are technically sound and do what they claim:

- The E-01 test reproduces a real, precisely-located defect (unbound `attempted` → `NameError` →
  masked as `quota_unavailable` → reservation stranded at 71) and fails for exactly that reason.
- The E-02 tests reproduce partial-sum settlement in both governors, with the known-zero guard
  correctly passing.
- Assertion quality is good: expectations are read back from the reservation row, prohibited values
  are named in failure messages, and the stub refuses unexpected attempts.

Conditions on acceptance:

- **C1 — Authority claim must be corrected.** The header calls B5 "the approved contract". B5 is
  `PENDING` / `NOT APPROVED`. Do not land the header as written; it misstates the repository's own
  decision record.
- **C2 — Landing policy must be decided first.** `D1` (strict-xfail / land-with-U1 / skip) is
  `PENDING` / `NOT APPROVED`. Four failing tests cannot be admitted to the suite without that
  decision.
- **C3 — The header's failing-test description must be corrected** (§8): one `test_e02_unknown_*`
  test exists, not two; the failing set is four tests, not three.
- **C4 — The C-07 divergence scenario should be added** (§6.3) before this module is presented as
  B5/C-07 evidence, since it is the only scenario that proves the governors disagree.
- **C5 — E-01 should not silently forbid a reorder-based fix** (§4.3).

Not a condition, but recommended: split E-02 into its two root causes so remediation of one cannot be
mistaken for remediation of both.

## 11. Recommended remediation order

Ordered so that each step unblocks the next; no code change is proposed here.

1. **Resolve `B5`** (owner decision; Option A is the register's recommendation). Until decided, the
   settlement target for E-02 is undefined.
2. **Resolve `D1`** — the policy for landing failing tests. This determines whether the module lands
   as `xfail(strict=True)`, alongside U1, or not at all.
3. **Correct the module header** (§8 and §7.2): the failing-test set, and "approved" → "proposed".
4. **Add the known-then-unknown budgeted scenario** (§6.3) as the C-07 evidence test.
5. **Split E-02 into E-02a** (success path never sets `provider_usage_unknown`, `:1897–1954`) **and
   E-02b** (quota block ignores the flag, `:603`), so each defect has its own failing evidence.
6. **Relax or document the E-01 reservation-ordering constraint** (§4.3).
7. Only then begin production remediation — C-07 first (`finish()` should receive the unknown-usage
   flag in the quota branch), then E-02a (set the flag on the success path), then E-01 (bind
   `attempted` before the reservation window or reorder).

**No remediation was implemented. No file was modified, staged, committed, or reformatted.**

---

## Addendum — coverage in `tests/test_user_quotas.py` (added after the review above)

Everything above concerns `tests/test_r6_settlement_integrity.py` only. The two
observations below concern that module's predecessor, which the review's stated
scope excludes. They are recorded separately so that no earlier section is altered.

Labels per the repository evidence standard: **VERIFIED (source)**, **INFERRED**.

### A-1 — `test_provider_failure_holds_estimate` cannot detect partial-sum settlement

VERIFIED (source) — `tests/test_user_quotas.py:390-399`:

```python
def test_provider_failure_holds_estimate():
    stub = StubLiteLLMClient(failures={"primary": 5})
    client, service, state, app = make_quota_client(stub)

    response = service.post("/v1/chat/completions", json=marked())

    assert response.status_code == 502
    usage = store_quota_usage(state)
    assert usage["reserved_tokens"] == 0
    assert usage["consumed_tokens"] > 0
```

The test is named for the B5 invariant (§7.1: "Original estimate remains the
conservative anchor when unknown") but never reads the reservation's estimate. Its
only settlement assertion is `consumed_tokens > 0`, which **every** positive
settlement satisfies — including the partial sum that §5.1 and §5.2 identify as the
defect.

INFERRED: under E-02 as it stands at HEAD, this test stays green. It establishes
"something was consumed", not "the estimate was held". Contrast the R6 module,
which reads the expected figure back from the reservation row (`_quota_snapshot`)
and asserts against it — the construction §7.1 correctly credits.

### A-2 — `test_unknown_usage_holds_estimate` proves the wrong layer

VERIFIED (source) — `tests/test_user_quotas.py:187-198`:

```python
def test_unknown_usage_holds_estimate(tmp_path):
    ...
    assert store.check_and_reserve_quota(UID, "r1", 60, window, 100) is True
    store.settle_quota(UID, "r1", None)
    assert store.get_quota_usage(UID, window) == {
        "reserved_tokens": 0,
        "consumed_tokens": 60,
    }
```

This calls `settle_quota(..., None)` directly. It proves the **store** maps `None`
to the reservation estimate — which §6.1 already establishes as correct in both
implementations (`store.py:1343-1391`, `conftest.py:141-166`), and which is not in
dispute.

It does not prove the **request path** ever produces a `None`. That is precisely the
defect: `finish()` recomputes `quota_total` from raw parts at `:603` and never hands
the quota branch a `None` when usage is unknown (§6.1, C-07). The module docstring's
claim to prove "conservative unknown-usage handling"
(`tests/test_user_quotas.py:2-4`) is therefore satisfied at the one layer that is
already correct.

### Consequence

Both observations are consistent with the suite being green on
`test_user_quotas.py` while E-02 is fully present. Neither is a false positive in
the sense of §9 — neither passes *vacuously* — but neither would change colour under
a partial-sum settlement, so neither constitutes evidence either way about B5 at the
request layer.

Recommended when the file is next touched (not done here — no test or source file
was modified):

1. Strengthen A-1 to assert `consumed_tokens ==` the reservation's estimate and
   rename it to match what it proves, or delete it as superseded by
   `test_e02_spec5_quota_governor_holds_estimate`.
2. Keep A-2 as a store-level unit test but retitle it to say so, and rely on the R6
   module for request-path coverage.

No condition is added to §10: these concern a file outside this review's scope, and
neither weakens a B5 assertion.

**This addendum was appended after the review. No section above was edited, no test
or source file was modified, and the target-file digests recorded in §2 are
unaffected.**
