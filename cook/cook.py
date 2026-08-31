#!/usr/bin/env python3
"""Run the Aesthetic Food Product in a throwaway project and check its screen.

    python3 cook/cook.py doctor --project-root /tmp/cook-run
    python3 cook/cook.py run    --project-root /tmp/cook-run
    python3 cook/cook.py clean  --project-root /tmp/cook-run
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "first" / "aesthetic"
COMPANION = ".superpowers/brainstorm"
HTTP_TIMEOUT = 5
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}

PLACEHOLDER_HEADING = "brainstorm companion"


class CookError(Exception):
    """A Food Product round that cannot be trusted, with the reason a human needs."""


class Screen(HTMLParser):
    """Just enough of the served document to tell a screen from the shell."""

    def __init__(self) -> None:
        super().__init__()
        self.headings: list[str] = []
        self.tags: set[str] = set()
        self.rankable_elements: set[str] = set()
        self._in_heading = False
        self._depth = 0
        self._decision_rows: list[tuple[str, int]] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.tags.add(tag)
        values = dict(attrs)
        classes = str(values.get("class") or "").split()
        element = str(values.get("data-element") or "").strip()
        if "dh-fb" in classes and element:
            self._decision_rows.append((element, self._depth))
        if self._decision_rows and "data-rank" in values:
            self.rankable_elements.add(self._decision_rows[-1][0])
        if tag in ("h1", "h2"):
            self._in_heading = True
        if tag not in VOID_TAGS:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag not in VOID_TAGS:
            self._depth = max(0, self._depth - 1)
            while self._decision_rows and self._decision_rows[-1][1] >= self._depth:
                self._decision_rows.pop()
        if tag in ("h1", "h2"):
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        if self._in_heading and data.strip():
            self.headings.append(data.strip().lower())


def check_not_the_repo(project_root: Path) -> None:
    """Keep Food Product project state outside the skill source tree."""
    resolved = project_root.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise CookError(
            f"{resolved} is inside {REPO}. A Food Product round writes project state -- "
            "corpus, ledger, renders, companion sessions -- and writing it here puts "
            "one project's work in the same tree as the skill source that produced "
            "it, which is the contamination cook exists to catch. Pass a "
            "--project-root outside the repository.")


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
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            return response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as problem:
        raise CookError(
            f"companion unreachable on port {port}: {problem}") from problem


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


def doctor(project_root: Path) -> dict:
    """Assert a designer opening the URL would see a screen. The whole point."""
    check_not_the_repo(project_root)
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

    return {"url": url, "checks": checks, "errors": errors,
            "passed": not errors, "screens": [str(p) for p in on_disk]}


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


def harness(project_root: Path, *argv: str) -> subprocess.CompletedProcess:
    """One call into the skill under test, run the way a user runs it."""
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "bootstrap_harness.py"), *argv,
         "--project-root", str(project_root)],
        capture_output=True, text=True, cwd=project_root)


def run(project_root: Path) -> dict:
    """Run one complete rankable round, then apply `doctor`."""
    check_not_the_repo(project_root)
    project_root.mkdir(parents=True, exist_ok=True)
    screen = project_root / "round.html"
    preview = project_root / "cook-proposal.png"
    source_preview = next(iter(sorted(REPO.glob("moodboards/**/*.png"))), None)
    if source_preview is None:
        raise CookError("the repository moodboards hold no PNG for the Food Product proposal")
    shutil.copy2(source_preview, preview)
    steps = (
        ("init", "--source-root", str(REPO / "moodboards"),
         "--profiles", "art-direction"),
        ("open", "--status", "Cook Food Product round"),
        ("decide", "--element", "cook.round.rankable", "--verdict", "proposed",
         "--stars", "0", "--evidence", "agent: Cook Food Product proposal",
         "--source", "agent", "--preview", preview.name,
         "--title", "Cook Food Product proposal",
         "--description", "A real proposal row used to prove ranking works.",
         "--implemented", "Published with a preview and an unscored rank control."),
        ("article", "--out", str(screen), "--cohort", "cook.round.rankable",
         "--round-label", "Cook Food Product proposal",
         "--asks", "How strong is this proposal?"),
        ("publish", "--screen", str(screen)),
    )
    opened = ""
    for verb, *flags in steps:
        done = harness(project_root, verb, *flags)
        if done.returncode != 0:
            raise CookError(f"{verb} failed: {(done.stderr or done.stdout).strip()}")
        if verb == "open":
            opened = done.stdout.strip()
    try:
        return {"opened": opened, **doctor(project_root)}
    finally:
        stop_companion(project_root)


def clean(project_root: Path) -> dict:
    check_not_the_repo(project_root)
    stopped = stop_companion(project_root)
    if project_root.exists():
        shutil.rmtree(project_root)
    return {"removed": str(project_root), "stopped": stopped}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("doctor", "assert the companion serves a real screen"),
                            ("run", "open a round in a scratch tree, then doctor it"),
                            ("clean", "delete the scratch tree")):
        one = sub.add_parser(name, help=help_text)
        one.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = {"doctor": doctor, "run": run, "clean": clean}[args.command](
            args.project_root)
    except CookError as problem:
        print(json.dumps({"passed": False, "error": str(problem)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
