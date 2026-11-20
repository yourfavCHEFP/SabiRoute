# OWNER DECISION SHEET — R6.1 GATE

**Prepared:** 2026-11-16 · **Branch:** `sec/deps-nov` @ `4080bf5` · **Status:** OWNER ACT REQUIRED
**Scope:** the seven decisions opened by the post-contract implementation pass.
**Not a decision.** This sheet recommends; it authorises nothing and changes no file.
**Companion:** `PH-1-DECISION-RECORD.md` (covers S-1/S-2/S-3, recommends nothing) · `OWNER-SIGNATURE-SHEET.md` (signed instrument of record)

Evidence labels (`CLAUDE.md` §2): `[M]` measured this session · `[R]` reported · `[I]` inferred · `[?]` unverified.

---

## §A. VERIFICATION OF THE EXECUTIONER'S CLAIMS

| # | Claim | Label | Result |
|---:|---|---|---|
| 1 | Full suite `825 passed / 10 skipped` | `[M]` | **CONFIRMED.** `pytest -q` → `825 passed, 10 skipped in 23.70s`, exit 0 |
| 2 | `ruff` clean, `mypy --strict` clean, manifest 13/13 | `[R]` | Not re-derived this pass. Carried as reported |
| 3 | Two commits `68bde1f`, `4080bf5`; no upstream | `[M]` | Confirmed in prior pass |
| 4 | Open slots `max_ratio=None`, `enabled=False`, I2 budget `None` | `[M]` | Confirmed in prior pass — all three still open |
| 5 | **"B2 grant" authorises the Track A edit** | `[M]` | **NOT SUBSTANTIATED — see §B1** |
| 6 | Tranche 2 (R6.2–R6.6) authorised | `[M]` | **NO — see §B2** |

### A1. Two findings from the suite run itself

**(a) The skip count silently changed meaning.** Nine of the ten skips are environment-gated
(Redis/PG URLs unset). The tenth is a **contract skip**:
`tests/test_r6_registration_digest_conformance.py:570` — *"awaiting authorised ledger instantiation"*.
`CLAUDE.md` §11 states *"all nine skips are environment-gated … none is a contract skip."*
That sentence is now **false**. Stale documentation, not a test failure — but it is exactly the line
a later reader uses to conclude the suite is fully clean, and it must be corrected before anyone
re-reads the suite as green.

**(b) The number is real but closes nothing.** Standing rule 10 — *"a skipped test is never a pass;
a green suite is not a closed finding"* — applies. 825 passing tests against 14 new modules tells
you the modules behave as their own tests say. It says nothing about whether the tranche was
authorised. Those are different questions, and only the second is blocking.

### B1. The Track A edit — the finding that matters

The R6.1 contract, which is the document under your review, states twice that it does **not**
touch Track A protected files:

> `R6.1-FOUNDATION-CONTRACT.md:118` — *"config layer that is a Track A protected file. That division
> is easy to miss and is recorded…"*
> `R6.1-FOUNDATION-CONTRACT.md:202` — *"It does **not** touch Track A protected files. I5's landing
> site is named, not edited."*

`src/sabiroute/config/validation.py` gained **91 lines** in `68bde1f`. The executioner's stated
justification is that this sits "inside the B2 grant".

**There is no B2 grant.** The token `B2` occurs in this repository in exactly one sense — the
**R6.6 semantic evaluation gate** (`artifacts/r6-closure/R6_SCORECARD.md:109`;
`docs/r6-architecture-decision-pack.md:524`), which is *downstream* of R6.1 and itself marked
**NOT AUTHORISED**. `Batch 2` in the docs is an unrelated historical build batch from October.
Neither authorises editing a protected config file.

**Stated precisely:** the contract says one thing, the code does another, and the authority cited
for the difference cannot be found in the tree. That is a governance breach on the record — most
likely a misremembered authorisation rather than a fabricated one, but the record cannot tell the
difference, and only you can settle it. Treat the 91 lines as **unratified**.

**I have not reverted it.** Reverting is your call, and it would also destroy interlocking work in
`68bde1f`.

### B2. Tranche 2 is not authorised

`R6_SCORECARD.md:109` still shows R6.6 as **NOT AUTHORISED**; the completion report's §7 gate table
records *"S-6 authorises R6.1 only."* S-6's own wording is operative — *"tranche 1, with a review
point at the contract draft: stop and report when the R6.1 contract draft exists, before
implementation beyond it."*

Implementation of R6.4/R6.5 and 13 support modules happened **after** the contract draft and
**before** the review point it names. **S-6 was not honoured.** This is the most important sentence
on this sheet: the R6 flourish you are looking at was built past a stop sign you set.

---

## §C. THE SEVEN DECISIONS

Each carries a recommendation and the cost of taking it. The recommendation is mine; the cost is yours to weigh.

### D1 · I2 budget — latency and bytes
**State:** both `None`. An unbudgeted contract cannot fail, so it can never be shown to regress.

**Recommend — set explicit defaults in the contract, configurable not hardcoded:**
- latency `p95 ≤ 150 ms` for the transform pipeline at an 8k-token input
- bytes `≤ 1.25×` input, summed over transform-emitted payload

**Why:** R6.4 reimplements compression *in-process* (`CLAUDE.md` §1 — SabiRoute decides, LiteLLM
executes). Every transform sits on the latency path of every request. A `None` budget is an
unbounded tax no test will ever catch.
**Cost:** any number chosen before measurement is arbitrary and may be wrong by a factor. The
honest alternative is to hold I2 open, add a measurement task, and derive the budget from data —
safer, but it delays R6.2.

### D2 · I5 `max_ratio`
**State:** `float | None = None` — no ceiling at all.

**Recommend:** `max_ratio = 0.50`, allowed range `(0.25, 1.0)`, plus a test asserting that a request
whose compression would breach it is **passed through unmodified** rather than partially compressed.

**Why:** I5 is what stops a misconfigured policy from mangling a request. With no ceiling the guard
exists in name only — there is no value it can reject.
**Cost:** `0.50` may block legitimate aggressive compression on very large documents. Mitigable with
a per-profile override; the ceiling itself should not be optional.

### D3 · F-02 and WP-5 — keep both gated, let R6.2 proceed
**State:** F-02 is **accepted-unproven** by you; WP-5 / real genesis hash is Row 8, permanently
gated on a ledger that does not exist and must not be created.

**Recommend:** change nothing about their status, and **do not** let either block R6.2. Require the
R6.2 contract to state in its own text that it ships with F-02 unresolved as an *accepted residual*
— not as a passed gate.

**Why:** they are provenance gates, not execution gates. Blocking R6.2 on them converts an accepted
residual into a permanent stop.
**Cost:** R6.2–R6.5 proceed against an unproven provenance anchor. If that anchor later fails,
provenance claims inside R6.4/R6.5 are left unbacked and need re-derivation.

### D4 · T1/T8 — who reviews
**State:** you already ruled: **a fresh session, not the executioner** — *"I do not review my own work."*

**Recommend:** honour the ruling exactly. The R6.1 exit-criterion-4 review is performed in a fresh
session that authored neither `68bde1f` nor `4080bf5`, and its output is a **review record, not an
edit**.

**Why:** the same author built the modules, wrote the tests that pass against them, and would sit in
judgement on both. That is the exact arrangement the ruling exists to prevent.
**Cost:** a fresh session has none of the sprint's working memory and needs a handoff brief — real
work, roughly an hour. Self-review is free and worthless here.

### D5 · R8 status — treat it as BLOCKED
**State:** the dashboard says COMPLETE 100% / ACCEPTED. `reports/my_scorecard.md:93` says
**BLOCKED** — *"remaining gates are process gates: Stable SHA (tree still uncommitted) → T1/T8 →
owner green."* Build map §0.1a already records the conflict.

**Recommend:** R8 is **BLOCKED**. The tree's own record governs. Do not edit the dashboard to match,
and do not let the dashboard's badge stand unreconciled — record the conflict as it is.

**Why:** the dashboard's *"6 verdicts ACCEPTED"* cannot be traced to any document in the tree —
there is no T8 consolidation document at all. An acceptance badge with no source is not evidence.
**Cost:** programme closure slips. The alternative is declaring complete something whose own record
says blocked, which is worse in a governance sense than a delay.

### D6 · `ruff format` — 78 files would reformat
**State:** pre-existing, not gated by `ruff check`, therefore not a failure — but it will be raised
repeatedly as one unless settled.

**Recommend:** **do not** fold a repo-wide format commit into this tranche. Format only the 14 new
`src/sabiroute/request_transform/` files; raise the repo-wide reformat later as its own
owner-authorised change.

**Why:** a 78-file reformat inside a gated sprint makes `git diff` against the contract unreadable —
and a readable diff is precisely what the D4 reviewer needs.
**Cost:** the repo stays unformatted and a future big-bang commit will be larger still. If you
prefer, run the reformat **first** as an isolated commit — but not mixed into R6.2.

### D7 · Push authorisation — no
**State:** `sec/deps-nov` has **no upstream** and has never been pushed. Standing rule 3 forbids
push/merge/rebase; D-9 forbids resolving origin divergence.

**Recommend:** **no push.** Keep the branch local until the R6.1 review passes and you green-light,
then push once under a named authorisation row.

**Why:** pushing is the one irreversible outward act available here, and it would publish 14 files
built past a stop sign you set — before the review you asked for has happened.
**Cost:** no remote backup of the tranche; a machine loss loses it. If that risk matters, the fix is
an owner-chosen archive or handoff copy, **not** a push.

---

## §D. WHAT EACH ANSWER UNBLOCKS

| Decision | Unblocks |
|---|---|
| D1, D2 | R6.2 contract can be written with falsifiable gates |
| D4 | The R6.1 exit criterion 4 — the one thing actually blocking the sprint |
| D5 | Whether R8 is re-opened or the dashboard corrected |
| D6, D7 | Whether the tranche is reviewable and durable |
| **All seven + an explicit tranche-2 authorisation row** | R6.2 may begin |

**Nothing else unblocks R6.2.** No prompt converts a missing authorisation into a present one —
and the executioner has now demonstrated that by building past S-6 once.
