# OPEN-POINTS DISPOSITION — 2026-11-17

**Purpose:** settle every point that can be settled from the tree and the four owner rows, and name
exactly what still requires a new owner act. No commit authority beyond Row C is assumed.

---

## 1. Settled by owner rows

| Point | Disposition | Evidence |
|---|---|---|
| WP-5 owner closure | **OWNER ACCEPTED** | Row A; contract §10 |
| R6.1 exit criterion 4 | **MET by owner override** | Row B; contract §6 and §10 |
| Reviewer’s “do not accept” | **Explicitly overridden**, not erased | Row B; `R6.1-REVIEW-RECORD.md` §5 stands as history |
| Defects 12 and 13 | **Fixed** with falsifiable tests | Contract §9A; commit `ac859fd` |
| Defect 14 | **Re-derived 13/13 OK** `[M]` | Contract §9A; manifest recheck |
| Defect 15 | **Accepted as unauthenticated** | Row B; no provenance claim |
| 91 Track A lines | **Ratified** | Row B; contract §9 and `validation.py` |
| One scoped R6.1 commit | **DONE** | Row C; `ac859fd`, 14 paths |
| R6.2–R6.5 authority | **GRANTED** | Row D; `R6.2-CONTRACT.md` |
| R6.6/R6.7 specification | **DONE, execution not authorised** | `R6.6-VALIDATION-SPEC.md`, `R6.7-ROLLOUT-DESIGN.md` |
| R7 offline items | **WRITTEN, not run/pushed** | `R7-OFFLINE-REPORT.md` |

---

## 2. Recorded and deliberately not changed

| Point | State | Why |
|---|---|---|
| R8 | **BLOCKED** | D5 and scorecard; Row D does not accept it |
| Dashboard “6 verdicts ACCEPTED” | **Conflict recorded, not edited** | D5 says record the conflict; no source document supports the badge |
| F-02 | **accepted-unproven, not resolved** | Row A; real genesis hash needs the permanently gated ledger |
| Registration ledger | **Never instantiate** | authorisation row 8; no row overrides it |
| T1/T8 verdict | **Not issued** | owner ruled it must be a fresh session, not the executioner |
| `training_authorized` | **false** | no authorisation to change it |
| U3 trusted-checkpoint anchoring | **UNRESOLVED by design** | satisfaction deferred; specification exists, implementation unauthorised |
| `VER:v1` token question | **OPEN / correction DEFERRED** | recorded owner disposition; no new ruling in Rows A–D |
| F-10/F-11 absence | **not established** | absence searches were inconclusive; not converted to a fact |
| Push | **NONE** | D7 and every later row withhold it |

---

## 3. Needs a new named row

| Point | Why it cannot be settled here |
|---|---|
| `R6_SCORECARD.md` WP-5 cell and detail are now patched in the working tree | Row C expressly said “No other paths”, so the correction is unstaged. A new named commit row must name the file. |
| `REPORTS-PROVENANCE.md` remains unstaged | Row C expressly excluded it. A new commit row must name it. |
| R8 acceptance / dashboard edit | Requires T1/T8 from a fresh session and owner green; D5 forbids unilateral edit. |
| Any Row D or record-fix commit | Row D authorises work, not a commit. A new row must name paths and message. |

---

## 4. Overall position

Every in-scope Sprint Phoenix point is now either closed, explicitly accepted as a residual, or
recorded with its blocking authority named. Nothing has been silently relabelled DONE to make the
percentage look better.

`PH-5: DONE · PH-6: AUTHORISED AND DOCUMENTED, AWAITING ONE NAMED COMMIT ROW · R8: BLOCKED`
