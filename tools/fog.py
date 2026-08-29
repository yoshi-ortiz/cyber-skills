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

from pathlib import Path, PurePosixPath

# Exact paths, relative to the repository root.
FOG_FILES = (
    "CLAUDE.md",
    "GOAL.md",
    "SPEC.md",
    "SKILL_SPEC.md",
    "UBIQUITOUS_LANGUAGE.md",
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
    # A design project run inside this repository. Its state, its references,
    # and its renders are one project's work, not any skill's payload.
    ".claude",
    ".superpowers",
    "spec",
    "design",
    "shots",
    "moodboards",
)

# Basename patterns, matched anywhere in the tree.
FOG_GLOBS = (
    "test_*.py",
    "inference-attempts.jsonl",
    "inference-trace.json",
    "context-tags-inbox.jsonl",
)

# Never walked, on either side of a publish.
SKIP_DIRS = {".git", "__pycache__"}

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


def walk(root: Path) -> list[Path]:
    """Every real file under `root`, repo-relative and sorted.

    One skip policy. `publish.py` and `check_publication.py` each carried their
    own copy, which is the same disagreement this module exists to prevent one
    level up: the builder and the gate have to count the same files.
    """
    return [path.relative_to(root) for path in sorted(root.rglob("*"))
            if path.is_file() and path.name != ".DS_Store"
            and not any(part in SKIP_DIRS for part in path.relative_to(root).parts)]


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
        "CLAUDE.md": "routes a Repo-Dev session between the burndown and the rail "
                     "audit; a consuming agent is in neither mode",
        "GOAL.md": "why this package's shape is the shape; a rail document that "
                   "designs the command surface, never a runtime instruction",
        "SPEC.md": "the settled contract for the command surface; Repo-Dev state",
        "SKILL_SPEC.md": "one owner and one burndown state per promised command; "
                         "a rail document, and burndown state is never payload",
        "UBIQUITOUS_LANGUAGE.md": "the Repo-Dev glossary. A skill carries its own; "
                                  "reading this one inside a run is the derail",
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
        ".claude": "skills for an agent working ON this repository. A consuming "
                   "agent installs skills from a published tree; it does not "
                   "inherit the ones that build it",
        ".superpowers": "companion runtime state: pids, logs, and a session's "
                        "ledger. Local to the machine that produced it",
        "spec": "one design project's harness state -- brief, corpus, "
                "candidates, and recorded attempts. Dev-only evidence",
        "design": "rendered comps from a design project run here; work product, "
                  "not skill payload",
        "shots": "screenshots from a design project run here",
        "moodboards": "reference imagery a user supplied to one project; theirs, "
                      "and never redistributed with a skill",
        "test_*.py": "the correctness guard runs on dev; no consuming agent runs it",
        "inference-attempts.jsonl": "recorded inference outcomes; local dev-only "
                                    "evidence a learner reads, never a skill",
        "inference-trace.json": "a compiler trace, written for a maintainer "
                                "reviewing one pass; development state",
        "context-tags-inbox.jsonl": "one maintainer's reviewed judgements about "
                                    "context, which is training data and never "
                                    "an instruction a skill carries",
        "aesthetic/scripts/contracts.py": "development tooling",
        "aesthetic/scripts/verify_references.py": "development tooling",
        "aesthetic": "alpha channel; not published to main",
        "genesis": "alpha channel; not published to main",
        "knowledge": "alpha channel; not published to main",
        "silly": "alpha channel; not published to main",
    }
