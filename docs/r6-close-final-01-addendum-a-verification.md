# R6-CLOSE-FINAL-01 — Addendum A: Independent Source Re-Verification

**Status: SUPPLEMENTARY VERIFICATION RECORD. R6.0 REMAINS NOT CLOSED, NOT FROZEN, NOT SIGNED.**
**Subordinate to:** `docs/r6-close-final-01-r6.0-closure-package.md` (the closure package, 647 lines).
**Supersedes:** nothing. **Amends:** nothing. **Replaces:** nothing. The package remains the authoritative closure document.
**Files created:** this document only. **Files modified:** none. **Registers amended:** none.
**No implementation. No production code change. No test execution. No provider call. No migration. No deployment. No commit. No staging. No reset. No cleanup. No rebase. No destructive Git operation.**
**No owner decision, external approval, signature, test result, threshold or gate acceptance invented below.**

---

## 0. Why this addendum exists

The closure package states in its §0 that its Git-level facts are **INHERITED, not re-derived**, because
command execution was unavailable. That limitation is **not removed by this document** — command
execution was again unavailable (the execution classifier blocked every `git` invocation, and the
symbol-search tool is degraded by a missing tree-sitter build).

What *was* possible in this session, and had not been done at the time the package was written, is
**direct re-reading of the source anchors** on which the package's two most load-bearing technical
findings rest. Those two findings carry the verdict's technical weight:

- **TB-2 / correction C-07** — dual-governor divergence (budget honours `provider_usage_unknown`; quota
  structurally cannot).
- **TB-3 / correction C-05** — pre-loop `finish()` `NameError` masking, eight sites.

If either were wrong, the package's blocker inventory and part of the B5 analysis would be wrong. They
were therefore re-verified line by line rather than cited.

**Verdict effect: NONE.** Both findings are **confirmed exactly**. One **new** in-source observation is
recorded in §3 that the package did not capture; it *strengthens* TB-2 without changing the verdict.

---

## 1. Method and its limits

| Check | Attempted | Result |
|---|---|---|
| `git rev-parse`, `git status`, `git rev-list` | Yes (×3) | **BLOCKED** — classifier blocked execution |
| `ls`, `find`, `grep` via shell | Yes | **BLOCKED** |
| Symbol search (`smart_search`) | Yes | **DEGRADED** — tree-sitter CLI absent; 0 symbols indexed |
| Direct file read at absolute path | Yes | **SUCCEEDED** — module located and read |

**Consequence:** every claim in §2 is labelled **VERIFIED (this session)** — read directly from the
working tree at the exact line cited. Git-level facts remain **INHERITED** and are **not** re-asserted
here. **RC-13 of the package (`baseline re-derived at closure time`) remains `UNMET`.**

Module under verification: `src/sabiroute/api/completions.py`.

---

## 2. Re-verified anchors

| # | Package claim | Anchor | Observed this session | Status |
|---|---|---|---|---|
| 1 | `finish()` has **no** `usage_unknown` parameter | `:542–550` | Signature is `finish(response, *, deployment, tokens, failure_category, actual_cost, release_budget)`. **No `usage_unknown`/`provider_usage_unknown` parameter exists.** | **VERIFIED** |
| 2 | `finish()` declares `nonlocal` for budget/quota but **not** `attempted` | `:551` | `nonlocal budget_reserved, quota_reserved` — `attempted` **absent** | **VERIFIED** |
| 3 | `if attempted:` is read inside `finish()` | `:602` | `if attempted:` present in the quota block | **VERIFIED** |
| 4 | `attempted` is bound **after** `finish()` is defined and after the pre-loop call sites | `:1311` | `attempted: list[str] = []` | **VERIFIED** |
| 5 | Quota settlement **recomputes** the total from raw parts | `:603` | `quota_total = _sum_actual_tokens(actual_usage_parts)[2]` | **VERIFIED** |
| 6 | `provider_usage_unknown` initialised `False` | `:1316` | `provider_usage_unknown = False` | **VERIFIED** |
| 7 | Budget side **does** consult the flag at the call site | `:1321–1333` | `tokens=(None,None,None) if provider_usage_unknown else _sum_actual_tokens(...)` and `actual_cost=_actual_cost(state, cost_usage_parts, provider_usage_unknown)` | **VERIFIED** |
| 8 | `:1299` is the pre-loop **429 `budget_exceeded`** site | `:1299–1307` | `_error_response(429, "...budget would be exceeded.", "budget_exceeded", window=denial.split("_",1)[0], ...)` | **VERIFIED** |

**Finding 7 versus findings 1, 5 — the divergence, now demonstrated rather than inferred.** The
*caller* computes budget tokens and cost **flag-aware**, then hands them to a `finish()` that settles
**quota** from the same raw parts **flag-blind**. The two governors receive different inputs from the
same event, by construction. This is C-07, confirmed at the instruction level.

**Finding 2 versus findings 3 and 4 — the `NameError` mechanism, now demonstrated rather than
inferred.** `finish()` reads `attempted` at `:602`, does not declare it `nonlocal`, and the only
binding in scope is at `:1311` — after every pre-loop call site, including the `:1299` 429. A pre-loop
`finish()` therefore raises `NameError`, which the surrounding `except Exception` converts into a
**503 `QUOTA_UNAVAILABLE`** and a **suppressed reservation release** (`quota_reserved = False` at `:620`
is never reached). This is C-05/TB-3, confirmed.

---

## 3. New observation — the defect contradicts its own source comment

**Not recorded in the closure package.** At `:597–599`, immediately above the settlement code, the
in-source comment reads:

> "Quota settlement mirrors budget reconciliation: attempts made settle with summed actuals
> (**unknown usage holds the estimate**); a request denied before any attempt releases its reservation."

Line `:603` — two lines later — sums the raw parts unconditionally and **cannot** hold the estimate,
because it has no access to `provider_usage_unknown` (finding 1).

**Why this matters, and how it changes the record:**

| The package said | This observation adds |
|---|---|
| Quota "**structurally cannot**" honour the flag | It **cannot** — *and the author intended it to*. The comment states the intended semantics explicitly. |
| The divergence is a **capability gap** that might be a design choice | It is a **live defect against a stated in-source intent**, not an open design question |

**Consequence for B5 (unchanged in count, sharpened in framing).** The package correctly insists B5
must name **both** governors. This observation supplies the strongest available evidence for *why* they
must converge: the code already claims they do. An owner answering B5 is therefore not choosing a
settlement philosophy from scratch — they are **ruling on which of two already-contradictory statements
in the same function is canonical**. The comment records the intent; the code records the behaviour.

**No decision is taken here.** This observation does not answer B5, does not answer any of its five
sub-decisions, and does not promote any scenario marker. It is evidence, added to the record.

---

## 4. What remains unverified

| Item | Why | Status |
|---|---|---|
| Branch, HEAD, ahead/behind, dirty count | Execution blocked | **INHERITED** — package §0; **RC-13 `UNMET`** |
| Other six pre-loop `finish()` sites (`:1171, :1180, :1189, :1205, :1272, :1282, :1291`) | Not re-read individually this session; the **mechanism** (§2 findings 2–4) is proven and is site-independent | **PARTIALLY VERIFIED** — mechanism proven; per-site count inherited |
| Budget governor internals `:1944–1955`, `:1997–1998` | Not re-read; call-site flag-awareness (§2 finding 7) is the load-bearing element and **is** verified | **PARTIALLY VERIFIED** |
| Latch sites `:1572`, `:1574`, `:1628`, `:1693`, `:1812` | Not re-read this session | **INHERITED** |
| `store.py` settlement contracts `:1213–1247`, `:1343–1352` | Not re-read this session | **INHERITED** |
| All runtime behaviour | No execution permitted; no test run | **UNPROVEN** — unchanged |
| U0 test artefact | Not located this session (execution blocked); not executed, not modified | **PRESERVATION NOT REVERIFIED** |

**These gaps are stated rather than closed.** None of them is load-bearing for the verdict, because the
verdict rests on **decision and signature absences**, not on any of the above.

---

## 5. Effect on the closure verdict — stated explicitly

**The verdict is unchanged.**

- **R6.0 is NOT CLOSED, NOT FROZEN, NOT SIGNED.** Still **NO-GO**.
- **Canonically registered decisions: 0.** Unchanged.
- **Owner-selected: 1 (A3).** Unchanged.
- **`R6/G7`: NOT GRANTED.** Unchanged.
- **Track A / Terminals B–E / capability probe: `NOT OBTAINED`.** Unchanged.
- **Closure fraction: ~29%.** Unchanged — this addendum adds **no** governance progress, because
  verifying a defect does not register a decision.

**What did change:** two findings moved from *asserted with anchors* to *re-read and confirmed line by
line this session*, and one strengthening observation (§3) was added to the record. **That is a change
in evidential confidence, not in status.** TB-2 and TB-3 remain **unfixed** and still block **R6.1**.

---

## 6. Safety boundary — what this addendum did not do

| Prohibition | Status |
|---|---|
| Implement R6.1–R6.7 | **Not done** |
| Change production code | **Not done** — zero writes outside this document; source files opened read-only |
| Execute tests (incl. the U0 artefact) | **Not done** — nothing executed, nothing modified |
| Provider calls, migrations, deployments | **Not done** |
| Commits, staging, resets, cleanups, rebases, destructive Git | **Not done** |
| Amend a shared register or protected document | **Not done** |
| Invent an owner decision, approval, signature, test result, threshold or gate acceptance | **Not done** |
| Assume current HEAD / branch / worktree | **Not done** — still INHERITED and unverifiable |

---

## 7. Final status of this addendum

| Field | Value |
|---|---|
| **Purpose** | Re-verify the two load-bearing technical findings |
| **Findings re-verified** | **8 of 8 as stated** — TB-2/C-07 and TB-3/C-05 **confirmed** |
| **New observations** | **1** — in-source comment contradicts settlement code (§3) |
| **Verdict effect** | **NONE** — NO-GO stands |
| **R6.0** | **CONDITIONALLY READY — not closed, not frozen, not signed** |
| **Next action** | **Belongs to CHEF_P** — settle `C-02`, record `ADR-2/C-1`, register A3 then B1 |

**This addendum strengthens the evidence behind two blockers. It clears no blocker and advances no
decision, because evidence is not authority.**

---

**SabiRoute decides. LiteLLM executes. Evidence guides the path.**
