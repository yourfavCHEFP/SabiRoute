# R6-CLOSE-FINAL-06 — R6.0 Consolidated Closure Decision Pack

**Status:** CONSOLIDATED DECISION PACK — **NOT OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED**

**Date:** 2026-11-07 (UTC)

**Repository baseline at authoring:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`.

**Baseline correction (C-1, verified 2026-11-08).** The repository has since
advanced one commit to `1e69ada943f3d3921122219e7a569cdff989d3fd`, which
**commits** the two settlement modifications this pack records as uncommitted.
The authoring state above is preserved as historical context; the live baseline
is `1e69ada9`. Corrected values appear in §2.1, §7.3 and §11.

**Correction-report status (FINAL-07 `C-1…C-4`, applied 2026-11-08).** The four
documentation corrections recorded by FINAL-07 §3 are dispositioned as follows.
The settlement-integrity commit
`1e69ada943f3d3921122219e7a569cdff989d3fd` is the current baseline for every
value marked *current* below.

| # | Correction | Status in this pack | Where |
|---|---|---|---|
| **C-1** | Baseline is one commit behind | **FIXED** — `1e69ada9` note carried; `08201da8` retained as historical | §2.1, §7.3, §11 |
| **C-2** | FINAL-05 verifies 38 rows of a 39-row table | **RECORDED, NOT FIXED** — the patch target is FINAL-05 §3, which is outside this correction's authorised file set; FINAL-05 text is unchanged | §7.3 |
| **C-3** | Corpus count stale by one | **FIXED** — current count is **42** files on disk | §7.3 |
| **C-4** | "33 assertions plus the two behavioural tests" double-counts | **FIXED** here — the 33 are enumerated and "plus" dropped; the CF-03 half is outside this file set | §7.2 B-1 |

**Only two of the four are fully closed.** C-2 and the CF-03 half of C-4 target
documents this correction is not authorised to edit; they are recorded rather
than silently marked done. No U2-bound document (protocol, addendum, T16) was
touched, so no `protocol_sha256`, `addendum_sha256` or `t16_sha256` input changes,
and the genesis ordering hazard (R1) is untouched.

**Author identity:** Claude Code, which 03B-R1 §14 (`:268-280`) and addendum
`PARAM-F.2` (`:301-303`) designate as **registrar**. This document is therefore
**not** the `PARAM-F.3` independent verification, and it satisfies no part of it.

**Purpose.** This is the single consolidated decision pack for R6.0 closure. It
replaces the need to read six overlapping documents to answer "what is open, who
must act, and in what order." It **consolidates**; it does not supersede the
evidentiary record. Every claim below is traceable to a source document, and
where sources disagree the disagreement is recorded rather than smoothed.

**What this document is not.** It approves nothing, incorporates nothing,
executes nothing, signs nothing, and creates no REG record, VER record, ledger
entry, key, signature or checkpoint. It does not modify T16 or any canonical
document. It does not stage, commit or push.

---

## 0. Bottom line

**R6.0 IS NOT CLOSED. R6.0 REGISTRATION IS NO-GO. `R6/G7` IS NOT GRANTED.**

Three facts, each independently sufficient, define the current position:

1. **All 23 owner selections are recorded; none is registered.** T16 now records
   23 of 23 owner responses with 0 outstanding, but **0 approved, 0 registered,
   0 independently verified, 0 gate-accepted** (T16 §13, `:629`). Selection is
   not registration. The gap between them is the entire remaining R6.0 work.

2. **The registration protocol is not executable.** `marker_sha256` — a required
   field of the VER record — remains **uncomputable** because the owner has not
   answered **O1** (the U4 REG-marker digest boundary). The owner recorded O3,
   O4, O5 and R6.0-D on 2026-11-07 but **did not record O1 or O2**. Without O1 no
   VER record can be written, and without a VER record no registration can reach
   COMPLETE.

3. **The evidence is not durable.** The entire R6 governance corpus is
   **untracked** (`git ls-files | grep -c "r6-"` = **0**). Gate R6.0-D is
   **NOT MET**. A `git clean`, a fresh clone, or a branch switch that discards
   untracked files destroys the evidence the U2 digests bind.

**What is established and not in doubt.** The digest layer is mechanically sound
and reproduced at the authoring baseline: **67 passed, 2 skipped** in
`tests/test_r6_registration_digest_conformance.py` at this baseline (re-run for
this pack). The two skips are the executable form of O3 and O4/O5 — they are the
protocol asserting its own incompleteness, not pending work. The arithmetic is
correct. The **specification around it is not yet executable**, and the two
remaining specification gaps (O1, and the unapplied corrections C-1…C-7) are
owner acts, not registrar acts.

**Conformance correction (verified 2026-11-08).** The suite now reports
**81 passed, 1 skipped** (82 collected); the authoring measurement above stands
as the `08201da8` record and is not withdrawn. The one remaining skip is
`test_u11_genesis_entry_hash_is_computable`, reason *"awaiting authorised ledger
instantiation"* — the definition is incorporated (Amendment 1), so what is absent
is the **ledger artefact and the first-execution authority**, not an unanswered
decision. The O3-keyed skip resolved when O3 landed.

**A NO-GO here is not a finding that the work is wrong.** It is a finding that
the remaining distance is **owner-time and repository-time, not engineering-time**,
and that it is bounded and enumerable — which is what §8 does.

---

## 1. What this document consolidates

| Source | Role | Relationship to this pack |
|---|---|---|
| `r6-close-final-01-r6.0-closure-package.md` | Closure package of record; 23 decisions, RC-1…RC-13 checklist, ~29% | **Consumed.** Its checklist and percentage are carried forward in §2 and §7. |
| `r6-close-final-02-r6.0-closure-reverification-2026-11-05.md` | Re-verification; durability finding; fifth collision | **Consumed.** Durability is §7.3. |
| `r6-close-final-03-r6.0-registration-go-no-go-and-u4-decision-pack.md` | Registration NO-GO; O1–O5 register; U4 | **Consumed.** O1–O5 are §5. |
| `r6-close-final-04-r6.0-d-evidence-manifest-and-privacy-review-2026-11-07.md` | R6.0-D manifest (39 files + itself) and privacy scan | **Consumed.** §7.3. |
| `r6-close-final-05-independent-verification-2026-11-07.md` | Independent re-derivation of FINAL-04; F1–F4 | **Consumed.** §6. |
| `r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` | **Owner decisions O3, O4, O5, R6.0-D recorded** | **Consumed.** §5. |
| `r6-final-o3-o4-o5-canonical-corrections-proposal-2026-11-07.md` | C-1…C-7 corrections, unapplied | **Consumed.** §6. |
| `r6-registration-protocol-03b-r1.md` + `-owner-parameter-addendum.md` | The protocol and its parameters | **Consumed.** §4. |
| `r6-registration-protocol-03b-r1-u1-u3-*.md` (proposal, verification, independent verification, correction proposal) | U1–U3 digest definitions and their defects | **Consumed.** §4.3. |
| `r6-command-centre-01-master-ledger-and-workstream-assignments-2026-11-05.md` | Master ledger; N/M critical path | **Consumed.** §8. |
| `r6-g07-independent-closure-readiness-review.md` | Independent readiness review; G07-F1…F9, U1…U7 | **Consumed.** §9. |
| `r6-t16-r6-decision-option-register.md` | Canonical 23-card register | **Authoritative for decision state.** §3. |

**This pack creates no new register and renumbers nothing.** The canonical count
remains **23**. C-02 remains a governance interpretation, not a 24th card.

---

## 2. Verified baseline and current state

### 2.1 Baseline — re-derived for this pack, not inherited

| Fact | Command | Result |
|---|---|---|
| `HEAD` | `git rev-parse HEAD` | `08201da8013a58b486d5fa2d6c46b36588a27781` |
| Branch | `git branch --show-current` | `feat/sabiroute-routing-foundation` |
| Tracked modifications | `git status --porcelain --untracked-files=no` | **2** — `src/sabiroute/api/completions.py`, `tests/test_r6_settlement_integrity.py` — **superseded at `1e69ada9` — 0** |
| R6 documents tracked in Git | `git ls-files \| grep -c "r6-"` | **0** |
| Tracked files under `docs/` | `git ls-files docs \| wc -l` | **16** |
| R6 documents on disk | `ls -1 docs/ \| grep -c "^r6"` | **40** (39 manifest + FINAL-04; this pack is the 41st) — **superseded: 42 on disk at `1e69ada9`** |
| T16 owner responses | `grep -c "Owner response:"` | **23** |
| T16 still `PENDING` | `grep -c "Owner response:.*PENDING"` | **0** |
| Conformance suite | `.venv/bin/python -m pytest tests/test_r6_registration_digest_conformance.py -q` | **67 passed, 2 skipped** |

The two modified tracked files are **not** among the three U2-bound documents, so
**no digest in this pack is affected**. `completions.py` carries comment-only
reflow; `test_r6_settlement_integrity.py` is additive. Both are preserved and
untouched by this pack.

**Re-baselined (C-1, verified 2026-11-08).** At `1e69ada9` both files are
**committed** — `08201da` *fix: preserve unknown usage across budget and quota
settlement*, then `1e69ada` *test: strengthen settlement integrity regression
coverage* — and `git status --porcelain --untracked-files=no` reports **0**
tracked modifications on branch `sec/deps-nov`. The `08201da8` measurement above
is retained as the authoring baseline; it is not a current-state claim.

### 2.2 The five-status ledger — current, not historical

The five statuses are kept apart and never collapsed. This is the single most
important table in the pack.

| Layer | Count | Evidence |
|---|---|---|
| **Owner-selected** | **23 of 23** | T16 §13 `:629`; 0 outstanding |
| **Durably recorded** | **23 of 23 — but in an untracked file** | T16 is untracked (§7.3) |
| **Canonically registered** (REG) | **0 of 23** | T16 `:629` "0 REGISTRATIONS" |
| **Independently verified** (VER) | **0 of 23** | T16 `:629` "0 INDEPENDENT VERIFICATIONS" |
| **Gate-accepted** | **0 of 23** | T16 `:629` "NO GATE ACCEPTED" |

**The distinction that matters:** "durably recorded" here means *written into
T16*, which is itself untracked. It is recoverable, not durable. The corpus has
no version-control history at all (§7.3).

### 2.3 Provenance of the 23 selections — not uniform

T16 records three distinct provenance classes. They are **not** interchangeable
and must not be read as equally strong.

| Class | Decisions | Meaning |
|---|---|---|
| **`EXACT OWNER`** | `C1`–`C4`, `D1`–`D6` (10) | Direct owner instruction 2026-11-06, each identifier named against its disposition |
| **`CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED`** | `A1`, `A2`, `A4`, `B2`, `B3`, `B4`, `B5`, `B7`, `B8`, `B9` (10) | Supplied in conversation, transferred into T16; no timestamp, transcript or signature |
| **`MISSION-FRAMED`** | `A3` (1) | Confirmed directly in the ChatGPT project conversation; no local utterance |
| **Existing source references** | `B1`, `B6` (2) | Recorded in the 2026-11-04 supplement |

**Consequence.** Ten of the 23 selections rest on a source-limited provenance and
one on mission framing. This does not invalidate them — the owner has confirmed
them — but a `PARAM-F.3` verifier must be told which provenance class each
selection carries, because the verification of a `SOURCE LIMITED` selection is
weaker than that of an `EXACT OWNER` one. This is recorded, not resolved.

---

## 3. The 23 decisions — current state

All 23 are **selected and recorded in T16**; **none is approved, registered,
verified or gate-accepted**. The table below records the selection and the gate
each decision touches. It does not restate the full option text, which lives in
T16.

### 3.1 Group A — Architecture (4)

| ID | Selection recorded | Gate | Provenance |
|---|---|---|---|
| **A1** | Adopt §§8–15 as frozen architecture | R6.0 | SOURCE LIMITED |
| **A2** | Tier-1 metering fixes as integrity work | R6.0 | SOURCE LIMITED |
| **A3** | ADR-1 Option A — conditional, explicitly not implemented; P1–P5 unmet | R6.0 | MISSION-FRAMED |
| **A4** | Adopt T10-1…T10-7 scoping | R6.0 | SOURCE LIMITED |

### 3.2 Group B — Accounting and settlement (9)

| ID | Selection recorded | Gate | Provenance |
|---|---|---|---|
| **B1** | ADR-2 / T11 §8 I1–I9 as draft R6.1 foundation contract, with `ADR-2/C-1` resolution | **R6.0 and R6.1** | Existing source |
| **B2** | R6.1 scope = `/v1/chat/completions` only | R6.1 | SOURCE LIMITED |
| **B3** | Bypass authority operator-only, per-route, default-off | R6.1 | SOURCE LIMITED |
| **B4** | Phase-13 keep-out — no snapshot fields | R6.1 | SOURCE LIMITED |
| **B5** | Unknown wins at full original estimate, never a partial sum — **must name both governors** (C-07) | R6.1 | SOURCE LIMITED |
| **B6** | Monotone-shrink permanent unless re-baselined | R6.1 | Existing source |
| **B7** | Per-attempt re-derivation forbidden | R6.1 | SOURCE LIMITED |
| **B8** | Budget terminal-marker pattern (BL-15) | R6.1 | SOURCE LIMITED |
| **B9** | Reconciler in R6.7, marker migration in R6.1 | R6.1, Release | SOURCE LIMITED |

### 3.3 Group C — Capability and eligibility (4) — informs, does not gate R6.0

| ID | Selection recorded | Provenance |
|---|---|---|
| **C1** | **Deferred** (direct owner defer disposition) | EXACT OWNER |
| **C2** | Exclude non-Latin BM25 claims until Terminal D | EXACT OWNER |
| **C3** | Gate system/developer-role traffic until role-freeze proven | EXACT OWNER |
| **C4** | Extend the 2026-10-08 capability probe to `tool_use` / `structured_output` | EXACT OWNER |

### 3.4 Group D — Implementation authorisation (6)

| ID | Selection recorded | Provenance |
|---|---|---|
| **D1** | U0 merge policy — strict xfail | EXACT OWNER |
| **D2** | Authorise U0 separately under G7 | EXACT OWNER |
| **D3** | G7 scope = U0–U11, naming `tests/`, U12 in R6.7 | EXACT OWNER |
| **D4** | Authorise Track A engagement to schedule (BL-21) | EXACT OWNER |
| **D5** | Adopt T11 §15 T1–T8 numbering as canonical | EXACT OWNER |
| **D6** | Re-issue Terminal B/C/D/E prompts (BL-24) | EXACT OWNER |

**Recording D2/D3 grants no G7. Recording D4 contacts no reviewer. Recording D6
issues no prompt.** These are selections, not executions.

### 3.5 Non-decision items that must still be recorded

| Item | Status | Why it is not a 24th card |
|---|---|---|
| **`ADR-2/C-1`** — package-name conflict (`request_transform/` vs `compression/`) | **Unrecorded** | Must be a registration line or explicitly folded into B1; silence is not valid |
| **`C-02`** — Reading B (Group A + all Group B before BL-22) | Selected `EXACT OWNER`; **no register field exists** | Governance reading, not a card |
| **BL-22** — the R6.0 signature act | **NOT SIGNED** | Signature, not a decision |
| **`CLAUDE.md` §12** — documentation correction | Not authorised, not done | Documentation finding |

---

## 4. The registration protocol — what exists, what is executable

### 4.1 The protocol and its parameters

`r6-registration-protocol-03b-r1.md` (DRAFT) encodes owner-approved protocol
decisions **PROTOCOL/D-1…D-5**: separate response/approval axes; Protocol 03B
safeguards; five lifecycle counts; A3 as first intended registration; supplementary
evidence cannot replace canonical recording. It defines the REG marker grammar
(§5, nine fields), the VER record grammar (§6, six fields), the ten-item
inventory (§7), hash normalisation (§8), and the RECORD/REGISTER procedures
(§9–§10).

The addendum supplies `PARAM-A`…`PARAM-G`: record locations, hash/revision
contract, date contract, signature/checkpoint procedure, locking/parsing,
role assignments, and privacy exclusions.

**Roles (binding):** Owner = project owner; **Registrar = Claude Code**;
**Independent verifier = Claude Desktop**; Recovery engineer = GitHub Copilot.
Registrar and verifier must be distinct identities (`PARAM-F.5`).

### 4.2 The four digest classes — and the fifth that is missing

`PARAM-B` defines four digest classes: `PARAM-B.1` owner-response,
`PARAM-B.2` revision, `PARAM-B.3` extracted-card and whole-file. The U1–U3
proposal defines the byte boundaries for the extracted-card (U1), whole-file
(U2) and genesis (U3) digests, and the conformance suite asserts them.

**A fifth class is required and is not yet adopted.** `marker_sha256` — the
digest of the REG marker itself, carried by the VER record — has **no defined
byte boundary**. FINAL-03 §2.2 measured seven defensible readings producing six
distinct digests. This is **owner decision O1**, and it is **unanswered** (§5).

### 4.3 U1–U3 — defined, with four recorded defects

The U1–U3 proposal defines the digest boundaries and publishes 23 card digests,
3 whole-file digests and the genesis constant. The independent re-derivation
(`…-u1-u3-independent-verification-2026-11-07.md`) reproduced **every digest
exactly** but recorded four specification defects, and the correction proposal
(`…-u1-u3-correction-proposal-2026-11-07.md`) proposes fixes. **None is applied.**
The defects are: a contradiction in the ordinal origin, an uncomputable required
field, an incomplete open-decision list, and a test-vector column wrong for 3 of
23 cards (A4/B9/D6 — the corrected spans are `[168,180)`, `[322,334)`, `[473,485)`).

### 4.4 What is executable today

| Layer | Executable? | Why |
|---|---|---|
| U1 card digests | **Yes** | 23/23 reproduce; conformance suite asserts them |
| U2 whole-file digests | **Yes** | 3/3 reproduce |
| U3 genesis constant | **Yes** | `e893bd2c…d307` reproduces |
| `owner_sha256` (O3) | **Yes** | Alt-1 boundary recorded; A3 = `97dc52a6…f149`, 163 bytes |
| Genesis `entry_sha256` (O4) | **Yes** | Nine-field payload; `ad1484b0…af28` (508 bytes) |
| VER ledger schema (O5) | **Yes** | JSONL, eight payload + four envelope fields |
| **`marker_sha256` (O1)** | **NO** | **Boundary undefined — owner decision O1 unanswered** |
| **VER record** | **NO** | Requires `marker_sha256` |
| **Registration to COMPLETE** | **NO** | Requires a VER record with `result=PASS` |

**This is the crux.** Six of the eight layers are executable. The two that are
not are blocked on a single unanswered owner decision (O1), and they are the two
that gate the registration act itself.

---

## 5. Consolidated owner decision register

Every open owner decision in the corpus, in one table. **Recorded** decisions are
shown for completeness; **open** decisions are the owner's remaining work.

### 5.1 Recorded 2026-11-07 (O3/O4/O5 pack §0)

| ID | Decision | Selection | Consequence |
|---|---|---|---|
| **O3** | `owner_sha256` boundary for multi-line responses | **Alt-1** — exact extracted value, `A3: ` prefix retained, embedded LF preserved, §8-normalised; 161-byte stripped form retained as negative vector | `owner_sha256` computable |
| **O4** | Genesis `entry_sha256` canonicalisation | **Nine-field payload, proposal §3.1 canonicalisation**, with duplicate-key rejection, omitted-vs-null distinction, type enforcement, recomputation, UUIDv4 `ledger_id` | Genesis computable |
| **O5** | VER/genesis schema | **Append-only JSONL VER ledger authoritative**; HTML-comment `VER:v1` form superseded as container, six field names retained | Schema fixed |
| **R6.0-D** | Corpus durability | **Corpus must be tracked in Git before the registration act** | Repository act required |

### 5.2 OPEN — the owner's remaining decisions

| ID | Decision | Why it blocks | Recommended |
|---|---|---|---|
| **O1** | **Adopt the U4 REG-marker digest definition** (FINAL-03 §2.4, reading R-A: delimiters inclusive, no other change) as a fifth digest class | **`marker_sha256` uncomputable → no VER record → no registration** | **R-A** (R-C the only coherent alternative) |
| **O2** | Amend addendum §4 "four digest classes" → five, and correct §12.2 row 3 to name U4 as still open | Genesis validity post-amendment; must follow O1 | Adopt after O1 |
| **D-U3-1** | Checkpoint cadence | Already approved: one checkpoint per VER entry | Carried forward |
| **D-U3-2** | `ledger_id` scheme | Genesis field 4 | **UUIDv4** (carried forward) |
| **D-U3-3** | `allowed_signers` identity | Checkpoint binding | **`sabiroute-r6-owner`** (carried forward) |
| **R4** | `items_checked` bound (`0 ≤ n ≤ 10`) | Strict parser needs a bound; `items_checked=99` would parse | Add bound when parser rules open |

**D-U3-2 and D-U3-3 are first-execution values, not architecture decisions.** The
actual UUIDv4 and public-key fingerprint are generated at first execution and are
not supplied by any pack.

### 5.3 Recommended answering order

**O1 → O2 → (apply C-1…C-7) → (track corpus) → (re-derive U2) → genesis → register.**

O1 first because it is the only remaining hard block on the VER record. O2 second
because it records O1's outcome and, if applied before genesis, avoids the R1
ordering hazard (§9). The corrections and the tracking act follow, then U2 is
re-derived against the post-amendment files, then genesis is built from those
digests.

---

## 6. Canonical corrections C-1…C-7 — status

Seven corrections align the protocol and addendum with O3/O4/O5. **All are
proposed; none is applied.** The canonical documents are unchanged.

**Identifier scope.** The `C-1…C-7` in this section are the FINAL-O3/O4/O5
canonical corrections to the protocol and addendum. They are a **different
series** from the FINAL-07 `C-1…C-4` dispositioned in the header table and at
§7.4; the two share no numbering and must not be reconciled entry-for-entry.

| # | File | Anchor | Decision | Status |
|---|---|---|---|---|
| **C-1** | protocol | §6 `:112` | O5 — replace container sentence | Proposed |
| **C-2** | protocol | §6 `:114-117` | O5 — HTML-comment grammar → JSONL field table | Proposed |
| **C-3** | protocol | §6 `:130-135` | O5 — `VER record` → `VER ledger entry` | Proposed |
| **C-4** | addendum | `PARAM-A.2` `:93-97` | O5 — append JSONL realisation + checkpoint binding | Proposed |
| **C-5** | addendum | `PARAM-A.4` `:105-110` | O5 — `VER:v1 record` → `VER ledger entry` | Proposed |
| **C-6** | addendum | `PARAM-B.1` `:134-139` | O3 — append owner-response boundary rule | Proposed |
| **C-7** | addendum | after `PARAM-B.4` `:163` | O4 — insert `PARAM-B.5` canonical JSON + genesis | Proposed |

**Two corrections were themselves corrected after independent review (FINAL-05
F1–F4):**

- **F1 (material, remediated in the proposal):** C-7 originally cited proposal
  §3.2, whose worked example retains placeholders (`YYYY-MM-DD`, `<LEDGER_ID>`)
  that O4 forbids as test inputs; the placeholder line hashes to `f7749d46…`, not
  the published `ad1484b0…`. C-7 now names decision pack §3.5/§3.6 as the
  normative worked example.
- **F2 (low, remediated):** C-6 had appended a prospective single-line
  owner-response rule not authorised by O3. It is removed; O3 is not
  reinterpreted as Alt-3.
- **F3 (low, corrected):** decision pack §2.1 cited the A3 response at
  `T16:165-166`; it is at `163-164`.
- **F4 (informational, clarified):** FINAL-04 now states it excludes its own file
  from its own digest table; FINAL-05 is included in the revised manifest.

**No correction touches U4/O1.** The corrections implement O3, O4 and O5 only.
O1 remains a separate, unanswered decision.

---

## 7. Gates and blockers

### 7.1 Gate status

| Gate | Status | Basis |
|---|---|---|
| **R6.0-A** (adopt ADR-1 / A3) | **NOT MET** | A3 selected, unregistered |
| **R6.0-B** (adopt ADR-2 / B1 incl. `ADR-2/C-1`) | **NOT MET** | B1 selected, unregistered; `C-1` unrecorded |
| **R6.0-C** (record Group A + B, sign BL-22) | **NOT MET** | 0 registered; C-02 unsettled; BL-22 unsigned |
| **R6.0-D** (evidence durability) | **NOT MET** | Corpus untracked (§7.3) |
| **`R6/G7`** (implementation authorisation) | **NOT GRANTED** | Never requested; cannot be requested by a report |
| **R6.1** | **NOT READY** | Settlement integrity is its binding constraint; not authorised |
| **Track A / Terminals B–E** | **NOT OBTAINED** | No reviewer contacted |

### 7.2 Blockers that are not owner decisions

| # | Blocker | What closes it |
|---|---|---|
| **B-1** | **`PARAM-F.3` independent verification not performed.** Every digest reproduction was by Claude Code (registrar). A shared misreading survives all of them. | **Claude Desktop** must independently verify, using the corrected A4/B9/D6 spans, reproducing the 33 assertions (23 U1 + 3 U2 + U3 + 6 behavioural) and the two proposed additions (span identity; U4 marker fixture), and independently assessing whether the adopted U4 definition is unambiguous. |
| **B-2** | **Gate R6.0-D — evidence binds untracked files.** | Track the corpus (§7.3). |
| **B-3** | **BL-22 NOT SIGNED.** | Owner signature against a re-derived baseline, after C-02 settled and decisions registered. |
| **B-4** | **RC-8 UNMET** (BL-22 signed) and all 23 approval records `NOT APPROVED`. | Owner approval records. |
| **B-5** | **Operational registration authority DEFERRED.** | Separate operational authority grant. |

### 7.3 R6.0-D — the durability act

The owner has selected that the corpus must be tracked before registration. The
manifest evidence is FINAL-04: **39 files** with SHA-256, byte size and line
count, plus FINAL-04 itself as the 40th (excluded from its own table). FINAL-05
independently recomputed that manifest with **0 mismatches** and found **1
low-severity privacy finding** — an absolute home path at
`r6-registration-protocol-03b-r1-u1-u3-verification-report.md:229`, disclosing an
OS username; no credentials.

**Current corpus size (C-3, measured 2026-11-08 at `1e69ada9`): 42 files on
disk.** FINAL-06 and FINAL-07 lie outside the 39-row manifest. The privacy scan
has since been extended to all 42 files (§11) and returned the same single
finding above, so the conclusion is now measured for the whole corpus rather than
a 40-file subset.

**Smallest valid act (D-1, recommended):** a single dedicated commit adding the
`docs/r6-*.md` corpus, **excluding** the two settlement files
(`src/sabiroute/api/completions.py`, `tests/test_r6_settlement_integrity.py`),
which are unrelated and must not be swept in. (At authoring these were
uncommitted working-tree modifications; at `1e69ada9` they are **committed** and
the tree carries **0** tracked modifications — the exclusion still applies, but
the act is no longer one of avoiding dirty files.) After that commit, all three U2
digests are reproducible from a git object and R6.0-D is met.

**Ordering (binding).** Apply C-1…C-7 → track corpus → re-derive U2 against
post-amendment files → build genesis from those digests → register. Building
genesis from pre-amendment digests and amending afterwards yields a genesis entry
that does not match the files it claims to bind (R1).

### 7.4 Closing-gate status (verified 2026-11-08 at `1e69ada9`)

Five closing gates were proposed against this pack and FINAL-07. Each is recorded
with its measured status and the evidence for it. **No artifact was invented to
satisfy a gate, and no requirement has been added that a gate does not state.**

| Gate | Requirement | Status | Evidence |
|---|---|---|---|
| **G1** | FINAL-06/07 state `C-1…C-4` (FINAL-07 §3) fixed, with actual commit SHAs | **PARTIAL** | C-1 and C-3 **FIXED**; C-4 **fixed in this file only** (CF-03 half out of set); C-2 **RECORDED, NOT FIXED** (target FINAL-05 §3 outside the authorised set). Baseline SHA `1e69ada943f3…d3fd`. Single source of truth: the header table. |
| **G2** | Metrics router visible and linked to "all three" | **BLOCKED — underspecified** | Metrics are served by `admin_router` at `/admin/metrics` (`src/sabiroute/api/admin.py:85`, mounted `src/sabiroute/main.py:164`); there is no standalone metrics router. The gate names "three" without naming three of what, and the actual admin telemetry surface is **four** (`/admin/metrics`, `/admin/errors`, `/admin/usage`, `/admin/latency`). A count that does not resolve cannot be closed. |
| **G3** | Threat model covering five classes | **BLOCKED — artifact absent** | `grep -ril "threat model"` over `docs/`, `README.md`, `CLAUDE.md` and `security-reports/` returns **0** matches. There is no threat-model document to amend, and no five-class list is named anywhere in the corpus. |
| **G4** | CI redaction rule + allowlist with named deployment-epoch lines | **BLOCKED — artifact absent** | `.github/workflows/ci.yml` is 57 lines and carries neither a redaction rule nor an allowlist (one comment mentions secrets); `deployment-epoch` has **0** occurrences repo-wide; `src/sabiroute/security/redaction.py` exposes only `redact_secrets()` and has no allowlist concept. |
| **G5** | "FINAL-06 repeats the… KPI to four decimals… deploy-approved SHA… golden fixtures byte-identical… corpus at 34" | **BLOCKED — unreconstructable** | The gate text is truncated mid-sentence at two points. No KPI document exists; no deploy-approved SHA is recorded; no `golden*` fixture file exists; and the corpus stands at **42** files, not 34. |

**R6.0-D is NOT closed by this section.** The corpus remains untracked
(`git ls-files | grep -c "r6-"` = **0**). §7.1 and §7.3 are unchanged on this
point.

---

## 8. The single ordered closure sequence

Each step is a separate act with its own authority. **None is implied by this
document.** Steps marked **[OWNER]** are owner acts; **[REPO]** are repository
acts; **[VERIFIER]** requires an identity distinct from the registrar.

| # | Act | Actor | Unblocks |
|---|---|---|---|
| 1 | **Answer O1** — adopt U4 REG-marker digest (R-A or R-C) | **[OWNER]** | `marker_sha256` computable |
| 2 | **Answer O2** — amend addendum §4/§12.2 to five digest classes | **[OWNER]** | Genesis validity post-amendment |
| 3 | **Apply C-1…C-7** to protocol and addendum | **[OWNER]** authorises; registrar applies | Protocol aligned with O3/O4/O5 |
| 4 | **Record `ADR-2/C-1`** as its own line (or fold into B1 explicitly) | **[OWNER]** | B1 cleanly registrable |
| 5 | **Settle C-02** recording locus and propagate Reading B into T13 §19.1 / T16 §547 | **[OWNER]** | BL-22 scope unambiguous |
| 6 | **Track the R6 corpus** (D-1), excluding the two settlement files | **[REPO]** | Gate R6.0-D met |
| 7 | **Re-derive U2** (`protocol_sha256`, `addendum_sha256`, `t16_sha256`) from committed blobs | Registrar | Genesis inputs durable |
| 8 | **Build genesis** from post-amendment digests; verify against §3.6 negative vectors | Registrar | Chain head exists |
| 9 | **Owner signs the genesis checkpoint** | **[OWNER]** | Ledger anchored |
| 10 | **Register A1–A4, B1–B9, C1–C4, D1–D6** (23) under the consolidated schema | Registrar | 23 REG records |
| 11 | **Independent verification** by Claude Desktop, one VER entry per decision, checkpointed per D-U3-1 | **[VERIFIER]** | 23 VER records; `PARAM-F.3` satisfied |
| 12 | **Post-COMPLETE read-back** (03B-R1 §15) | **[VERIFIER]** | COMPLETE valid |
| 13 | **Sign BL-22** against a re-derived baseline | **[OWNER]** | R6.0 closure condition 3 |
| 14 | **Gate acceptance** | **[OWNER]** | R6.0 closed |

**Steps 1–5 are owner acts. Step 6 is a repository act. Step 11 requires an
identity distinct from the one that authored every prior pass. No registrar-side
computation can substitute for any of them.**

**What this sequence does not include:** `R6/G7`, Track A, Terminals B–E and the
capability probe. **They do not gate R6.0.** Including them would inflate the
apparent distance and invite the error of waiting on external lanes to close a
governance act.

---

## 9. Risks carried forward

| ID | Risk | Mitigation |
|---|---|---|
| **R1** | **Amendment ordering invalidates genesis digests.** Applying C-1…C-7 or O2 changes `protocol_sha256`/`addendum_sha256`. | Fix the document set before genesis; re-derive U2 at the genesis act (§8 steps 3→7→8). |
| **R2** | **`marker_sha256` uncomputable until O1.** Hard block on verification. | Answer O1 (§8 step 1). |
| **R3** | **`owner_sha256` boundary closed by O3 but has no test vector for a real marker.** | The 161-byte negative vector is in the conformance suite; a real marker is validated at first registration. |
| **R4** | **`items_checked` has no stated bound.** `items_checked=99` would parse. | Add `0 ≤ n ≤ 10` when parser rules open. |
| **R5** | **NFC divergence inert, not permanent.** All three source files are NFC today; the first non-NFC edit makes U1/U2 (and R-A/R-D for U4) diverge. | D-U1-1 exists to force the choice. |
| **R6** | **Evidence durability.** Gate R6.0-D NOT MET. | §7.3. |
| **R7** | **No pass in this corpus is independent.** Every digest reproduction is by the registrar. | `PARAM-F.3` by Claude Desktop (§7.2 B-1). |
| **R8** | **U4's chain layer is entirely unexercised.** No key, no ledger, no checkpoint. | Approving U4 must not be read as progress on U3. |
| **R9** | **Citation defect in a prior document.** The independent re-derivation cites addendum §12.2 at `:463` (row 2, field escaping); the issue-3 row is `:464`. | This pack cites `:464`. |
| **R10** | **Provenance is not uniform.** 10 selections are `SOURCE LIMITED`, 1 is `MISSION-FRAMED`. | A verifier must be told each class (§2.3). |
| **R11** | **Identifier collisions (5).** `ADR-2/C-1` vs `GROUP-C/C1`; `T12/A1`–`A6` vs `GROUP-A/A1`–`A4`; `C-02` (defect vs reading); `D`-series (pack vs register); `Q3`/`Q5`/`G16`/`G17` unresolvable. | Label discipline in prose; no renumbering; external input for `Q3`/`Q5`/`G16`/`G17`. |
| **R12** | **G07 findings open.** G07-F1 (test header asserts "approved" while B5 is not approved), G07-F3 (C-namespace collision), G07-F4 (Terminal B assigned R6.1 work), G07-F5/F6 (work sequenced ahead of `D3`/Track A), G07-U1 (F-05/G-06 unreconstructable). | Recorded; each is an owner-visible record defect, not a system defect. |

---

## 10. What this document does not do

- It does not approve, incorporate, adopt or execute O1, O2, O3, O4, O5, R6.0-D,
  or any part of the U1–U3 proposal or the correction proposal.
- It satisfies **no** part of `PARAM-F.3`.
- It does not create a REG or VER record, a ledger, an entry, a key, a signature,
  or a checkpoint.
- It does not modify T16, the protocol, the addendum, or any canonical document.
- It does not mark any gate COMPLETE, and it explicitly records Gate R6.0-D as
  **NOT MET**.
- It does not authorise BL-22, R6.1, or any implementation.
- It does not supply operational registration authority, which remains
  **DEFERRED**.
- It does not answer O1 or O2.
- It does not supersede CLOSE-FINAL-01 through -05; it consolidates them.

---

## 11. Attestation

- No file was staged, committed or pushed in producing this pack.
- No canonical document was modified. The **§6 canonical corrections `C-1…C-7`**
  remain proposals, not applied edits. (The FINAL-07 `C-1…C-4` in the header
  table are a separate series — see the identifier-scope note in §6.)
- The baseline was re-derived for this pack (§2.1), not inherited.
- The conformance suite was re-run at the authoring baseline (`08201da8`):
  **67 passed, 2 skipped**; re-measured at `1e69ada9` on 2026-11-08 as
  **81 passed, 1 skipped** (see the correction pass above).
- The two modified tracked files are preserved and untouched.
- Every digest cited in this pack is quoted from a source document that computed
  it; this pack computes no new digest and asserts none it did not read.

**Correction pass — 2026-11-08.** FINAL-07 `C-1`, `C-3` and the FINAL-06 half of
`C-4` were applied to this file as documentation corrections; `C-2` and the CF-03
half of `C-4` were recorded as out of the authorised file set. The following were
re-measured at `1e69ada943f3d3921122219e7a569cdff989d3fd` for this pass:

- `tests/test_r6_registration_digest_conformance.py` — **81 passed, 1 skipped**;
  the single skip is `test_u11_genesis_entry_hash_is_computable`, reason
  `awaiting authorised ledger instantiation` (`:570`).
- `tests/test_r6_settlement_integrity.py` — **6 passed**.
- Both suites together — **87 passed, 1 skipped**.
- Corpus on disk — **42** files; R6 documents tracked — **0**.
- Privacy scan, scope stated exactly: `grep -rn '/Users/' docs/r6-*.md` over all
  42 corpus files. It returned **two** occurrences: the absolute home path at
  `r6-registration-protocol-03b-r1-u1-u3-verification-report.md:229`, and one in
  FINAL-07 §5. The FINAL-07 occurrence was elided to `<USER>` in this pass; the
  source file is outside this correction's authorised set, was **not** edited, and
  its `:229` finding therefore **stands unresolved**. Post-edit, **1** occurrence
  remains corpus-wide.

No registration entry, ledger, genesis, key, signature or checkpoint was created;
no owner selection or approval was altered; nothing was staged, committed, pushed
or regenerated.

**Git state — before this pack:** HEAD `08201da8`, branch
`feat/sabiroute-routing-foundation`, 2 modified tracked files, 0 staged, 16
tracked files under `docs/`, 0 R6 documents tracked.

**Git state — verified 2026-11-08 (C-1):** HEAD `1e69ada9`, branch `sec/deps-nov`,
**0** modified tracked files — the two settlement files are committed at
`1e69ada9` — 0 staged, 0 R6 documents tracked.

**Git state — after this pack:** unchanged, plus this file as a new untracked
path. No staging, no commit, no push.

---

**CONSOLIDATED DECISION PACK — NOT OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED**

**VERDICT: R6.0 NOT CLOSED · R6.0 REGISTRATION NO-GO · `R6/G7` NOT GRANTED.**

**SabiRoute decides. LiteLLM executes. Evidence guides the path.**
