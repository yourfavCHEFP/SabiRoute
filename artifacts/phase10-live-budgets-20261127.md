# Phase 10 — Live Budgets & Rate Limits

**Date:** 2026-11-27
**Branch:** `docs/phase06-reverify` (post-merge checkout)
**Verdict:** **PASS** — rate limits, daily/monthly budgets, concurrent reservations, pricing,
fallback accounting and PostgreSQL restart persistence all exercised against live services.

This closes the scorecard gap for Phase 10: *"all 4 Redis rate-limit tests skipped locally;
rejection paths never exercised live"* → next action *"run with `SABIROUTE_TEST_REDIS_URL` set,
then force a real 429."*

---

## A bug had to be fixed first — this phase could never have passed

`scripts/verify_phase10.py` built the credential it handed to the application with:

```python
database_url_for_process = str(database)
```

SQLAlchemy's `URL.__str__` **masks the password as `***`**. The script's own
`create_engine(database)` therefore authenticated fine, while the application under test
received `postgresql+psycopg://sabiroute:***@127.0.0.1:5432/sabiroute` and died at startup:

```
Gateway startup failed: (psycopg.OperationalError) connection failed:
FATAL: password authentication failed for user "sabiroute"
RuntimeError: Could not create temporary Phase 10 API key.
```

The tell was the split inside a single run: `PostgreSQL reachable: database=sabiroute,
role=sabiroute` printed immediately before the app's startup failure. Same host, same role —
different credential.

**Fix:** `database.render_as_string(hide_password=False)`.

This is a harness defect, not a product defect. It is also why the "rejection paths never
exercised live" gap stayed open: the instrument was broken, so nobody had run it.

---

## What was run

```
set -a; . ./.env; set +a
PYTHONPATH=<worktree>/src ./.venv/bin/python scripts/verify_phase10.py
```

Services are the owner's native PostgreSQL (`:5432`) and Redis (`:6379`, password-authenticated).

```
PostgreSQL reachable: database=sabiroute, role=sabiroute
Redis atomic Lua burst: 8/8 admitted
Rate limits, daily/monthly budgets, concurrent reservations, pricing, fallback accounting,
and PostgreSQL restart persistence: PASS
```

Exit code: **0**.

The harness raises `RuntimeError` rather than printing a soft warning when a rejection is
missing. Assertions it enforces include:

| assertion (source line) | meaning |
|---|---|
| `second_request.status_code != 429` (216) | a rate-limited client is rejected with a real 429 |
| `daily_first != 200 or daily_second != 429` (262) | daily budget is enforced |
| `monthly_first != 200 or monthly_second != 429` (264) | monthly budget is enforced |
| `priced.status_code != 429 or error.type != "budget_exceeded"` (352) | priced request rejected with the typed error |

### Tests, with the previously-skipped gate now open

```
tests/test_rate_limit_redis.py                                    4 passed   (were 4 skipped)
tests/test_phase10.py + test_rate_limit.py + test_rate_limit_redis.py
                                                                 30 passed, 0 skipped
```

Setting `SABIROUTE_TEST_REDIS_URL` is what un-skipped them; the credential came from the
already-configured `REDIS_URL`, so `.env` was not modified.

---

## What this PASS does and does not establish

**Real:** Redis (atomic Lua token bucket), PostgreSQL (key/budget state, including persistence
across a restart), and the HTTP rejection paths.

**Stubbed:** the provider call. The harness installs `LocalCompletionStub` as the gateway client
(`scripts/verify_phase10.py:157`), so no provider is contacted. These are rejection-path proofs
against real infrastructure — deliberately not real-provider proofs, which is Phase 05's and
Phase 07's job.

**Residual, unchanged:** the token estimator is text-only
(`security/budgets.py::estimate_input_tokens`). Non-text content is not estimated before
admission. That is a property of the estimator, not something these runs changed.

---

## Roadmap position

Phase 10 — moves to **Complete**: implemented, tested, live-verified on the rejection paths
against real Redis and real PostgreSQL, with the text-only estimator recorded as residual.

## Next

With Phase 02 excluded by owner instruction, the earliest incomplete phase is **Phase 11**
(Routing Intelligence), whose gap is capability evidence for 11 of 14 deployments — which is,
unavoidably, the same provider-coverage problem Phase 02 names. Phases 12 and 14 are
implemented with synthetic-only evidence; 18 is implemented and needs a live regression run.
