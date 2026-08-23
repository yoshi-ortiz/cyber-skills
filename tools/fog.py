#!/usr/bin/env python3
"""What stays on `dev` and never reaches a published `main`.

An agent that consumes a skill pays context for every file it loads, and it
loads what is in front of it. Development state -- the burndown, the incident
log, the test suite, the records of why a boundary was drawn -- is real work
that belongs in version control and is worth nothing to that agent. Keeping
it on `dev` and publishing a tree without it is the difference between a
skill an agent reads and a repository an agent wades through.

This module is only the list, so `publish.py` and `check_publication.py`
cannot disagree about what fog is.
"""
from __future__ import annotations

from pathlib import PurePosixPath

# Exact paths, relative to the repository root.
FOG_FILES = (
    "ROADMAP.md",
    "BUGS.md",
    "CHANGELOG.md",
    "aesthetic/AGENTS.md",
)

# Whole directories, relative to the repository root.
FOG_DIRS = (
    "docs",
    ".audit",
    "tools",
    "aesthetic/docs",
)

# Basename patterns, matched anywhere in the tree.
FOG_GLOBS = (
    "test_*.py",
)

# Development tooling: it verifies the skill, it is not part of it.
FOG_FILES_EXTRA = (
    "aesthetic/scripts/contracts.py",
    "aesthetic/scripts/verify_references.py",
)

# Skills not ready for a stable tree. They stay on `dev` and ship on the alpha
# channel; `main` carries nothing under them, KEEP_ALWAYS included.
ALPHA_SKILLS = (
    "aesthetic",
    "genesis",
    "knowledge",
    "silly",
)

# Never fog, whatever else matches. The skill's own instructional payload is
# the reason `main` exists at all.
KEEP_ALWAYS = (
    "aesthetic/SKILL.md",
    "aesthetic/UBIQUITOUS_LANGUAGE.md",
    "aesthetic/CONTEXT.md",
    "README.md",
)


def is_alpha(relative: str) -> bool:
    """True when this path belongs to a skill that has not reached `main`."""
    return any(relative == skill or relative.startswith(skill + "/")
               for skill in ALPHA_SKILLS)


def is_fog(relative: str, channel: str = "main") -> bool:
    """True when this repo-relative path must not reach a published tree."""
    path = PurePosixPath(relative)
    text = path.as_posix()
    if channel == "main" and is_alpha(text):
        return True
    if text in KEEP_ALWAYS:
        return False
    if text in FOG_FILES or text in FOG_FILES_EXTRA:
        return True
    for directory in FOG_DIRS:
        if text == directory or text.startswith(directory + "/"):
            return True
    return any(path.match(pattern) for pattern in FOG_GLOBS)


def reasons() -> dict[str, str]:
    """Why each rule exists, for the error message a check prints."""
    return {
        "ROADMAP.md": "burndown state; an agent running the skill never reads it",
        "BUGS.md": "incident history; development state",
        "CHANGELOG.md": "release history; development state",
        "aesthetic/AGENTS.md": "how to DEVELOP this skill, and it cites tests "
                               "that a published tree does not carry",
        "docs": "requirements and distilled knowledge; development state",
        ".audit": "session decision log; development state",
        "tools": "publication tooling; it builds main, it does not ship on it",
        "aesthetic/docs": "ADRs explaining why durable boundaries were drawn; needed "
                          "to change the skill, not to run it",
        "test_*.py": "the correctness guard runs on dev; no consuming agent runs it",
        "aesthetic/scripts/contracts.py": "development tooling",
        "aesthetic/scripts/verify_references.py": "development tooling",
        "aesthetic": "alpha channel; not published to main",
        "genesis": "alpha channel; not published to main",
        "knowledge": "alpha channel; not published to main",
        "silly": "alpha channel; not published to main",
    }
