#!/usr/bin/env python3
"""The one next action for Genesis, computed from disk state.

`SKILL.md` is canonical: its state-machine table names every file a project
keeps state in, and this module reads that table rather than restating it. A
row added there is checked here without a Python edit, and a path this module
names that the doctrine dropped is a drift failure, not a silent no-op.

Ordering stays here on purpose. Which file must exist is doctrine; the order
the gaps are worth fixing in is behaviour, and the table has no order to read.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

SKILL_MD = Path(__file__).resolve().parents[1] / "SKILL.md"


def topology(skill_md: Path = SKILL_MD) -> dict[str, str]:
    """The canonical state files, read from the table in `SKILL.md`.

    A row is `| `path` | what it holds | the rule |`. Paths only: a table cell
    that is not a backticked file or directory is prose, not topology.
    """
    try:
        text = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    rows = re.findall(r"^\|\s*`([^`]+)`\s*\|([^|]*)\|", text, re.M)
    return {path: holds.strip() for path, holds in rows
            if path.endswith((".md", "/"))}


def _has_text_file(path: Path) -> bool:
    """Return True if path exists, is a file, and contains non-whitespace text."""
    if not path.is_file():
        return False
    try:
        content = path.read_text(encoding="utf-8").strip()
        return len(content) > 0
    except (OSError, UnicodeDecodeError):
        return False


def _has_spec_contracts(spec_dir: Path) -> bool:
    """Return True if spec_dir contains at least one non-empty markdown contract."""
    if not spec_dir.is_dir():
        return False
    try:
        for item in spec_dir.iterdir():
            if item.is_file() and item.suffix.lower() == ".md" and _has_text_file(item):
                return True
    except OSError:
        return False
    return False


def _parse_roadmap_states(roadmap_file: Path) -> dict[str, list[str]]:
    """Parse task statuses from a ROADMAP markdown file.

    Extracts tasks tagged with TODO, IN-PROGRESS, BLOCKED, or DONE.
    """
    states: dict[str, list[str]] = {
        "TODO": [],
        "IN-PROGRESS": [],
        "BLOCKED": [],
        "DONE": [],
    }
    if not _has_text_file(roadmap_file):
        return states

    try:
        text = roadmap_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return states

    pattern = re.compile(r"`(TODO|IN-PROGRESS|BLOCKED|DONE)`\s*\|\s*([^|\n]+)")
    for match in pattern.finditer(text):
        status, item = match.group(1), match.group(2).strip()
        states[status].append(item)

    alt_pattern = re.compile(r"[-*]\s*`(TODO|IN-PROGRESS|BLOCKED|DONE)`\s*:?\s*(.+)")
    for match in alt_pattern.finditer(text):
        status, item = match.group(1), match.group(2).strip()
        if item not in states[status]:
            states[status].append(item)

    return states


def _find_unproven_done(project_root: Path, done_tasks: Sequence[str]) -> list[str]:
    """Find DONE tasks that have no runtime verification record or proof artifact."""
    if not done_tasks:
        return []

    audit_proofs = project_root / ".audit" / "proofs"
    verification_md = project_root / "docs" / "verification.md"
    root_verification = project_root / "verification.md"

    if audit_proofs.is_dir() and any(audit_proofs.iterdir()):
        return []
    if _has_text_file(verification_md) or _has_text_file(root_verification):
        return []

    return list(done_tasks)


def _present(root: Path, path: str) -> bool:
    """Is this canonical path filled in? A directory counts once it holds text."""
    target = root / path
    return _has_spec_contracts(target) if path.endswith("/") else _has_text_file(target)


def read_state(project_root: Path, skill_md: Path = SKILL_MD) -> dict[str, Any]:
    """Read the Genesis topology on disk and return a state dictionary."""
    root = Path(project_root).resolve()
    present = {path: _present(root, path) for path in topology(skill_md)}
    roadmap_file = root / "ROADMAP.md"

    roadmap_states = _parse_roadmap_states(roadmap_file) if present.get("ROADMAP.md") else {
        "TODO": [], "IN-PROGRESS": [], "BLOCKED": [], "DONE": []
    }

    total_tasks = sum(len(items) for items in roadmap_states.values())
    in_progress = roadmap_states.get("IN-PROGRESS", [])
    done_tasks = roadmap_states.get("DONE", [])
    todo_tasks = roadmap_states.get("TODO", [])

    unproven_done = _find_unproven_done(root, done_tasks)

    return {
        "projectRoot": str(root),
        "present": present,
        "totalTasks": total_tasks,
        "inProgressCount": len(in_progress),
        "todoCount": len(todo_tasks),
        "doneCount": len(done_tasks),
        "unprovenDone": unproven_done,
    }


def has(state: Mapping[str, Any], path: str) -> bool:
    """Is a canonical state file filled in, per the doctrine table?"""
    return bool(state.get("present", {}).get(path, False))


# Each cell declares the doctrine paths it reads, so a path this table names
# and `SKILL.md` no longer lists fails the drift test instead of never firing.
# `docs/adr/` is canonical topology but not a cell: the doctrine makes a record
# conditional on a boundary decision, so its absence is not a gap by itself.
FLOW: tuple[tuple[str, tuple[str, ...], Callable[[Mapping[str, Any]], bool],
                  Callable[[Mapping[str, Any]], str]], ...] = (
    (
        "interview",
        ("docs/REQUIREMENTS.md",),
        lambda st: not has(st, "docs/REQUIREMENTS.md"),
        lambda st: "docs/REQUIREMENTS.md is missing or empty; interview scope before architecting",
    ),
    (
        "promote-spec",
        ("docs/REQUIREMENTS.md", "docs/SPEC/"),
        lambda st: has(st, "docs/REQUIREMENTS.md") and not has(st, "docs/SPEC/"),
        lambda st: "requirements exist but docs/SPEC/ has no committed contracts; promote requirements to a spec",
    ),
    (
        "declare-glossary",
        ("docs/SPEC/", "docs/GLOSSARY.md"),
        lambda st: has(st, "docs/SPEC/") and not has(st, "docs/GLOSSARY.md"),
        lambda st: "contracts exist in docs/SPEC/ but docs/GLOSSARY.md is missing; define ubiquitous language before code",
    ),
    (
        "sync-roadmap",
        ("ROADMAP.md",),
        lambda st: not has(st, "ROADMAP.md") or st.get("totalTasks", 0) == 0,
        lambda st: "ROADMAP.md is missing or carries no burndown tasks; establish the state machine",
    ),
    (
        "advance-task",
        (),
        lambda st: st.get("totalTasks", 0) > 0
        and st.get("inProgressCount", 0) == 0
        and st.get("todoCount", 0) > 0,
        lambda st: "tasks exist in ROADMAP.md, but none are marked IN-PROGRESS; advance next task before building",
    ),
    (
        "verify-proof",
        (),
        lambda st: bool(st.get("unprovenDone")),
        lambda st: f"tasks marked DONE lack runtime proof evidence: {', '.join(st.get('unprovenDone', []))}",
    ),
)


def next_action(state: Mapping[str, Any]) -> dict[str, str]:
    """Compute the single next action and why from the current state."""
    for action, _paths, condition, explanation in FLOW:
        if condition(state):
            return {"action": action, "reason": explanation(state)}
    return {"action": "done", "reason": "all genesis gates pass; topology, specs, glossary, and burndown are consistent"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect project topology against Genesis discipline and return next action."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to the target project directory (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit output in JSON format",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 only when all gates pass (action is 'done'), 1 otherwise",
    )

    args = parser.parse_args(argv)
    project_path = Path(args.project_root).resolve()
    state = read_state(project_path)
    result = next_action(state)

    if args.json:
        payload = {
            "state": state,
            "nextAction": result["action"],
            "reason": result["reason"],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Action: {result['action']}")
        print(f"Reason: {result['reason']}")

    if args.check and result["action"] != "done":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
