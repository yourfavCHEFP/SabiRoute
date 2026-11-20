# P1 assessment: synchronous database calls on the event loop (deferred)

Status: assessed, NOT remediated. No code changed by this document.

## Verified blocking paths

`PostgresApiKeyStore` methods are all synchronous `def` backed by sync
SQLAlchemy (`create_engine`, `store.py:124`): `create_usage_event`,
`append_pre_routing_feature_snapshot`, `finalize_usage_event`,
`reserve_budget`, `reconcile_budget`, `release_budget`, key/limit/budget
CRUD. Every call site in `api/completions.py` (admission `:236`, budget
`:265-267,502`, snapshot `:645`, finalize `:297`) invokes them directly
with no `await`, no `run_in_executor`, no thread offload — so each call
blocks the event loop for its full round-trip.

## Why the deadline cannot preempt it

`asyncio.timeout_at` delivers cancellation only at await checkpoints. A
thread blocked in synchronous socket I/O never yields, so neither the
300s deadline, nor client-disconnect delivery, nor any asyncio timeout
can interrupt it. Worst case: a wedged database stalls ALL concurrent
requests (not just the affected one), defeats the deadline guarantee,
and delays cancellation observability.

## Risk to isolation, latency, cancellation, reliability

- One slow query serializes every in-flight request (head-of-line
  blocking at the loop level).
- Cancellation of a request stuck behind a blocked loop is delayed until
  the blocking call returns.
- Deadline telemetry timestamps skew under blocking (elapsed measured
  honestly, but bud

gets burn while nothing progresses).

## Remediation options (deferred, needs approval)

1. **Threadpool offload (smallest):** wrap store calls in
   `asyncio.to_thread` at the existing call sites (or inside a thin
   async adapter). Keeps SQLAlchemy + schema; requires session/connection
   discipline: no shared Session across threads (current code uses
   short-lived `engine.begin()` blocks — thread-compatible if each call
   stays self-contained; pooled connections are thread-safe).
2. **Async engine migration (larger):** SQLAlchemy async engine +
   asyncpg; touches store internals broadly, needs new dep + migration
   review of transaction boundaries.
3. **Timeouts on DB ops (complementary):** statement/connection timeouts
   so blocking has a ceiling even before offload.

Recommended: option 1 first (bounded diff, existing tests still apply
with async wrappers awaited), then measure; option 2 only if profiling
justifies it.

## Tests required (deferred workstream)

- Slow-store (blocking 5s double) no longer stalls a concurrent fast
  request (two-client overlap test with fake clock or event gates).
- Cancellation delivered during a blocked store call surfaces promptly.
- Deadline still bounds requests under slow store.
- Transactional integrity under threaded execution (no partial writes).
- Existing finalize/pairing/budget tests pass unmodified.

## Session/thread-safety constraints

Engine/pool shared read-only across threads is safe; Sessions/connections
must not cross threads. Current short-transaction style complies —
verify per call site during implementation. Do not share the in-memory
test double's lock semantics as production proof.
