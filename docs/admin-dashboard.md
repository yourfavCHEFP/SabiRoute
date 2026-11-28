# SabiRoute Console (Phase 15)

A single-page, **read-only** console over the five admin endpoints that already
exist and are already authenticated. It is the page titled "SabiRoute Console"
served for Phase 15.

| Region | Source endpoint | Renders |
|---|---|---|
| Sidebar | — | wordmark, route search, five section links with an active rail |
| Verdict | `GET /admin/health`, `GET /admin/latency`, `GET /admin/metrics` | one display-size sentence: deployments available, failures in the poll window, the weighted gateway mean, and the names of DOWN/HELD routes |
| Ribbon | `GET /admin/metrics` | REQUESTS SINCE START, SUCCESS, FAILED, RATE-LIMITED — one flat row, no tiles, no sparklines |
| Routes table | `GET /admin/health` + `GET /admin/latency` | **one row per deployment**: ROUTE · STATE · OK · FAIL · REL · AVG · LAST · HOLD |
| Errors | `GET /admin/errors` | error category counts |
| Tokens by model | `GET /admin/usage` | total tokens by model |
| Traffic by model | `GET /admin/metrics` | per-model request counts |

It is authorised by the owner decision recorded in
`docs/architecture-decision-record.md` §7 (D9). It adds no new data surface,
no new authority, no new persistence, and no change to authentication. It does
not weaken admin authentication, does not expose provider credentials, and does
not bypass budgets, rate limits, capability filtering, or health filtering.

## Console v2

The page is one flat surface with hairline hierarchy, not a dashboard of cards.
It is built to `artifacts/console-v2-visual-spec-20261128.md`, as corrected by
the seven corrections and the D9 ruling in the approval ticket.

- **One table, one row per deployment.** Health and latency are joined on
  deployment name. Both payloads are flat objects keyed by that name, so the
  join is exact and costs no request. A latency record with no health record is
  a registry fault: it lands in the second `<tbody>` with `NO HEALTH`, never
  dropped and never folded into a second panel.
- **Reachability vocabulary.** `HELD` (cooldown), `DOWN` (`available: false`),
  `DEGRADED` (`healthy: false`), `UP`. Cooldown is tested first, so a
  deployment that is both unavailable and cooling reads `HELD`. Rows sort by
  state severity — DOWN, HELD, DEGRADED, UP — then by name.
- **The clock touches one text node per held route.** The one-second tick
  rewrites the HOLD cells it collected at render time. It never re-renders, so
  the filter, the scroll position and the section observer are untouched.
  `tests/test_phase15_console_routing_table.py` proves this by row identity:
  the row objects are the same objects after the tick, and the countdown text
  has advanced.
- **No sparklines, no tiles, no bars.** The admin endpoints report cumulative
  counters, not a time series, so a sparkline would describe a polling window
  while looking like traffic. The ribbon is a row of figures; the one trend
  available (state severity) is carried by sort order.
- **The orbit field.** A canvas in the content column draws four tilted
  elliptical rings of nodes with a fixed seeded geometry and a
  `--lime` accent count derived from the up ratio. It is one decorative layer,
  `aria-hidden="true"`, `pointer-events: none`, capped at 14% opacity and faded
  toward the table inside the canvas. It animates at 30fps, pauses on a hidden
  tab, caps device pixel ratio at 2, and **starts no animation loop at all**
  under `prefers-reduced-motion: reduce` (one frame at t = 0) or in **light
  mode** — the field is a dark-mode object and the light palette would turn it
  into a dark smudge.
- **Nothing animates that is not specified to.** Transitions are
  `cubic-bezier(0.32, 0.72, 0, 1)` at 120–180ms, and
  `prefers-reduced-motion: reduce` sets `none` rather than a shorter duration.
- **Type.** `--font-data` is the page — every number, identifier, column
  header and control. `--font-display` carries the display-size verdict, the
  wordmark, the nav labels and the one explanatory paragraph. All numerals are
  `tabular-nums lining-nums`.
- **Colour is rationed.** `--lime` appears only on the live dot, the active nav
  rail, the `UP` state, the orbit accents and the healthy verdict dot.
  `--warn`/`--bad` appear only where a value reports a state. The focus ring is
  `--text`, so lime stays a signal rather than decoration.
- **Nothing is hidden at any width.** Below 720px the sidebar becomes a 48px
  icon rail and the table scrolls horizontally with ROUTE pinned; no column is
  ever dropped.

Measured contrast (WCAG 2.1, computed from the shipped tokens): the smallest
labels are 5.11:1 in dark (`--text-3` on `--canvas`) and 5.15:1 in light;
`--text-2` is 7.53:1; `UP` is 4.91:1 in light. All clear AA for normal text,
which is the regression `611edd8` fixed and these tests hold.

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
  "That admin key was rejected (401). Paste a current key to reconnect.";
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

Behaviour is covered by four suites, **53 tests** in total:

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
  stated-preference media queries are present. Under D1 it asserts the stricter
  property: no `backdrop-filter` exists outside a `prefers-*` block, so a blur
  in the default path fails rather than being required.
- `tests/test_phase15_console_routing_table.py` — the merged table. Most of it
  runs `dashboard.js` in a stubbed DOM and inspects the rendered cells: one row
  per healthy deployment, a latency-only deployment in the second tbody with
  `NO HEALTH` and em dashes, one row carrying both health counters and observed
  latency in the specified order, the four reachability labels including
  cooldown-before-unavailable precedence, severity-then-name ordering, REL%
  thresholds, the weighted gateway mean, the filter across both tbodies, the
  stated empty case, the `/` focus guard, and the in-place countdown proved by
  row identity. The rest pins the structure and the design rules: two
  eight-column tbodies in one table, the four `stat-*` ids on the ribbon
  figures, no tiles, no sparklines, no shadow or gradient or blur, one
  decorative layer, dark as the base surface, a single transition curve, and no
  column ever dropped.

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

**2026-11-28 — second revision.** The console was rebuilt with its own design
system, sparklines, a live cooldown countdown and staleness labelling, and its
rendered DOM was asserted in headless Chrome against a stubbed server returning
the same fixture shapes.

**2026-11-28 — this revision (Console v2).** The four KPI tiles were removed,
health and latency were merged into one routing table with two tbodies, the
reachability vocabulary became `UP`/`DEGRADED`/`HELD`/`DOWN`, sparklines and
meters were deleted, and the visual system was replaced with the flat,
dark-first one above.

**Not yet done, and not claimed:** this revision has not been opened in a
browser. Its DOM behaviour is asserted by executing `dashboard.js` itself in
Node against a stub DOM (not by matching strings in it), and its stylesheet is
asserted structurally. Two visual judgements therefore remain open and belong to
the owner: whether the orbit field reads as an instrument panel rather than
noise at the shipped opacity, and whether the corrected 20px verdict floor
still fits the 728px content column at 1024px wide without wrapping. The
arithmetic behind that second one is the spec's measurement, not a rendered
one.
