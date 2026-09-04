#!/usr/bin/env python3
"""Canonical facts about every skill in this repository."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kit" / "silly" / "scripts"))
from alias import Also, MARKER, Stub, frontmatter

ORIGIN = "yoshi-ortiz/cyber-skills"
WORKFLOW = frozenset({"kit", "first", "build", "land", "check", "fix"})
SKIP = frozenset({
    "tools", "assets", "docs", "design", "shots", "moodboards", "spec",
    ".git", ".claude", ".superpowers", ".audit", "cook",
})
GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("kit", ("kit", "silly", "ora")),
    ("first", ("genesis", "knowledge", "aesthetic")),
    # The family router sorts after the skills it routes, so shipping it does
    # not renumber rows the index already promised.
    ("check", ("build-context-token-vectors", "tokens-qa", "check")),
    ("build", ("build",)),
    ("land", ("land",)),
    ("fix", ("fix",)),
)
ALPHA_SKILLS = ("genesis", "tokens-qa", "knowledge", "silly",
                "build", "land", "check", "fix")


@dataclass(frozen=True)
class SkillRecord:
    """One skill fact, independent of the adapter consuming it."""

    name: str
    family: str | None
    channel: str
    origin: str
    path: Path
    skill_md: Path
    description: str
    translations: tuple[tuple[str, str], ...]
    aliases: tuple[str, ...]
    also: tuple[Also, ...]
    stubs: tuple[Stub, ...]
    body: str
    body_bytes: int

    @property
    def names(self) -> tuple[str, ...]:
        return (self.name, *(name for _code, name in self.translations),
                *self.aliases, *(name for name, _kind, _detail in self.stubs))


def _family(name: str, relative: Path) -> str | None:
    grouped = [family for family, members in GROUPS if name in members]
    if len(grouped) == 1:
        return grouped[0]
    return relative.parts[0] if relative.parts and relative.parts[0] in WORKFLOW else None


def _body(text: str) -> str:
    match = re.match(r"\s*---\s*\n.*?\n---\s*\n?", text, re.S)
    return text[match.end():].strip() if match else text.strip()


def _skill_directories(root: Path) -> list[Path]:
    found: list[Path] = []

    def harvest(container: Path) -> None:
        for child in sorted(container.iterdir()):
            if not child.is_dir():
                continue
            entry = child / "SKILL.md"
            if entry.is_file():
                fields, _translations, _aliases, _also, _stubs = frontmatter(entry)
                if not fields.get(MARKER):
                    found.append(child)
                    continue
            harvest(child)

    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name in SKIP or entry.name.startswith("."):
            continue
        skill_md = entry / "SKILL.md"
        if skill_md.is_file():
            fields, _translations, _aliases, _also, _stubs = frontmatter(skill_md)
            if not fields.get(MARKER):
                found.append(entry)
        if entry.name in WORKFLOW:
            harvest(entry)
    return found


def catalog(root: Path, origin: str = ORIGIN) -> list[SkillRecord]:
    """Return repository skills sorted by canonical identity.

    Duplicate identities are an invalid catalog rather than last-write-wins.
    """
    root = root.resolve()
    records: dict[str, SkillRecord] = {}
    for directory in _skill_directories(root):
        entry = directory / "SKILL.md"
        fields, translations, aliases, also, stubs = frontmatter(entry)
        name = fields.get("name") or directory.name
        if name in records:
            other = records[name].path
            raise ValueError(
                f"duplicate skill name {name!r}: {other.as_posix()} and "
                f"{directory.relative_to(root).as_posix()}"
            )
        text = entry.read_text(encoding="utf-8")
        body = _body(text)
        relative = directory.relative_to(root)
        records[name] = SkillRecord(
            name=name,
            family=_family(name, relative),
            channel="alpha" if name in ALPHA_SKILLS else "main",
            origin=origin,
            path=relative,
            skill_md=relative / "SKILL.md",
            description=fields.get("description", "").strip('"\''),
            translations=tuple(translations.items()),
            aliases=tuple(aliases),
            also=tuple(also),
            stubs=tuple(stubs),
            body=body,
            body_bytes=len(body.encode("utf-8")),
        )
    return [records[name] for name in sorted(records)]


def owner_of(relative: Path, records: list[SkillRecord]) -> SkillRecord | None:
    """Return the record whose directory contains a repository-relative path."""
    candidates = [record for record in records
                  if relative == record.path or record.path in relative.parents]
    return max(candidates, key=lambda record: len(record.path.parts), default=None)


def grouped_names() -> list[str]:
    return [name for _family_name, members in GROUPS for name in members]
