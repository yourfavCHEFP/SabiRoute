#!/usr/bin/env python3
"""
SabiRoute live monitor.

Stdlib only. No dependencies, no build step, runs on the project venv or system python3.

Everything it shows is read from disk and from git/rig on every tick -- nothing is cached
in memory across restarts and nothing is invented. If a source is unreachable the field
goes null and the UI shows it as unavailable rather than as zero.

    python3 tools/monitor/server.py            # http://localhost:8899
    MONITOR_PORT=9000 python3 .../server.py    # different port
"""
import json
import os
import re
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = "/Users/airm2/My ML Hub/SabiRoute"
WORKTREE = "/Users/airm2/.sabiroute-pr"
BRANCH = "replay/main-pr-20261127"
RIG = "factory"
LOG = "/Users/airm2/My ML Hub/SabiRoute/tools/monitor/pr-replay.log"
QITEM = "qitem-chefp-replay-20261127"
TOTAL = 43
HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("MONITOR_PORT", "8899"))

_cache = {}


def run(cmd, timeout=8, cwd=None):
    """Run a command, never raise, never hang the tick."""
    try:
        r = subprocess.run(
            cmd, shell=isinstance(cmd, str), cwd=cwd,
            capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def cached(key, ttl, fn):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    try:
        val = fn()
    except Exception as exc:  # a broken source must not kill the tick
        val = {"error": str(exc)[:200]}
    _cache[key] = (now, val)
    return val


def _wt():
    return WORKTREE if os.path.isdir(WORKTREE) else REPO


def git_info():
    def f():
        wt = _wt()
        ahead = run(["git", "-C", wt, "rev-list", "--count", "origin/main..HEAD"])
        head = run(["git", "-C", wt, "rev-parse", "--short", "HEAD"])
        subject = run(["git", "-C", wt, "log", "-1", "--format=%s"])
        remote = run(["git", "-C", wt, "ls-remote", "origin", "refs/heads/" + BRANCH])
        main = run(["git", "-C", wt, "ls-remote", "origin", "main"])
        # unpushed = committed locally but not yet on the remote branch
        unpushed = run(["git", "-C", wt, "rev-list", "--count",
                        "origin/%s..HEAD" % BRANCH]) if remote else ""
        recent = run(["git", "-C", wt, "log", "--format=%h\x1f%s",
                      "-60", "origin/main..HEAD"])
        commits = []
        for line in recent.splitlines():
            if "\x1f" in line:
                sha, subj = line.split("\x1f", 1)
                commits.append({"sha": sha, "subject": subj})
        return {
            "ahead": int(ahead) if ahead.isdigit() else None,
            "head": head or None,
            "subject": subject or None,
            "remote_tip": (remote.split()[0][:8] if remote else None),
            "main_tip": (main.split()[0][:8] if main else None),
            "unpushed": int(unpushed) if unpushed.isdigit() else None,
            "commits": commits,
            "on_main": bool(remote and main and remote.split()[0] == main.split()[0]),
        }
    return cached("git", 5, f)


def seats():
    def f():
        out = run(["rig", "ps", "--nodes", "--rig", RIG], timeout=12)
        rows = []
        for line in out.splitlines():
            p = line.split()
            if len(p) >= 4 and p[0] == RIG and "@" in p[1]:
                rows.append({
                    "session": p[1],
                    "lifecycle": p[2],
                    "activity": p[3],
                    "work": p[4] if len(p) > 4 else "",
                })
        return rows
    return cached("seats", 8, f)


def queue():
    def f():
        out = run(["rig", "queue", "show", QITEM], timeout=12)
        if not out:
            return {"state": None, "summary": None}
        d = json.loads(out)
        q = d.get("item", d)
        return {
            "state": q.get("state"),
            "summary": q.get("summary"),
            "destination": q.get("destination"),
            "blocked_on": q.get("blockedOn"),
        }
    return cached("queue", 8, f)


ENTRY = re.compile(r"^(\d\d:\d\d:\d\d)\s+(\d+)/(\d+)\s+([0-9a-f]{7,})\s+(.*)$")
STOPL = re.compile(r"^(\d\d:\d\d:\d\d)\s+STOP\s+(.*)$")


def replay_log():
    try:
        with open(LOG, "r", errors="replace") as fh:
            lines = [l.rstrip() for l in fh if l.strip()]
    except Exception:
        return {"lines": [], "entries": [], "done": 0, "stopped": None,
                "missing": True, "total_lines": 0}

    entries = []
    stopped = None
    for l in lines:
        m = ENTRY.match(l)
        if m:
            entries.append({
                "at": m.group(1), "n": int(m.group(2)), "total": int(m.group(3)),
                "sha": m.group(4), "detail": m.group(5),
            })
            continue
        s = STOPL.match(l)
        if s and stopped is None:
            stopped = {"at": s.group(1), "what": s.group(2)}
    if stopped is None:
        for l in reversed(lines):
            if "STOP" in l.upper():
                stopped = {"at": "", "what": l}
                break

    return {
        "lines": lines[-16:],
        "entries": entries,
        "done": len(entries),
        "stopped": stopped,
        "missing": False,
        "total_lines": len(lines),
    }


def gates():
    info = replay_log()
    last = info["entries"][-1] if info["entries"] else None
    if last is None:
        return {"last_line": None, "green": False, "deferred": False}
    return {
        "last_line": "%d/%d %s %s" % (last["n"], last["total"], last["sha"], last["detail"]),
        "green": "green" in last["detail"],
        "deferred": "deferred" in last["detail"],
    }


def state():
    return {
        "ts": time.time(),
        "total": TOTAL,
        "git": git_info(),
        "seats": seats(),
        "queue": queue(),
        "log": replay_log(),
        "gates": gates(),
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json", extra=None):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            with open(os.path.join(HERE, "index.html"), "rb") as fh:
                self._send(200, fh.read(), "text/html; charset=utf-8")
        elif path == "/bg.jpg":
            try:
                with open(os.path.join(HERE, "bg.jpg"), "rb") as fh:
                    self._send(200, fh.read(), "image/jpeg")
            except Exception:
                self._send(404, b"", "image/jpeg")
        elif path == "/api/state":
            self._send(200, json.dumps(state()))
        elif path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                while True:
                    payload = json.dumps(state())
                    self.wfile.write(("data: " + payload + "\n\n").encode())
                    self.wfile.flush()
                    time.sleep(2)
            except (BrokenPipeError, ConnectionResetError):
                return
        else:
            self._send(404, json.dumps({"error": "not found"}))


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    print("SabiRoute monitor -> http://localhost:%d" % PORT, flush=True)
    Server(("127.0.0.1", PORT), Handler).serve_forever()
