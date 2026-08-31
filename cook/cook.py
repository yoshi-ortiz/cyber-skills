#!/usr/bin/env python3
"""Run a skill the way a user runs it, then check what the user would see.

Every other gate in this repository reads an exit code. The companion bug is
what that misses: `bootstrap_harness.py open` exited zero, printed a live URL,
and served "Waiting for the agent to push a screen..." -- a success-shaped
return in front of an empty page, handed to the designer as the first line of
the reply because `user-communication.md` says the URL comes first.

So the assertion here is never "it exited zero". It is "the page a designer
opens carries a screen", fetched over HTTP from the running companion.

    python3 cook/cook.py doctor --project-root /tmp/cook-run
    python3 cook/cook.py run    --project-root /tmp/cook-run
    python3 cook/cook.py clean  --project-root /tmp/cook-run
"""
from __future__ import annotations

import argparse
import json
import shutil
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

# What the companion serves when `<session>/content/` holds no screen. Matched
# on parsed structure rather than on the sentence, so rewording the placeholder
# does not silently turn this check green.
PLACEHOLDER_HEADING = "brainstorm companion"


class CookError(Exception):
    """A dogfood round that cannot be trusted, with the reason a human needs."""


class Screen(HTMLParser):
    """Just enough of the served document to tell a screen from the shell."""

    def __init__(self) -> None:
        super().__init__()
        self.headings: list[str] = []
        self.tags: set[str] = set()
        self._in_heading = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.tags.add(tag)
        if tag in ("h1", "h2"):
            self._in_heading = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h1", "h2"):
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        if self._in_heading and data.strip():
            self.headings.append(data.strip().lower())


def check_not_the_repo(project_root: Path) -> None:
    """Refuse the repository root as a design project root.

    The skill package and one project's shot tests must not be the same tree.
    No flag opens this: a round that writes its state next to the source that
    produced it has already contaminated the context it was meant to test.
    """
    resolved = project_root.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise CookError(
            f"{resolved} is inside {REPO}. A dogfood round writes project state -- "
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
    """Fetch the page a designer actually lands on, not the redirect shim.

    `/?key=` only stashes the key and redirects to `/`; parsing it was how the
    first version of this check went green against an empty companion. The key
    is mirrored into a cookie, so send that and read the real document.
    """
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
    """Every screen the companion could serve, newest first.

    `publish_screen` serves the newest-mtime html in the newest session's
    `content/`. An empty `content/` is exactly the state that produces the
    placeholder, so it is worth naming separately from an HTTP failure.
    """
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

    # Default deny. A document this cannot recognise is a failure, never a
    # pass: the first version of this check treated "no heading found" as
    # "not the placeholder" and went green against the empty page it existed
    # to catch. An assertion that cannot see the page has not checked it.
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

    rankable = bool(parsed.tags & {"form", "input", "button"})
    checks.append({"id": "screen-is-rankable", "passed": rankable})
    if on_disk and not rankable:
        errors.append("the served screen carries no scoring control; nothing to rank.")

    return {"url": url, "checks": checks, "errors": errors,
            "passed": not errors, "screens": [str(p) for p in on_disk]}


def harness(project_root: Path, *argv: str) -> subprocess.CompletedProcess:
    """One call into the skill under test, run the way a user runs it."""
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "bootstrap_harness.py"), *argv,
         "--project-root", str(project_root)],
        capture_output=True, text=True, cwd=project_root)


def run(project_root: Path) -> dict:
    """A full round in a scratch tree, then the same assertion as `doctor`."""
    check_not_the_repo(project_root)
    project_root.mkdir(parents=True, exist_ok=True)
    opened = harness(project_root, "open", "--status", "cook dogfood round")
    if opened.returncode != 0:
        raise CookError(f"open failed: {opened.stderr.strip()}")
    return {"opened": opened.stdout.strip(), **doctor(project_root)}


def clean(project_root: Path) -> dict:
    check_not_the_repo(project_root)
    if project_root.exists():
        shutil.rmtree(project_root)
    return {"removed": str(project_root)}


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
