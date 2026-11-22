# Copilot Prompt — Land Sprint Work & Strip Claude Attribution (Sprint 3)

**Authoritative as of 2026-11-23.** Supersedes
`artifacts/production-readiness/COPILOT-PUSH-PROMPT.md` (2026-11-20), which was written
against a repository state that no longer exists.

Copy everything between the two rules into Copilot Chat. Do not run any of it from a Claude
session.

---

You are operating on the local repository at `/Users/airm2/My ML Hub/SabiRoute`
(remote `origin` = `https://github.com/yourfavCHEFP/SabiRoute.git`).

## Verified starting state (re-derive it, do not trust it)

Before you touch anything, run and quote:

```
git rev-parse --abbrev-ref HEAD
git rev-parse --short HEAD
git rev-list --count origin/main
git status --porcelain
git log --oneline origin/main -5
```

As of 2026-11-23 it was:

- Current branch `sprint-1-alias-remediation`, HEAD `bb490f6`.
- **`main` and `origin/main` were identical** — 0 ahead, 0 behind. There is no history
  divergence left to reconcile. `feat/sabiroute-routing-foundation` is fully merged.
- `origin/main` holds **84 commits**.
- These commits sit ahead of `main`, and are the entire point of this task:
  - `9475aae` fix(sprint1): correct retired provider model names and regenerate proxy config
  - `380ece4` fix(phase13): scope audit to current feature schema and record the verdict
  - `bb490f6` chore(repo): track the protocol and handoff docs; ignore local agent state
  - `2623651` docs(sprint3): re-derive repo state and write the guarded push handoff

  Re-run `git rev-list --count main..sprint-1-alias-remediation` before merging; if the count
  is higher than the list above, that is expected — the sprint branch may have gained
  commits. Merge whatever is there; do not cherry-pick a subset.

## Task 1 — Land the sprint commits on main

1. `git checkout main`, confirm it equals `origin/main`.
2. `git merge --no-ff sprint-1-alias-remediation` (a merge commit is fine and preferred; it
   keeps the sprint boundary visible). If a conflict appears, **stop and report it** — do
   not resolve it yourself.
3. Verify before pushing: `git diff --stat origin/main..main` should show only the changes
   from those three commits, and `./.venv/bin/python -m pytest -q` should show
   **866 passed, 10 skipped**. Do not push if the test count differs.
4. `git push origin main` — a plain fast-forward push. Push in batches of at most 300
   commits; with three commits this is a single batch.

**Never**: force-push, rebase, reset, cherry-pick onto `main`, delete a branch, or push any
`backup/*`, `worktree-agent-*`, `sec/deps-nov`, `docs/*` or `feat/sabiroute-f06a-*` branch
to `main`. See Task 4 — those branches must not be merged.

## Task 2 — Remove Claude attribution

The facts, which are smaller than the earlier plan assumed:

- **0 commits are authored by Claude.** Authors are only `yourfavCHEFP`,
  `woolcoxm`, and `yourfavCHEF_P`. Claude is therefore **not** a contributor, and nothing
  needs to be removed from the contributors list.
- **20 of 84 commits** carry a `Co-Authored-By: Claude ... <noreply@anthropic.com>` trailer.
- **0 commits** carry a `🤖 Generated with [Claude Code]` footer.
- Some bodies also contain an `x-anthropic-billing-header:` line or a Claude model name;
  strip those too.

Procedure — a history rewrite is the only way, so it must be careful:

1. **Back up first, outside the repo:**
   `git clone --mirror . ../SabiRoute-backup-$(date +%Y%m%d).git`
2. **Inventory and confirm before rewriting.** Produce the exact list of the 20 commit SHAs
   and show them to me. Wait for my explicit "proceed with the rewrite".
3. Rewrite **only commit messages** on `main`, using `git filter-repo --message-callback`
   (preferred) or `git filter-branch --msg-filter`. The filter must remove any line matching
   `^Co-Authored-By:.*[Cc]laude`, `^🤖 Generated with.*Claude`, and
   `^x-anthropic-billing-header:`. Leave every other line untouched.
4. **Prove nothing but messages changed.** For every rewritten commit compare the tree:
   `git diff <old_sha>^{tree} <new_sha>^{tree}` must be empty. Report a table of old → new
   SHA with an empty-tree-diff confirmation for each. If any tree differs, stop and restore
   from the mirror backup.
5. Push with `git push --force-with-lease origin main` only after step 4 is fully clean and I
   have said so in this chat. `--force-with-lease`, never `--force`.
6. For pull requests, remove the `🤖 Generated with [Claude Code]` footer from each PR body
   with `gh pr edit <n> --body-file <cleaned>`. Report which PRs you changed. Do not close,
   reopen, or retarget any PR.

## Task 3 — Preserve README.md

`README.md` on `main` is correct as it stands. Do not rewrite it, do not regenerate it, do not
"improve" it, and do not replace it with `SabiRoute-README-draft.md`. The only acceptable
change to README.md is the one already made on `sprint-1-alias-remediation`
(the `scripts/audit_routing_dataset.py` row) — that arrives via the merge in Task 1.

## Task 4 — Branches you must not merge

These exist locally and are **not** to be merged into `main`. Merging any of them destroys
work:

| Branch | Why not |
|---|---|
| `feat/sabiroute-f06a-p3-liteLLm-pin` | Diffs against `main` as **1,327 files changed, 235,380 deletions** — it is an old narrow tree that would delete `web/`, the test suite and the docs. |
| `backup-sabiroute-release-f090f15` | Backup of an earlier release line. Preserved, never merged. |
| `backup/feat-routing-pre-trailer-removal` | Backup of pre-rewrite history. Preserved, never merged. |
| `worktree-agent-ae6f14cadd1c8cc84` | An agent worktree snapshot. |
| `sec/deps-nov` | Its one extra commit (`04d01c0`, the scan-outputs ignore rule) is already superseded on `main`. Stale. |
| `docs/community-governance-publication`, `docs/publish-request-flow-diagram` | Predate `main`; merged content already exists. Re-verify with `git diff --stat main <branch>` before considering anything here. |

If you believe one of these *should* be merged, stop and ask me — do not decide it yourself.

## Task 5 — Hard guardrails

- **Never run `git add -A` or `git add .`.** Stage files by explicit path only. `.claude/`,
  `.mcp.json`, `.playwright-cli/`, `brag-output/`, `claude-full-inventory.txt` and
  `SabiRoute_review_*.zip` are local machine state (about 15 MB) and are gitignored; do not
  un-ignore them or force-add them.
- **Never touch these protected paths:** `.env`, `uv.lock`, `.github/**`, `.mcp.json`,
  `.claude/**`, `.playwright-cli/**`, `brag-output/**`, `reports/provider_verification.json`.
  Never hand-edit `uv.lock`.
- **Never print or commit a secret.** Report environment variable names and set/empty status
  only. If a push is rejected by GitHub secret scanning (GH013), stop and report — do not
  rewrite history to work around it.
- **Never delete a file, branch or commit** that you did not create in this task.
- **Do not modify** `training_authorized`, the Phase 13 readiness gate, or any file under
  `src/sabiroute/intelligence/`.
- **Do not change the architecture.** SabiRoute decides, LiteLLM executes.
- Use `./.venv/bin/python` and `uv` only. Do not use pip, conda, or system Python.

## Task 6 — Report

Finish with a table: batch number, commits pushed, push result, and any rejection with its
verbatim message. Then state the final `git rev-parse --short HEAD` of `main` and confirm
`git status --porcelain` is clean apart from ignored local state.

Start with the dry-run in Task 2 step 2 and the state re-derivation above. Wait for my
"proceed" before any rewrite or push.

---

End of prompt.
