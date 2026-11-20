# OWNER APPROVAL — D1–D7

**Recorded:** 2026-11-17 · **Branch:** `sec/deps-nov` @ `4080bf5`
**Status:** APPROVED BY THE OWNER · **Transcribed by:** `claude-opus-5-5` (executor)

---

## What this document is

`OWNER-DECISION-SHEET-R6.1.md` recommends seven decisions and states plainly at `:5` that it
**"recommends; it authorises nothing and changes no file."** The signature sheet
(`OWNER-SIGNATURE-SHEET.md`) predates it and covers only S-1…S-6 and C-1…C-3. Neither document
therefore authorised D1–D7.

The owner has now approved all seven, in words, in session `cded5bf9-48c5-4e09-ad7f-d758743987ed`
on 2026-11-17. This file is the **instrument of record** for that act. The contract (§8) and
`src/sabiroute/config/validation.py` cite this file, and this file alone, as the authority for
D1–D7.

## Evidence label and limit

`[M]` — the approval was given; the quoted words below are verbatim from the session transcript.

**This is a transcription, not a hand signature.** The owner's approval was conveyed in writing
in a Claude Code session and recorded here by the executor. It carries the owner's authority
because the owner gave it. It does not carry the owner's hand. If a hand-signed instrument is
later required for D1–D7, this file is superseded by it and should say so in a new row rather
than be edited.

## The approval, verbatim

> i approve all the D1-D7 decisions we've had, implement it !

Preceded, in the same session, by:

> approve all seven decisions D1–D7 in `artifacts/sprint-phoenix/OWNER-DECISION-SHEET-R6.1.md` §C
> and "get everything done please."

## What is approved

The seven recommendations as written in `OWNER-DECISION-SHEET-R6.1.md` §C, at their
recommended answers:

| # | Decision | Approved value |
|---|---|---|
| **D1** | I2 budget | `p95 ≤ 150 ms`, `≤ 1.25×` input, configurable, not hardcoded |
| **D2** | `max_ratio` | `0.50`, range `(0.25, 1.0)`; a request whose compression would breach the ceiling passes through **unmodified** |
| **D3** | F-02 / WP-5 | Both stay gated; R6.2 proceeds; F-02 recorded as an **accepted residual** in the contract's own text |
| **D4** | Exit criterion 4 | Review by a **fresh session** authoring neither `68bde1f` nor `4080bf5`; output is a **record, not an edit** |
| **D5** | R8 | **BLOCKED, not complete**; the dashboard conflict recorded as it stands; no dashboard edit |
| **D6** | `ruff format` | New files only; no 78-file reformat |
| **D7** | Push | **No** — the one irreversible outward act |

## What this approval does NOT do

- It does **not** authorise a push. D7 answers that question **no**.
- It does **not** authorise R6.2 Phase 1. That tranche gate is untouched and remains **GATED**.
- It does **not** tick exit criterion 4. D4 assigns that act to a fresh session's review and,
  after it, to the owner. `R6.1-REVIEW-RECORD.md` recommends that the criterion **not** be
  accepted in its current state; that recommendation stands and is not overridden here.
- It does **not** ratify the 91 Track A lines added in `68bde1f`. Those remain **unratified**;
  D1/D2 authorise the *values*, not the earlier commit.

---

*Owner approval transcribed 2026-11-17. Authoritative for D1–D7 and for nothing else.*
