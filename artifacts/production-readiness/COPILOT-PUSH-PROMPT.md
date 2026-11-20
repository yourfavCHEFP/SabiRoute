# Copilot Prompt — Push Everything to Origin Main (run later, not here)

Paste the following into Copilot (GitHub Copilot Chat / Copilot CLI) when you are ready to push. Do NOT run any of these commands from this Claude session.

---

## PROMPT TO GIVE COPILOT

You are operating on the local repository `SabiRoute` (owner `yourfavCHEFP`, remote `https://github.com/yourfavCHEFP/SabiRoute.git`). The authoritative development branch is `sec/deps-nov` (HEAD `13d0377`), which is diverged from origin (3 origin-only commits, 6 local-only commits). There are also several local-only branches: `backup-sabiroute-release-f090f15`, `backup/feat-routing-pre-trailer-removal`, `docs/community-governance-publication`, `docs/publish-request-flow-diagram`, `feat/sabiroute-f06a-p3-liteLLm-pin`, `feat/sabiroute-routing-foundation`, `worktree-agent-ae6f14cadd1c8cc84`, and the just-pushed `sec/deps-nov-ci`.

Task:
1. Push ALL local commits and branches to `origin/main` so that `origin/main` contains the complete history. Work in batches of at most 500 commits per push (500 folds). If a single push exceeds 500 commits, split it into multiple pushes of ≤500 commits each, pushing oldest-first, and confirm each batch succeeds before starting the next. Use `git push origin <branch>` with the appropriate refspec; never use `--force` unless a non-fast-forward rejection occurs AND I have explicitly confirmed force-push in this chat. If a push is rejected as non-fast-forward, stop and report the rejection — do not auto-resolve with merge/rebase/cherry-pick/reset without my explicit go-ahead.

2. For every commit and PR that lists "Claude", "Claude Sonnet", "Anthropic", "noreply@anthropic.com", or any `Co-Authored-By: Claude` / `🤖 Generated with Claude Code` trailer as a contributor or co-author, remove that attribution. Specifically:
   - Rewrite commit messages to strip `Co-Authored-By: Claude ... <noreply@anthropic.com>` and `🤖 Generated with [Claude Code](...)` lines, and any "Claude" author metadata, across all branches being pushed. Use `git filter-branch` or `git filter-repo` (preferred) with a message/callback that removes those trailers, preserving all other content. Do this on a fresh clone/backup first; never rewrite the only copy.
   - For pull requests on GitHub, edit each PR body to remove the `🤖 Generated with [Claude Code]` footer and any Claude co-author mentions, and remove Claude from the PR's contributor list where the platform allows (squash-merge with cleaned messages, or edit via `gh pr edit`).
   - Do NOT alter code, file contents, or non-attribution metadata. Only attribution/authorship fields and trailers.
   - Report, before pushing, the full list of commits/PRs that contained Claude attribution and confirm with me before rewriting.

3. Safety constraints:
   - Never push to `main` directly without my explicit "push to main now" confirmation in this chat (this prompt IS that confirmation once I say go).
   - Never force-push without my explicit confirmation.
   - Never delete a branch or commit; preserve all pre-existing local changes and untracked files.
   - Work on a backup clone first; verify with `git log`/`git diff` that only attribution changed.
   - Report batch-by-batch progress (batch N of M, commits pushed, any rejections).

Start with a dry-run report: list branches, commit counts per branch, and which commits/PRs contain Claude attribution. Wait for my "proceed" before any rewrite or push.

---

End of prompt. Do not execute any of the above from this Claude session. The user will hand this to Copilot separately.