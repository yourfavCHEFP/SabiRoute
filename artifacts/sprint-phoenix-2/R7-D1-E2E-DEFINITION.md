# R7 D1 — E2E DEFINITION

**Authority:** Row D, Tranche D1. **Status:** DEFINED · NOT RUN.

No managed service, provider credential or GitHub workflow run is authorised. This is a definition
only.

## Scenarios

| ID | Scenario | Expected |
|---|---|---|
| E1 | `enabled=false`, ordinary chat request | Provider receives byte-identical original messages |
| E2 | `enabled=true`, compressible history | Message count shrinks; canonical bytes do not expand |
| E3 | Tool exchange present | Tool call and its results are removed together or retained together |
| E4 | Cached prefix present | No message up to and including the last `cache_control` breakpoint is modified |
| E5 | Required capability would be dropped | Original sent; reason `capability_loss` |
| E6 | Transform raises | Original sent; reason `transform_error` |
| E7 | Cancellation during transform | `CancelledError` propagates; no original fallback |
| E8 | Invalid policy at startup | Process fails at startup, not mid-request |

## Preconditions

- Fixed corpus version pinned by SHA-256.
- Stub provider captures exact bytes sent.
- No real provider, real Redis or managed PostgreSQL is contacted.

## Exit gate

E1–E8 pass under controlled replay with exact captured bytes. This definition does not authorise
executing them in CI or production.
