#!/usr/bin/env python3
"""Kit may only cite harness commands the harness actually has.

Kit holds no logic; it tells an agent which `harness.py` command to run. It
once documented `harness.py domain` and a `~/.harness-core.json` state file
that harness-core never shipped, so every `kit <domain>` failed on a clean
install while every gate here stayed green. The harness lives in another
repository, so its interface is pinned here, and drift is checked against a
local checkout whenever one exists.

    python3 tools/kit_gate.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from skill_discovery import names

ROOT = Path(__file__).resolve().parent.parent
HARNESS = Path.home() / ".harness-core" / "harness.py"

# harness-core ac8cb31. Update with the harness, never ahead of it.
COMMANDS = {"sync", "status", "version", "add", "upgrade", "onboard"}
# Paths the harness reads or writes. Anything else Kit names as state is fiction.
STATE = {"collection.toml"}

DOCS = ["kit/SKILL.md", "SPEC.md", "SKILL_SPEC.md", "first/big-bang/cyber-skills.md"]
CITED = re.compile(r"harness\.py\s+([a-z][a-z-]*)")
FICTION = re.compile(r"~/\.harness-core\.json")
CHOICES = re.compile(r"choices=\(([^)]*)\)", re.S)
RESERVED = re.compile(r"^RESERVED = \{(.*?)^\}", re.S | re.M)
# A quoted name, not a dict key such as `"codex":`.
NAME = re.compile(r'"([a-z-]+)"(?!\s*:)')


def cited(text: str) -> set[str]:
    return set(CITED.findall(text))


def harness_commands(source: str) -> set[str] | None:
    """The command choices a harness.py declares, read without running it."""
    found = CHOICES.search(source)
    return set(re.findall(r'"([a-z-]+)"', found.group(1))) if found else None


def builtins(source: str) -> set[str]:
    """The built-in names, across every app, the harness refuses to install over."""
    found = RESERVED.search(source)
    return set(NAME.findall(found.group(1))) if found else set()


def check(root: Path = ROOT, harness: Path = HARNESS,
          shipped: list[str] | None = None) -> list[str]:
    problems: list[str] = []
    for rel in DOCS:
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for name in sorted(cited(text) - COMMANDS):
            problems.append(f"{rel} cites `harness.py {name}`, which the harness does not have")
        if FICTION.search(text):
            problems.append(f"{rel} names ~/.harness-core.json; the harness keeps state in "
                            f"{', '.join(sorted(STATE))}")
    if harness.is_file():
        source = harness.read_text(encoding="utf-8")
        actual = harness_commands(source)
        if actual is not None and actual != COMMANDS:
            problems.append(f"{harness} commands {sorted(actual)} differ from the pin "
                            f"{sorted(COMMANDS)}; update COMMANDS and Kit together")
        if shipped is None:
            shipped = names(root) if root == ROOT else []
        for name in sorted(set(shipped) & builtins(source)):
            problems.append(f"skill `{name}` would take over a built-in command (B-036)")
    return problems


def main() -> int:
    problems = check()
    for line in problems:
        print(f"kit-gate: {line}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
