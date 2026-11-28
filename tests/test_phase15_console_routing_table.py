"""Console v2: the merged deployment table, and the two rules that keep it.

The headline defect in v1 was that an operator had to reconcile deployment
names by eye across two separate cards. The fix is one table, one row per
deployment, joining ``/admin/health`` and ``/admin/latency`` on deployment
name.

Two further rules are held here because both are easy to break by accident and
neither shows up as an error at runtime:

* the one-second clock must update existing HOLD text nodes in place, never
  re-render the table (ticket correction 2 — the most likely bug in the build);
* the orbit field must start no animation loop at all under
  ``prefers-reduced-motion: reduce``, and must not start in light mode.

The behavioural half executes ``dashboard.js`` against a stub DOM and canned
payloads and inspects the rendered cells. A string match on a function name
would not prove that one row carries both health counters and observed
latency, so it is not used for that claim.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

DASHBOARD_DIR = Path(__file__).resolve().parents[1] / "web" / "dashboard"
INDEX = DASHBOARD_DIR / "index.html"
SCRIPT = DASHBOARD_DIR / "dashboard.js"
STYLESHEET = DASHBOARD_DIR / "dashboard.css"

DASH = "—"
COLUMNS = ("ROUTE", "STATE", "OK", "FAIL", "REL", "AVG", "LAST", "HOLD")

ID_PATTERN = re.compile(r"<(?P<tag>[a-zA-Z][a-zA-Z0-9]*)\b[^>]*?\bid=\"(?P<id>[^\"]+)\"")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _elements_from_markup() -> list[dict[str, str]]:
    """Every id in the real page, with its tag, so a missing id fails the run."""
    markup = read(INDEX)
    return [
        {"id": match.group("id"), "tag": match.group("tag")}
        for match in ID_PATTERN.finditer(markup)
    ]


HARNESS = r"""
const vm = require("node:vm");
const fs = require("node:fs");

const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const source = fs.readFileSync(process.argv[3], "utf8");

let clockOffset = 0;
const RealDate = Date;
const DateShim = new Proxy(RealDate, {
  get(target, key) {
    if (key === "now") return () => RealDate.now() + clockOffset;
    return Reflect.get(target, key);
  }
});

let rafCalls = 0;
let drawCalls = 0;
let filterFocus = 0;

function makeContext() {
  return {
    strokeStyle: "",
    lineWidth: 0,
    fillStyle: "",
    globalCompositeOperation: "source-over",
    setTransform() {},
    clearRect() {},
    drawImage() {},
    beginPath() {},
    ellipse() {},
    stroke() {},
    arc() {},
    fill() {
      drawCalls += 1;
    },
    fillRect() {},
    createLinearGradient() {
      return { addColorStop() {} };
    }
  };
}

class El {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.attrs = {};
    this.listeners = {};
    this._text = "";
    this.className = "";
    this.hidden = false;
    this.disabled = false;
    this.value = "";
    this.offsetParent = {};
    this.clientWidth = 900;
    this.clientHeight = 520;
  }
  get firstChild() {
    return this.children.length ? this.children[0] : null;
  }
  get parentNode() {
    return null;
  }
  appendChild(child) {
    this.children.push(child);
    return child;
  }
  removeChild(child) {
    const at = this.children.indexOf(child);
    if (at >= 0) this.children.splice(at, 1);
    return child;
  }
  replaceChildren() {
    this.children.length = 0;
    this._text = "";
  }
  setAttribute(name, value) {
    this.attrs[name] = String(value);
  }
  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attrs, name) ? this.attrs[name] : null;
  }
  removeAttribute(name) {
    delete this.attrs[name];
  }
  addEventListener(type, handler) {
    (this.listeners[type] = this.listeners[type] || []).push(handler);
  }
  fire(type, event) {
    (this.listeners[type] || []).forEach((handler) => handler(event));
  }
  getBoundingClientRect() {
    return { width: this.clientWidth, height: this.clientHeight };
  }
  focus() {
    if (this.attrs.id === "filter") filterFocus += 1;
    document.activeElement = this;
  }
  getContext() {
    return makeContext();
  }
  set textContent(value) {
    this.children.length = 0;
    this._text = value === null || value === undefined ? "" : String(value);
  }
  get textContent() {
    if (this.children.length) return this.children.map((c) => c.textContent).join("");
    return this._text;
  }
}

const byId = new Map();
for (const entry of spec.elements) {
  const el = new El(entry.tag);
  el.attrs.id = entry.id;
  byId.set(entry.id, el);
}

const documentListeners = {};
const document = {
  readyState: "complete",
  visibilityState: "visible",
  activeElement: null,
  documentElement: new El("html"),
  getElementById: (id) => byId.get(id) || null,
  createElement: (tag) => new El(tag),
  createElementNS: (ns, tag) => new El(tag),
  querySelectorAll: () => [],
  addEventListener: (type, handler) => {
    (documentListeners[type] = documentListeners[type] || []).push(handler);
  }
};
document.activeElement = document.documentElement;

const storage = new Map([["sabiroute.console.admincredential", "synthetic-admin-key"]]);
const sessionStorage = {
  getItem: (k) => (storage.has(k) ? storage.get(k) : null),
  setItem: (k, v) => storage.set(k, String(v)),
  removeItem: (k) => storage.delete(k)
};

const fetch = (path) =>
  Promise.resolve({
    status: 200,
    ok: true,
    json: () => Promise.resolve(spec.payloads[path])
  });

const intervals = [];
const window = {
  devicePixelRatio: 3,
  setInterval: (fn, ms) => {
    intervals.push({ fn, ms });
    return intervals.length;
  },
  clearInterval: () => {},
  requestAnimationFrame: () => {
    rafCalls += 1;
    return rafCalls;
  },
  cancelAnimationFrame: () => {},
  matchMedia: (query) => ({
    matches:
      query.indexOf("prefers-color-scheme: dark") !== -1
        ? spec.prefs.dark
        : query.indexOf("prefers-reduced-motion: reduce") !== -1
        ? spec.prefs.reduceMotion
        : false
  })
};

const sandbox = {
  document,
  sessionStorage,
  fetch,
  window,
  Date: DateShim,
  Math,
  Object,
  Array,
  String,
  Number,
  Promise,
  console,
  isFinite,
  isNaN
};

vm.createContext(sandbox);
vm.runInContext(source, sandbox, { filename: "dashboard.js" });

function rows(id) {
  const body = byId.get(id);
  if (!body) return null;
  return body.children.map((row) => ({
    cells: row.children.map((cell) => {
      const inner = cell.children.length ? cell.children[0] : null;
      return {
        text: cell.textContent,
        cls: cell.className,
        tone: cell.getAttribute("data-tone"),
        innerState: inner ? inner.getAttribute("data-state") : null,
        innerUntil: inner ? inner.getAttribute("data-until") : null
      };
    }),
    state: row.getAttribute("data-state"),
    orphan: row.getAttribute("data-orphan"),
    dim: row.getAttribute("data-dim-route")
  }));
}

function text(id) {
  const el = byId.get(id);
  return el ? el.textContent : null;
}

function dispatchDocument(type, event) {
  (documentListeners[type] || []).forEach((handler) => handler(event));
}

setTimeout(() => {
  const result = {};

  result.health = rows("health-body");
  result.latency = rows("latency-body");
  result.verdict = text("verdict-text");
  const verdictNode = byId.get("verdict");
  result.tone = verdictNode ? verdictNode.getAttribute("data-tone") : null;
  result.ribbon = {
    total: text("stat-total"),
    success: text("stat-success"),
    failed: text("stat-failed"),
    limited: text("stat-rate-limited")
  };
  result.errors = rows("errors-body");
  result.usage = rows("usage-body");
  result.byModel = rows("by-model-body");
  result.rafCalls = rafCalls;
  result.drawCalls = drawCalls;
  const canvas = byId.get("field");
  result.canvas = { width: canvas.width, cssWidth: canvas.clientWidth, dprCap: 2 };

  /* --- the filter, on both halves of the merged set --- */
  const filter = byId.get("filter");
  filter.value = "ghost";
  filter.fire("input", {});
  const ghostLatency = rows("latency-body");
  result.filterGhost = {
    health: rows("health-body").length,
    latency: ghostLatency.length,
    first: ghostLatency.length ? ghostLatency[0].cells[0].text : null
  };

  filter.value = "nothing-matches-this";
  filter.fire("input", {});
  const emptyRows = rows("health-body");
  result.filterEmpty = {
    count: emptyRows.length,
    text: emptyRows.length ? emptyRows[0].cells[0].text : null
  };

  filter.value = "";
  filter.fire("input", {});

  /* --- the clock: text nodes only, no rebuild --- */
  const body = byId.get("health-body");
  const beforeRows = body.children.slice();
  /* An empty registry renders one colspan-8 row, so the HOLD cell may not
   * exist. Read it defensively. */
  const holdText = (row) => (row.children[7] ? row.children[7].textContent : null);
  const beforeHolds = beforeRows.map(holdText);
  clockOffset += 10000;
  intervals
    .filter((entry) => entry.ms === 1000)
    .forEach((entry) => {
      entry.fn();
    });
  const afterRows = body.children.slice();
  result.clock = {
    sameRowObjects:
      beforeRows.length === afterRows.length && beforeRows.every((row, i) => row === afterRows[i]),
    rowCount: afterRows.length,
    beforeHolds,
    afterHolds: afterRows.map(holdText)
  };

  /* --- the "/" shortcut must not eat a keystroke in a field --- */
  const keydown = {
    key: "/",
    preventDefault() {
      this.prevented = true;
    }
  };
  document.activeElement = byId.get("admin-key");
  dispatchDocument("keydown", keydown);
  result.keyFromInput = filterFocus;
  document.activeElement = document.documentElement;
  dispatchDocument("keydown", keydown);
  result.keyFromBody = filterFocus;

  process.stdout.write(JSON.stringify(result));
}, 0);
"""


def _run(
    tmp_path: Path,
    *,
    dark: bool = True,
    reduce_motion: bool = False,
    empty: bool = False,
) -> dict[str, object]:
    node = shutil.which("node")
    if node is None:
        pytest.fail("node is required to exercise the console script; the gate runs node --check")

    cooldown = (datetime.now(UTC) + timedelta(seconds=30)).isoformat()
    payloads = {
        "/admin/health": {
            "gw-alpha": {
                "healthy": True,
                "available": True,
                "consecutive_failures": 0,
                "total_successes": 1000,
                "total_failures": 0,
                "last_success": None,
                "last_failure": None,
                "cooldown_until": None,
            },
            # Unavailable *and* cooling: precedence says this reads HELD, not DOWN.
            "gw-beta": {
                "healthy": False,
                "available": False,
                "consecutive_failures": 10,
                "total_successes": 40,
                "total_failures": 10,
                "last_success": None,
                "last_failure": None,
                "cooldown_until": cooldown,
            },
            "gw-delta": {
                "healthy": False,
                "available": False,
                "consecutive_failures": 12,
                "total_successes": 0,
                "total_failures": 12,
                "last_success": None,
                "last_failure": None,
                "cooldown_until": None,
            },
        },
        "/admin/latency": {
            "gw-alpha": {"samples": 1000, "average_ms": 120.4, "last_ms": 118.0},
            "gw-beta": {"samples": 50, "average_ms": 2400.0, "last_ms": 2500.0},
            "gw-delta": {"samples": 12, "average_ms": 900.0, "last_ms": 900.0},
            # Reports latency but has no health record: a registry fault.
            "gw-ghost": {"samples": 10, "average_ms": 300.0, "last_ms": 300.0},
        },
        "/admin/metrics": {
            "requests_total": 1050,
            "requests_successful": 1040,
            "requests_failed": 10,
            "requests_rate_limited": 0,
            "requests_by_model": {"model-one": 1050},
        },
        "/admin/errors": {"upstream_timeout": 10},
        "/admin/usage": {"model-one": 5000},
    }

    if empty:
        # Fourteen deployments can be configured in config/config.yaml while
        # /admin/health returns {} because nothing has been observed yet.
        payloads = {
            "/admin/health": {},
            "/admin/latency": {},
            "/admin/metrics": {
                "requests_total": 0,
                "requests_successful": 0,
                "requests_failed": 0,
                "requests_rate_limited": 0,
                "requests_by_model": {},
            },
            "/admin/errors": {},
            "/admin/usage": {},
        }

    harness = tmp_path / "harness.js"
    harness.write_text(HARNESS, encoding="utf-8")
    spec = tmp_path / "spec.json"
    spec.write_text(
        json.dumps(
            {
                "elements": _elements_from_markup(),
                "payloads": payloads,
                "prefs": {"dark": dark, "reduceMotion": reduce_motion},
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [node, str(harness), str(spec), str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


@pytest.fixture(scope="module")
def rendered(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    return _run(tmp_path_factory.mktemp("console-v2"))


def cells(row: dict[str, object]) -> list[str]:
    return [cell["text"] for cell in row["cells"]]


# ------------------------------------------------ the merge, behaviourally --


def test_one_row_per_deployment_in_the_health_body(rendered: dict[str, object]) -> None:
    rows = rendered["health"]
    assert rows is not None, "the merged table body is missing from the page"
    assert len(rows) == 3, f"expected one row per healthy deployment, saw {len(rows)}"
    for row in rows:
        assert len(cells(row)) == len(COLUMNS)


def test_a_latency_only_deployment_lands_in_the_second_tbody(
    rendered: dict[str, object],
) -> None:
    """A route with latency but no health record is a registry fault, not a
    second panel. It belongs in the same table, in the same eight columns."""
    rows = rendered["latency"]
    assert rows is not None
    assert len(rows) == 1
    row = rows[0]
    assert len(cells(row)) == len(COLUMNS)
    assert cells(row)[0] == "gw-ghost"
    assert cells(row)[1] == "NO HEALTH"
    assert row["orphan"] == "true"
    # No health record means no counters: em dash in --text-3, never 0.
    for index in (2, 3, 4):
        assert cells(row)[index] == DASH
        assert "is-idle" in row["cells"][index]["cls"]


def test_each_row_carries_health_and_latency_from_both_payloads(
    rendered: dict[str, object],
) -> None:
    alpha = next(row for row in rendered["health"] if cells(row)[0] == "gw-alpha")
    # ROUTE, STATE, OK, FAIL, REL, AVG, LAST, HOLD
    assert cells(alpha)[1] == "UP"
    assert cells(alpha)[2] == "1,000"
    assert cells(alpha)[3] == "0"
    assert cells(alpha)[4] == "100.0"
    assert cells(alpha)[5] == "120ms"
    assert cells(alpha)[6] == "118ms"
    assert cells(alpha)[7] == DASH


def test_reliability_is_coloured_by_threshold_and_carries_no_bar(
    rendered: dict[str, object],
) -> None:
    beta = next(row for row in rendered["health"] if cells(row)[0] == "gw-beta")
    # 40/50 is below 90% but not below 70%, so it is a warn, not a bad.
    assert cells(beta)[4] == "80.0"
    assert beta["cells"][4]["tone"] == "warn"

    delta = next(row for row in rendered["health"] if cells(row)[0] == "gw-delta")
    assert cells(delta)[4] == "0.0"
    assert delta["cells"][4]["tone"] == "bad"


def test_reachability_labels_and_precedence(rendered: dict[str, object]) -> None:
    labels = {cells(row)[0]: cells(row)[1] for row in rendered["health"]}
    assert labels == {"gw-delta": "DOWN", "gw-beta": "HELD", "gw-alpha": "UP"}
    # gw-beta is both unavailable and cooling down. Cooling is tested first, so
    # it reads HELD. That precedence is v1's and must not drift.
    beta = next(row for row in rendered["health"] if cells(row)[0] == "gw-beta")
    assert re.fullmatch(r"\d+s left", cells(beta)[7]), cells(beta)[7]
    assert beta["cells"][7]["innerUntil"] is not None


def test_a_broken_route_is_dimmed_in_column_one(rendered: dict[str, object]) -> None:
    for row in rendered["health"]:
        name = cells(row)[0]
        if name in ("gw-delta", "gw-beta"):
            assert row["dim"] == "true", name
        else:
            assert row["dim"] is None, name


def test_sort_is_state_severity_then_name(rendered: dict[str, object]) -> None:
    """DOWN, HELD, DEGRADED, UP: the broken route is the one you came to find."""
    order = [cells(row)[0] for row in rendered["health"]]
    assert order == ["gw-delta", "gw-beta", "gw-alpha"]


def test_verdict_answers_in_one_line_and_names_the_broken_route(
    rendered: dict[str, object],
) -> None:
    verdict = rendered["verdict"]
    assert verdict is not None
    # The contract phrases the existing tests assert.
    assert "deployments available" in verdict
    assert "no failures in the last 15s" in verdict
    # The weighted gateway mean, over every latency record including the orphan.
    assert "avg 237 ms" in verdict
    # A broken route is named, not merely counted.
    assert "gw-delta" in verdict
    assert rendered["tone"] == "warn"


def test_ribbon_carries_the_four_preserved_figures(rendered: dict[str, object]) -> None:
    ribbon = rendered["ribbon"]
    assert ribbon["total"] == "1,050"
    assert ribbon["success"] == "99.0%"
    assert ribbon["failed"] == "10"
    assert ribbon["limited"] == "0"


def test_secondary_ledgers_render(rendered: dict[str, object]) -> None:
    assert cells(rendered["errors"][0]) == ["upstream_timeout", "10"]
    assert cells(rendered["usage"][0]) == ["model-one", "5,000"]
    assert cells(rendered["byModel"][0]) == ["model-one", "1,050"]


# ------------------------------------------- correction 2: the clock rule --


def test_the_countdown_updates_text_in_place_and_never_rebuilds_the_table(
    rendered: dict[str, object],
) -> None:
    """The single most likely bug in the build.

    A 1s tick that called render() would clear the filter, re-evaluate the
    observer and rebuild the table 60 times a minute. The tick must touch the
    HOLD text nodes and nothing else, which is proven by row object identity
    surviving the tick while the countdown text advances."""
    clock = rendered["clock"]
    assert clock["sameRowObjects"] is True, "the tick rebuilt the table"
    assert clock["rowCount"] == 3
    assert clock["beforeHolds"] != clock["afterHolds"], "the tick wrote nothing"
    # 30s left, advanced by 10s. gw-beta sorts second, so index 1 is the HOLD.
    assert clock["afterHolds"][1] == "20s left", clock["afterHolds"]


# ------------------------------------------ correction 3: the "/" shortcut --


def test_the_slash_shortcut_ignores_keystrokes_inside_a_field(
    rendered: dict[str, object],
) -> None:
    # Typing "/" into the admin key field must not steal focus.
    assert rendered["keyFromInput"] == 0
    # From the page body it focuses the filter exactly once.
    assert rendered["keyFromBody"] == 1


def test_search_filters_both_tbodies_and_states_its_empty_case(
    rendered: dict[str, object],
) -> None:
    ghost = rendered["filterGhost"]
    assert ghost["health"] == 0
    assert ghost["latency"] == 1
    assert ghost["first"] == "gw-ghost"

    empty = rendered["filterEmpty"]
    assert empty["count"] == 1, "an empty result must be one stated row, not a blank panel"
    assert empty["text"] == "No route matches"


def test_an_empty_health_payload_never_claims_to_know_the_config(tmp_path: Path) -> None:
    """The console can see /admin/health, not config/config.yaml.

    An empty health payload is what a gateway with fourteen configured
    deployments and no observations yet actually returns, so saying "nothing is
    configured" is false, and the page has no evidence for either claim. It
    states only what it observed: nothing is reporting.
    """
    empty = _run(tmp_path, empty=True)
    verdict = empty["verdict"]
    assert "No deployments reporting" in verdict
    assert "configured" not in verdict.lower()
    # The table states the same thing once, rather than sitting blank.
    assert empty["health"][0]["cells"][0]["text"] == "No deployments reporting"
    # Still a warning: zero routes reporting is not a healthy gateway.
    assert empty["tone"] == "warn"


# ------------------------------------- correction 5 / 3.7: the field rules --


def test_reduced_motion_starts_no_animation_loop(tmp_path: Path) -> None:
    still = _run(tmp_path, dark=True, reduce_motion=True)
    assert still["rafCalls"] == 0, "reduced motion must not start a rAF loop"
    # Exactly one frame is drawn at t = 0.
    assert still["drawCalls"] >= 1
    # And the table still renders: the page is the design, the field is not.
    assert len(still["health"]) == 3


def test_the_field_does_not_start_in_light_mode(tmp_path: Path) -> None:
    light = _run(tmp_path, dark=False, reduce_motion=False)
    assert light["rafCalls"] == 0, "the field is a dark-mode object"
    assert len(light["health"]) == 3


def test_the_animated_path_caps_the_device_pixel_ratio(rendered: dict[str, object]) -> None:
    canvas = rendered["canvas"]
    assert rendered["rafCalls"] >= 1, "the page must animate when it is allowed to"
    # devicePixelRatio is 3 in the harness; the field caps at 2.
    assert canvas["width"] == canvas["cssWidth"] * canvas["dprCap"]


def test_the_field_is_decorative() -> None:
    markup = read(INDEX)
    assert 'id="field" class="field" aria-hidden="true"' in markup
    stylesheet = read(STYLESHEET)
    field_rule = stylesheet[stylesheet.index("\n.field {") :]
    field_rule = field_rule[: field_rule.index("}")]
    assert "pointer-events: none" in field_rule


# --------------------------------------------------------------- structure --


def test_the_page_has_one_table_with_two_eight_column_tbodies() -> None:
    markup = read(INDEX)
    assert markup.count('id="health-body"') == 1
    assert markup.count('id="latency-body"') == 1
    routes = markup[markup.index('<table class="routes">') : markup.index("</table>")]
    # Both halves of the merged table are tbodies of the one routes table, so
    # the eight columns cannot drift apart between them.
    assert '<tbody id="health-body"' in routes
    assert '<tbody id="latency-body"' in routes
    assert routes.count("<col ") == len(COLUMNS)
    assert routes.count('scope="col"') == len(COLUMNS)
    for column in COLUMNS:
        assert f">{column}</th>" in routes, column


def test_the_ribbon_replaced_the_tiles_and_puts_the_ids_on_the_figures() -> None:
    markup = read(INDEX)
    assert 'class="tile"' not in markup
    assert 'class="tiles"' not in markup
    for stat in ("stat-total", "stat-success", "stat-failed", "stat-rate-limited"):
        # The figure carries the id; the caption sits beside it.
        assert f'id="{stat}" class="figure"' in markup, stat
    # Correction 6: the caption says the number is cumulative since start.
    assert "REQUESTS SINCE START" in markup
    # No sparklines at all in v2: the ribbon is a row of numbers.
    assert "spark" not in markup
    assert "spark" not in read(SCRIPT)


def test_the_verdict_separator_is_a_rule_not_a_middot() -> None:
    script = read(SCRIPT)
    stylesheet = read(STYLESHEET)
    assert "verdict-sep" in script
    assert "·" not in script, "the middot is the generated-UI tell the spec removes"
    assert ".verdict-sep" in stylesheet
    rule = stylesheet[stylesheet.index(".verdict-sep") :]
    assert "width: 1px" in rule[:200]


def test_the_display_clamp_floor_fits_a_1024px_laptop() -> None:
    """Correction 1, measured: 26px renders 756px into a 728px column and wraps."""
    stylesheet = read(STYLESHEET)
    assert "clamp(20px, 2.4vw, 34px)" in stylesheet
    assert "clamp(26px, 2.4vw, 34px)" not in stylesheet


def test_default_path_is_flat() -> None:
    stylesheet = read(STYLESHEET)
    assert "box-shadow" not in stylesheet
    assert "background: linear-gradient(" not in stylesheet
    assert "radial-gradient(" not in stylesheet
    assert "blur(" not in stylesheet
    for dead in ("--shadow-card", "--radius-card", "--radius-tile"):
        assert dead not in stylesheet

    radii = [int(value) for value in re.findall(r"border-radius:\s*(\d+)px", stylesheet)]
    assert radii and max(radii) <= 10
    # Controls take 6px; the auth gate is the 10px ceiling.
    assert 6 in radii


def test_there_is_exactly_one_decorative_layer() -> None:
    """Correction 4: the dot grid is cut. The orbit field, and nothing else."""
    stylesheet = read(STYLESHEET)
    markup = read(INDEX)
    assert markup.count("<canvas") == 1
    for dead in ("dot-grid", "dotgrid", "radial-gradient", "texture"):
        assert dead not in stylesheet, dead


def test_dark_is_the_base_surface_and_light_is_derived() -> None:
    stylesheet = read(STYLESHEET)
    dark_block = stylesheet.index("@media (prefers-color-scheme: dark)")
    assert "color-scheme: dark" in stylesheet[:dark_block]
    light = stylesheet.index("@media (prefers-color-scheme: light)")
    assert "color-scheme: light" in stylesheet[light:]
    # Correction 5: the field is not merely recoloured in light mode, it stops.
    assert ".field {\n    display: none;" in stylesheet[light:]


def test_transitions_use_one_house_curve_and_reduced_motion_removes_them() -> None:
    """Correction 7: one curve, and `none` under reduced motion — not a shorter
    duration."""
    stylesheet = read(STYLESHEET)
    assert "--ease: cubic-bezier(0.32, 0.72, 0, 1)" in stylesheet
    assert stylesheet.count("cubic-bezier(") == 1, "a second curve was introduced"
    reduced = stylesheet[stylesheet.index("@media (prefers-reduced-motion: reduce)") :]
    assert "transition: none !important" in reduced[:400]


def test_monospace_is_the_page() -> None:
    stylesheet = read(STYLESHEET)
    assert "--font-data:" in stylesheet
    assert "--font-display:" in stylesheet
    assert "font-variant-numeric: tabular-nums lining-nums" in stylesheet
    assert "font-family: var(--font-data);" in stylesheet


def test_no_column_is_ever_hidden_at_any_width() -> None:
    stylesheet = read(STYLESHEET)
    narrow = stylesheet[stylesheet.index("@media (max-width: 720px)") :]
    for column in ("col-route", "col-state", "col-ok", "col-fail", "col-rel", "col-avg"):
        assert f".{column}" not in narrow, f"{column} is touched at narrow width"
    assert ".routes tbody td" not in narrow
    # The only things hidden at rail width are the nav labels and the filter.
    assert "display: none" in narrow
    # The table scrolls and ROUTE stays pinned instead.
    assert "position: sticky" in stylesheet
    assert "left: 0" in stylesheet
    assert "min-width: 720px" in stylesheet
