#!/usr/bin/env python3
"""Run the Aesthetic Food Product in a throwaway project and check its screen.

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
from pathlib import Path

import deliver as release
import prove as proving
import route as routing
from doctor import doctor, stop_companion
from errors import CookError
from qa import feedback

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "first" / "aesthetic"


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
                            ("clean", "delete the scratch tree"),
                            ("feedback", "read the round back against what the user "
                                         "said about it, in the real project"),
                            ("deliver", "report the release boundary; never cross it"),
                            ("prove", "one real round, recorded as a Shot and "
                                      "read back as a table")):
        one = sub.add_parser(name, help=help_text)
        one.add_argument("--project-root", type=Path, required=True)
        if name == "deliver":
            one.add_argument("--confirmed", action="append", default=[],
                             help="a review the user has actually done; "
                                  f"one of {', '.join(release.REVIEWS)}")
            one.add_argument("--channel", default="",
                             help="the channel a publication would target")
        if name == "feedback":
            one.add_argument("--session", type=Path, default=None,
                             help="transcript to read, for an agent app cook does not know")
            one.add_argument("--invocation", default="",
                             help="audit this run id rather than the latest")
    walk = sub.add_parser("route", help="the skills a round walks, and whether "
                                        "they resolve")
    walk.add_argument("--skills-root", type=Path, default=routing.SKILLS)
    args = parser.parse_args(argv)
    try:
        if args.command == "route":
            result = routing.resolve(args.skills_root)
        elif args.command == "prove":
            check_not_the_repo(args.project_root)
            result = proving.prove(args.project_root, run)
        elif args.command == "deliver":
            result = release.report(args.project_root, args.confirmed, args.channel)
        elif args.command == "feedback":
            result = feedback(args.project_root, args.session, args.invocation)
        else:
            # `doctor` guards here rather than inside itself: the guard needs
            # REPO, which belongs to the runner, and `run`/`clean` already call it.
            check_not_the_repo(args.project_root)
            result = {"doctor": doctor, "run": run, "clean": clean}[args.command](
                args.project_root)
    except CookError as problem:
        print(json.dumps({"passed": False, "error": str(problem)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
