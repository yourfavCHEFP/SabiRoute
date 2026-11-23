"use strict";

/* SabiRoute Phase 15 admin dashboard -- read-only.
 *
 * Every figure on this page comes from the five authenticated admin
 * endpoints. The page holds no credential of its own: the operator pastes an
 * admin key, it is kept in this tab's session storage only, and it is sent as
 * the normal Authorization Bearer header on each GET request.
 *
 * There are no mutating requests in this file. Rendering uses textContent and
 * DOM construction only -- never HTML string injection.
 */

const STORAGE_KEY = "sabiroute.adminKey";

const ENDPOINTS = [
  ["health", "/admin/health"],
  ["metrics", "/admin/metrics"],
  ["latency", "/admin/latency"],
  ["errors", "/admin/errors"],
  ["usage", "/admin/usage"],
];

const el = (id) => document.getElementById(id);

let adminKey = "";

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function readStoredKey() {
  try {
    return sessionStorage.getItem(STORAGE_KEY) || "";
  } catch (_) {
    return "";
  }
}

function writeStoredKey(key) {
  try {
    sessionStorage.setItem(STORAGE_KEY, key);
  } catch (_) {
    /* Storage may be unavailable in some browser modes; the key still works
       for this page load because it is also held in memory below. */
  }
}

function clearStoredKey() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch (_) {
    /* ignore */
  }
}

async function getJson(path) {
  let response;
  try {
    response = await fetch(path, {
      method: "GET",
      headers: {
        Authorization: "Bearer " + adminKey,
        Accept: "application/json",
      },
      cache: "no-store",
    });
  } catch (_) {
    throw new HttpError(0, "Couldn't reach the SabiRoute backend.");
  }
  if (response.status === 401) {
    throw new HttpError(401, "Your admin key was rejected.");
  }
  if (response.status === 503) {
    throw new HttpError(503, "Admin authentication is unavailable on the server.");
  }
  if (!response.ok) {
    throw new HttpError(response.status, "The server returned " + response.status + ".");
  }
  try {
    return await response.json();
  } catch (_) {
    throw new HttpError(response.status, "The server returned an unreadable response.");
  }
}

function clear(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function makeCell(text) {
  const td = document.createElement("td");
  td.textContent = text;
  return td;
}

function appendRow(body, values) {
  const tr = document.createElement("tr");
  for (let i = 0; i < values.length; i += 1) {
    tr.appendChild(makeCell(values[i]));
  }
  body.appendChild(tr);
}

function fillTable(bodyId, emptyId, rows) {
  const body = el(bodyId);
  const empty = el(emptyId);
  clear(body);
  if (rows.length === 0) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  for (let i = 0; i < rows.length; i += 1) {
    appendRow(body, rows[i]);
  }
}

function pairs(value) {
  if (!value || typeof value !== "object") {
    return [];
  }
  return Object.keys(value).map((key) => [key, value[key]]);
}

function fmt(value) {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  return String(value);
}

function yesNo(value) {
  return value ? "yes" : "no";
}

function renderMetrics(metrics) {
  el("stat-total").textContent = fmt(metrics.requests_total);
  el("stat-success").textContent = fmt(metrics.requests_successful);
  el("stat-failed").textContent = fmt(metrics.requests_failed);
  el("stat-rate-limited").textContent = fmt(metrics.requests_rate_limited);
  fillTable(
    "by-model-body",
    "by-model-empty",
    pairs(metrics.requests_by_model).map((pair) => [pair[0], fmt(pair[1])])
  );
}

function renderHealth(health) {
  fillTable(
    "health-body",
    "health-empty",
    pairs(health).map((pair) => {
      const item = pair[1] || {};
      return [
        pair[0],
        yesNo(item.healthy),
        yesNo(item.available),
        fmt(item.total_successes),
        fmt(item.total_failures),
        fmt(item.cooldown_until),
      ];
    })
  );
}

function renderLatency(latency) {
  fillTable(
    "latency-body",
    "latency-empty",
    pairs(latency).map((pair) => {
      const item = pair[1] || {};
      return [pair[0], fmt(item.samples), fmt(item.average_ms), fmt(item.last_ms)];
    })
  );
}

function renderErrors(errors) {
  fillTable(
    "errors-body",
    "errors-empty",
    pairs(errors).map((pair) => [pair[0], fmt(pair[1])])
  );
}

function renderUsage(usage) {
  fillTable(
    "usage-body",
    "usage-empty",
    pairs(usage).map((pair) => [pair[0], fmt(pair[1])])
  );
}

function showAuth(message) {
  el("data-view").hidden = true;
  el("auth-panel").hidden = false;
  el("auth-message").textContent = message;
  el("auth-forget").hidden = readStoredKey() === "";
  const input = el("admin-key");
  input.value = "";
  input.focus();
}

function showData() {
  el("auth-panel").hidden = true;
  el("data-view").hidden = false;
}

function showBanner(message) {
  const banner = el("status-banner");
  banner.textContent = message;
  banner.hidden = false;
}

function hideBanner() {
  const banner = el("status-banner");
  banner.textContent = "";
  banner.hidden = true;
}

async function load() {
  hideBanner();
  const responses = await Promise.all(ENDPOINTS.map((entry) => getJson(entry[1])));
  const data = {};
  for (let i = 0; i < ENDPOINTS.length; i += 1) {
    data[ENDPOINTS[i][0]] = responses[i];
  }
  renderHealth(data.health);
  renderMetrics(data.metrics);
  renderLatency(data.latency);
  renderErrors(data.errors);
  renderUsage(data.usage);
  showData();
  el("last-updated").textContent = "Updated " + new Date().toLocaleTimeString();
}

async function refresh() {
  if (!adminKey) {
    showAuth("Paste your admin key to load the dashboard.");
    return;
  }
  try {
    await load();
  } catch (err) {
    const status = err instanceof HttpError ? err.status : 0;
    const message =
      err && err.message ? err.message : "The dashboard could not load.";
    if (status === 401) {
      showAuth("Your admin key was rejected (401). Paste a valid admin key.");
    } else if (status === 503) {
      showAuth("Admin authentication is unavailable on the server (503).");
    } else if (el("data-view").hidden) {
      showAuth(message);
    } else {
      showBanner(message);
    }
  }
}

function forget() {
  clearStoredKey();
  adminKey = "";
  showAuth("Paste your admin key to load the dashboard.");
}

function init() {
  const form = el("auth-form");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = el("admin-key");
    const key = input.value.trim();
    if (!key) {
      el("auth-message").textContent = "Enter your admin key to continue.";
      return;
    }
    adminKey = key;
    writeStoredKey(key);
    input.value = "";
    refresh();
  });

  el("auth-forget").addEventListener("click", forget);
  el("sign-out").addEventListener("click", forget);
  el("refresh").addEventListener("click", () => {
    refresh();
  });

  adminKey = readStoredKey();
  if (adminKey) {
    refresh();
  } else {
    showAuth("Paste your admin key to load the dashboard.");
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
