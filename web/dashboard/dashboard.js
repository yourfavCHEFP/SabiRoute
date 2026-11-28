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
 * A note on the sparklines: the admin endpoints report cumulative counters,
 * not time series. Each poll appends the delta since the previous poll, so a
 * sparkline describes the polling window, not all-time traffic. The tile
 * figure is the cumulative number; the sparkline beneath it is the window, and
 * the note under the summary strip says so in the markup.
 */

"use strict";

(function () {
  var KEY_STORAGE = "sabiroute.console.admincredential";
  var POLL_MS = 15000;
  var STALE_MS = 45000;
  var SVG_NS = "http://www.w3.org/2000/svg";

  var ENDPOINTS = {
    health: "/admin/health",
    metrics: "/admin/metrics",
    latency: "/admin/latency",
    errors: "/admin/errors",
    usage: "/admin/usage"
  };

  var history = {
    total: [],
    successRate: [],
    failed: [],
    rateLimited: []
  };
  var previous = { total: null, failed: null, rateLimited: null };
  var lastLoad = 0;
  var pollTimer = null;
  var loading = false;
  var clockTimer = null;

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
    verdict: byId("verdict"),
    verdictText: byId("verdict-text"),
    healthBody: byId("health-body"),
    healthEmpty: byId("health-empty"),
    healthSummary: byId("health-summary"),
    latencyBody: byId("latency-body"),
    latencyEmpty: byId("latency-empty"),
    errorsBody: byId("errors-body"),
    errorsEmpty: byId("errors-empty"),
    usageBody: byId("usage-body"),
    usageEmpty: byId("usage-empty"),
    byModelBody: byId("by-model-body"),
    byModelEmpty: byId("by-model-empty"),
    statTotal: byId("stat-total"),
    statSuccess: byId("stat-success"),
    statFailed: byId("stat-failed"),
    statRateLimited: byId("stat-rate-limited"),
    sparkTotal: byId("spark-total"),
    sparkSuccess: byId("spark-success"),
    sparkFailed: byId("spark-failed"),
    sparkRateLimited: byId("spark-rate-limited")
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
    if (element) {
      element.replaceChildren();
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

  function formatMilliseconds(value) {
    if (typeof value !== "number" || !isFinite(value)) {
      return "—";
    }
    if (value >= 1000) {
      return (value / 1000).toFixed(2) + " s";
    }
    return Math.round(value) + " ms";
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
      return 0;
    }
    return Math.max(0, Math.min(100, (part / whole) * 100));
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

  /* ---------- sparklines ---------- */

  function drawSpark(container, series, colour) {
    if (!container) {
      return;
    }
    clear(container);
    container.style.color = colour || "";
    if (series.length < 2) {
      container.appendChild(node("div", "spark-empty"));
      return;
    }

    var width = 100;
    var height = 32;
    var pad = 3;
    // Anchor the domain at zero. Scaling to the series' own min/max makes a
    // flat zero and a flat three render identically, which would turn a trend
    // line into decoration.
    var max = Math.max.apply(null, series);
    var span = Math.max(max, 1);
    var step = width / (series.length - 1);
    var points = series.map(function (value, index) {
      var x = index * step;
      var y = height - pad - (value / span) * (height - pad * 2);
      return [x, y];
    });

    var line = points
      .map(function (point, index) {
        return (index === 0 ? "M" : "L") + point[0].toFixed(2) + " " + point[1].toFixed(2);
      })
      .join(" ");
    var area = line + " L " + width + " " + height + " L 0 " + height + " Z";

    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 " + width + " " + height);
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("role", "presentation");

    var areaPath = document.createElementNS(SVG_NS, "path");
    areaPath.setAttribute("d", area);
    areaPath.setAttribute("class", "spark-area");

    var linePath = document.createElementNS(SVG_NS, "path");
    linePath.setAttribute("d", line);
    linePath.setAttribute("class", "spark-line");

    svg.appendChild(areaPath);
    svg.appendChild(linePath);
    container.appendChild(svg);
  }

  function pushHistory(series, value, limit) {
    series.push(value);
    while (series.length > limit) {
      series.shift();
    }
  }

  /* ---------- tiles ---------- */

  function renderTiles(metrics) {
    var total = Number(metrics.requests_total) || 0;
    var successful = Number(metrics.requests_successful) || 0;
    var failed = Number(metrics.requests_failed) || 0;
    var limited = Number(metrics.requests_rate_limited) || 0;
    var rate = total > 0 ? (successful / total) * 100 : null;

    ui.statTotal.textContent = formatCount(total);
    ui.statSuccess.textContent = rate === null ? "—" : rate.toFixed(1) + "%";
    ui.statFailed.textContent = formatCount(failed);
    ui.statRateLimited.textContent = formatCount(limited);

    var deltaTotal = previous.total === null ? 0 : Math.max(0, total - previous.total);
    var deltaFailed = previous.failed === null ? 0 : Math.max(0, failed - previous.failed);
    var deltaLimited =
      previous.rateLimited === null ? 0 : Math.max(0, limited - previous.rateLimited);
    previous.total = total;
    previous.failed = failed;
    previous.rateLimited = limited;

    pushHistory(history.total, deltaTotal, 40);
    pushHistory(history.failed, deltaFailed, 40);
    pushHistory(history.rateLimited, deltaLimited, 40);
    pushHistory(history.successRate, rate === null ? 0 : rate, 40);

    drawSpark(ui.sparkTotal, history.total, "");
    drawSpark(ui.sparkSuccess, history.successRate, "");
    drawSpark(ui.sparkFailed, history.failed, history.failed.some(function (v) { return v > 0; }) ? "var(--bad)" : "");
    drawSpark(ui.sparkRateLimited, history.rateLimited, history.rateLimited.some(function (v) { return v > 0; }) ? "var(--warn)" : "");

    return { deltaTotal: deltaTotal, deltaFailed: deltaFailed };
  }

  /* ---------- verdict ---------- */

  // One line that answers the only question an operator has at 2am: is this
  // gateway healthy right now? Built from data already fetched — no endpoint.
  function renderVerdict(health, latency, summary) {
    if (!ui.verdict || !ui.verdictText) {
      return;
    }

    var deployments = (health && health.deployment) || {};
    var names = Object.keys(deployments);
    var available = names.filter(function (name) {
      var entry = deployments[name];
      return Boolean(entry) && entry.available !== false;
    }).length;

    var window = Math.round(POLL_MS / 1000) + "s";
    var deltaFailed = summary ? Number(summary.deltaFailed) || 0 : 0;

    // Weight each deployment's average by its sample count, so one loud
    // deployment cannot drag the number on its own.
    var weighted = 0;
    var weight = 0;
    var latencies = (latency && latency.deployment) || {};
    Object.keys(latencies).forEach(function (name) {
      var entry = latencies[name] || {};
      var count = Number(entry.samples) || 0;
      var average = Number(entry.average_ms);
      if (count > 0 && isFinite(average) && average >= 0) {
        weighted += average * count;
        weight += count;
      }
    });
    var meanMs = weight > 0 ? weighted / weight : null;

    var parts = [];
    parts.push(
      names.length === 0
        ? "No deployments configured"
        : available + "/" + names.length + " deployments available"
    );
    parts.push(
      deltaFailed > 0
        ? deltaFailed + " failed in the last " + window
        : "no failures in the last " + window
    );
    if (meanMs !== null) {
      parts.push("avg " + Math.round(meanMs) + " ms");
    }

    var tone = "ok";
    if (names.length === 0 || available < names.length || deltaFailed > 0) {
      tone = "warn";
    }
    if (names.length > 0 && available === 0) {
      tone = "bad";
    }
    ui.verdict.setAttribute("data-tone", tone);

    clear(ui.verdictText);
    parts.forEach(function (part, index) {
      if (index > 0) {
        ui.verdictText.appendChild(node("span", "verdict-sep", "·"));
      }
      ui.verdictText.appendChild(node("span", "verdict-part", part));
    });
  }

  /* ---------- health ---------- */

  function healthState(entry) {
    var now = Date.now();
    var cooling = false;
    if (entry.cooldown_until) {
      var until = Date.parse(entry.cooldown_until);
      cooling = isFinite(until) && until > now;
    }
    if (cooling) {
      return { label: "Cooling down", kind: "warn" };
    }
    if (entry.available === false) {
      return { label: "Unavailable", kind: "bad" };
    }
    if (entry.healthy === false) {
      return { label: "Unhealthy", kind: "warn" };
    }
    return { label: "Available", kind: "ok" };
  }

  function renderHealth(health) {
    clear(ui.healthBody);
    var names = Object.keys(health || {}).sort();
    ui.healthEmpty.hidden = names.length > 0;

    var available = 0;
    names.forEach(function (name) {
      var entry = health[name] || {};
      if (entry.available !== false) {
        available += 1;
      }
      var state = healthState(entry);

      var row = document.createElement("tr");

      var nameCell = node("td");
      nameCell.appendChild(node("span", "name", name));
      row.appendChild(nameCell);

      var stateCell = node("td");
      var stateNode = node("span", "state", state.label);
      stateNode.setAttribute("data-state", state.kind);
      stateCell.appendChild(stateNode);
      if (entry.cooldown_until) {
        var until = Date.parse(entry.cooldown_until);
        if (isFinite(until) && until > Date.now()) {
          var countdown = node("span", "countdown", "");
          countdown.setAttribute("data-until", entry.cooldown_until);
          stateCell.appendChild(document.createTextNode(" "));
          stateCell.appendChild(countdown);
        }
      }
      row.appendChild(stateCell);

      row.appendChild(node("td", "num", formatCount(Number(entry.total_successes) || 0)));
      row.appendChild(node("td", "num", formatCount(Number(entry.total_failures) || 0)));

      var successes = Number(entry.total_successes) || 0;
      var failures = Number(entry.total_failures) || 0;
      var attempts = successes + failures;
      var ratio = percent(successes, attempts);

      var reliabilityCell = node("td");
      var wrapper = node("div", "reliability");
      var track = node("div", "track");
      var fill = node("i");
      fill.style.width = (attempts > 0 ? ratio : 0) + "%";
      track.setAttribute("data-tone", ratio >= 90 ? "ok" : ratio >= 70 ? "warn" : "bad");
      track.appendChild(fill);
      wrapper.appendChild(track);
      wrapper.appendChild(node("span", "pct", attempts > 0 ? Math.round(ratio) + "%" : "—"));
      reliabilityCell.appendChild(wrapper);
      row.appendChild(reliabilityCell);

      ui.healthBody.appendChild(row);
    });

    if (ui.healthSummary) {
      ui.healthSummary.textContent = names.length > 0 ? available + " of " + names.length + " available" : "—";
      ui.healthSummary.className =
        "pill " + (available === names.length && names.length > 0 ? "pill-ok" : names.length > 0 ? "pill-warn" : "pill-neutral");
    }
  }

  /* ---------- latency ---------- */

  function renderLatency(latency) {
    clear(ui.latencyBody);
    var names = Object.keys(latency || {}).sort();
    ui.latencyEmpty.hidden = names.length > 0;

    var maxAverage = 0;
    names.forEach(function (name) {
      var average = Number((latency[name] || {}).average_ms) || 0;
      if (average > maxAverage) {
        maxAverage = average;
      }
    });

    names.forEach(function (name) {
      var entry = latency[name] || {};
      var average = Number(entry.average_ms) || 0;

      var row = document.createElement("tr");
      var nameCell = node("td");
      nameCell.appendChild(node("span", "name", name));
      var meter = node("div", "row-meter");
      var fill = node("i");
      fill.style.width = percent(average, maxAverage) + "%";
      meter.appendChild(fill);
      nameCell.appendChild(meter);
      row.appendChild(nameCell);

      row.appendChild(node("td", "num", formatMilliseconds(average)));
      row.appendChild(node("td", "num", formatMilliseconds(Number(entry.last_ms))));
      ui.latencyBody.appendChild(row);
    });
  }

  /* ---------- count tables ---------- */

  function renderCounts(source, body, empty, formatter) {
    clear(body);
    var entries = Object.keys(source || {})
      .map(function (name) {
        return { name: name, value: Number(source[name]) || 0 };
      })
      .sort(function (a, b) {
        return b.value - a.value || a.name.localeCompare(b.name);
      });

    empty.hidden = entries.length > 0;
    var max = entries.reduce(function (accumulator, entry) {
      return Math.max(accumulator, entry.value);
    }, 0);

    entries.forEach(function (entry) {
      var row = document.createElement("tr");
      var nameCell = node("td");
      nameCell.appendChild(node("span", "name", entry.name));
      var meter = node("div", "row-meter");
      var fill = node("i");
      fill.style.width = percent(entry.value, max) + "%";
      meter.appendChild(fill);
      nameCell.appendChild(meter);
      row.appendChild(nameCell);
      row.appendChild(node("td", "num", formatter(entry.value)));
      body.appendChild(row);
    });
  }

  /* ---------- cooldown clock ---------- */

  function tick() {
    var nodes = document.querySelectorAll("[data-until]");
    nodes.forEach(function (element) {
      var until = Date.parse(element.getAttribute("data-until") || "");
      if (!isFinite(until)) {
        element.textContent = "";
        return;
      }
      var remaining = until - Date.now();
      element.textContent = remaining > 0 ? formatRemaining(remaining) : "recovering";
    });

    if (lastLoad > 0 && Date.now() - lastLoad > STALE_MS) {
      setLive("stale", "Stale");
    }
  }

  /* ---------- orchestration ---------- */

  function render(health, metrics, latency, errors, usage) {
    var summary = renderTiles(metrics || {});
    renderHealth(health || {});
    renderLatency(latency || {});
    renderCounts(errors || {}, ui.errorsBody, ui.errorsEmpty, formatCount);
    renderCounts(usage || {}, ui.usageBody, ui.usageEmpty, formatCompact);
    renderCounts((metrics || {}).requests_by_model || {}, ui.byModelBody, ui.byModelEmpty, formatCount);
    renderVerdict(health || {}, latency || {}, summary);
    tick();
  }

  function load() {
    if (!readKey()) {
      showAuth();
      setLive("idle", "Not connected");
      return Promise.resolve();
    }

    if (loading) {
      return Promise.resolve();
    }
    loading = true;
    setBusy(true);
    return loadAll()
      .then(function (results) {
        hideBanner();
        showData();
        render(results[0], results[1], results[2], results[3], results[4]);
        lastLoad = Date.now();
        setLive("live", "Live");
        if (ui.lastUpdated) {
          ui.lastUpdated.textContent = "Updated " + new Date().toLocaleTimeString();
        }
      })
      .catch(function (error) {
        if (error && error.kind === "unauthorized") {
          dropKey();
          setLive("error", "Key rejected");
          showAuth(
            "That admin key was rejected (401). Paste a valid admin key to continue."
          );
          return;
        }
        setLive("stale", "Stale");
        var status = error && error.status ? error.status : "unknown";
        showBanner(
          "Could not read the gateway (status " + status + "). The last figures stay on screen until the next successful poll."
        );
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
      if (document.visibilityState === "visible") {
        load();
      }
    }, POLL_MS);
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
    previous.total = null;
    previous.failed = null;
    previous.rateLimited = null;
    history.total.length = 0;
    history.failed.length = 0;
    history.rateLimited.length = 0;
    history.successRate.length = 0;
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
      ui.refresh.addEventListener("click", function () {
        load();
      });
    }
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible" && Date.now() - lastLoad > POLL_MS) {
        load();
      }
    });

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
