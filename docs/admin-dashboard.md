# SabiRoute Console (Phase 15)

A single-page, **read-only** console over the five admin endpoints that already
exist and are already authenticated. It is the page titled "SabiRoute Console"
served for Phase 15.

| Panel | Source endpoint | Renders |
|---|---|---|
| Request summary (4 tiles) | `GET /admin/metrics` | total, success rate, failures, rate-limited, each with a sparkline |
| Deployment health | `GET /admin/health` | per-deployment state, successes, failures, reliability, live cooldown countdown |
| Latency | `GET /admin/latency` | per-deployment samples, average ms, last ms |
| Errors | `GET /admin/errors` | error category counts |
| Tokens | `GET /admin/usage` | total tokens by model |
| Traffic by model | `GET /admin/metrics` | per-model request counts |

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
   http://127.0.0.1:<port>/admin/dashboard/
   ```

   The listener binds to loopback by default. ADR-010 (`docs/remote-access.md`)
   makes any non-loopback bind a startup error unless
   `SABIROUTE_ALLOW_NON_LOOPBACK_BIND=1` is set deliberately. To reach the
   console from another device, keep the loopback bind and put a private
   tailnet in front of it — `tailscale serve --bg --https=443
   http://127.0.0.1:8000` — or use an SSH tunnel. Do not widen the bind to
   reach this page.

4. Paste your admin key into the page and choose **Connect**.

The page is served from the same FastAPI application that serves the API and
the SabiChat UI at `/app/`. It is a zero-build static bundle
(`web/dashboard/index.html`, `dashboard.js`, `dashboard.css`) — no bundler, no
external CDN, no third-party script, no network request other than the five
admin endpoints.

## How authentication works

The console does **not** bypass admin auth. The static page is a secret-free
shell; it is served without a credential, and it holds none. The operator
pastes their admin key into the page. The page:

- keeps the key in this tab's `sessionStorage` only, under
  `sabiroute.console.admincredential` (never `localStorage`, never a cookie,
  never a URL, never a log);
- sends it as the normal `Authorization: Bearer <key>` header on each `GET`
  to `/admin/health`, `/admin/metrics`, `/admin/latency`, `/admin/errors`, and
  `/admin/usage`, with `credentials: "omit"` and `cache: "no-store"`;
- clears the key from storage when the server answers `401`, and shows
  "That admin key was rejected (401). Paste a valid admin key to continue.";
- offers **Forget key** in the top bar, which drops the stored key immediately.

Every data request therefore passes through the existing `require_admin_key`
dependency. The API's own behaviour is unchanged: the same endpoints return
`401` without a valid admin key, and remain the only path by which the console
can read data.

## Reading the numbers

Two conventions matter, because the admin endpoints report **cumulative**
counters, not time series:

- **The tile figure is cumulative.** "Requests" is every request since the
  process started, not since the page opened.
- **The sparkline is the polling window.** Each poll plots the delta since the
  previous poll, so a sparkline shows the shape of recent traffic and starts
  over on reload. The page says so beneath the summary strip. A counter reset
  clamps to zero rather than plotting a negative spike. The plot is anchored at
  zero, so a flat no-traffic line and a flat busy line do not look identical.

The page polls every 15 seconds and **pauses while the tab is hidden**. A
successful poll updates "Updated <time>". If nothing succeeds for 45 seconds the
live indicator reads **Stale** — the last figures stay on screen but are never
presented as current. A `403` or `5xx` raises a banner and keeps the last
figures. Cooldown times tick down once a second locally and read "recovering"
when they expire.

## What it will not do

- No `POST`, `PUT`, `PATCH`, or `DELETE`. Nothing in the UI mutates gateway
  state; key management stays on the API.
- No credentials in HTML, JavaScript, CSS, logs, or committed files.
- No rendering by HTML-string injection — the page builds DOM nodes with
  `createElement` and writes text with `textContent`. There is no `innerHTML`,
  `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval` or `new Function`
  in the bundle.

## Mount path

The console is mounted at `/admin/dashboard`, beside the admin router rather
than over it, so it can never shadow `/admin/health` and friends. Requesting
the bare path `/admin/dashboard` (no trailing slash) redirects to
`/admin/dashboard/`.

Because the dashboard lives under `web/`, the existing `/app` mount also serves
it at `/app/dashboard/`. That is the same secret-free static shell and has no
additional access; the data endpoints are unaffected.

Note that the console shares an origin with `/app` and `/docs`, so the key sits
in origin-scoped `sessionStorage`. Any script-execution bug in those surfaces
could read it. If the admin key is ever meant to outrank the chat UI, the
console belongs on its own origin rather than a path on this one. That is
recorded as a known limitation, not a property of this page.

## Verification

Behaviour is covered by three suites, **25 tests** in total:

- `tests/test_phase15_dashboard_serving.py` — serving, content types, the
  mount not shadowing the API, and proof that admin authentication is
  unchanged (missing key, wrong key, and a valid *client* key all get `401`;
  the correct admin key gets `200`).
- `tests/test_phase15_dashboard_static.py` — no embedded secret, session
  storage only, read-only requests, endpoint references, safe DOM rendering,
  and a `node --check` syntax gate.
- `tests/test_phase15_console_quality.py` — the page is self-contained (no
  `http`/`https`/CDN reference), the accessible skeleton holds (`scope="col"`,
  `aria-live`, `role="alert"`, a bound label, a password field), and the
  stated-preference media queries are present.

`dashboard.js` is plain JavaScript and passes `node --check`. CI currently runs
`node --check web/app.js` for the SabiChat bundle; extending that step to the
dashboard file is an owner/CI decision, so this change does not edit
`.github/**`.

## Browser verification

**2026-11-23 — previous console revision.** Performed in a real Chrome against a
locally running server, not via `TestClient`. Harness:
`scripts/phase15_browser_verify.py` starts the real app with seeded **fixture**
telemetry so the page has something worth rendering. That data is a UI fixture,
not provider evidence; real provider telemetry was verified separately in
Phase 07 and Phase 12. This run is what closed Phase 15.

**2026-11-28 — current revision.** The console was rebuilt (design system,
sparklines, live cooldown countdown, staleness labelling) and its rendered DOM
was asserted in headless Chrome against a stubbed server returning the same
fixture shapes: the tiles, the cooling-down state, the countdown, the latency
and token panels all rendered, and the live indicator settled on
`data-state="live"`. This is a DOM assertion, not an eyeball check — the visual
design has not yet been reviewed by the owner.
