#!/usr/bin/env python3
"""Query bounded Repo-Dev facts without loading the rail's whole history."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from skill_discovery import catalog, owner_of

ROOT = Path(__file__).resolve().parents[1]
STATE = re.compile(r"\b(TODO|IN-PROGRESS|BLOCKED|DONE)\b")
LINK = re.compile(r"\[([^]]+)]\([^)]+\)")
BUG_HEADING = re.compile(r"^## (B-\d+)\s+·\s+(.+?)\s+·\s+(.+)$")


def _cell(text: str) -> str:
    text = LINK.sub(r"\1", text)
    return text.replace("`", "").strip()


def _tables(path: Path) -> list[dict[str, str]]:
    """Read every Markdown table by its headers, regardless of column order."""
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, str]] = []
    index = 0
    while index + 1 < len(lines):
        line = lines[index]
        separator = lines[index + 1]
        if not line.startswith("|") or not separator.startswith("|") \
                or not re.fullmatch(r"[|:\- ]+", separator):
            index += 1
            continue
        headers = [_cell(part).lower() for part in line.strip("|").split("|")]
        index += 2
        while index < len(lines) and lines[index].startswith("|"):
            values = [_cell(part) for part in lines[index].strip("|").split("|")]
            values += [""] * (len(headers) - len(values))
            rows.append(dict(zip(headers, values)))
            index += 1
    return rows


def roadmap_rows(root: Path) -> list[dict[str, str]]:
    rows = []
    for row in _tables(root / "ROADMAP.md"):
        identity = row.get("id", "")
        if not re.fullmatch(r"R-\d+", identity):
            continue
        match = STATE.search(row.get("state", ""))
        if not match:
            continue
        rows.append({**row, "id": identity, "state": match.group(1)})
    return rows


def roadmap_state(root: Path, state: str) -> list[dict[str, str]]:
    wanted = state.upper()
    if wanted not in {"TODO", "IN-PROGRESS", "BLOCKED", "DONE"}:
        raise ValueError(f"unknown roadmap state {state!r}")
    return [row for row in roadmap_rows(root) if row["state"] == wanted]


def _exact_roadmap_item(root: Path, identity: str) -> dict[str, str]:
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
    return {"goal": evidence, "roadmap": _exact_roadmap_item(root, identity)}


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
    record = next((candidate for candidate in records
                   if query in candidate.names), None)
    if record is None:
        record = owner_of(Path(query), records)
    if record is None:
        raise LookupError(f"no catalog module owns {query!r}")
    return {"name": record.name, "family": record.family,
            "channel": record.channel, "origin": record.origin,
            "path": record.path.as_posix(),
            "context": (record.path / "CONTEXT.md").as_posix()}


def summary(root: Path) -> dict[str, object]:
    goal = next((line.strip() for line in (root / "GOAL.md").read_text(
        encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")), "")
    return {
        "goal": goal,
        "in_progress": roadmap_state(root, "IN-PROGRESS"),
        "modules": [module_context(root, record.name) for record in catalog(root)],
    }


def _print_human(result: object) -> None:
    if isinstance(result, list):
        for row in result:
            print(f"{row.get('id')}  {row.get('state', '')}  {row.get('item', '')}".rstrip())
    elif isinstance(result, dict):
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("summary")
    state = commands.add_parser("state")
    state.add_argument("state")
    item = commands.add_parser("item")
    item.add_argument("id")
    bug = commands.add_parser("bug")
    bug.add_argument("id", nargs="?")
    bug.add_argument("--latest", action="store_true")
    module = commands.add_parser("module")
    module.add_argument("query")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "summary":
            result = summary(root)
        elif args.command == "state":
            result = roadmap_state(root, args.state)
        elif args.command == "item":
            result = item_context(root, args.id)
        elif args.command == "bug":
            result = latest_bug(root) if args.latest else exact_bug(root, args.id)
        else:
            result = module_context(root, args.query)
    except (LookupError, ValueError) as error:
        print(f"repo-context: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        _print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
