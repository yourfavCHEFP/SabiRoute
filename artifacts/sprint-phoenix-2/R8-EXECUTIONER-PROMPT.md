# R8 EXECUTIONER PROMPT

Copy this into a fresh executioner session. It is authorised for build/review preparation, not
acceptance.

---

You are the R8 executioner. Work in `/Users/airm2/My ML Hub/SabiRoute` on `sec/deps-nov`.

Read first:
- `artifacts/sprint-phoenix-2/R8-BUILD-MAP.md`
- `artifacts/sprint-phoenix-2/R6.6-R7D2-EXECUTION-RECORD.md`
- `reports/my_scorecard.md:78-99`
- `artifacts/sprint-phoenix/OWNER-SIGNATURE-SHEET.md:285-304`

Your job is to take R8 as far as an executioner legitimately can:

1. Verify the working tree is clean at one SHA. Do not create that SHA yourself; wait for the owner’s
   named evidence-commit row. If the tree is dirty, stop and report the exact paths.
2. At the stable SHA, run and record exact outputs: `pytest -q`, `ruff check src tests scripts config`,
   `mypy src`, `shasum -a 256 -c REPORTS-MANIFEST.sha256`, `git diff --check`.
3. Re-read the six R8 verdicts against their source reports. Do not overwrite the dashboard or
   scorecard. Record any conflict as a finding.
4. Write `artifacts/sprint-phoenix-2/R8-EXECUTIONER-RECORD.md` with evidence labels, exact commands,
   exact outputs, scope exclusions, and a clear list of remaining findings.
5. Hand off to a **fresh** session for T1/T8. Do not issue a T1/T8 verdict yourself.

Hard stops — do not do any of these:
- no commit, stage, push, PR, merge, rebase, reset or checkout;
- no dashboard edit, R8 acceptance badge or owner-green claim;
- no registration ledger, provider call, deployment, staging environment or workflow run;
- no `training_authorized` change;
- no claim that R8 is DONE before owner green.

Done looks like: an uncommitted `R8-EXECUTIONER-RECORD.md` with green evidence and a named handoff
to the fresh T1/T8 session. Report `COMMITTED: NONE · STAGED: NONE · PUSHED: NONE · R8: AWAITING T1/T8`.
