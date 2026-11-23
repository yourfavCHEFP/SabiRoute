# Claude Co-Author Removal — Verified Dry Run (2026-11-23)

## ACTION COMPLETED

Performed on a **throwaway clone at `/tmp/sr-rewrite`**. The live repository, `main`,
`origin/main` and every branch were **not** modified. Nothing was pushed.

Method: `git clone file:///…/SabiRoute /tmp/sr-rewrite`, then
`git filter-branch --msg-filter 'python3 /tmp/strip_claude.py' -- --all` on the clone only.

Files created (outside the repo): `/tmp/sr-rewrite`, `/tmp/strip_claude.py`,
`/tmp/before_sha.txt`, `/tmp/after_sha.txt`, `/tmp/tree_cmp.txt`.

## WHY

Removing a `Co-Authored-By` trailer rewrites commit messages, which changes commit hashes and
forces a `--force-with-lease` push. That must not be attempted on a live repository until it
is proven to leave every file untouched.

## RESULT (VERIFIED BY RUNTIME)

| Check | Result |
|---|---|
| Commits before / after | 84 / 84 |
| Per-commit tree comparison | **84 identical, 0 differing** |
| `main` tip tree, before | `7202f4bee990bfb6f4c1e22a1912c722fba9696b` |
| `main` tip tree, after | `7202f4bee990bfb6f4c1e22a1912c722fba9696b` |
| Commits with `Co-Authored-By: Claude` on `main`, after | **0** |
| Occurrences of "claude" in any `main` commit message, after | **0** |
| Commit SHAs changed | 84 (all — the earliest rewritten commit is near the root) |

**Conclusion:** the rewrite changes commit messages only. Every tree in the history is
byte-identical, and all 20 co-author trailers are gone. The rewrite is safe to perform.

### What it implies

- All 84 commit SHAs change, so the push **must** be `--force-with-lease`, never `--force`.
- Any open pull request targeting a rewritten commit will show its base as diverged and may
  need reopening or retargeting; that is an owner decision, not an automatic step.
- Other refs in the clone (`sec/deps-nov`, `worktree-agent-*`, backup branches) still carry
  their own copies of these trailers. They are not being pushed to `main`, so they are out of
  scope unless the owner asks for them separately.

## The filter used

```python
import re, sys
pat = re.compile(r'^(Co-Authored-By:.*[Cc]laude|🤖 Generated with.*[Cc]laude|x-anthropic-billing-header:)', re.I)
out = [ln for ln in sys.stdin.read().splitlines() if not pat.match(ln.strip())]
while out and not out[-1].strip():
    out.pop()
sys.stdout.write("\n".join(out) + "\n")
```

It removes only whole lines matching those three prefixes, collapses trailing blank lines,
and leaves every other line — subject, body, issue references — untouched.

## ARCHITECTURAL POSITION

No change to the pipeline. No source, config, dependency, schema or database action. The
repository content is proven identical.

## ROADMAP POSITION

Release hygiene only. No phase status changes.

## DEPENDENCY IMPACT

Copilot's push step depends on this proof. Because it passed, the rewrite may proceed under
the guardrails already written in
`artifacts/sprint-3/COPILOT-PUSH-PROMPT-2026-11-23.md`.

## NEXT STEP

Hand the verification and the push prompt to Copilot. Copilot repeats the same procedure on
the real repository after taking a mirror backup, then force-pushes with
`--force-with-lease`.

## DO NOT TOUCH YET

- `origin/main` until the owner says "proceed" and Copilot has the mirror backup in place.
- Branches whose names include `backup/`.
- `training_authorized`, the Phase 13 gate, `.env`, `uv.lock`, and the other protected paths.

## CURRENT PROJECT STATUS

```
CURRENT GATE: Co-author rewrite proven safe to execute; not yet executed on the real repository.
CURRENT PHASE: Phase 13 READY_FOR_HUMAN_REVIEW (Copilot reviews); training NOT authorized.
PROVEN: 84/84 trees identical; main tip tree unchanged (7202f4b); 0 Claude trailers and 0 "claude" strings in main messages after rewrite; all 84 SHAs change.
UNPROVEN: nothing about the rewrite itself; the live force-push is untried by design.
BLOCKED BY: owner "proceed" plus a mirror backup before any force-push.
NEXT: Copilot performs the rewrite on the real repo and force-pushes with --force-with-lease.
```
