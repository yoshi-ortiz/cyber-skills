#!/usr/bin/env python3
"""Where skills live in this monorepo.

Skills sit at the repository root only for workflow family containers that are
also skills (`kit/`). Every other skill lives under a family directory, at any
depth (`first/genesis/`, `kit/spanish/ora/`). The harness still installs by
skill name, not by family path.
"""
from __future__ import annotations

from pathlib import Path

from skill_catalog import (ALPHA_SKILLS, GROUPS, ORIGIN, SKIP, WORKFLOW,
                           SkillRecord, catalog, grouped_names, owner_of)


def discover(root: Path) -> list[tuple[str, Path]]:
    """Compatibility projection as ``(canonical name, absolute directory)``."""
    return [(record.name, root.resolve() / record.path) for record in catalog(root)]


def names(root: Path) -> list[str]:
    return [name for name, _ in discover(root)]


def grouped() -> list[str]:
    """Every grouped skill, in the order the index table must list them."""
    return grouped_names()
