# Phase 17 — Security Scan Run Transcript (2026-11-23)

Read-and-report pass. No code changed, nothing committed, no branch created.
Full narrative and findings table: `docs/security-hardening-2026-11-23.md`.

**Target:** `/Users/airm2/My ML Hub/SabiRoute-claude-fix` · `main` @ `be10ab9` · clean tree.
**Scratch output:** `/tmp/phase17-sec/` (outside the repository; the tracked
`security-reports/` directory was not modified).

---

## Commands and headline results

| # | Command | Exit | Headline |
|---|---|---|---|
| 1 | `git rev-parse --abbrev-ref HEAD` / `git rev-parse HEAD` / `git status --porcelain` | 0 | `main`, `be10ab97b820a85d7d656dc95254d57d1e211733`, clean |
| 2 | `gitleaks dir . --redact` | 0 | 22.22 MB scanned in 3.55 s — **6 hits** |
| 3 | `gitleaks git . --all --redact` | 0 | 231 commits, 264.40 MB in 1 m 28 s — **129 hits**, 16 distinct commits |
| 4 | `bandit -r src -f json` | 1 | **14 results**, all LOW: 11×B101, 2×B110, 1×B105 |
| 5 | `semgrep scan --config p/python --config p/security-audit src` | 0 | **346 rules loaded, 1 result** (`avoid-sqlalchemy-text`, `migrate.py:48`) |
| 6 | `osv-scanner scan -L uv.lock` | 0 | **177 packages, 0 advisories** |
| 7 | `trivy fs --scanners vuln,misconfig,secret .` | 1 | **UNAVAILABLE — network refused** (`mirror.gcr.io` DB download, connection reset) |
| 8 | `hadolint Dockerfile` | 1 | **2 results**: DL3066 (info), DL3025 (warning) |
| 9 | `checkov -d . --framework dockerfile,github_actions` | 0 | **70 passed, 0 failed** |
| 10 | `zizmor .github/workflows` | 14 | **6 findings**: 3×unpinned-uses (High), 1×dangerous-triggers, 1×excessive-permissions, 1×artipacked |
| 11 | `git log --all -- .env` / `-- .env.backup` | 0 | empty — never tracked |
| 12 | `git for-each-ref --contains 195dad20df` | 0 | `refs/original/refs/heads/main`, `refs/original/refs/stash` |
| 13 | `python3` masked inspection of `.env.example` | 0 | 45 assignments; credential values are placeholders |

## Manual review (no output artefacts)

Read: `security/auth.py`, `keys.py`, `store.py`, `budgets.py`, `rate_limit.py`,
`redaction.py`, `store_executor.py`; `api/admin.py`, `completions.py`, `chat.py`, `health.py`,
`shutdown.py`; `chat/passwords.py`, `chat/store.py`; `migrate.py`, `main.py`; `web/app.js`,
`web/index.html`; both workflow files.

Greps with clean results: `subprocess|os.system|eval|exec|__import__` (none),
`pickle|yaml.load|marshal|dill` (none), `api_base|base_url` (env-only, no user control),
`innerHTML|document.write|eval(` in `web/` (none).

---

## Result summary

- **One critical item, pending validation:** credential material committed inside a scanner
  report at commit `195dad20df`. Values not reproduced. Rotation required.
- **CI hardening:** 6 zizmor findings, all `.github/**` — protected path, reported not fixed.
- **Source:** no injection sink, no unsafe deserialization, no subprocess, no SSRF surface, no
  SQL string construction, no client/admin authorization-boundary defect.
- **Dependencies:** 0 advisories (lockfile-based, single source).
- **Container:** Trivy unavailable; Hadolint and Checkov clean.

## Not covered

No deployed probe, no penetration test, no hosted-CI observation, no dynamic SabiChat testing,
no load or DoS testing, no `litellm-test.yaml` or compose runtime-secret review.
