#!/usr/bin/env python3
"""The release boundary, reported and never crossed.

R-74 wants doctrine, architecture, diff and checks reviewed before a commit or
a push, and a channel named before a publication. None of those four is
something a program can observe: they are human judgements. So this reports the
state a human needs in order to make them, records which ones were confirmed,
and stops.

It reads git and writes nothing. There is deliberately no flag that commits,
pushes or publishes, the same way `cook run` has no flag to open the repository
as a project root: the absence is the guarantee, and a flag is an argument
waiting to be won.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from errors import CookError

# The four reviews R-74 names, in the order a release actually needs them.
REVIEWS = ("doctrine", "architecture", "diff", "checks")


def git(project_root: Path, *argv: str) -> list[str]:
    try:
        done = subprocess.run(["git", "-C", str(project_root), *argv],
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    return done.stdout.splitlines() if done.returncode == 0 else []


def tree(project_root: Path) -> dict:
    """What a reviewer needs to see before deciding, read-only."""
    branch = next(iter(git(project_root, "rev-parse", "--abbrev-ref", "HEAD")), "")
    upstream = next(iter(git(project_root, "rev-parse", "--abbrev-ref",
                             "--symbolic-full-name", "@{u}")), "")
    return {"branch": branch, "upstream": upstream,
            "dirty": [line[3:] for line in
                      git(project_root, "status", "--porcelain") if line[3:]],
            # No upstream means nothing is pushed anywhere, which is a fact a
            # reviewer needs rather than an error to swallow.
            "unpushed": git(project_root, "log", "--oneline", "@{u}..")
            if upstream else []}


def report(project_root: Path, confirmed: list[str], channel: str = "") -> dict:
    unknown = sorted(set(confirmed) - set(REVIEWS))
    if unknown:
        raise CookError(
            f"{', '.join(unknown)} is not one of the reviews this boundary "
            f"names ({', '.join(REVIEWS)}). Confirming a review cook does not "
            "know would satisfy the gate without anyone having done the work.")
    outstanding = [item for item in REVIEWS if item not in confirmed]
    errors = [f"{item} has not been reviewed" for item in outstanding]
    if channel:
        errors.append(
            f"publishing to {channel} is a second decision and a third one for "
            "the channel; cook reports it and does not make it.")
    return {"reviews": {item: item in confirmed for item in REVIEWS},
            "outstanding": outstanding, "tree": tree(project_root),
            "channel": channel, "errors": errors, "passed": not errors,
            "next": "the user commits and pushes, or explicitly authorizes it; "
                    "cook has no flag that does either."}
