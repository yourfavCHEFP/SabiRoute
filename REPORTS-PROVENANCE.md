# REPORTS-PROVENANCE.md — B0 evidence provenance (Run 6)

## Scope rule (owner-settled, Run 5/Run 6; R1-governed)
- Include: the 12 Markdown reports under `reports/` plus
  `reports/provider_verification.json` (machine-readable verification
  output with `generated_at`, per-model results, and summary).
- Exclude: `reports/mission-state-2026-10-26T095838.json` (mission-state
  snapshot; evidentiary role as output not established); the
  `reports/evidence/sabichat-closeout-2026-10-16/` bundle (4 PNGs +
  `server.log`; excluded per owner ruling — preserved unchanged, and
  exclusion is not invalidation); post-attestation reconciliation
  documents (newer than the attestation run; out of the attested set by
  documented exclusion, never silent drift); top-level prompts, review
  archives, and working documents (not identified as release-evidence
  artifacts); and `REPORTS-MANIFEST.sha256` itself (no circular
  checksum claims).
- The attested set is closed and explicit: only the files in
  `EXPLICIT_INCLUDE` in `scripts/generate_reports_manifest.py` are
  indexed. New files under `reports/` are never silently included;
  adding an artifact requires editing that list (a governance decision).

## Included artifacts (13)
| Path | Kind | Evidence status |
|---|---|---|
| reports/audit-acceptance-and-disposition.md | report | historical |
| reports/implementation_12h.md | report | historical |
| reports/mission-c-evidence-audit-2026-10-26.md | report | historical (2026-10-26 run) |
| reports/mission-runlog-2026-10-26T095838.md | run log | direct (2026-10-26 mobilization) |
| reports/mobilization-reconciliation-2026-10-26.md | report | historical (2026-10-26 run) |
| reports/my_scorecard.md | report | historical |
| reports/part-i-sprints-1-8-overnight-report-2026-10-26.md | report | historical (2026-10-26 run) |
| reports/pre-roadmap-audit.md | report | historical |
| reports/provider_verification.json | verification output | direct (generated 2026-10-10, per embedded timestamp) |
| reports/r02-kill-switch-remediation.md | report | historical |
| reports/reconciliation-plan.md | report | historical (R-series reconciliation) |
| reports/remediation-roadmap-and-gates.md | report | historical |
| reports/sprint-02b-unattended-core.md | report | historical |

Source-run attribution above is supported only where filenames, embedded
timestamps, or contents establish it; all other provenance is marked
historical rather than fabricated. No owner-approval record is asserted:
owner decisions referenced in R-series work live in prompt text, not in a
separately hashed decision record (see A0 open item).

## Exclusions (documented, not invalidated)
- `reports/mission-state-2026-10-26T095838.json` — mission-state snapshot.
- `reports/evidence/sabichat-closeout-2026-10-16/` (5 files) — SabiChat
  closeout screenshots/logs; out of B0 Core scope per owner ruling.
- Post-attestation reconciliation documents (e.g.
  `reports/reconciliation-2026-10-31.md`) — newer than the attestation;
  preserved unchanged, never silently indexed. Inclusion requires an
  explicit governance decision plus an `EXPLICIT_INCLUDE` edit.
- Top-level prompts/archives/working docs (e.g. release prompt, review
  zip, build checklists/drafts) — not release-evidence artifacts.
- `REPORTS-MANIFEST.sha256` itself — excluded from its own checksum list.

## Integrity statement and limits
- The manifest records SHA-256 hashes of the exact file bytes of the 13
  included artifacts. It proves byte consistency against those hashes —
  **nothing else.** In particular it does **not** prove, and must never
  be represented as proving, any of the following (owner decisions
  D-R1-1/D-R1-2):
  - (A) BYTE INTEGRITY: "these bytes match the indexed hashes" — proven.
  - (B) EVIDENCE VALIDITY: whether the contents are correct — **not proven.**
  - (C) OWNERSHIP/APPROVAL: who wrote or approved them — **not proven;**
    requires explicit review/owner governance.
  - (D) RELEASE READINESS: whether the product is releasable — **not
    implied by the manifest.**
- Deterministic regeneration: `uv run python
  scripts/generate_reports_manifest.py` rewrites the manifest from the
  closed `EXPLICIT_INCLUDE` set; `shasum -c REPORTS-MANIFEST.sha256`
  verifies it independently. `--check` exits 1 when stale.
- This provenance document is protected by review and by the manifest's
  agreement with it on the artifact set; it is **not** covered by a
  self-referential hash.
- Decision-record inventory in support of A0 (status-labeled per claim):
  - `docs/architecture-decision-record.md` — 16,107 bytes, sha256
    `f987fb1b78d38fb39d06e539509f1798c3638219bc65839e8dc76e58847d104b`
    (VERIFIED BY RUNTIME); content VERIFIED BY INSPECTION: records owner
    decisions D1–D8 (Green Closure, 2026-10-27 through D8 2026-10-31),
    including D3 accepting this ADR itself as the canonical decision log
    "subject to normal repository tracking and review," and D4 settling
    the no-push-without-authorization policy. Contains zero R1-manifest
    decisions (grep for `manifest`/`D-R1`/`B0 manifest`: 0 hits). The file
    is untracked and not ignored (VERIFIED BY RUNTIME) — its D3-noted
    canonical status takes effect on review/tracking, which is
    owner-gated, not effected here.
  - `artifacts/sprint13-policy-experiment/deadline-policy-decision.md` —
    explicitly labeled "proposal awaiting owner approval"
    (VERIFIED BY INSPECTION); not an approval record.
  - No other owner-decision record exists in the repository (filename
    inventory over non-dependency paths; VERIFIED BY INSPECTION). In
    particular, no file records D-R1-1…D-R1-5: those decisions exist in
    R1 prompt text only and are referenced — not reproduced — in the
    integrity statement above. A separately hashed owner-decision record
    covering R1 therefore remains an UNRESOLVED GOVERNANCE ITEM for A0.
  - Per-report authorship beyond what filenames and contents establish
    remains unestablished (UNRESOLVED, unchanged).

## Tracking / governance status (R1 closure, 2026-10-31, VERIFIED BY RUNTIME)

As of HEAD `b360ffc` on `feat/sabiroute-routing-foundation`
(diverged: local 2 ahead / origin 3 behind):

- `REPORTS-MANIFEST.sha256`, `REPORTS-PROVENANCE.md`, and
  `scripts/generate_reports_manifest.py` are **untracked** (not ignored —
  `git check-ignore` confirms no ignore rule matches them — but never
  staged). The attestation is therefore reproducible from the working
  tree; its canonical committed state awaits an owner-authorized
  stage/commit/push (not performed in this lane).
- Canonical review unblocked: `.gitignore` now carries narrow per-file
  exceptions for all 13 attested artifacts (`git check-ignore` proves
  none of the 13 is ignored), while `reports/*` still ignores everything
  else — including every documented exclusion (mission-state JSON,
  `reconciliation-2026-10-31.md`, the `reports/evidence/` bundle).
  Previously only 5 of 13 were un-ignored; committing then would have
  fractured the attested set. Staging/commit/push remain owner-gated;
  nothing was staged here.
- Scorecard cost reference: `14/14` denotes the R1-assumed entry count
  repaired earlier this lane; the actual attested set is **13 entries**
  (12 Markdown + `provider_verification.json`). The "14" bound the
  stale-hash symptom, not the set size. Future re-attestation must use
  the real count.
- The scorecard's "Open integrity note" (claiming `my_scorecard.md:
  FAILED`) is historical: `my_scorecard.md` verifies OK in the current
  manifest, and that note predates the repair. It is left intact for
  audit; it must not be read as a live finding.

## Tracking / governance status — dated correction (2026-11-16)

**Supersedes the HEAD and divergence figures in the 2026-10-31 section above. That section is
retained unchanged as the historical record.**

As of 2026-11-16, measured:

- HEAD is `1e69ada943f3d3921122219e7a569cdff989d3fd` on branch **`sec/deps-nov`**.
- **No upstream is configured** for this branch. The "local 2 ahead / origin 3 behind" figure
  recorded for `b360ffc` on `feat/sabiroute-routing-foundation` does not describe the current
  branch state and must not be read as current.
- `feat/sabiroute-routing-foundation` also points at `1e69ada9`.
- `REPORTS-MANIFEST.sha256`, `REPORTS-PROVENANCE.md` and
  `scripts/generate_reports_manifest.py` are all three **TRACKED** in git at this HEAD
  (verified with `git ls-files --error-unmatch`). **This contradicts the 2026-10-31 section's
  statement that they are untracked.** That statement is stale and must not be relied on; it is
  left intact above as the historical record. Nothing was staged or committed by this
  correction — the working-tree change to this file is unstaged and remains owner-gated.
- **All 13 attested artifacts verify OK** against the manifest, including
  `reports/my_scorecard.md`. The historical "Open integrity note" at the end of the 2026-10-31
  section is confirmed historical and is not a live finding.
- The attested set remains **13 entries** (12 Markdown + `provider_verification.json`). The
  `14/14` scorecard reference remains a stale-hash symptom, not a set size.
- The A0 `UNRESOLVED GOVERNANCE ITEM` (no separately hashed owner-decision record covering R1)
  is **unchanged**.

This entry corrects a stale figure. It does not rewrite the record it corrects, and it does not
assert any approval, tracking or release readiness.

**Attribution (recorded 2026-11-16, WO-3).** The dated correction above was written by
**Claude Code (executioner)** on **2026-11-16** during the WP-3 manifest reconciliation. It was
omitted from the PH-0/PH-3 execution report's §10 working-tree table — a reporting defect, now
recorded here. Its HEAD figure (`1e69ada9`) is **stale**: HEAD has since advanced to `e0530e5`
("docs: track the R6.0 corpus (42 documents)"). Every other statement in the correction was
re-verified on 2026-11-16 and still holds. This file remains **unstaged**; nothing here is
committed.
