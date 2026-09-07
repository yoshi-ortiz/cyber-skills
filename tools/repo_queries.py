#!/usr/bin/env python3
"""Read bounded roadmap, bug, goal and skill-catalog facts."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from skill_discovery import catalog, owner_of

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "first/genesis/scripts"))
import compass

LINK = re.compile(r"\[([^]]+)]\([^)]+\)")
BUG_HEADING = re.compile(r"^## (B-\d+)\s+·\s+(.+?)\s+·\s+(.+)$")


def _cell(text: str) -> str:
    return LINK.sub(r"\1", text).replace("`", "").strip()


def roadmap_rows(root: Path) -> list[dict[str, str]]:
    return compass.roadmap_rows(root)


def roadmap_state(root: Path, state: str) -> list[dict[str, str]]:
    wanted = state.upper()
    if wanted not in {"TODO", "IN-PROGRESS", "BLOCKED", "DONE"}:
        raise ValueError(f"unknown roadmap state {state!r}")
    return [row for row in roadmap_rows(root) if row["state"] == wanted]


def exact_roadmap_item(root: Path, identity: str) -> dict[str, str]:
    found = [row for row in roadmap_rows(root) if row["id"] == identity]
    if len(found) != 1:
        raise LookupError(f"expected one roadmap item {identity}, found {len(found)}")
    return found[0]


def item_context(root: Path, identity: str) -> dict[str, object]:
    exact = re.compile(rf"(?<![A-Za-z0-9-]){re.escape(identity)}(?![A-Za-z0-9-])")
    evidence = []
    for line in (root / "GOAL.md").read_text(encoding="utf-8").splitlines():
        if exact.search(line):
            evidence.append(" | ".join(_cell(part) for part in line.strip("|").split("|")))
    return {"goal": evidence, "roadmap": exact_roadmap_item(root, identity)}


def bugs(root: Path) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    body: list[str] = []
    for line in (root / "BUGS.md").read_text(encoding="utf-8").splitlines():
        match = BUG_HEADING.match(line)
        if match:
            if current is not None:
                current["body"] = "\n".join(body).strip()
                found.append(current)
            current = {"id": match.group(1), "title": match.group(2),
                       "status": match.group(3)}
            body = []
        elif current is not None:
            body.append(line)
    if current is not None:
        current["body"] = "\n".join(body).strip()
        found.append(current)
    return found


def latest_bug(root: Path) -> dict[str, str]:
    found = bugs(root)
    if not found:
        raise LookupError("no bug records found")
    return found[-1]


def exact_bug(root: Path, identity: str) -> dict[str, str]:
    found = [bug for bug in bugs(root) if bug["id"] == identity]
    if len(found) != 1:
        raise LookupError(f"expected one bug {identity}, found {len(found)}")
    return found[0]


def module_context(root: Path, query: str) -> dict[str, object]:
    records = catalog(root)
    record = next((candidate for candidate in records if query in candidate.names), None)
    if record is None:
        record = owner_of(Path(query), records)
    if record is None:
        raise LookupError(f"no catalog module owns {query!r}")
    return {"name": record.name, "family": record.family,
            "channel": record.channel, "origin": record.origin,
            "path": record.path.as_posix(),
            "context": (record.path / "CONTEXT.md").as_posix()}


def summary(root: Path) -> dict[str, object]:
    text = (root / "GOAL.md").read_text(encoding="utf-8")
    text = text.split("## The goal, in one line", 1)[-1]
    paragraphs = re.split(r"\n\s*\n", text.strip())
    goal = next((" ".join(part.split()) for part in paragraphs
                 if part.strip() and not part.startswith("#")), "")
    return {"goal": goal, "in_progress": roadmap_state(root, "IN-PROGRESS"),
            "modules": [module_context(root, record.name) for record in catalog(root)]}
