#!/usr/bin/env python3
"""Where skills live in this monorepo.

Skills sit at the repository root only for workflow family containers that are
also skills (`kit/`). Every other skill lives under a family directory, at any
depth (`first/genesis/`, `kit/spanish/ora/`). The harness still installs by
skill name, not by family path.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kit" / "silly" / "scripts"))
from alias import MARKER, frontmatter

# Six rail families from SPEC.md. A directory with this name may hold skills.
WORKFLOW = frozenset({"kit", "first", "build", "land", "check", "fix"})

# Top-level trees that are never skills, even if they contain a SKILL.md.
SKIP = frozenset({
    "tools", "assets", "docs", "design", "shots", "moodboards", "spec",
    ".git", ".claude", ".superpowers", ".audit",
})

# README index: one group per family that ships skills today.
GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("kit", ("kit", "silly", "ora")),
    ("first", ("genesis", "knowledge", "aesthetic")),
    ("check", ("build-context-token-vectors",)),
)


def is_skill(skill_md: Path) -> bool:
    """True when this SKILL.md names a real skill, not an installed alias stub."""
    return not frontmatter(skill_md)[0].get(MARKER)


def harvest(container: Path, found: dict[str, Path]) -> None:
    """Find skill directories under a workflow family tree."""
    for child in sorted(container.iterdir()):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if skill_md.is_file() and is_skill(skill_md):
            found[child.name] = child
        else:
            harvest(child, found)


def discover(root: Path) -> list[tuple[str, Path]]:
    """Every skill as (canonical name, directory), sorted by name."""
    found: dict[str, Path] = {}
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name in SKIP or entry.name.startswith("."):
            continue
        skill_md = entry / "SKILL.md"
        if skill_md.is_file() and is_skill(skill_md):
            found[entry.name] = entry
        if entry.name in WORKFLOW:
            harvest(entry, found)
    return sorted(found.items())


def names(root: Path) -> list[str]:
    return [name for name, _ in discover(root)]


def grouped() -> list[str]:
    """Every grouped skill, in the order the index table must list them."""
    return [name for _, members in GROUPS for name in members]
