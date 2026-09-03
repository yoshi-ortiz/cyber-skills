#!/usr/bin/env python3
"""The companion, and whether a designer opening its URL would see a screen.

Split out of `cook.py` so the runner holds the round and this holds the
assertion. The two read different things on purpose: `screens_on_disk` reads
the filesystem and `served_document` reads HTTP, so a green pair is two
witnesses rather than one restated twice.
"""
from __future__ import annotations

import os
import signal
import time
import urllib.error
import urllib.request
from pathlib import Path

from errors import CookError
from screen import PLACEHOLDER_HEADING, Screen

COMPANION = ".superpowers/brainstorm"
HTTP_TIMEOUT = 5
STARTUP_GRACE = 10
STARTUP_POLL = 0.1


def companion_address(project_root: Path) -> tuple[str, str]:
    """The port and key a designer's browser would use, from companion state."""
    base = project_root / COMPANION
    port, token = base / ".last-port", base / ".last-token"
    for path in (port, token):
        if not path.is_file():
            raise CookError(f"no companion state at {path}; run `cook run` first")
    return port.read_text().strip(), token.read_text().strip()


def served_document(port: str, token: str) -> str:
    """Fetch `/` with the key cookie; `/?key=` is only a redirect shim."""
    request = urllib.request.Request(
        f"http://localhost:{port}/",
        headers={"Cookie": f"brainstorm-key-{port}={token}"})
    # `run` starts the companion and fetches immediately, so a refused
    # connection usually means the socket is not bound YET, not that the
    # companion is broken. Retrying only that case keeps a startup race from
    # reading as a failed round, while a server that answers with an error
    # still fails on the first try. Widening the timeout would not have
    # helped: nothing is listening to be slow.
    deadline = time.monotonic() + STARTUP_GRACE
    while True:
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
                return response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as problem:
            raise CookError(
                f"companion answered {problem.code} on port {port}") from problem
        except (urllib.error.URLError, OSError) as problem:
            refused = isinstance(getattr(problem, "reason", problem),
                                 ConnectionRefusedError)
            if not refused or time.monotonic() >= deadline:
                raise CookError(
                    f"companion unreachable on port {port}: {problem}") from problem
            time.sleep(STARTUP_POLL)


def screens_on_disk(project_root: Path) -> list[Path]:
    """Newest screen from the newest session that contains one."""
    sessions = sorted((project_root / COMPANION).glob("*/"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    for session in sessions:
        found = sorted((session / "content").glob("*.html"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        if found:
            return found
    return []


def stop_companion(project_root: Path) -> list[int]:
    """Signal companion servers started under this project."""
    base = project_root / COMPANION
    stopped = []
    for pid_file in list(base.glob("*/state/server.pid")) + list(base.glob(".server.pid")):
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            stopped.append(pid)
        except (ValueError, OSError):
            continue  # already gone, or never ours to signal
    return stopped


def doctor(project_root: Path) -> dict:
    """Assert a designer opening the URL would see a screen. The whole point."""
    checks, errors = [], []

    on_disk = screens_on_disk(project_root)
    checks.append({"id": "screen-published", "passed": bool(on_disk)})
    if not on_disk:
        errors.append(
            "no screen in any session's content/: the companion has nothing to "
            "serve, so it will render the placeholder. `open` does not create "
            "one -- `article` then `publish` do.")

    port, token = companion_address(project_root)
    url = f"http://localhost:{port}/?key={token}"
    parsed = Screen()
    parsed.feed(served_document(port, token))

    if PLACEHOLDER_HEADING in parsed.headings:
        verdict, why = False, (
            f"the page at {url} is the empty-companion placeholder. This is the "
            "failure `open` hides: it returns a live URL and exit 0 either way, "
            "and user-communication.md then puts that URL first in the reply.")
    elif "key required" in " ".join(parsed.headings):
        verdict, why = False, (
            "the companion refused the session key, so what a designer sees is "
            "unknown and this round proves nothing.")
    elif not parsed.headings:
        verdict, why = False, (
            f"no heading parsed from {url}; cook cannot tell a screen from the "
            "shell, so it refuses to report a pass it cannot support.")
    else:
        verdict, why = True, ""
    checks.append({"id": "not-placeholder", "passed": verdict})
    if not verdict:
        errors.append(why)

    rankable = bool(parsed.rankable_elements)
    checks.append({"id": "screen-is-rankable", "passed": rankable})
    if on_disk and not rankable:
        errors.append(
            "the served screen carries no decision row with a data-rank control; "
            "unrelated forms and buttons do not give the designer a proposal to rank.")

    # A row can be structurally rankable and still show the designer a white
    # rectangle, which is what `screen-is-rankable` alone let through.
    blank = sorted(el for el, shot in parsed.shots.items() if not shot["drawn"])
    offsite = sorted(el for el, shot in parsed.shots.items() if shot["offsite"])
    checks.append({"id": "preview-renders",
                   "passed": bool(parsed.shots) and not blank and not offsite})
    if rankable and not parsed.shots:
        errors.append(
            "no preview accompanies any ranked row, so the designer is asked to "
            "score a proposal they cannot see.")
    if blank:
        errors.append(
            f"preview draws nothing for {', '.join(blank)}: the row renders as an "
            "empty rectangle, which is not rankable however complete the markup is.")
    if offsite:
        broken = sorted({src for shot in parsed.shots.values() for src in shot["offsite"]})
        errors.append(
            f"preview for {', '.join(offsite)} points outside the served document "
            f"({', '.join(broken)}). The companion serves from its own session "
            "directory, so that path resolves to nothing and paints white.")

    return {"url": url, "checks": checks, "errors": errors,
            "passed": not errors, "screens": [str(p) for p in on_disk]}
