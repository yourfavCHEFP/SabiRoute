# R6 T16 — R6.0 Decision Option Register

**Status:** canonical decision register. **This register records owner selections where supported by the canonical evidence, approves no decision, grants no G7 and authorises no implementation, test, or U0/U1/R6.1/Track A work.**
**Mode:** documentation extraction and reconciliation. Exactly one new file was created. **T13, T14 and T15 were not modified by T16.**
**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`, upstream `origin/feat/sabiroute-routing-foundation`, divergence **ahead 6 / behind 3**. The working tree carried pre-existing untracked files only; no tracked modification existed before T16 and none was introduced.
**Authority:** `docs/r6-t13-documentation-correction-and-owner-decision-preparation.md` (T13, the decision register), as audited by `docs/r6-t14-independent-t13-audit-and-decision-readiness.md` (T14, verdict `READY WITH CORRECTIONS`) and briefed by `docs/r6-t15-r6-owner-decision-brief.md` (T15).

**Canonical count: 23 decisions. `23 canonical decisions; 23 owner selections recorded; 0 approved by this extraction mission.`**

---

## Canonical Authority and Registration Status
This document is the canonical R6 decision register and the authoritative record for the 23 decisions identified in its decision cards.

It supersedes the preparation-only role previously assigned to this document. T13, T14 and T15 remain source, audit and briefing materials and retain their historical evidentiary value.

Canonical designation does not itself select, approve, register, independently verify or gate-accept any decision.

Each decision retains its individual owner-response and approval states. A decision remains PENDING until an explicit owner selection is recorded. Selection does not constitute approval.

REG records provide canonical registration evidence. Independent VER records provide verification evidence. Gate acceptance remains a separate governance act.

The 23 decision identifiers and their existing option structures are preserved. C-02 remains a governance interpretation, not an additional decision card.

Historical extraction provenance and prior decision evidence must be retained.

### Historical Origin and Extraction Provenance
**Original authorised change.** The original authorised change — and the only change made at that time — was the creation of `docs/r6-t16-r6-decision-option-register.md`. The instruction was quoted verbatim:

> "Create exactly one new document: docs/r6-t16-r6-decision-option-register.md"

**Original preparation-only purpose.** T16 was originally the working document for the R6.0 owner decision session. It was created as a flat, traceable extraction: one index, 23 cards and one response sheet. It added no analysis and removed no ambiguity; it made the existing ambiguity visible in one place so the owner session did not have to search three documents. That preparation-only status is historical and has been superseded by the canonical designation above.

**Original relationship to source materials.** T16 was originally read *alongside*, not instead of, its sources: T13 remained the authoritative decision register containing the exact questions and the `X-1…X-6`/`C-01…C-08` corrections; T14 remained the independent audit; and T15 remained the narrative brief. T13, T14 and T15 retain their historical evidentiary value.

**Original duplicate/superseding-document finding.** No prior `t16` artefact existed anywhere in the working tree (`find` over the repository excluding `.git`/`node_modules/` returned nothing). No existing document claimed to be a consolidated option register. At creation, this file superseded nothing and duplicated nothing; it was purely additive.

**Why the consolidated extraction was created.** T13 was a correction and preparation report whose decisions were distributed across §§7–§10, with briefs in §§11–§12 and gate logic in §§19–§20, interleaved with gate reassessment, Terminal packets and the `X-*`/`C-*` corrections. T15 was a narrative brief that walked the owner through two preconditions, two ADRs and one settlement boundary in prose and deliberately did not enumerate all 23 decisions in card form. T16 consolidated those materials into one flat, traceable 23-card register for the owner session.

**Original non-authority boundary.** T16 was originally not an approval record, ADR, gate decision, signature or implementation order. A recommendation was not a decision, a prepared card was not a taken decision, and silence was not approval. Those historical constraints remain consistent with the canonical designation, which likewise does not itself select, approve, register, independently verify or gate-accept any decision.

### Current owner-selection provenance
The following ten selections were explicitly supplied by the owner in the conversation and subsequently transferred into the corresponding T16 owner-response fields during this reconciliation:

`A1`, `A2`, `A4`, `B2`, `B3`, `B4`, `B5`, `B7`, `B8`, and `B9`.

Their provenance classification is **CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED**. This records the known origin and the later transfer into T16; it does not assert an exact timestamp, signed document, transcript filename, archived message, cryptographic signature, or independently authenticated owner signature. The selections were not individually present in the repository evidence inspected by the independent verifier before this transfer, and the November 4 owner supplement did not contain all 13 selections. A3 remains separately classified as `MISSION-FRAMED`; B1 and B6 retain their existing source references and provenance classifications.

### Group C and Group D owner-selection provenance (2026-11-06)

The following ten selections were supplied by the owner as an explicit, direct instruction on **2026-11-06** and transferred into the corresponding T16 owner-response fields by the T16 Group C/D owner decision transfer:

`C1`, `C2`, `C3`, `C4`, `D1`, `D2`, `D3`, `D4`, `D5`, and `D6`.

Their provenance classification is **`EXACT OWNER`**. The owner's instruction stated the ten dispositions directly, in the same message that authorised this transfer, and named each decision identifier against its disposition. It is therefore an exact owner source — not a mission-framed reconstruction and not a conversation-derived inference. The recorded dispositions are: `C1=defer`, `C2=yes`, `C3=gated`, `C4=yes`, `D1=strict`, `D2=yes`, `D3=yes`, `D4=yes`, `D5=yes`, `D6=yes`.

`EXACT OWNER` records the origin and authority of the selection. It does **not** constitute approval, registration, independent verification or gate acceptance. All ten approval records remain `NOT APPROVED`. Recording `D2` and `D3` grants no G7; recording `D4` contacts no Track A reviewer; recording `D6` issues no Terminal B/C/D/E prompt. The Group A and Group B provenance classifications above are unchanged by this transfer.

---

## 2. Executive summary

- **Purpose:** give the owner one authoritative working document from which the R6.0 decision session can be conducted.
- **Source documents:** T13 (§7–§12, §19, §20 and corrections `C-02`, `C-03`, `C-07`), T14 (audit), T15 (brief, including its `ADR-2/C-1` versus `GROUP-C/C1` warning).
- **Canonical decision count:** **23**.
- **Group breakdown:** A = 4 · B = 9 · C = 4 · D = 6 · **Total = 23**.

| Group | Register | Canonical IDs | Count |
|---|---|---|---:|
| A | T13 §7 — R6.0 Architecture Approval | A1, A2, A3, A4 | 4 |
| B | T13 §8 — Accounting and Settlement Policy | B1…B9 | 9 |
| C | T13 §9 — Capability Recovery and Eligibility | C1, C2, C3, C4 | 4 |
| D | T13 §10 — R6.1 Implementation Authorization | D1…D6 | 6 |
| **Total** | | | **23** |

- **Lifecycle status:** all 23 decisions are in scope; all 23 owner selections are supplied and canonically recorded (A1–A4, B1–B9, C1–C4 and D1–D6); 0 remain outstanding; 0 are approved, registered, independently verified or gate-accepted. C1 is recorded as a direct owner **defer** disposition rather than an option selection.
- **What the register does not authorise:** no ADR adoption, no architecture selection, no G7 grant, no U0/U1/R6.1/Track A implementation, no test execution, no deployment, no config or infrastructure action.

**Deliberately excluded from the canonical 23** (each is represented elsewhere in this document without inflating the count):
- **BL-22** — the R6.0 signature act (T13 §20 item 24). Not a Group decision; see §9 and §10.
- **CLAUDE.md §12 correction** — a documentation finding (T13 §20 item 25), separately authorised.
- **`ADR-2/C-1`, `ADR-2/C-2`, `ADR-2/C-3`** — ADR-2's internal conflicts (T13 §12.4). See §7.
- **D3's three sub-choices** — separately answerable components of one canonical decision (T13 §10, T14 C-03). See §6.

---

## 3. Master decision index

All 23 canonical decisions, each exactly once. Wording is T13's except where marked.

| ID | Group | Decision | Existing recommendation | Alternatives | Dependencies | Blocks | Status | Source |
|---|---|---|---|---|---|---|---|---|
| **A1** | A | Adopt §§8–15 as the frozen architecture? | **Yes** | Return D14/D19-Tier-2 for re-scope | Group B record | **R6.0** | `SELECTED` | T13 §7, §20-1 |
| **A2** | A | Treat Tier-1 metering fixes as integrity work, not optional feature work? | **Yes** — BL-01…BL-04/A6/BL-06/BL-07 close live holes | Defer post-v1 | — | **R6.0** | `SELECTED` | T13 §7, §20-2 |
| **A3** | A | Adopt ADR-1: Option A conditional, explicitly not implemented? | **Yes** (honest freeze) | Redefine target as inline-hardened | §11 brief | **R6.0** | `SELECTED` | T13 §7, §11, §20-3 |
| **A4** | A | Adopt T10-1…T10-7 scoping? | **Yes** | Proceed without coupling/tokenizer/null/capability/governor guardrails | — | **R6.0** | `SELECTED` | T13 §7, §20-4 |
| **B1** | B | Adopt ADR-2: T11 §8 I1–I9 as the draft R6.1 foundation contract? | **Yes**, with C-1 name resolution | Require an external R6.1 design doc first | §12 brief; `ADR-2/C-1` | **R6.0, R6.1** | `SELECTED` | T13 §8, §12, §20-5 |
| **B2** | B | Restrict R6.1 scope to `/v1/chat/completions`, excluding `api/chat.py`? | **Yes** | Include the SabiChat path | — | **R6.1** | `SELECTED` | T13 §8, §20-6 |
| **B3** | B | Bypass authority: operator-only, per-route, default-off? | **Yes** | Trusted-service signal | T4 flag | **R6.1** | `SELECTED` | T13 §8, §20-7 |
| **B4** | B | Phase-13 keep-out: R6.1 emits no snapshot fields? | **Yes** | Amend to schema-1.2 now | — | **R6.1** (R6.0 if deferred) | `SELECTED` | T13 §8, §20-8 |
| **B5** | B | Settlement basis: unknown wins at the full original estimate, never a partial sum? | **Yes** — this is T12 §12's contract | Partial-sum settlement | `C-07` (both governors) | **R6.1** | `SELECTED` | T13 §8, §20-9; T15 §5 |
| **B6** | B | Monotone-shrink **permanent** unless the reservation is re-baselined? | **Yes** | Allow expansion | — | **R6.1** | `SELECTED` | T13 §8, §20-10 |
| **B7** | B | Per-attempt re-derivation of the effective request forbidden? | **Yes** — forbid | Allow re-derivation | — | **R6.1** | `SELECTED` | T13 §8, §20-11 |
| **B8** | B | Adopt the budget terminal-marker pattern (BL-15) transferred from `_QUOTA_RESERVATIONS`? | **Yes** | Design a new state machine | — | **R6.1** | `SELECTED` | T13 §8, §20-12 |
| **B9** | B | Reconciler placement: R6.7, with the marker migration in R6.1? | **Yes** | Pull the reconciler into R6.1 | U9 | Release (not R6.0/R6.1) | `SELECTED` | T13 §8, §20-13 |
| **C1** | C | Resolve byok/paid semantics and billing-source scope (BL-30)? | "Owner conversation before any BOUNDED+ claim" *(see §12.1)* | — | — | Release claims | `DEFERRED` | T13 §9, §20-14 |
| **C2** | C | Exclude non-Latin BM25 relevance claims until Terminal D establishes a corpus? | **Yes** | Claim multilingual now | Terminal D | Release (G4) | `SELECTED` | T13 §9, §20-15 |
| **C3** | C | Gate system/developer-role traffic until role-freeze behaviour is proven (BL-09)? | **Gated** until role-freeze proven | FULL now | U5 | Partial R6.1 | `SELECTED` | T13 §9, §20-16 |
| **C4** | C | Extend the proven 2026-10-08 capability probe to `tool_use` and `structured_output` (BL-10)? | **Yes** — repeat a known procedure | Commission new methodology | §4.5 evidence | Release | `SELECTED` | T13 §9, §20-17 |
| **D1** | D | **U0 merge policy: strict-xfail, land-with-U1, or skip?** | **Strict xfail** | Land with U1; skip | §14 spec | **R6.1** | `SELECTED` | T13 §10, §20-18 |
| **D2** | D | Authorise U0 **separately** under G7, ahead of U1–U12? | **Yes** — test-only and reversible | Bundle with U1 | D1, D3 | **R6.1** | `SELECTED` | T13 §10, §20-19 |
| **D3** | D | Define G7 scope as U0–U11, explicitly naming `tests/`, with U12 in R6.7? | **Yes** | Include U12 | — | **R6.1** | `SELECTED` | T13 §10, §20-20 |
| **D4** | D | Authorise Track A engagement to schedule (BL-21) once T-numbering converges? | **Yes** | Defer | D5 | **R6.1** | `SELECTED` | T13 §10, §20-21 |
| **D5** | D | Adopt T11 §15's T1–T8 numbering as canonical? | **Yes** | Use campaign §15's T1–T7 | §6 | **R6.1** | `SELECTED` | T13 §10, §20-22 |
| **D6** | D | Re-issue Terminal B/C/D/E prompts (BL-24)? | **Yes** — prompts exist in campaign §13 | Defer | §15–§18 packets | Release | `SELECTED` | T13 §10, §20-23 |

---

## 4. Group A — Architecture decisions (A1–A4)

> All four Group A decisions are `SELECTED`; none is approved, independently verified or gate-accepted.

### A1 — Adopt §§8–15 as the frozen architecture

**Decision question:** Adopt §§8–15 as the frozen architecture?
**Existing recommendation:** **Yes** (T13 §7).
**Option A:** Adopt §§8–15 as the frozen architecture. *Consequence:* the freeze package proceeds on the current §8–§15 text.
**Option B:** Return D14/D19-Tier-2 for re-scope. *Consequence:* re-scope re-opens §§11 and §14 and restarts the freeze package.
**Additional options:** none documented.
**Dependencies:** Group B record.
**Gate impact:** R6.0.
**Evidence status:** options are proposals recorded in T13; no option is verified as correct and none is adopted.
**Owner response:** A1: Option A — Adopt §§8–15 as the frozen architecture.
**Approval record:** `NOT APPROVED`

### A2 — Tier-1 metering fixes as integrity work

**Decision question:** Treat Tier-1 metering fixes as integrity work, not optional feature work?
**Existing recommendation:** **Yes** — BL-01…BL-04/A6/BL-06/BL-07 close live holes (T13 §7).
**Option A:** Treat them as integrity work. *Consequence:* the confirmed defects are fixed as mandatory correctness work.
**Option B:** Defer post-v1. *Consequence:* deferring ships documented under-billing plus a quota leak in v1 accounting (T13 §7 note: quota under-charge on mixed usage, budget settlement at a partial sum, pre-execution denials misreported as 503 quota outages).
**Additional options:** none documented.
**Dependencies:** — (none recorded).
**Gate impact:** R6.0.
**Evidence status:** T13 states plainly that A2 is the highest-consequence item in Group A. Verified defects are source-inspected (§13); the *decision* is unresolved.
**Owner response:** A2: Option A — Treat Tier-1 metering fixes as integrity work.
**Approval record:** `NOT APPROVED`

### A3 — Adopt ADR-1 (Telemetry)

**Decision question:** Adopt ADR-1: Option A conditional, explicitly not implemented?
**Existing recommendation:** **Yes** (honest freeze) (T13 §7).
**Option A:** Adopt ADR-1 Option A — conditional and **explicitly not implemented**. *Consequence:* freezes a telemetry *target shape* and its tripwires while labelling the live system as interim. Adopting implements nothing.
**Option B:** Redefine the target as inline-hardened. *Consequence:* contradicts T8 D14's direction and **requires a new ADR**; it also ratifies the inline fail-closed shape T10 rejected.
**Additional options:** none documented.
**Dependencies:** T13 §11 brief.
**Gate impact:** R6.0 (condition 1, §19.1).
**Evidence status:**
- *Verified:* at `319a711` there is no `sabiroute_optimization_records` table, builder, projection or writer; inline synchronous fail-closed telemetry is the live behaviour (T13 §11.1–§11.2; T14 AF-16).
- *Proposed:* ADR-1 itself is `PROPOSED`, not adopted.
- *Unresolved:* prerequisites **P1–P5** are all currently unmet (§11.3). If P1 slips, Option A "reverts to conditional-with-no-schedule and must be recorded as such — not silently dropped" (§11.4).
**ADR-1 reference:** full brief at **T13 §11** (proposed target §11.1, interim behaviour §11.2, prerequisites §11.3, owner ask §11.4). T16 neither rewrites nor adopts ADR-1.
**Owner response:** A3: ADOPT Option A — ADR-1 conditional, explicitly not implemented.  
Acknowledge that P1–P5 remain unmet and that this selection authorises no implementation.
**Source provenance:** `MISSION-FRAMED` and source-limited; the direct owner utterance is unavailable and this record must not be treated as `EXACT OWNER`.
**Approval record:** `NOT APPROVED`

### A4 — Adopt T10-1…T10-7 scoping

**Decision question:** Adopt T10-1…T10-7 scoping?
**Existing recommendation:** **Yes** (T13 §7).
**Option A:** Adopt the T10-1…T10-7 scoping. *Consequence:* adapter work proceeds under the guardrail set.
**Option B:** Proceed without coupling/tokenizer/null/capability/governor guardrails. *Consequence:* adapter work proceeds without the guardrail set; increases later rework.
**Additional options:** none documented.
**Dependencies:** — (none recorded).
**Gate impact:** R6.0.
**Evidence status:** proposals per T13; unresolved.
**Owner response:** A4: Option A — Adopt the T10-1…T10-7 scoping.
**Approval record:** `NOT APPROVED`

---

## 5. Group B — Accounting and settlement decisions (B1–B9)

> **B1 blocks R6.0 and R6.1; B1–B8 block R6.1; B9 blocks Release** (T13 §8). All nine are `SELECTED`; none is approved, independently verified or gate-accepted.

### B1 — Adopt ADR-2 (R6.1 Foundation Contract)

**Decision question:** Adopt ADR-2: T11 §8 I1–I9 as the draft R6.1 foundation contract?
**Existing recommendation:** **Yes**, with C-1 name resolution (T13 §8).
**Option A:** Adopt ADR-2 with the `ADR-2/C-1` name resolution. *Consequence:* fixes the package, file list, U4 unit and Track A surface; **narrows** R6.1 — excludes `api/chat.py`, registries, provider adapters and all telemetry writes (§12.4); authorises no code.
**Option B:** Require an external R6.1 design document first. *Consequence:* **delay; second authorship of the same contract** (§8).
**Additional options:** none documented.
**Dependencies:** T13 §12 brief; `ADR-2/C-1` must be recorded (see §7).
**Gate impact:** **R6.0 and R6.1** (R6.0 condition 2, §19.1).
**Evidence status:**
- *Proposed:* ADR-2 is `PROPOSED`, not adopted; adopting authorises no code.
- *Verified:* no `request_transform` package exists in `src/` at `319a711`; loop entry is `completions.py:1345` (T13 §12.1).
- *Unresolved:* I2's 250 ms / 2× byte budget is unspecified; I5's configuration schema is described, not written (§12.3). Both are named so they are not mistaken for settled.
**ADR-2 reference:** full brief at **T13 §12** (proposed foundation §12.1, naming conflict §12.2, unresolved items §12.3, conflicts §12.4).
**⚠ Precondition:** B1 should **not** be answered independently of `ADR-2/C-1` name resolution. The recommendation couples adoption to one of ADR-2's own unresolved conflicts (T14 AF-15). See §7.
**Owner response:** B1: Option A — adopt ADR-2 (T11 §8, I1–I9) as the draft R6.1 foundation contract, with the package-name conflict resolved to `src/sabiroute/request_transform/`.

C-02: Reading B — Group A plus all of Group B (B1–B9) must be recorded before BL-22 is signed.

"This adopts the draft contract; it does not authorise implementation."
"I2's latency/byte budget and I5's configuration schema remain unresolved design requirements and must be closed before R6.1 implementation."
"This decision does not grant G7 or Track A authorisation."

**C-1 package resolution:** the `ADR-2/C-1` versus `GROUP-C/C1` identifier conflict is resolved to the package `src/sabiroute/request_transform/`. This is a package-boundary resolution only; it does not settle the separate identifier-collision question raised at T16 §7.
**Approval record:** `NOT APPROVED`

### B2 — Restrict R6.1 scope to `/v1/chat/completions`

**Decision question:** Restrict R6.1 scope to `/v1/chat/completions`, excluding `api/chat.py`?
**Existing recommendation:** **Yes** (T13 §8).
**Option A:** Restrict scope as stated. *Consequence:* the SabiChat path stays outside R6.1.
**Option B:** Include the SabiChat path. *Consequence:* a second admission and store surface enters R6.1; scope widens materially.
**Additional options:** none documented.
**Dependencies:** — (none recorded).
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved.
**Owner response:** B2: Option A — Restrict R6.1 scope to `/v1/chat/completions`, excluding `api/chat.py`.
**Approval record:** `NOT APPROVED`

### B3 — Bypass authority: operator-only, per-route, default-off

**Decision question:** Bypass authority: operator-only, per-route, default-off?
**Existing recommendation:** **Yes** (T13 §8).
**Option A:** Operator-only, per-route, default-off. *Consequence:* bypass authority is an operator surface with a per-route switch off by default.
**Option B:** Trusted-service signal. *Consequence:* requires provenance machinery comparable to `sabichat_service_key_id`.
**Additional options:** none documented.
**Dependencies:** T4 flag.
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved.
**Owner response:** B3: Option A — Operator-only, per-route, default-off.
**Approval record:** `NOT APPROVED`

### B4 — Phase-13 keep-out

**Decision question:** Phase-13 keep-out: R6.1 emits no snapshot fields?
**Existing recommendation:** **Yes** (T13 §8).
**Option A:** R6.1 emits no snapshot fields. *Consequence:* Phase-13 work stays outside R6.1.
**Option B:** Amend to schema-1.2 now. *Consequence:* pulls Phase-13 coordination inside R6.1.
**Additional options:** none documented.
**Dependencies:** — (none recorded).
**Gate impact:** **R6.1** (R6.0 if deferred).
**Evidence status:** proposal per T13; unresolved.
**Owner response:** B4: Option A — R6.1 emits no snapshot fields.
**Approval record:** `NOT APPROVED`

### B5 — Settlement basis (with C-07 annotation)

**Decision question:** Settlement basis: unknown wins at the full original estimate, never a partial sum?
**Existing recommendation:** **Yes** — this is T12 §12's contract (T13 §8).
**Option A:** Unknown usage wins at the **full original estimate**, never a partial sum. *Consequence:* the reservation continues to bound the request when provider usage is unknown.
**Option B:** Partial-sum settlement. *Consequence:* **partial-sum settlement *is* the confirmed defect; choosing it ratifies the bug** (T13 §8).
**Additional options:** none documented.
**Dependencies:** `C-07` (both governors).
**Gate impact:** R6.1. B5 is the gating decision for U1 — U1 cannot be written without a decided settlement contract (T13 §8).
**Evidence status:** proposal per T13; unresolved. **Not implemented.**

**⚠ C-07 annotation — required by T15 §5.** C-07 establishes that the *current* budget and quota settlement paths **can disagree on the same response**:
- The **budget** governor honours the unknown-usage flag (`completions.py:1944–1955`, `:1961–1972`; `_actual_cost` returns `None` at `:1997–1998`).
- The **quota** governor does **not**: `finish()` has no `usage_unknown` parameter (`:542–550`), so the quota block recomputes `quota_total` from raw parts at `:603` and never receives the flag.

Therefore, **B5's future acceptance contract must explicitly cover both budget settlement and quota settlement.** A settlement fix is not complete when one governor is repaired. This register does **not** narrow the settlement scope to the budget governor alone, and does **not** claim the proposed contract has been implemented — it has not.
**Owner response:** B5: Option A — Unknown usage wins at the full original estimate, never a partial sum, for both budget and quota settlement.
**Approval record:** `NOT APPROVED`

### B6 — Monotone-shrink permanent unless re-baselined

**Decision question:** Monotone-shrink **permanent** unless the reservation is re-baselined?
**Existing recommendation:** **Yes** (T13 §8).
**Option A:** Monotone-shrink permanent unless the reservation is re-baselined. *Consequence:* the reservation keeps bounding the request across any change.
**Option B:** Allow expansion. *Consequence:* expansion breaks reservation authority — the reservation would no longer bound the request.
**Additional options:** none documented.
**Dependencies:** — (none recorded).
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved. **B6 is one of the two rulings T11 §18 omitted** (X-4); it is load-bearing for ADR-2 and cannot be left implicit.
**Owner response:** Q4: APPROVE Option A — B6 monotone-shrink permanent unless the reservation is explicitly re-baselined.

All seven boundary conditions, preserved:

1. The original reservation estimate remains the authoritative upper bound on the effective request throughout transformation and optimisation.
2. Any transformation that would increase the effective request beyond the reserved bound must be rejected unless an explicit, auditable re-baselining operation has occurred.
3. Re-baselining must not be implicit, silent, or performed merely because a later transformation produces a larger estimate.
4. Re-baselining must have its own defined authority, accounting semantics, failure behaviour, and evidence requirements. This decision does not design or implement that mechanism.
5. B6 remains independent of B7. Do not combine their decisions.
6. Preserve the existing B5 settlement requirements. B6 does not weaken unknown-usage handling or settlement integrity for either budget or quota.
7. This is an in-session owner decision only, subject to durable recording and R6.0 governance.

Also stated: the decision does not authorise implementation, schema changes, migrations, benchmark execution, provider calls, G7, Track A, BL-22, or R6.1–R6.7 execution.
**Approval record:** `NOT APPROVED`

### B7 — Per-attempt re-derivation forbidden

**Decision question:** Per-attempt re-derivation of the effective request forbidden?
**Existing recommendation:** **Yes** — forbid (T13 §8).
**Option A:** Forbid per-attempt re-derivation. *Consequence:* the effective request keeps a stable identity across retries.
**Option B:** Allow re-derivation. *Consequence:* breaks D12 and reservation identity across retries; without B7 the effective request changes identity between attempts, which invalidates every settlement argument in T12 §12.
**Additional options:** none documented.
**Dependencies:** — (none recorded).
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved. **B7 is the second ruling T11 §18 omitted** (X-4). B6 and B7 are independent decisions and are **not** to be combined.
**Owner response:** B7: Option A — Forbid per-attempt re-derivation.
**Approval record:** `NOT APPROVED`

### B8 — Budget terminal-marker pattern

**Decision question:** Adopt the budget terminal-marker pattern (BL-15) transferred from `_QUOTA_RESERVATIONS`?
**Existing recommendation:** **Yes** (T13 §8).
**Option A:** Adopt the transferred marker pattern. *Consequence:* reuses a solved state machine.
**Option B:** Design a new state machine. *Consequence:* an unnecessary second state machine for an already-solved problem.
**Additional options:** none documented.
**Dependencies:** — (none recorded).
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved.
**Owner response:** B8: Option A — Adopt the transferred marker pattern.
**Approval record:** `NOT APPROVED`

### B9 — Reconciler placement

**Decision question:** Reconciler placement: R6.7, with the marker migration in R6.1?
**Existing recommendation:** **Yes** (T13 §8).
**Option A:** Reconciler in R6.7, marker migration in R6.1. *Consequence:* R6.1 stays bounded.
**Option B:** Pull the reconciler into R6.1. *Consequence:* materially widens R6.1 scope.
**Additional options:** none documented.
**Dependencies:** U9.
**Gate impact:** **Release** (not R6.0/R6.1).
**Evidence status:** proposal per T13; unresolved.
**Owner response:** B9: Option A — Reconciler in R6.7, marker migration in R6.1.
**Approval record:** `NOT APPROVED`

---

## 6. Group C and Group D

### 6.1 Group C — Capability recovery and eligibility (C1–C4)

> Group C **informs; it does not gate R6.0** (T13 §9). All four are answered: **C1 is `DEFERRED`** by direct owner disposition, and **C2, C3 and C4 are `SELECTED`**. None is approved, independently verified or gate-accepted. **No alias promotion follows from any C decision** — the ladder remains `UNKNOWN → UNCALIBRATED → BOUNDED → CALIBRATED`.

#### C1 — Byok/paid semantics and billing-source scope

**Decision question:** Resolve byok/paid semantics and billing-source scope (BL-30)?
**Existing recommendation:** **"Owner conversation before any BOUNDED+ claim"** (T13 §9, recommendation column).
**Options:** **NONE DOCUMENTED.** T13 records the alternatives column as "—". C1 is an **open conversation, not a binary choice**, and **no option is invented here**. *(See §12.1 for the source discrepancy on this field.)*
**Additional options:** none.
**Dependencies:** — (none recorded).
**Gate impact:** Release claims.
**Evidence status:** *Unresolved.* T13's technical consequence: any BOUNDED+ claim made first would rest on undefined billing semantics.
**Owner response:** C1: **DEFER** — the owner defers resolution of byok/paid semantics and billing-source scope (BL-30). This is a direct owner defer disposition, not a selection among options: **no option label is assigned**, and no claim is made that T13 supplied alternatives for C1 (T13 records the alternatives column as "—"; see §12.1). The decision remains unresolved, no BOUNDED+ claim is authorised, and the deferral is not an approval of any billing semantics.
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

#### C2 — Non-Latin BM25 relevance claims

**Decision question:** Exclude non-Latin BM25 relevance claims until Terminal D establishes a corpus?
**Existing recommendation:** **Yes** (T13 §9).
**Option A:** Exclude until Terminal D establishes a corpus. *Consequence:* claims stay within evidence.
**Option B:** Claim multilingual now. *Consequence:* unevidenced multilingual claim; not defensible against review.
**Dependencies:** Terminal D.
**Gate impact:** Release (G4).
**Evidence status:** proposal per T13; unresolved.
**Owner response:** C2: Option A — Exclude non-Latin BM25 relevance claims until Terminal D establishes a corpus.
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

#### C3 — System/developer-role traffic gate

**Decision question:** Gate system/developer-role traffic until role-freeze behaviour is proven (BL-09)?
**Existing recommendation:** **Gated** until role-freeze proven (T13 §9).
**Option A:** Gated until role-freeze proven. *Consequence:* privileged-role traffic stays gated pending proof.
**Option B:** FULL now. *Consequence:* byte-identity unproven for privileged roles.
**Dependencies:** U5.
**Gate impact:** Partial R6.1.
**Evidence status:** proposal per T13; unresolved.
**Owner response:** C3: Option A — Gated until role-freeze proven. System/developer-role traffic stays gated pending proof of role-freeze behaviour (BL-09).
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

#### C4 — Extend the capability probe

**Decision question:** Extend the proven 2026-10-08 capability probe to `tool_use` and `structured_output` (BL-10)?
**Existing recommendation:** **Yes** — repeat a known procedure (T13 §9).
**Option A:** Repeat the established procedure on the two additional capability keys. *Consequence:* cheap, because three aliases already carry dated 2026-10-08 evidence for `chat` and one for `chat`+`streaming` (T13 §9 note).
**Option B:** Commission new methodology. *Consequence:* new methodology is a research project; the established procedure already exists.
**Dependencies:** §4.5 evidence.
**Gate impact:** Release.
**Evidence status:** proposal per T13; unresolved.
**Owner response:** C4: Option A — Repeat the established procedure on the two additional capability keys (`tool_use` and `structured_output`), extending the proven 2026-10-08 capability probe (BL-10).
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

### 6.2 Group D — Implementation authorisation (D1–D6)

> D1, D2, D3 and D5 block R6.1 (T13 §10). All six are `SELECTED`; none is approved, independently verified or gate-accepted. **No U0, U1 or R6.1 execution is authorised by this extraction.** Recording D2 and D3 grants no G7; recording D4 contacts no Track A reviewer; recording D6 issues no Terminal B/C/D/E prompt.

#### D1 — U0 merge policy

**Decision question:** U0 merge policy: strict-xfail, land-with-U1, or skip?
**Existing recommendation:** **Strict xfail** (T13 §10).
**Option A:** Strict xfail. *Consequence:* defects are recorded as failing tests under `xfail(strict=True)` and proven independently.
**Option B:** Land with U1. *Consequence:* loses independent proof and violates "tests first".
**Additional option:** **Skip.** *Consequence:* proves nothing.
**Dependencies:** §14 spec.
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved.
**Owner response:** D1: Option A — Strict xfail. Defects are recorded as failing tests under `xfail(strict=True)` and proven independently.
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

#### D2 — Authorise U0 separately

**Decision question:** Authorise U0 **separately** under G7, ahead of U1–U12?
**Existing recommendation:** **Yes** — test-only and reversible (T13 §10).
**Option A:** Authorise U0 separately under G7, ahead of U1–U12. *Consequence:* test-only, reversible; captures the cheapest risk reduction early.
**Option B:** Bundle with U1. *Consequence:* bundling forfeits the cheapest risk-reduction available.
**Dependencies:** D1, D3.
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved. D2 must be distinguished from bundling: separate authorisation is the recommendation; bundling is the alternative.
**Owner response:** D2: Option A — Authorise U0 **separately** under G7, ahead of U1–U12. Recording this selection grants no G7 and authorises no U0 execution; it records the owner's chosen authorisation policy only.
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

#### D3 — Define G7 scope (composite — three separately answerable components)

**Decision question:** Define G7 scope as U0–U11, explicitly naming `tests/`, with U12 in R6.7?
**Existing recommendation:** **Yes** (T13 §10).
**Option A:** Define G7 scope as U0–U11, explicitly naming `tests/`, with U12 in R6.7. *Consequence:* R6.7 stays out of the earlier scope.
**Option B:** Include U12. *Consequence:* pulls R6.7 forward into R6.1.
**Additional options:** none documented beyond the composite components below.

**⚠ T14 C-03 — the three components are separately answerable.** D3 bundles three distinct choices and an owner may **accept one and reject another**:
- **(i)** G7 scope = **U0–U11**.
- **(ii)** G7 scope text **explicitly names `tests/`**.
- **(iii)** **U12 placement in R6.7** rather than in the earlier scope.

These are **explanatory sub-choices under D3**, not three canonical decisions. The canonical count is unchanged at 23. T13 §10 states that G7's scope must name `tests/` in words because U0 appears in no Track A row — without that text U0 has no authorisation basis at all. D2 reads its scope from D3.
**Dependencies:** — (none recorded).
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved. Component separation is a T14 correction (C-03), integrated.
**Owner response:** D3: Option A — Define G7 scope as U0–U11, explicitly naming `tests/`, with U12 in R6.7. The owner answered the composite affirmatively, so components **(i)** G7 scope = U0–U11, **(ii)** G7 scope text explicitly names `tests/`, and **(iii)** U12 placement in R6.7 are recorded as accepted together. The owner did not disaggregate the components and this record invents no partial acceptance. Recording this selection grants no G7.
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

#### D4 — Track A engagement to schedule

**Decision question:** Authorise Track A engagement to schedule (BL-21) once T-numbering converges?
**Existing recommendation:** **Yes** (T13 §10).
**Option A:** Authorise once T-numbering converges. *Consequence:* Track A surface can start after numbering is fixed.
**Option B:** Defer. *Consequence:* blocks all Track A surface; nothing touching protected files can start.
**Dependencies:** D5.
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved. D4 depends on D5 (T-numbering convergence) — see X-3.
**Owner response:** D4: Option A — Authorise Track A engagement to schedule (BL-21) once T-numbering converges. Recording this selection contacts no Track A reviewer and issues no engagement.
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

#### D5 — Adopt T1–T8 numbering

**Decision question:** Adopt T11 §15's T1–T8 numbering as canonical?
**Existing recommendation:** **Yes** (T13 §10).
**Option A:** Adopt T11 §15's T1–T8. *Consequence:* numbering converges; `T7` is unambiguous.
**Option B:** Use campaign §15's T1–T7. *Consequence:* ambiguous `T7`; reviewer may sign the wrong artefact (X-3).
**Dependencies:** §6.
**Gate impact:** R6.1.
**Evidence status:** proposal per T13; unresolved. X-3 documents that Track A numbering does not converge across three documents.
**Owner response:** D5: Option A — Adopt T11 §15's T1–T8 numbering as canonical. Numbering converges and `T7` becomes unambiguous.
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

#### D6 — Re-issue Terminal prompts

**Decision question:** Re-issue Terminal B/C/D/E prompts (BL-24)?
**Existing recommendation:** **Yes** — prompts exist in campaign §13 (T13 §10).
**Option A:** Re-issue the prompts. *Consequence:* G4/G5 proceed.
**Option B:** Defer. *Consequence:* G4/G5 remain blocked.
**Dependencies:** §15–§18 packets.
**Gate impact:** Release.
**Evidence status:** proposal per T13; unresolved. Packets are drafted (§15–§18) but none is issued.
**Owner response:** D6: Option A — Re-issue the Terminal B/C/D/E prompts (BL-24). Recording this selection issues no prompt; the packets remain drafted and unissued.
**Source provenance:** `EXACT OWNER` — explicit owner instruction, 2026-11-06 (T16 Group C/D owner decision transfer).
**Approval record:** `NOT APPROVED`

---

## 7. Identifier collision — `ADR-2/C-1` versus `GROUP-C/C1`

**This section exists because the two registers are one keystroke apart and B1's recommendation contains a bare "C-1".**

T13 contains **two distinct identifier systems**:

| Register | Symbols | Meaning |
|---|---|---|
| **ADR-2 internal conflicts** (T13 §12.4) | `C-1`, `C-2`, `C-3` (hyphenated) | `C-1` = the ADR-2 **package-name conflict** (`request_transform/` vs `compression/`). `C-2` = insertion point. `C-3` = statuses. |
| **Group C owner decisions** (T13 §9) | `C1`, `C2`, `C3`, `C4` (unhyphenated) | `C1` = byok/paid billing semantics and billing-source scope. |

**The collision in one line:** B1's recommendation says "**with C-1 name resolution**". That is **`ADR-2/C-1`** — package naming. It is **not** `GROUP-C/C1` (byok/paid billing semantics), which has nothing to do with package naming.

**Rules applied in this register:**
1. Every original identifier is preserved; neither register is renamed.
2. In **cross-references and explanatory prose**, the ADR-2 conflicts are written `ADR-2/C-1`, `ADR-2/C-2`, `ADR-2/C-3`.
3. In **explanatory cross-references**, the Group C decisions are written `GROUP-C/C1`, `GROUP-C/C2`, etc.
4. In the **actual decision register** (index, cards, response sheet), the canonical IDs remain exactly `C1`–`C4` and the ADR-2 conflicts are never given a decision ID.
5. **No new decision ID is created** for the naming conflict.

**Owner-session instruction:** when answering B1, write the *name*, not the label — e.g. "`ADR-2/C-1` — package-name conflict resolved to `request_transform/`", never a bare "C-1".

---

## 8. Governance interpretation — C-02

**This is not a 24th decision card.** C-02 is a governance interpretation governing the scope of T13 §19.1 condition 3 and must remain separate from the 23 canonical cards.

**Owner-selected interpretation:** **Reading B — 13 total / 10 outstanding at the prior reconciliation state.**

The historical baseline is **13 total / 10 outstanding at the prior reconciliation state**. Reading B means Group A plus all of Group B (A1–A4 and B1–B9) must be recorded before BL-22 is signed. The register enumerates 4 Group A cards and 9 Group B cards, for 13 total; the current status is **13 selected / 0 outstanding** and all 13 selections are recorded in T16.

This interpretation does not approve, register, independently verify or gate-accept any decision. It does not convert C-02 into a decision card.

---

## 9. Proposed decision session order

**This is a recommendation inherited from T13 §20's "Recommended session order", adjusted only where T14/T15 corrections require it. It is not a decision and it does not preselect any option.**

T13 §20 recommends: **A3 and B1 first** (the two ADRs; both gate the signature) → A1, A2, A4 → B2–B9 → C → D. It notes **D1 and D3 can be settled independently at any point** and unblock U0 without touching the architecture questions.

| Stage | Decisions | Gate served | Answerable now? |
|---|---|---|---|
| **0. Preconditions** | `C-02` recording/propagation (not a decision) and `ADR-2/C-1` registration | Unblocks B1 and BL-22 meaning | Must precede B1 and the signature |
| **1. ADRs** | **A3** | R6.0 condition 1 | Yes — independent of B1 |
| | **B1** | R6.0 condition 2 | **Only after `ADR-2/C-1`** (or owner states C-1 is folded in) |
| **2. Remaining Group A** | A1, A2, A4 | R6.0 | A1 depends on Group B record; A2, A4 answerable now |
| **3. Settlement contract** | **B5** (must name both budget and quota governors) → B6, B7 → B2, B3, B4, B8, B9 | R6.1 | Yes, after B1 |
| **4. Signature** | BL-22 (not a decision) | R6.0 | Only after Group A + B1 recorded and `C-02` settled |
| **5. U0 readiness** | D1, D3 (then D2) | R6.1 | Yes — independent of every architecture question |
| **6. Remaining D, then C** | D4, D5, D6 → C1–C4 | R6.1 / Release | D4 needs D5; C1 deferred by owner (2026-11-06) |

**Gate grouping (so the owner can see what each stage buys):**

| Category | Decisions |
|---|---|
| **Needed for R6.0** | A3, B1 (conditions 1–2); then Group A + B1 recorded, then BL-22 |
| **Needed for R6.1** | B1–B8 (B9 is Release); D1, D2, D3, D5 (and D4 after D5) |
| **Needed for Release** | B9, D6 |
| **Inform claims, do not gate R6.0** | C1, C2, C3, C4 |
| **Separately authorise implementation** | D2 (U0 under G7); D3 defines G7 scope; BL-22 is the signature act, not an implementation authorisation |

**What cannot be bundled:** A3 and B1 are separate decisions. B6 and B7 are separate. Do not present all 23 as one approval. B1 is not answerable independently of `ADR-2/C-1`.

---

## 10. Governance status and authority boundary

| Statement | Status | Basis |
|---|---|---|
| ADR-1 | **PROPOSED** — not adopted | T13 §11; T12 bucket 4; T14 §9 |
| ADR-2 | **PROPOSED** — not adopted | T13 §12; T12 bucket 4; T14 §9 |
| R6.0 architecture freeze | **CONDITIONALLY READY** — not fully frozen | T13 §19; §19.2 |
| R6.1 overall | **NOT READY** | T13 §19; nine conditions from T11 §6 stand |
| U0 | **READY FOR SEPARATE OWNER AUTHORIZATION** | T13 §19; conditions reduced to two by §14.6 |
| U1 | **NOT READY** | T13 §19 |
| G7 | **NOT GRANTED** | T13 §19 — never requested |
| Track A | **NOT OBTAINED** | T13 §19 — no reviewer contacted |
| Terminal B/C/D/E | **NOT OBTAINED** — packets drafted (§15–§18), none issued | T13 §19 |

**Rules restated:** every decision starts `OUTSTANDING`. No recommendation is an approval. No source verification is an approval. No successful test is an approval. No absence of objection is an approval. A prepared decision is not a taken decision (T13 §19.2).

---

## 11. Owner decision response template

**Current canonical response sheet.** All 23 owner selections are recorded: A1–A4, B1–B9, C1–C4 and D1–D6. Every approval record remains `NOT APPROVED`; no owner-response field remains `PENDING`.

| Decision ID | Owner selection | Conditions / notes | Approval status |
|---|---|---|---|
| **A1** | A1: Option A — Adopt §§8–15 as the frozen architecture. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED` | NOT APPROVED |
| **A2** | A2: Option A — Treat Tier-1 metering fixes as integrity work. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED` | NOT APPROVED |
| **A3** | A3: ADOPT Option A — ADR-1 conditional, explicitly not implemented. | `MISSION-FRAMED`; P1–P5 unmet; source-limited | NOT APPROVED |
| **A4** | A4: Option A — Adopt the T10-1…T10-7 scoping. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED` | NOT APPROVED |
| **B1** | B1: Option A — adopt ADR-2 with `src/sabiroute/request_transform/`. | C-02 Reading B; I2 and I5 unresolved; no implementation authority | NOT APPROVED |
| **B2** | B2: Option A — Restrict R6.1 scope to `/v1/chat/completions`, excluding `api/chat.py`. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED` | NOT APPROVED |
| **B3** | B3: Option A — Operator-only, per-route, default-off. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED` | NOT APPROVED |
| **B4** | B4: Option A — R6.1 emits no snapshot fields. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED` | NOT APPROVED |
| **B5** | B5: Option A — Unknown usage wins at the full original estimate, never a partial sum, for both budget and quota settlement. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED`; must cover both governors — see §5 C-07 | NOT APPROVED |
| **B6** | Q4: APPROVE Option A — monotone-shrink permanent unless explicitly re-baselined. | Separate from B7; preserves B5 budget/quota requirements; no implementation authority | NOT APPROVED |
| **B7** | B7: Option A — Forbid per-attempt re-derivation. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED`; separate from B6 | NOT APPROVED |
| **B8** | B8: Option A — Adopt the transferred marker pattern. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED` | NOT APPROVED |
| **B9** | B9: Option A — Reconciler in R6.7, marker migration in R6.1. | `CONVERSATION-DERIVED OWNER DECISION — SOURCE LIMITED` | NOT APPROVED |
| **C1** | C1: **DEFER** — owner defers byok/paid semantics and billing-source scope (BL-30). | `EXACT OWNER`; direct defer disposition, no option label assigned; no BOUNDED+ claim authorised | NOT APPROVED |
| **C2** | C2: Option A — Exclude non-Latin BM25 relevance claims until Terminal D establishes a corpus. | `EXACT OWNER` | NOT APPROVED |
| **C3** | C3: Option A — Gated until role-freeze proven. | `EXACT OWNER` | NOT APPROVED |
| **C4** | C4: Option A — Repeat the established procedure on `tool_use` and `structured_output`. | `EXACT OWNER` | NOT APPROVED |
| **D1** | D1: Option A — Strict xfail. | `EXACT OWNER` | NOT APPROVED |
| **D2** | D2: Option A — Authorise U0 separately under G7, ahead of U1–U12. | `EXACT OWNER`; grants no G7, authorises no U0 execution | NOT APPROVED |
| **D3** | D3: Option A — G7 scope U0–U11, naming `tests/`, U12 in R6.7. | `EXACT OWNER`; components (i)/(ii)/(iii) accepted together; grants no G7 | NOT APPROVED |
| **D4** | D4: Option A — Authorise Track A engagement to schedule once T-numbering converges. | `EXACT OWNER`; contacts no Track A reviewer | NOT APPROVED |
| **D5** | D5: Option A — Adopt T11 §15's T1–T8 numbering as canonical. | `EXACT OWNER` | NOT APPROVED |
| **D6** | D6: Option A — Re-issue the Terminal B/C/D/E prompts. | `EXACT OWNER`; issues no prompt | NOT APPROVED |

**Non-decision items to record separately (not in the count above):**
- **`ADR-2/C-1`** — package-name conflict; must be recorded (or explicitly folded into B1 by the owner).
- **`C-02` interpretation** — Reading B; historical baseline 13 total / 10 outstanding at the prior reconciliation state; current status 13 selected / 0 outstanding; recorded separately from the canonical cards.
- **BL-22** — the signature act (T13 §20 item 24), after Group A + B1 are recorded.
- **CLAUDE.md §12** — documentation correction (T13 §20 item 25), separately authorised.

---

## 12. Extraction integrity — discrepancies and limits

**Everything below is reported, not resolved.** No conflict was repaired by guessing.

1. **C1's recommendation field (source discrepancy).** T13 §9's table records C1's recommendation as **"Owner conversation before any BOUNDED+ claim"** and its alternatives as "—". T14 C-03 and T15 §1 characterise C1 as having recommendation **and** alternatives both "—". T16 follows the **T13 table** as the authority (as the mission requires) and records the recommendation verbatim, while treating C1 as an **open conversation with no documented options** — which is the substance T14/T15 intended. No option was invented. The owner subsequently **deferred** C1 on 2026-11-06; that defer is recorded in §6.1 as a direct owner disposition, still without inventing an option label.
2. **`C-1` / `C1` collision.** Live and material; handled in §7 without renaming either register.
3. **C-02 scope interpretation.** Reading B is owner-selected; its 13-total/10-outstanding arithmetic and non-card recording are now stated in §8.
4. **B5 scope.** C-07 requires the settlement contract to name **both** governors; recorded in §5. Not implemented.
5. **D3 composite.** Three sub-choices separated under D3; canonical count unchanged.
6. **B6/B7.** Present as independent decisions (the two rulings T11 §18 omitted).
7. **Excluded items.** BL-22, CLAUDE.md §12, `ADR-2/C-1…C-3`, and D3's sub-choices are represented without inflating the canonical 23.
8. **Statuses.** Re-verified against T13 §19 and the ADR briefs' `PROPOSED` headings at `319a711`; not copied blindly from a summary.
9. **No runtime proof.** This register records no executed test and claims no runtime behaviour beyond what T13/T14/T15 already label `VERIFIED` by source read or `STATIC-ANALYSIS FINDING`.

---

## 13. Final status

**T16 CANONICAL REGISTER — 23 DECISION CARDS PRESERVED; ALL 23 DECISIONS ARE IN SCOPE; ALL 23 OWNER SELECTIONS ARE SUPPLIED AND CANONICALLY RECORDED (A1–A4, B1–B9, C1–C4 AND D1–D6), WITH C1 RECORDED AS A DIRECT OWNER DEFER DISPOSITION; 0 REMAIN OUTSTANDING; 0 APPROVED; 0 REGISTRATIONS; 0 INDEPENDENT VERIFICATIONS; NO GATE ACCEPTED; R6.0 OPEN; BL-22 UNSIGNED; G7 NOT GRANTED; R6.1 IMPLEMENTATION NOT AUTHORISED; T13/T14/T15 UNMODIFIED.**

*This section approves nothing. An extracted option is not a chosen option, and a recommendation is not a decision.*

**SabiRoute decides. LiteLLM executes. Evidence guides the path.**
