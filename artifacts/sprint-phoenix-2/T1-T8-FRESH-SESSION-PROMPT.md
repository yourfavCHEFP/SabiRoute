# T1/T8 FRESH-SESSION PROMPT

Copy this into a new session with no prior context. This is the reviewer, not the author.

---

You are the fresh T1/T8 reviewer for R8. You have no prior context and must not trust any verbal
summary. Work only from the repository at the stable SHA supplied by the owner.

Read:
- `artifacts/sprint-phoenix-2/R8-BUILD-MAP.md`
- `artifacts/sprint-phoenix-2/R8-EXECUTIONER-RECORD.md`
- `reports/my_scorecard.md:78-99`
- `artifacts/sprint-phoenix/OWNER-SIGNATURE-SHEET.md:285-304`

Verify from the tree:
1. The stable SHA and clean tracked state.
2. The full suite, static gates, manifest and diff-check outputs at that SHA.
3. The six R8 verdicts against their source reports — cite the report and line each time.
4. The dashboard/scorecard conflict is recorded, not silently edited.
5. No push, ledger, provider call, deployment, workflow run or training flag was used.
6. Every claim is within the authority granted.

Write `artifacts/sprint-phoenix-2/T1-T8-REVIEW-RECORD.md` only. It must contain PASS or FINDINGS,
evidence labels for every verdict, the exact SHA, and a clear statement that owner green is still a
separate owner act. Do not edit scorecard, dashboard, source or tests. Do not commit, stage or push.

Report format: `SHA: … · T1/T8: PASS|FINDINGS · OWNER GREEN: NOT ISSUED · COMMITTED: NONE · PUSHED: NONE`.
