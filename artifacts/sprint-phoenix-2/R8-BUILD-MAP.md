# R8 BUILD MAP — from BLOCKED to DONE

**Issued:** 2026-11-17 · **Current HEAD:** `6f972f8`
**Authority:** owner authorised a fresh-session R8 build tranche and T1/T8 review; no dashboard edit, R8 badge, push, ledger, deployment or `training_authorized` change.

---

## 0. Has R8 started?

Yes as a *process claim*, no as an accepted state. The 2026-11-02 dashboard says R8 COMPLETE
100%, but `reports/my_scorecard.md:93` governs and says **BLOCKED**: stable SHA → T1/T8 → owner
green. D5 makes the scorecard authoritative and records the conflict without editing the dashboard.

There is no accepted R8 verdict in the repository. The work below closes the process gap.

---

## 1. Stage 0 — commit the evidence

The R6.6 replay and R7 D2 check are now recorded, but the files are uncommitted. T1/T8 must review
a stable SHA, so these paths must first be committed under a named row:

- `artifacts/sprint-phoenix-2/R6.6-R7D2-EXECUTION-RECORD.md`
- `artifacts/sprint-phoenix-2/R6.7-D3-DISPOSITION.md`
- `artifacts/sprint-phoenix-2/R6.6-VALIDATION-SPEC.md`
- `artifacts/sprint-phoenix-2/R7-D2-check_backup_restore.py`
- `artifacts/sprint-phoenix-2/R7-D2-BACKUP-RESTORE.md`
- `artifacts/sprint-phoenix-2/R7-OFFLINE-REPORT.md`

No push is required for T1/T8, but if you push, record the SHA before starting review.

**Exit:** tracked tree clean at one SHA; `git diff --cached` empty.

---

## 2. Stage 1 — reproduce the evidence at the stable SHA

Run, record exact output:

- `pytest -q`
- `ruff check src tests scripts config`
- `mypy src`
- `shasum -a 256 -c REPORTS-MANIFEST.sha256`
- `git diff --check`

Expected baseline from this lane: `839 passed, 10 skipped`; service skips and the ledger skip named,
never hidden.

**Exit:** all green; no live provider, managed service, ledger or deployment used.

---

## 3. Stage 2 — fresh T1/T8 review

A **fresh session with no prior context** reviews:

1. The six R8 verdicts re-read against their source reports.
2. `reports/my_scorecard.md:93` against the fresh evidence.
3. The dashboard conflict: recorded, not silently edited.
4. Whether stable SHA, full suite, static gates, manifest and scope exclusions are reproducible.
5. Whether any claim exceeds authority (push, live provider, ledger, deployment, training).

The reviewer issues a written T1/T8 record. The author does not review their own work; an
executioner verdict is not a verdict.

**Exit:** T1/T8 verdict PASS or FINDINGS. Findings are recorded, not edited away.

---

## 4. Stage 3 — owner green

Only you can accept R8. T1/T8 PASS does not accept it. No dashboard edit or R8 badge until owner
green is recorded in a named row.

**Exit:** owner green recorded with SHA and T1/T8 reference.

---

## 5. Stage 4 — close R8

With owner green recorded, update only the scorecard/dashboard paths named in that row. R8 becomes
DONE. No push, ledger, deployment or training flag.

---

## 6. Definition of DONE

`R8 DONE` means: evidence committed at a stable SHA, fresh suite green, T1/T8 PASS from a fresh
session, owner green recorded, and the scorecard updated by named row. Nothing less is DONE.
