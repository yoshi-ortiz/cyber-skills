#!/usr/bin/env python3
"""Every verification gate this repository has, in one run.

The gates were documented in two places that never referenced each other --
repo-root `CONTEXT.md` names five, `first/aesthetic/AGENTS.md` names four, and the
overlap is two. A contributor could run either list in full and still miss half
the board. This is that board.

Each gate is run the way its own documentation spells it, as a subprocess:
composing the gates through their Python APIs would couple this file to nine
signatures that have no reason to agree, and the command line is the interface
the docs already promise.

    python3 tools/check.py            # every gate
    python3 tools/check.py contracts  # only gates whose name contains this

Exits non-zero if any gate fails. Nothing is filtered out: a checker with an
allowlist of failures it forgives is the same thing as no checker -- but a
checker whose red is permanent is read as one too, which is why
`contracts-declared` and `contracts-budget` are counted apart rather than as
one gate that stayed red through the R-15 debt.

The test gates are found rather than listed. `release.py` asks this board
before it publishes, so one registry answers what proved means for a local
run and for a release.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_gates(py: str) -> list[tuple[str, list[str]]]:
    """Every `test_*.py` in the repository, run the way its own shape says.

    B-023: the gate list named each test file by hand, so a file could be
    written, pass when invoked, and be executed by nothing. Four were, at the
    time this replaced the list. Finding the files removes the gap by
    construction -- a new test is inside a gate the moment it lands.

    Two conventions live here and both are real. A file with a `TestCase` is
    found by `unittest discover` over its directory. A file without one puts
    its assertions in a `test()` behind `__main__`, which discovery imports and
    never calls, so it is run as the script it is. Sniffing the file is what
    keeps the third case -- listed nowhere -- from existing again.
    """
    files = [path for path in sorted(ROOT.rglob("test_*.py"))
             if not any(part.startswith(".") or part == "__pycache__"
                        for part in path.relative_to(ROOT).parts)]
    scripts = [path for path in files
               if "TestCase" not in path.read_text(encoding="utf-8")]
    directories = sorted({path.parent for path in files if path not in scripts})
    return [
        ("feature compass", [py, "tools/repo_context.py", "check"]),
        *((f"tests {directory.relative_to(ROOT)}",
           [py, "-m", "unittest", "discover", "-s",
            str(directory.relative_to(ROOT)), "-p", "test_*.py"])
          for directory in directories),
        *((f"tests {path.relative_to(ROOT)}", [py, str(path.relative_to(ROOT))])
          for path in scripts),
    ]


def gates(tree: Path) -> list[tuple[str, list[str]]]:
    """Name each gate by the question it answers, not the file it runs."""
    py, node = sys.executable, shutil.which("node")
    return [
        # Split on purpose. `contracts-declared` must be green: a directory that
        # never declared itself is one commit from fixed. `contracts-budget` is
        # the standing R-15 debt. One permanent red hid the other for long
        # enough that two new undeclared directories shipped unnoticed.
        ("contracts-declared", [py, "first/aesthetic/scripts/contracts.py",
                                "--root", ".", "--only", "declared"]),
        ("contracts-budget", [py, "first/aesthetic/scripts/contracts.py",
                              "--root", ".", "--only", "budget"]),
        ("harness self-test", [py, "first/aesthetic/scripts/bootstrap_harness.py", "self-test"]),
        # Found, not listed. The list this replaces is B-023's root cause.
        *test_gates(py),
        ("index gate", [py, "tools/index_gate.py"]),
        ("loanwords", [py, "tools/loanwords.py"]),
        ("publish main",[py, "tools/publish.py", "--out", str(tree / "main"), "--check"]),
        ("publish alpha", [py, "tools/publish.py", "--out", str(tree / "alpha"),
                           "--channel", "alpha", "--check"]),
        ("published tree is fog-free", [py, "tools/check_publication.py", str(tree / "main")]),
        # The only gate that asserts on what a designer sees rather than on an
        # exit code. `--project-root` is the runner's tempdir because cook
        # refuses one inside the repository, and it is outside by construction.
        ("Cook Food Product round", [py, "cook/cook.py", "run", "--project-root", str(tree / "cook")]),
        *((f"{path.parent.name}/{path.name} parses", [node, "--check", str(path.relative_to(ROOT))])
          for path in sorted(ROOT.glob("first/aesthetic/*/*.js")) if node),
    ]


def run(name: str, argv: list[str]) -> bool:
    done = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    ok = done.returncode == 0
    print(f"{'ok  ' if ok else 'FAIL'}  {name}")
    if not ok:
        # The whole output, not a tail: `contracts` reports its violations in the
        # middle of a long list of directories that passed, and a tail of that is
        # the one thing on screen that says nothing went wrong.
        for line in (done.stdout + done.stderr).strip().splitlines():
            print(f"        {line}")
    return ok


def main(argv: list[str] | None = None) -> int:
    wanted = (argv if argv is not None else sys.argv[1:])
    with tempfile.TemporaryDirectory(prefix="cyber-skills-check-") as temp:
        chosen = [(name, cmd) for name, cmd in gates(Path(temp))
                  if not wanted or any(w in name for w in wanted)]
        if not chosen:
            print(f"no gate matches {' '.join(wanted)}")
            return 2
        failed = [name for name, cmd in chosen if not run(name, cmd)]
    print(f"\n{len(chosen) - len(failed)}/{len(chosen)} gates pass")
    if failed:
        print("failing: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
