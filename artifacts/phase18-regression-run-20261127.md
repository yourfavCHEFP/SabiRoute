# Phase 18 — Full Regression Run (2026-11-27)

**Branch:** `docs/phase10-budgets` (off `origin/main` at `a9e1145`)
**Verdict:** **PASS** — no regressions; and the environment-gated skip count is now driven
to **1**, with that last skip a contract await rather than a missing credential.

This record supersedes the **figures** in `docs/phase18-testing-evidence.md`
(1123 passed / 9 skipped), which are stale on this tree. It does not replace that document.

---

## Result — VERIFIED BY RUNTIME

| run | environment | result |
|---|---|---|
| plain | no integration gates | **1474 passed, 15 skipped**, rc=0 |
| gates open | `SABIROUTE_TEST_PG_URL` + `SABIROUTE_TEST_REDIS_URL` | **1488 passed, 1 skipped**, rc=0 |

The plain run reproduces the documented `origin/main` baseline exactly (`1474 passed,
15 skipped`), which is the regression signal: nothing drifted.

Opening both gates converts **14 environment skips into 14 passing integration tests** —
real PostgreSQL and real Redis, not stubs.

`1488 − 1474 = 14`, which reconciles the two runs exactly. No test changed side; the same
suite simply executed more of itself.

---

## The one remaining skip is not environmental

```
SKIPPED [1] tests/test_r6_registration_digest_conformance.py:570:
           awaiting authorised ledger instantiation
```

This is a **contract skip**, not a credential gate. It waits on an authorised ledger
instantiation outside this repository's authority, and it should not be "fixed" by
provisioning anything locally. Note that CLAUDE.md §11's historical claim that "none is a
contract skip" no longer holds on this tree.

---

## How the gates were opened

Credentials came from variables already configured in `.env` — `REDIS_URL` was passed through
as `SABIROUTE_TEST_REDIS_URL`, and `SABIROUTE_TEST_PG_URL` was already present. **`.env` was
not modified**, and no value was printed.

```
set -a; . ./.env; set +a
SABIROUTE_TEST_REDIS_URL="$REDIS_URL" ./.venv/bin/python -m pytest -q
```

---

## Residual — belongs to Phase 19, not here

The scorecard's second half of this gap, *"no regression baseline pinned in CI"*, is **not**
addressed by this run. Local execution proves the suite; pinning `1488 passed / 1 skipped` as
the CI expectation is a CI/CD concern and is recorded against Phase 19.

---

## Roadmap position

Phase 18 — local regression evidence is now current and complete: the suite runs green with
integration gates open, and the skip set is down to one contract await.

## Note on ordering

Phase 18 was taken before 15, 16 and 17 because it is *verification* work that requires no new
construction, while 15 needs a UI built, 16 needs remote-access decisions, and 17 is held open
by `security/permissions.py` being a deliberate zero-byte placeholder (CLAUDE.md §12). That is
a deliberate ordering choice, not an oversight of the numeric order.
