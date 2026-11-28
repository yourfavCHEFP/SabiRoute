/* SabiRoute gateway console.
 *
 * Read-only by construction: this file issues GET requests only, against the
 * five authenticated admin endpoints. It holds the operator's admin key in
 * this tab's session storage and sends it as a Bearer token per request. No
 * credential is ever written into the page, the URL, or a file.
 *
 * Rendering is text-only. Every node is built with createElement and filled
 * with textContent, so gateway-supplied strings can never become markup.
 *
 * Two rules govern the whole file, and both are easy to break by accident:
 *
 * 1. The one-second clock updates the HOLD cells' existing text nodes in
 *    place. It never calls render, so the filter, the scroll position and the
 *    observer are untouched sixty times a minute.
 * 2. Nothing animates that is not specified to animate. Data appears; it does
 *    not travel.
 */

"use strict";

(function () {
  var KEY_STORAGE = "sabiroute.console.admincredential";
  var POLL_MS = 15000;
  var STALE_MS = 45000;
  var DASH = "—";

  /* The orbit field ships behind this one constant. Set it to false and the
   * page is the same design with a still background. */
  var FIELD_ENABLED = true;

  var ENDPOINTS = {
    health: "/admin/health",
    metrics: "/admin/metrics",
    latency: "/admin/latency",
    errors: "/admin/errors",
    usage: "/admin/usage"
  };

  var previous = { total: null, failed: null, rateLimited: null, metrics: null };
  var lastLoad = 0;
  var pollTimer = null;
  var clockTimer = null;
  var loading = false;

  /* The merged deployment set, as last rendered. The filter and the sort both
   * read this rather than re-deriving from payloads. */
  var models = [];
  var sortMode = "severity";

  /* Live handles for the countdown: {el, until}. Nothing else is touched by
   * the tick. */
  var holds = [];

  function byId(id) {
    return document.getElementById(id);
  }

  var ui = {
    authPanel: byId("auth-panel"),
    authForm: byId("auth-form"),
    authKey: byId("admin-key"),
    authMessage: byId("auth-message"),
    authForget: byId("auth-forget"),
    dataView: byId("data-view"),
    banner: byId("status-banner"),
    live: byId("live-indicator"),
    liveLabel: byId("live-label"),
    refresh: byId("refresh"),
    signOut: byId("sign-out"),
    lastUpdated: byId("last-updated"),
    filter: byId("filter"),
    verdict: byId("verdict"),
    verdictText: byId("verdict-text"),
    healthBody: byId("health-body"),
    latencyBody: byId("latency-body"),
    errorsBody: byId("errors-body"),
    usageBody: byId("usage-body"),
    byModelBody: byId("by-model-body"),
    statTotal: byId("stat-total"),
    statSuccess: byId("stat-success"),
    statFailed: byId("stat-failed"),
    statRateLimited: byId("stat-rate-limited")
  };

  /* ---------- small DOM helpers ---------- */

  function node(tag, className, text) {
    var element = document.createElement(tag);
    if (className) {
      element.className = className;
    }
    if (text !== undefined && text !== null) {
      element.textContent = String(text);
    }
    return element;
  }

  function clear(element) {
    if (!element) {
      return;
    }
    if (typeof element.replaceChildren === "function") {
      element.replaceChildren();
      return;
    }
    while (element.firstChild) {
      element.removeChild(element.firstChild);
    }
  }

  function formatCount(value) {
    if (typeof value !== "number" || !isFinite(value)) {
      return "0";
    }
    return value.toLocaleString();
  }

  function formatCompact(value) {
    if (typeof value !== "number" || !isFinite(value)) {
      return "0";
    }
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
    }
    if (value >= 10000) {
      return (value / 1000).toFixed(1).replace(/\.0$/, "") + "k";
    }
    return formatCount(Math.round(value));
  }

  /* Table cells get the compact form: the column is 68px wide. */
  function formatMilliseconds(value) {
    if (typeof value !== "number" || !isFinite(value) || value < 0) {
      return DASH;
    }
    if (value >= 1000) {
      return (value / 1000).toFixed(1) + "s";
    }
    return Math.round(value) + "ms";
  }

  function formatRemaining(milliseconds) {
    var seconds = Math.ceil(milliseconds / 1000);
    if (seconds >= 60) {
      var minutes = Math.floor(seconds / 60);
      var rest = seconds % 60;
      return rest === 0 ? minutes + "m left" : minutes + "m " + rest + "s left";
    }
    return Math.max(seconds, 1) + "s left";
  }

  function percent(part, whole) {
    if (!whole || whole <= 0) {
      return null;
    }
    return Math.max(0, Math.min(100, (part / whole) * 100));
  }

  function asNumber(value) {
    var parsed = Number(value);
    return isFinite(parsed) ? parsed : null;
  }

  /* ---------- credential handling ---------- */

  function readKey() {
    try {
      return sessionStorage.getItem(KEY_STORAGE) || "";
    } catch (error) {
      return "";
    }
  }

  function writeKey(value) {
    try {
      sessionStorage.setItem(KEY_STORAGE, value);
    } catch (error) {
      /* Session storage can be unavailable in hardened browsers. The console
       * still works for this page view; the key simply is not remembered. */
    }
  }

  function dropKey() {
    try {
      sessionStorage.removeItem(KEY_STORAGE);
    } catch (error) {
      /* Nothing to clean up. */
    }
  }

  /* ---------- transport ---------- */

  function getJson(path) {
    return fetch(path, {
      method: "GET",
      headers: {
        Authorization: "Bearer " + readKey(),
        Accept: "application/json"
      },
      cache: "no-store",
      credentials: "omit"
    }).then(function (response) {
      if (response.status === 401) {
        throw { kind: "unauthorized", status: 401 };
      }
      if (!response.ok) {
        throw { kind: "http", status: response.status };
      }
      return response.json();
    });
  }

  function loadAll() {
    return Promise.all([
      getJson(ENDPOINTS.health),
      getJson(ENDPOINTS.metrics),
      getJson(ENDPOINTS.latency),
      getJson(ENDPOINTS.errors),
      getJson(ENDPOINTS.usage)
    ]);
  }

  /* ---------- chrome state ---------- */

  function setLive(state, label) {
    if (ui.live) {
      ui.live.setAttribute("data-state", state);
    }
    if (ui.liveLabel) {
      ui.liveLabel.textContent = label;
    }
  }

  function showBanner(message) {
    if (!ui.banner) {
      return;
    }
    ui.banner.textContent = message;
    ui.banner.hidden = false;
  }

  function hideBanner() {
    if (ui.banner) {
      ui.banner.hidden = true;
      ui.banner.textContent = "";
    }
  }

  function showAuth(message) {
    if (ui.authPanel) {
      ui.authPanel.hidden = false;
    }
    if (ui.dataView) {
      ui.dataView.hidden = true;
    }
    if (ui.authForget) {
      ui.authForget.hidden = true;
    }
    if (message && ui.authMessage) {
      ui.authMessage.textContent = message;
    }
    if (ui.authKey) {
      ui.authKey.focus();
    }
  }

  function showData() {
    if (ui.authPanel) {
      ui.authPanel.hidden = true;
    }
    if (ui.dataView) {
      ui.dataView.hidden = false;
    }
  }

  function setBusy(busy) {
    if (!ui.refresh) {
      return;
    }
    ui.refresh.disabled = busy;
    ui.refresh.textContent = busy ? "Refreshing" : "Refresh";
  }

  /* ---------- reachability ---------- */

  /* The four labels are a display vocabulary over the existing health
   * conditions. Cooldown is tested first, so a deployment that is both
   * unavailable and cooling down reads HELD, not DOWN. That precedence is
   * inherited and must not drift: changing it would change the routing
   * readout, which is behaviour and not a restyle. */
  function healthState(entry, now) {
    var when = typeof now === "number" ? now : Date.now();
    if (!entry) {
      return { label: "DOWN", kind: "bad", rank: 0 };
    }
    var until = entry.cooldown_until ? Date.parse(entry.cooldown_until) : NaN;
    if (!isNaN(until) && until > when) {
      return { label: "HELD", kind: "warn", rank: 1 };
    }
    if (entry.available === false) {
      return { label: "DOWN", kind: "bad", rank: 0 };
    }
    if (entry.healthy === false) {
      return { label: "DEGRADED", kind: "warn", rank: 2 };
    }
    return { label: "UP", kind: "ok", rank: 3 };
  }

  /* ---------- the merged deployment set ---------- */

  /* /admin/health and /admin/latency are both flat objects keyed by
   * deployment name, so the join is exact and costs no extra request. A
   * latency record with no health record is a registry fault and is kept, not
   * dropped. */
  function merge(health, latency) {
    var records = health && typeof health === "object" ? health : {};
    var observed = latency && typeof latency === "object" ? latency : {};
    var merged = [];
    var name;

    for (name in records) {
      if (Object.prototype.hasOwnProperty.call(records, name)) {
        merged.push({
          name: name,
          health: records[name] || {},
          latency: Object.prototype.hasOwnProperty.call(observed, name) ? observed[name] : null,
          orphan: false
        });
      }
    }

    for (name in observed) {
      if (
        Object.prototype.hasOwnProperty.call(observed, name) &&
        !Object.prototype.hasOwnProperty.call(records, name)
      ) {
        merged.push({ name: name, health: null, latency: observed[name] || {}, orphan: true });
      }
    }

    return merged;
  }

  function averageOf(record) {
    return record ? asNumber(record.average_ms) : null;
  }

  function compareNames(a, b) {
    return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
  }

  function compareModels(a, b) {
    if (sortMode === "avg") {
      var left = averageOf(a.latency);
      var right = averageOf(b.latency);
      /* A route with no latency sample sorts last: it is not fast, it is
       * unknown. */
      if (left === null && right === null) {
        return compareNames(a, b);
      }
      if (left === null) {
        return 1;
      }
      if (right === null) {
        return -1;
      }
      if (right !== left) {
        return right - left;
      }
      return compareNames(a, b);
    }

    var leftRank = a.orphan ? 4 : healthState(a.health, Date.now()).rank;
    var rightRank = b.orphan ? 4 : healthState(b.health, Date.now()).rank;
    if (leftRank !== rightRank) {
      return leftRank - rightRank;
    }
    return compareNames(a, b);
  }

  /* ---------- one row ---------- */

  function buildRow(model) {
    var state = model.orphan
      ? { label: "NO HEALTH", kind: "warn", rank: 4 }
      : healthState(model.health, Date.now());

    var row = document.createElement("tr");
    row.setAttribute("data-state", state.kind);
    if (model.orphan) {
      row.setAttribute("data-orphan", "true");
    }
    /* A broken or held route is dimmed in column one, so it is visible while
     * the eye is still on the names. */
    if (!model.orphan && (state.label === "DOWN" || state.label === "HELD")) {
      row.setAttribute("data-dim-route", "true");
    }

    var routeCell = node("td", "route-cell");
    if (model.orphan) {
      routeCell.setAttribute("data-tone", "warn");
    }
    routeCell.textContent = model.name;
    row.appendChild(routeCell);

    var stateCell = node("td", "state-cell");
    var word = node("span", "state-word", state.label);
    word.setAttribute("data-state", state.kind);
    stateCell.appendChild(word);
    row.appendChild(stateCell);

    var successes = model.health ? asNumber(model.health.total_successes) : null;
    var failures = model.health ? asNumber(model.health.total_failures) : null;

    row.appendChild(counterCell(successes));
    row.appendChild(counterCell(failures));

    var attempts = (successes || 0) + (failures || 0);
    var ratio = model.health ? percent(successes || 0, attempts) : null;
    var relCell = node("td", "num");
    if (ratio === null) {
      relCell.className = "num is-idle";
      relCell.textContent = DASH;
    } else {
      relCell.textContent = ratio.toFixed(1);
      if (ratio < 70) {
        relCell.setAttribute("data-tone", "bad");
      } else if (ratio < 90) {
        relCell.setAttribute("data-tone", "warn");
      }
    }
    row.appendChild(relCell);

    row.appendChild(dimensionCell(model.latency, "average_ms"));
    row.appendChild(dimensionCell(model.latency, "last_ms"));

    /* HOLD: the only cell that changes every second. The tick below rewrites
     * this node's text and nothing else. */
    var holdCell = node("td", "num");
    var until = model.health && model.health.cooldown_until ? Date.parse(model.health.cooldown_until) : NaN;
    if (!isNaN(until) && until > Date.now()) {
      var clock = node("span", null, formatRemaining(until - Date.now()));
      clock.setAttribute("data-until", model.health.cooldown_until);
      holdCell.appendChild(clock);
      holds.push({ el: clock, until: until });
    } else {
      holdCell.className = "num is-idle";
      holdCell.textContent = DASH;
    }
    row.appendChild(holdCell);

    return row;
  }

  function counterCell(value) {
    var cell = node("td", "num");
    if (value === null) {
      cell.className = "num is-idle";
      cell.textContent = DASH;
      return cell;
    }
    cell.textContent = formatCount(value);
    return cell;
  }

  function dimensionCell(record, field) {
    var cell = node("td", "num");
    var value = record ? asNumber(record[field]) : null;
    if (value === null) {
      cell.className = "num is-idle";
      cell.textContent = DASH;
      return cell;
    }
    cell.textContent = formatMilliseconds(value);
    return cell;
  }

  function emptyRow(message) {
    var row = document.createElement("tr");
    row.className = "empty-row";
    var cell = node("td", null, message);
    cell.setAttribute("colspan", "8");
    row.appendChild(cell);
    return row;
  }

  /* ---------- the table ---------- */

  function renderTable() {
    clear(ui.healthBody);
    clear(ui.latencyBody);
    holds.length = 0;

    var query = ui.filter && ui.filter.value ? String(ui.filter.value).trim().toLowerCase() : "";
    var visible = models.filter(function (model) {
      return !query || model.name.toLowerCase().indexOf(query) !== -1;
    });
    visible.sort(compareModels);

    var healthy = 0;
    var orphaned = 0;

    visible.forEach(function (model) {
      var row = buildRow(model);
      if (model.orphan) {
        if (ui.latencyBody) {
          ui.latencyBody.appendChild(row);
        }
        orphaned += 1;
      } else {
        if (ui.healthBody) {
          ui.healthBody.appendChild(row);
        }
        healthy += 1;
      }
    });

    if (healthy === 0 && orphaned === 0 && ui.healthBody) {
      ui.healthBody.appendChild(
        emptyRow(query ? "No route matches" : "No deployments reporting")
      );
    }
  }

  /* The countdown. This writes text into handles collected when the rows were
   * built; it never rebuilds a row, never re-runs the filter, and never
   * touches the observer. */
  function tick() {
    var now = Date.now();
    /* A reading older than the stale window stops claiming to be live even if
     * no poll has failed yet. */
    if (lastLoad && now - lastLoad > STALE_MS && ui.live && ui.live.getAttribute("data-state") === "ok") {
      setLive("stale", "Stale");
    }
    if (!holds.length) {
      return;
    }
    for (var index = 0; index < holds.length; index += 1) {
      var hold = holds[index];
      var remaining = hold.until - now;
      hold.el.textContent = remaining > 0 ? formatRemaining(remaining) : "0s left";
    }
  }

  /* ---------- verdict ---------- */

  function renderVerdict() {
    var configured = models.filter(function (model) {
      return !model.orphan;
    });
    var available = configured.filter(function (model) {
      return model.health && model.health.available !== false;
    }).length;

    var window = Math.round(POLL_MS / 1000) + "s";
    var failed = previous.metrics ? asNumber(previous.metrics.requests_failed) : null;
    var deltaFailed =
      previous.failed === null || failed === null ? 0 : Math.max(0, failed - previous.failed);

    /* A gateway mean, weighted by sample count, so one loud deployment cannot
     * drag the number on its own. */
    var weighted = 0;
    var weight = 0;
    models.forEach(function (model) {
      var record = model.latency;
      if (!record) {
        return;
      }
      var samples = asNumber(record.samples) || 0;
      var average = asNumber(record.average_ms);
      if (samples > 0 && average !== null && average >= 0) {
        weighted += average * samples;
        weight += samples;
      }
    });
    var meanMs = weight > 0 ? weighted / weight : null;

    var parts = [];
    if (!configured.length) {
      /* The console cannot see config/config.yaml, so it must not claim to
       * know what is configured. An empty /admin/health means only that
       * nothing is reporting — which is also true when fourteen deployments
       * are configured and none has an observation yet. */
      parts.push("No deployments reporting");
    } else {
      parts.push(available + "/" + configured.length + " deployments available");
    }
    parts.push(
      deltaFailed > 0
        ? deltaFailed + " failed in the last " + window
        : "no failures in the last " + window
    );
    if (meanMs !== null) {
      parts.push("avg " + Math.round(meanMs) + " ms");
    }

    /* Name the routes that need a human, up to three. At 2am "3/6 available"
     * is a number; "gw-delta" is an instruction. */
    var attention = configured
      .filter(function (model) {
        var state = healthState(model.health, Date.now());
        return state.label === "DOWN" || state.label === "HELD";
      })
      .map(function (model) {
        return model.name;
      });
    if (attention.length) {
      var named = attention.slice(0, 3).join(", ");
      var rest = attention.length - 3;
      parts.push(rest > 0 ? named + " +" + rest + " more" : named);
    }

    var tone = "ok";
    if (!configured.length || available < configured.length || deltaFailed > 0) {
      tone = "warn";
    }
    if (configured.length > 0 && available === 0) {
      tone = "bad";
    }
    if (ui.verdict) {
      ui.verdict.setAttribute("data-tone", tone);
    }

    clear(ui.verdictText);
    parts.forEach(function (part, index) {
      if (index > 0) {
        ui.verdictText.appendChild(node("span", "verdict-sep"));
      }
      ui.verdictText.appendChild(node("span", "verdict-part", part));
    });
  }

  /* ---------- ribbon ---------- */

  function renderRibbon(metrics) {
    if (!metrics) {
      return;
    }
    var total = asNumber(metrics.requests_total) || 0;
    var successful = asNumber(metrics.requests_successful) || 0;
    var failed = asNumber(metrics.requests_failed) || 0;
    var limited = asNumber(metrics.requests_rate_limited) || 0;
    var rate = percent(successful, total);

    if (ui.statTotal) {
      ui.statTotal.textContent = formatCount(total);
    }
    if (ui.statSuccess) {
      ui.statSuccess.textContent = rate === null ? DASH : rate.toFixed(1) + "%";
    }
    if (ui.statFailed) {
      ui.statFailed.textContent = formatCount(failed);
    }
    if (ui.statRateLimited) {
      ui.statRateLimited.textContent = formatCount(limited);
    }
  }

  /* ---------- secondary ledgers ---------- */

  function renderLedger(body, entries, formatter) {
    clear(body);
    if (!body || !entries || typeof entries !== "object") {
      return;
    }
    var names = Object.keys(entries).sort();
    if (!names.length) {
      var empty = document.createElement("tr");
      var emptyCell = node("td", "is-idle", DASH);
      emptyCell.setAttribute("colspan", "2");
      empty.appendChild(emptyCell);
      body.appendChild(empty);
      return;
    }
    names.forEach(function (name) {
      var row = document.createElement("tr");
      row.appendChild(node("td", null, name));
      row.appendChild(node("td", "num", formatter(asNumber(entries[name]))));
      body.appendChild(row);
    });
  }

  function renderSecondary(metrics, errors, usage) {
    renderLedger(ui.errorsBody, errors, formatCount);
    renderLedger(ui.usageBody, usage, function (value) {
      return value === null ? DASH : formatCompact(value);
    });
    renderLedger(ui.byModelBody, metrics ? metrics.requests_by_model : null, formatCount);
  }

  /* ---------- the orbit field ---------- */

  var field = (function () {
    /* 64-bit seed, folded to the 32 bits mulberry32 takes. A fixed seed is
     * what makes the field a designed object rather than a random emitter. */
    var SEED_HIGH = 0x5a9b1c3d;
    var SEED_LOW = 0x2f6e8a41;

    var RADII = [0.3, 0.47, 0.64, 0.83];
    var TILTS = [-8, -3, 4, 9];
    var COUNTS = [12, 15, 17, 20];
    var PERIODS = [46, 54, 64, 78];
    /* The two outer rings are the fainter pair. */
    var ALPHAS = [0.14, 0.14, 0.1, 0.1];
    var YSCALE = 0.58;

    var canvas = null;
    var ctx = null;
    var layer = null;
    var scrim = null;
    var cssWidth = 0;
    var cssHeight = 0;
    var nodes = [];
    var accents = 4;
    var rafId = null;
    var lastFrame = 0;
    var elapsed = 0;
    var running = false;
    var started = false;

    function mulberry32(seed) {
      var state = seed >>> 0;
      return function () {
        state = (state + 0x6d2b79f5) >>> 0;
        var t = state;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };
    }

    function seedNodes(random) {
      nodes = [];
      for (var ring = 0; ring < COUNTS.length; ring += 1) {
        for (var index = 0; index < COUNTS[ring]; index += 1) {
          nodes.push({
            ring: ring,
            theta0: random() * Math.PI * 2,
            radius: RADII[ring] * (0.965 + random() * 0.07),
            dot: 1 + random() * 0.7,
            phi: random() * Math.PI * 2
          });
        }
      }
    }

    function centre() {
      return { x: cssWidth * 0.78, y: cssHeight * 0.34 };
    }

    function rasterise() {
      /* The rings never move, so they are painted once into an offscreen
       * canvas and blitted per frame. Only a resize redoes this. */
      if (typeof document.createElement !== "function") {
        return;
      }
      layer = document.createElement("canvas");
      if (typeof layer.getContext !== "function") {
        layer = null;
        return;
      }
      layer.width = Math.max(1, Math.round(cssWidth * 2));
      layer.height = Math.max(1, Math.round(cssHeight * 2));
      var paint = layer.getContext("2d");
      if (!paint) {
        layer = null;
        return;
      }
      paint.setTransform(2, 0, 0, 2, 0, 0);
      var origin = centre();
      var half = Math.min(cssWidth, cssHeight) / 2;
      for (var ring = 0; ring < RADII.length; ring += 1) {
        paint.beginPath();
        paint.ellipse(
          origin.x,
          origin.y,
          half * RADII[ring],
          half * RADII[ring] * YSCALE,
          (TILTS[ring] * Math.PI) / 180,
          0,
          Math.PI * 2
        );
        paint.strokeStyle = "rgba(200, 255, 122, " + ALPHAS[ring] + ")";
        paint.lineWidth = 1;
        paint.stroke();
      }
    }

    function drawAt(seconds) {
      if (!ctx) {
        return;
      }
      ctx.clearRect(0, 0, cssWidth, cssHeight);
      if (layer) {
        ctx.drawImage(layer, 0, 0, cssWidth, cssHeight);
      }
      var origin = centre();
      var half = Math.min(cssWidth, cssHeight) / 2;
      for (var index = 0; index < nodes.length; index += 1) {
        var item = nodes[index];
        var direction = item.ring % 2 === 0 ? 1 : -1;
        var theta = item.theta0 + direction * ((Math.PI * 2 * seconds) / PERIODS[item.ring]);
        var radius =
          item.radius * half * (1 + 0.014 * Math.sin((Math.PI * 2 * seconds) / 96 + item.phi));
        var tilt = (TILTS[item.ring] * Math.PI) / 180;
        var dx = Math.cos(theta) * radius;
        var dy = Math.sin(theta) * radius * YSCALE;
        var x = origin.x + dx * Math.cos(tilt) - dy * Math.sin(tilt);
        var y = origin.y + dx * Math.sin(tilt) + dy * Math.cos(tilt);
        var lit = index < accents;
        ctx.beginPath();
        ctx.arc(x, y, lit ? 2.2 : item.dot, 0, Math.PI * 2);
        ctx.fillStyle = lit ? "#c8ff7a" : "rgba(200, 255, 122, 0.55)";
        ctx.fill();
      }

      /* The scrim. Destination-in against a vertical gradient thins the field
       * toward the deployment table, so it never sits behind dense data at
       * reading strength. Applied here rather than in the stylesheet so the
       * decorative layer stays one object with one fade. */
      if (scrim) {
        ctx.globalCompositeOperation = "destination-in";
        ctx.fillStyle = scrim;
        ctx.fillRect(0, 0, cssWidth, cssHeight);
        ctx.globalCompositeOperation = "source-over";
      }
    }

    function frame(stamp) {
      rafId = window.requestAnimationFrame(frame);
      /* 30fps cap by accumulator: a 144Hz display must not get 144 frames. */
      if (stamp - lastFrame < 33) {
        return;
      }
      elapsed += (stamp - lastFrame) / 1000;
      lastFrame = stamp;
      drawAt(elapsed);
    }

    function start() {
      if (running || typeof window.requestAnimationFrame !== "function") {
        return;
      }
      running = true;
      lastFrame =
        typeof performance === "object" && performance.now ? performance.now() : Date.now();
      rafId = window.requestAnimationFrame(frame);
    }

    function stop() {
      running = false;
      if (rafId !== null && typeof window.cancelAnimationFrame === "function") {
        window.cancelAnimationFrame(rafId);
      }
      rafId = null;
    }

    function measure() {
      if (!canvas) {
        return;
      }
      var box = canvas.getBoundingClientRect ? canvas.getBoundingClientRect() : null;
      cssWidth = Math.max(1, Math.round((box && box.width) || canvas.clientWidth || 1));
      cssHeight = Math.max(1, Math.round((box && box.height) || canvas.clientHeight || 520));
      var ratio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(cssWidth * ratio);
      canvas.height = Math.round(cssHeight * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      scrim = ctx.createLinearGradient(0, 0, 0, cssHeight);
      scrim.addColorStop(0, "rgba(0, 0, 0, 1)");
      scrim.addColorStop(1, "rgba(0, 0, 0, 0.25)");
      rasterise();
    }

    function init() {
      if (!FIELD_ENABLED || started) {
        return;
      }
      canvas = byId("field");
      if (!canvas || typeof canvas.getContext !== "function") {
        return;
      }
      /* Dark mode only. In light mode the field is not started at all. */
      if (typeof window.matchMedia === "function") {
        var dark = window.matchMedia("(prefers-color-scheme: dark)");
        if (dark && dark.matches === false) {
          return;
        }
      }
      ctx = canvas.getContext("2d");
      if (!ctx) {
        return;
      }
      started = true;

      var random = mulberry32((SEED_HIGH ^ ((SEED_LOW << 16) | (SEED_LOW >>> 16))) >>> 0);
      seedNodes(random);
      measure();

      var reduced =
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches === true;

      if (reduced) {
        /* Exactly one frame at t = 0, then nothing. No loop is started. */
        drawAt(0);
        return;
      }

      start();

      if (typeof document.addEventListener === "function") {
        document.addEventListener("visibilitychange", function () {
          if (document.visibilityState === "hidden") {
            stop();
          } else {
            start();
          }
        });
      }

      if (typeof window.ResizeObserver === "function" && canvas.parentNode) {
        var observer = new window.ResizeObserver(function () {
          measure();
          if (!running) {
            drawAt(elapsed);
          }
        });
        observer.observe(canvas);
      } else if (typeof window.addEventListener === "function") {
        window.addEventListener("resize", measure);
      }
    }

    return {
      init: init,
      /* A coarse readout of the up ratio, not a census of live deployments:
       * the count is a clamped map of the ratio into [3, 7]. */
      setAccents: function (up, total) {
        if (!started) {
          return;
        }
        if (!total) {
          accents = 4;
          return;
        }
        accents = Math.max(3, Math.min(7, Math.round(3 + (4 * up) / total)));
      }
    };
  })();

  /* ---------- render ---------- */

  function render(payloads) {
    var health = payloads[0] || {};
    var metrics = payloads[1] || {};
    var latency = payloads[2] || {};
    var errors = payloads[3] || {};
    var usage = payloads[4] || {};

    models = merge(health, latency);

    /* The verdict reports the failure delta for this polling window, so it
     * must read the counters from the previous poll. Advance them afterwards,
     * never before. */
    renderVerdict();
    previous.metrics = metrics;
    previous.total = asNumber(metrics.requests_total);
    previous.failed = asNumber(metrics.requests_failed);
    previous.rateLimited = asNumber(metrics.requests_rate_limited);

    renderRibbon(metrics);
    renderTable();
    renderSecondary(metrics, errors, usage);

    var configured = models.filter(function (model) {
      return !model.orphan;
    });
    var up = configured.filter(function (model) {
      return model.health && model.health.available !== false;
    }).length;
    field.setAccents(up, configured.length);

    if (ui.lastUpdated) {
      ui.lastUpdated.textContent = "Updated " + new Date().toLocaleTimeString();
    }
  }

  function load() {
    if (loading) {
      return;
    }
    loading = true;
    setBusy(true);
    lastLoad = Date.now();

    loadAll()
      .then(function (payloads) {
        hideBanner();
        render(payloads);
        setLive("ok", "Live");
        showData();
      })
      .catch(function (error) {
        if (error && error.kind === "unauthorized") {
          dropKey();
          setLive("error", "Key rejected");
          showAuth("That admin key was rejected (401). Paste a current key to reconnect.");
          return;
        }
        /* A stale reading stays labelled rather than passing for current. */
        setLive("stale", "Stale");
        var status = error && error.status ? error.status : "unknown";
        showBanner(
          "Could not read the gateway (status " +
            status +
            "). The last figures stay on screen until the next successful poll."
        );
        if (ui.lastUpdated) {
          ui.lastUpdated.textContent = "Stale since " + new Date().toLocaleTimeString();
        }
      })
      .then(function () {
        loading = false;
        setBusy(false);
      });
  }

  function startPolling() {
    if (pollTimer) {
      window.clearInterval(pollTimer);
    }
    pollTimer = window.setInterval(function () {
      /* A hidden tab does not poll: nothing is being read, so nothing is
       * gained by spending the request. */
      if (document.visibilityState === "visible") {
        load();
      }
    }, POLL_MS);
  }

  /* ---------- navigation ---------- */

  function setupNav() {
    var items =
      typeof document.querySelectorAll === "function" ? document.querySelectorAll(".nav-item") : [];

    Array.prototype.forEach.call(items, function (item) {
      item.addEventListener("click", function () {
        /* Latency is not a second table: it is the same table, sorted. */
        sortMode = item.getAttribute("data-sort") === "avg" ? "avg" : "severity";
        renderTable();
      });
    });

    if (typeof window.IntersectionObserver !== "function") {
      return;
    }
    var regions = ["overview", "routing", "errors", "tokens"]
      .map(function (name) {
        return byId(name);
      })
      .filter(Boolean);
    if (!regions.length) {
      return;
    }

    var observer = new window.IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) {
            return;
          }
          var id = entry.target.id;
          Array.prototype.forEach.call(items, function (item) {
            if (item.getAttribute("data-target") === id) {
              item.setAttribute("aria-current", "true");
            } else {
              item.removeAttribute("aria-current");
            }
          });
        });
      },
      { rootMargin: "-45% 0px -45% 0px" }
    );
    regions.forEach(function (region) {
      observer.observe(region);
    });
  }

  /* ---------- wiring ---------- */

  function onSubmit(event) {
    event.preventDefault();
    if (!ui.authKey) {
      return;
    }
    var value = ui.authKey.value.trim();
    if (!value) {
      if (ui.authMessage) {
        ui.authMessage.textContent = "Enter your admin key to connect.";
      }
      ui.authKey.focus();
      return;
    }
    writeKey(value);
    ui.authKey.value = "";
    if (ui.authForget) {
      ui.authForget.hidden = false;
    }
    showData();
    load();
  }

  function onForget() {
    dropKey();
    if (ui.authMessage) {
      ui.authMessage.textContent =
        "The key was forgotten for this tab. Paste it again to reconnect.";
    }
    showAuth();
    setLive("idle", "Not connected");
    clear(ui.healthBody);
    clear(ui.latencyBody);
    clear(ui.errorsBody);
    clear(ui.usageBody);
    clear(ui.byModelBody);
    models = [];
    holds.length = 0;
    previous.total = null;
    previous.failed = null;
    previous.rateLimited = null;
    previous.metrics = null;
    if (ui.lastUpdated) {
      ui.lastUpdated.textContent = "Not updated yet";
    }
  }

  function isTyping(target) {
    if (!target) {
      return false;
    }
    var tag = String(target.tagName || "").toUpperCase();
    return tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable === true;
  }

  function onKeydown(event) {
    if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey) {
      return;
    }
    /* The shortcut must not eat a "/" typed into the key field or into the
     * filter itself. */
    if (isTyping(document.activeElement)) {
      return;
    }
    /* At rail width the filter is not rendered, so there is nothing to focus
     * and the keystroke is left alone. */
    if (!ui.filter || ui.filter.offsetParent === null) {
      return;
    }
    event.preventDefault();
    ui.filter.focus();
  }

  function init() {
    if (ui.authForm) {
      ui.authForm.addEventListener("submit", onSubmit);
    }
    if (ui.authForget) {
      ui.authForget.addEventListener("click", onForget);
    }
    if (ui.signOut) {
      ui.signOut.addEventListener("click", onForget);
    }
    if (ui.refresh) {
      /* Re-fetch. Never reconstruct the page. */
      ui.refresh.addEventListener("click", function () {
        load();
      });
    }
    if (ui.filter) {
      ui.filter.addEventListener("input", function () {
        renderTable();
      });
    }

    document.addEventListener("keydown", onKeydown);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible" && Date.now() - lastLoad > POLL_MS) {
        load();
      }
    });

    setupNav();
    field.init();

    clockTimer = window.setInterval(tick, 1000);
    startPolling();

    if (readKey()) {
      showData();
      load();
    } else {
      showAuth();
      setLive("idle", "Not connected");
    }
  }

  init();
})();
