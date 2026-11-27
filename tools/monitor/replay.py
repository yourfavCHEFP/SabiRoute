#!/usr/bin/env python3
"""
Replay feat/sabiroute-routing-foundation onto origin/main, one commit at a time.

Runs unattended. Writes a plain progress log the monitor reads. Stops dead on any
failure and records why. Never force-pushes, never touches main directly.
"""
import os
import re
import subprocess
import sys
import time

REPO = "/Users/airm2/My ML Hub/SabiRoute"
WT = "/Users/airm2/.sabiroute-pr"
BR = "replay/main-pr-20261127"
SRC = "feat/sabiroute-routing-foundation"
D = os.path.join(REPO, "tools", "monitor")
LOG = os.path.join(D, "pr-replay.log")
SET = os.path.join(D, ".set.txt")
PYO = os.path.join(D, ".pyo.txt")
ENV = dict(os.environ, PATH=os.path.join(REPO, ".venv", "bin") + ":" + os.environ.get("PATH", ""))


def say(msg):
    with open(LOG, "a") as fh:
        fh.write("%s %s\n" % (time.strftime("%H:%M:%S"), msg))


def sh(args, cwd=None, timeout=900):
    return subprocess.run(args, cwd=cwd, env=ENV, capture_output=True, text=True, timeout=timeout)


def main():
    open(LOG, "w").close()
    say("=== start ===")

    sh(["git", "-C", REPO, "worktree", "remove", "--force", WT])
    sh(["git", "-C", REPO, "branch", "-D", BR])
    r = sh(["git", "-C", REPO, "worktree", "add", "-b", BR, WT, "origin/main"])
    if r.returncode != 0:
        say("FATAL worktree: " + (r.stderr or "").strip()[:300])
        return 1
    venv = os.path.join(WT, ".venv")
    if os.path.islink(venv) or os.path.exists(venv):
        os.remove(venv)
    os.symlink(os.path.join(REPO, ".venv"), venv)

    cherry = sh(["git", "-C", REPO, "cherry", "-v", "origin/main", SRC])
    shas = [ln.split()[1] for ln in cherry.stdout.splitlines() if ln.startswith("+")]
    with open(SET, "w") as fh:
        fh.write("\n".join(shas) + "\n")
    total = len(shas)
    say("replay set: %d" % total)

    for i, sha in enumerate(shas, 1):
        r = sh(["git", "cherry-pick", "-x", sha], cwd=WT)
        if r.returncode != 0:
            say("STOP %d/%d %s CONFLICT" % (i, total, sha))
            sh(["git", "cherry-pick", "--abort"], cwd=WT)
            return 1

        body = sh(["git", "log", "-1", "--format=%B"], cwd=WT).stdout
        kept = [ln for ln in body.splitlines()
                if not re.match(r"^co-authored-by:.*(claude|codex|anthropic|gpt|openai)",
                                ln, re.I)]
        msg = "\n".join(kept).rstrip() + "\n"
        r = sh(["git", "commit", "--amend", "-F", "-"], cwd=WT) if False else None
        tmp = os.path.join(D, ".msg.txt")
        with open(tmp, "w") as fh:
            fh.write(msg)
        r = sh(["git", "commit", "--amend", "-F", tmp, "--quiet"], cwd=WT)
        if r.returncode != 0:
            say("STOP %d/%d %s AMEND" % (i, total, sha))
            return 1

        if sh(["ruff", "check", ".", "--extend-ignore", "UP012,E501,UP037"], cwd=WT).returncode:
            say("STOP %d/%d %s RUFF" % (i, total, sha))
            return 1
        if sh(["mypy", "src"], cwd=WT).returncode:
            say("STOP %d/%d %s MYPY" % (i, total, sha))
            return 1

        head = sh(["git", "rev-parse", "--short", "HEAD"], cwd=WT).stdout.strip()
        if i == total:
            r = sh([os.path.join(WT, ".venv", "bin", "python"), "-m", "pytest", "tests", "-q"],
                   cwd=WT, timeout=1800)
            with open(PYO, "w") as fh:
                fh.write(r.stdout + r.stderr)
            if r.returncode != 0:
                say("STOP %d/%d %s PYTEST" % (i, total, sha))
                for ln in (r.stdout + r.stderr).splitlines()[-20:]:
                    say("  " + ln)
                return 1
            m = re.search(r"(\d+) passed", r.stdout)
            say("%d/%d %s green %s passed" % (i, total, head, m.group(1) if m else "?"))
        else:
            say("%d/%d %s green tests-deferred" % (i, total, head))

    say("final strict ruff")
    if sh(["ruff", "check", "."], cwd=WT).returncode:
        say("STOP final RUFF")
        return 1
    say("final pytest")
    r = sh([os.path.join(WT, ".venv", "bin", "python"), "-m", "pytest", "tests", "-q"],
           cwd=WT, timeout=1800)
    with open(PYO, "w") as fh:
        fh.write(r.stdout + r.stderr)
    if r.returncode != 0:
        say("STOP final PYTEST")
        for ln in (r.stdout + r.stderr).splitlines()[-20:]:
            say("  " + ln)
        return 1
    m = re.search(r"(\d+) passed", r.stdout)
    say("final %s passed" % (m.group(1) if m else "?"))

    say("pushing")
    r = sh(["git", "push", "-u", "origin", BR], cwd=WT)
    if r.returncode != 0:
        say("STOP push: " + (r.stderr or "").strip()[:300])
        return 1
    say("DONE " + sh(["git", "rev-parse", "HEAD"], cwd=WT).stdout.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
