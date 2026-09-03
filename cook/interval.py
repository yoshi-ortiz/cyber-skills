#!/usr/bin/env python3
"""When a run began, and which of the dirty paths it actually touched.

The working tree keeps no history, so `git status --porcelain` carries no
clock. A tree that was already dirty before a run therefore read as that run
having changed something, and a round that heard a complaint and edited nothing
passed on somebody else's uncommitted work. mtime is the only clock the working
tree has.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

# The marker a skill's payload opens with. It is not something the user said,
# so it is skipped as a turn -- but it names the skill directory that ran,
# which is what scopes this whole read.
SKILL_MARKER = re.compile(r"Base directory for this skill: (\S+)")


def text_of(entry: dict) -> tuple[str, list]:
    """One transcript row's prose, and its blocks. The Claude Code shape.

    The only place this package knows what an agent app's rows look like. A
    second app is a second reader here, not a second reader in every caller.
    """
    content = entry.get("message", {}).get("content")
    blocks = content if isinstance(content, list) else []
    if isinstance(content, str):
        return content, blocks
    return " ".join(b.get("text", "") for b in blocks
                    if isinstance(b, dict) and b.get("type") == "text"), blocks


class Invocation(NamedTuple):
    """One skill run, bounded at both ends by the start of the next one.

    `end` bounds the transcript rows and `ended` bounds the clock; both are
    empty for the last run, which is the only one whose window legitimately
    reaches the end of the file. A run needs both: the turns live at row
    indices, and the commits live in time.
    """
    run_id: str
    skill: str
    started: str
    ended: str
    start: int
    end: int


def invocations(rows, skill: str = "") -> list[Invocation]:
    """Every run in one transcript, each ending where the next one begins.

    The end bound is taken from the next run of *any* skill, then the list is
    filtered. A different skill starting is still the end of this run, and
    bounding against the next run of the same skill would swallow it.
    """
    marks = []
    for index, entry in enumerate(rows):
        if entry.get("type") != "user":
            continue
        hit = SKILL_MARKER.search(text_of(entry)[0])
        if hit:
            marks.append((Path(hit.group(1).split("\\n")[0]).name,
                          entry.get("timestamp", ""), index))
    runs = [Invocation(f"{name}@{at}", name, at,
                       marks[i + 1][1] if i + 1 < len(marks) else "",
                       index,
                       marks[i + 1][2] if i + 1 < len(marks) else -1)
            for i, (name, at, index) in enumerate(marks)]
    return [run for run in runs if not skill or run.skill == skill]


def pick(runs: list[Invocation], run_id: str = "") -> Invocation | None:
    """The named run, or the latest. A named run that is absent is not the
    latest: silently auditing a different round than the one asked for is the
    false correlation this module exists to remove."""
    if not run_id:
        return runs[-1] if runs else None
    return next((run for run in runs if run.run_id == run_id), None)


def latest_run(rows, skill: str = "") -> tuple[str, str, int]:
    """The latest run's name, timestamp and line index."""
    run = pick(invocations(rows, skill))
    return (run.skill, run.started, run.start) if run else ("", "", -1)


def began(since: str) -> float:
    """The run's start as an epoch, or 0 when the stamp is not a real time."""
    try:
        return datetime.fromisoformat(since).timestamp()
    except ValueError:
        return 0.0


def touched_between(project_root: Path, paths: list[str],
                    since: str, until: str = "") -> list[str]:
    """The porcelain paths whose file was modified inside the run's window.

    A path that cannot be stat'ed -- deleted, or gone from the tree -- is
    dropped rather than kept. Cook denies what it cannot see, and a file that is
    gone cannot show *when* it went.
    """
    floor, ceiling = began(since), began(until)
    if not floor:
        return paths  # no clock in the transcript, so nothing to scope against
    kept = []
    for path in paths:
        # `R  old -> new` names the destination; the source no longer exists.
        try:
            when = (project_root / path.split(" -> ")[-1]).stat().st_mtime
        except OSError:
            continue
        if when >= floor and (not ceiling or when < ceiling):
            kept.append(path)
    return kept
