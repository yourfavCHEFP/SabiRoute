# Admin Dashboard (Phase 15)

A single-page, **read-only** dashboard over the five admin endpoints that
already exist and are already authenticated:

| Panel | Source endpoint | Renders |
|---|---|---|
| Requests | `GET /admin/metrics` | totals, successful, failed, rate-limited, requests by model |
| Deployment health | `GET /admin/health` | per-deployment healthy/available, successes, failures, cooldown |
| Latency | `GET /admin/latency` | per-deployment samples, average ms, last ms |
| Error categories | `GET /admin/errors` | error category counts |
| Token usage | `GET /admin/usage` | total tokens by model |

It is authorised by the owner decision recorded in
`docs/architecture-decision-record.md` §7 (D9). It adds no new data surface,
no new authority, no new persistence, and no change to authentication. It does
not weaken admin authentication, does not expose provider credentials, and does
not bypass budgets, rate limits, capability filtering, or health filtering.

## Open it

1. Set the admin secret for the server process (variable **name** only — never
   commit a value):

   ```
   SABIROUTE_ADMIN_KEY=<your-admin-key>
   ```

2. Start the gateway as usual:

   ```
   sabiroute
   ```

3. Browse to:

   ```
   http://<host>:<port>/admin/dashboard/
   ```

4. Paste your admin key into the page and choose **Load dashboard**.

The page is served from the same FastAPI application that serves the API and
the SabiChat UI at `/app/`. It is a zero-build static bundle
(`web/dashboard/index.html`, `dashboard.js`, `dashboard.css`) — no bundler, no
external CDN, no third-party script.

## How authentication works

The dashboard does **not** bypass admin auth. The static page is a secret-free
shell; it is served without a credential, and it holds none. The operator
pastes their admin key into the page. The page:

- keeps the key in this tab's `sessionStorage` only (never `localStorage`,
  never a cookie);
- sends it as the normal `Authorization: Bearer <key>` header on each `GET`
  to `/admin/health`, `/admin/metrics`, `/admin/latency`, `/admin/errors`, and
  `/admin/usage`;
- shows a clear "paste your admin key" state on `401`, and a distinct message
  when admin authentication is unavailable (`503`).

Every data request therefore passes through the existing `require_admin_key`
dependency. The API's own behaviour is unchanged: the same endpoints return
`401` without a valid admin key, and remain the only path by which the
dashboard can read data.

## What it will not do

- No `POST`, `PUT`, `PATCH`, or `DELETE`. Nothing in the UI mutates gateway
  state; key management stays on the API.
- No credentials in HTML, JavaScript, CSS, logs, or committed files.
- No rendering by HTML-string injection — the page builds DOM nodes and writes
  text with `textContent`.

## Mount path

The dashboard is mounted at `/admin/dashboard`, beside the admin router rather
than over it, so it can never shadow `/admin/health` and friends. Requesting
the bare path `/admin/dashboard` (no trailing slash) redirects to
`/admin/dashboard/`.

Because the dashboard lives under `web/`, the existing `/app` mount also serves
it at `/app/dashboard/`. That is the same secret-free static shell and has no
additional access; the data endpoints are unaffected.

## Verification

Behaviour is covered by:

- `tests/test_phase15_dashboard_serving.py` — serving, content types, the
  mount not shadowing the API, and proof that admin authentication is
  unchanged (missing key, wrong key, and a valid *client* key all get `401`;
  the correct admin key gets `200`).
- `tests/test_phase15_dashboard_static.py` — no embedded secret, session
  storage only, read-only requests, endpoint references, safe DOM rendering,
  and a `node --check` syntax gate.

`dashboard.js` is plain JavaScript and passes `node --check`. CI currently runs
`node --check web/app.js` for the SabiChat bundle; extending that step to the
dashboard file is an owner/CI decision, so this change does not edit
`.github/**`.

## Browser verification (2026-11-23)

Performed in a real Chrome against a locally running server — not via
`TestClient`, which is what makes this live verification rather than a serving check.

Harness: `scripts/phase15_browser_verify.py` starts the real app with seeded
**fixture** telemetry so the page has something worth rendering. That data is a
UI fixture, not provider evidence; real provider telemetry was verified separately
in Phase 07 and Phase 12.

| Step | Observed |
|---|---|
| Load `/admin/dashboard/` | 200; title "SabiRoute Admin Dashboard"; 5 tables present |
| Unauthenticated | "Paste your admin key to load the dashboard." |
| Correct admin key | all five panels populated: 6 requests / 4 successful / 2 failed / 0 rate-limited; per-model request counts; deployment health including the cooldown column; per-deployment latency samples; error categories `server=1`, `auth=1`; token usage 110 / 44 / 80 / 60 |
| Wrong admin key | "Your admin key was rejected (401). Paste a valid admin key." with **zero rows populated** |

**Recorded minor issue:** after a 401 the rejected key remains in `sessionStorage`
under `sabirooute.adminKey` until the operator clears it. It is the operator's own
input in their own tab, so this is a UX wart rather than an exposure. It is
recorded rather than ignored.
