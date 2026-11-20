# Deadline policy options review (decision package, not implemented)

Status: proposal. No code changed. Framework versions verified in-repo:
FastAPI 0.141.1, Starlette 1.7.0, httpx 0.28.1, uvicorn 0.54.0.

## 1. Verified source-derived lifecycle

1. ASGI ingress → Starlette `ServerErrorMiddleware` (outermost, stock) →
   router → dependencies (`require_client_key`) → endpoint
   (`completions.py:chat_completions`).
2. Endpoint: admission record → rate/budget gates → classification →
   eligibility → attempt loop (`:538`) → LiteLLM execution.
3. Endpoint returns a response object; Starlette then invokes it:
   `StreamingResponse.stream_response` sends headers FIRST, then iterates
   `body_iterator` (`responses.py:250-257`). The SabiRoute generator
   (`stream_body`) therefore runs AFTER the endpoint function returns.
4. Disconnect: server cancels the response task; `CancelledError` lands
   at the generator's yield point (existing handling distinguishes it).
5. Finalization (`finish()`) runs inside request flow (non-stream) or
   generator tail (stream); store rejects double-finalize; unfinalized
   stays auditable. No custom middleware exists today.

Consequences: a timeout context inside the endpoint CANNOT cover body
iteration (it exits on return). A middleware-level timeout CAN — it wraps
the whole downstream call including `stream_response`. Unhandled
mid-stream timeouts surface through `ServerErrorMiddleware` as 500s, so
the middleware must catch its own timeout and shape the outcome itself.
`asyncio.TimeoutError` (builtin `TimeoutError` subclass) is distinct from
`asyncio.CancelledError` — but the generator's generic `except Exception`
branch would currently misclassify a deadline `TimeoutError` as an
upstream stream failure. Implementation must add an explicit branch.

## 2. Models A–D comparison

| Aspect | A ingress deadline (middleware) | B post-admission deadline | C split execution/stream budgets | D hybrid |
|---|---|---|---|---|
| Bounds | Everything incl. admission+stream | Attempts+stream; admission separate | Processing vs stream separately | All layers with precedence |
| Outside bound | Nothing (cleanup bounded separately) | Admission stalls (Redis-bounded ~5s, acceptable) | Cross-boundary accounting | Complexity itself |
| ASGI enforceability | Full (wraps response call) | Partial (endpoint return ends coverage) | Same split issue for stream part | Full if middleware-anchored |
| Auth/admission | Inside budget (correct: owned work) | Outside; needs own caps | Same as B | Same as A |
| Retry/fallback | Gated starts + absolute backstop | Same, minus admission | Per-budget gates | Same, layered |
| Streaming | Covered incl. post-byte | Post-byte uncovered | Explicit idle+total rules | Covered |
| Cancel/disconnect | Distinct exception types preserved | Same | Same | Same |
| Cleanup/finalize | Must be fast or separately bounded (store I/O currently unbounded — P3 note) | Same | Same | Same |
| API compat | 503 pre-byte; truncation post-byte | Same minus admission | Same | Same |
| Config complexity | One number | One number + admission caps | Two numbers + idle rule | Most knobs |
| Testability | Middleware + fake clocks, deterministic | Same | Same | Same |

**Recommended architecture: A-anchored hybrid (D done minimally)** —
one middleware deadline from ingress covering everything, with the
existing before-attempt gate kept as the graceful path and per-operation
httpx timeouts unchanged underneath. Do NOT adopt B alone (streaming
escapes it — proven §1). C's split adds config for no verified gain.

## 3. Numeric comparison (all values PROPOSED, none approved)

Production per-operation default is 120s (NOT a bound: up to ~360s
adversarial non-stream; unbounded trickle streams).

| Total | Covers at 120s/op | Cuts | Verdict |
|---|---|---|---|
| 60s | Nothing fully (one slow attempt exceeds it) | Legitimate slow successes | Too tight; risks false failures |
| 120s | One nominal attempt | Any fallback, most slow successes | Too tight |
| 180s | One adversarial attempt + slack | 3-attempt policies mid-sequence | Defensible only with per-policy derivation |
| 300s | Full 120s-class attempt + fallback + finalize | Little legitimate traffic (typical <10s) | **Recommended default** |

Drill 10s numbers must never enter prod math. Interactive vs stream:
same total pre-first-byte; post-byte streams exempt from the total and
governed by 120s read-inactivity plus a future explicit idle policy
(owner decision). No traffic percentiles invented; numbers derive from
configured bounds, not observed distributions (which remain unmeasured).

## 4. Ingress vs post-admission scope

Recommend **ingress** (Model A §2): admission stalls are SabiRoute-owned
work and Redis-bounded (~5s), so including them costs little and yields
clean "no request lives past N" semantics. No client-supplied deadlines
(unauthenticated timing input rejected as before).

## 5. Streaming & idle recommendations

Pre-byte expiry → 503 `deadline_exceeded`, no attempt. Post-byte → stop
yielding, end without `[DONE]`, finalize failure/`deadline_exceeded`.
Disconnect → `client_cancelled` (existing). Upstream read timeout keeps
`timeout` mapping; deadline expiry is never labeled `timeout` (it is a
local budget decision, distinct category). Propose a future stream-idle
rule (e.g., N seconds without a chunk, owner-set) as follow-up, not in
the initial change.

## 6. Error/cancellation semantics

New category `deadline_exceeded` only; 503 pre-byte (existing
unavailable family — no novel 504); post-byte no status possible.
CancelledError vs TimeoutError kept distinct by exception type, with an
explicit generator branch for the latter (required fix noted in §1).
Malformed-200, health, usage-null, finalize-once rules unchanged.

## 7. Retry comparison (unchanged findings)

Defaults (3×), r1 (2×), r0 (1×) per proxy inbound — measured. 401 never
retried; 429 unmeasured. Deadline and retry budget are orthogonal: the
deadline bounds SabiRoute waiting; it cannot un-execute upstream work
(stated constraint). Selective per-status proxy retries do not exist in
the pinned version.

## 8. Regression coverage & locations

All in `tests/test_completions.py` (gateway path) plus refresh of the
`tests/test_proxy_attempt_census.py` timeout tests: middleware expiry
pre-route, expiry mid-await, expiry between fallbacks, no-start-past-
expiry, cancel-vs-deadline distinction, pre/post-byte streaming expiry,
disconnect, finalize-once, null-usage, malformed-200 intact, health
intact, trickle-stream termination. Fake monotonic clock + controlled
hanging/reset transports; zero sleep-based assertions. New middleware
needs its own unit tests (no-gateway-needed scope construction).

## 9. Unknowns & measurements still required

Provider-side timing/billing; multi-worker; live distributions for
tuning 300s; openai-constant in-image (behaviorally covered); 429 proxy
count (lab follow-up proposed).

## 10. Owner decisions required before implementation

(1) Architecture D-minimal as specified; (2) 300s default; (3) post-byte
truncation rule + future idle policy; (4) r1 vs r0 (with 429 caveat);
(5) 429-closing lab run; (6) any implementation, proxy change, or push.
