#!/usr/bin/env python3
"""Read-only target-project Burndown selection, using only the standard library.

Tables need ID and State headers. Nonempty Workstream opts a row into managed
validation and automatic selection. Depends on contains comma/semicolon-separated
IDs. Priority is a nonnegative integer, lower first; blank sorts last. Deferred
accepts true/false, yes/no, or 1/0. Legacy dependency prose remains readable but
cannot establish eligibility. select raises ValueError for invalid state or an
ineligible explicit item. No selection returns next_action=no-ready-item; it
never implies completion or authorizes work. Shot closure belongs to the caller.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

STATES = {"TODO", "IN-PROGRESS", "BLOCKED", "DONE"}
EMPTY = {"", "-", "—", "–"}
TRUE = {"true", "yes", "1"}
FALSE = {"false", "no", "0"} | EMPTY


def _cell(value: str) -> str:
    return re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value).replace("`", "").strip()


def _cells(line: str) -> list[str]:
    return [_cell(cell.replace(r"\|", "|"))
            for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def roadmap_rows(root: Path) -> list[dict[str, str]]:
    """Return header-keyed string dictionaries, preserving legacy extra columns."""
    lines = (Path(root) / "ROADMAP.md").read_text(encoding="utf-8").splitlines()
    rows = []
    headers = []
    fence = ""
    for index, line in enumerate(lines):
        stripped = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if marker:
            token = marker.group(1)
            if not fence:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = ""
            headers = []
            continue
        if fence:
            continue
        if "|" not in stripped:
            headers = []
            continue
        cells = _cells(stripped)
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            headers = [_cell(cell).lower() for cell in _cells(lines[index - 1])] if index else []
            if "id" not in headers or "state" not in headers:
                headers = []
            continue
        if not headers:
            continue
        row = dict(zip(headers, cells + [""] * len(headers)))
        # Existing roadmaps use empty identity/state rows as section labels.
        if not any(row.get(key, "") for key in ("id", "state", "workstream")):
            continue
        state = row["state"]
        match = re.fullmatch(r"[^\w]*\b(TODO|IN-PROGRESS|BLOCKED|DONE)\b[^\w]*", state)
        if match:
            row["state"] = match.group(1)
        rows.append(row)
    return rows


def _dependencies(row: dict[str, str]) -> list[str]:
    value = row.get("depends on", "")
    return [] if value in EMPTY else [part.strip() for part in re.split(r"[,;]", value)]


def _errors(rows: list[dict[str, str]]) -> list[str]:
    errors = []
    by_id = {}
    active = {}
    for row in rows:
        identity = row["id"]
        if not identity:
            errors.append("roadmap row has empty ID")
        elif identity in by_id:
            errors.append(f"duplicate ID: {identity}")
        by_id[identity] = row
        if row["state"] not in STATES:
            errors.append(f"{identity}: invalid state {row['state']!r}")
        stream = row.get("workstream", "")
        if not stream:
            continue
        for field in ("priority", "budget tokens"):
            value = row.get(field, "")
            if value not in EMPTY and not re.fullmatch(r"[0-9]+", value):
                errors.append(f"{identity}: {field} must be a nonnegative integer")
        if row.get("deferred", "").lower() not in TRUE | FALSE:
            errors.append(f"{identity}: invalid deferred value")
        if row["state"] == "IN-PROGRESS":
            if stream in active:
                errors.append(f"{stream}: multiple IN-PROGRESS items: {active[stream]}, {identity}")
            active[stream] = identity
    graph = {}
    for row in rows:
        if not row.get("workstream"):
            continue
        identity = row["id"]
        deps = _dependencies(row)
        for dep in deps:
            if dep not in by_id or not dep:
                errors.append(f"{identity}: unresolved dependency {dep!r}")
            elif row["state"] == "IN-PROGRESS" and by_id[dep]["state"] != "DONE":
                errors.append(f"{identity}: active dependency {dep} is not DONE")
        graph[identity] = {dep for dep in deps if dep in by_id and by_id[dep].get("workstream")}
    # Iterative removal also handles roadmaps deeper than Python's recursion limit.
    while graph:
        leaves = {identity for identity, deps in graph.items() if not deps}
        if not leaves:
            errors.append("managed dependency cycle: " + ", ".join(sorted(graph)))
            break
        graph = {identity: deps - leaves for identity, deps in graph.items() if identity not in leaves}
    return errors


def check(root: Path) -> list[str]:
    """Return structural errors; missing or unreadable ROADMAP.md is an error."""
    try:
        return _errors(roadmap_rows(root))
    except (OSError, UnicodeError) as exc:
        return [f"cannot read ROADMAP.md: {exc}"]


def select(root: Path, item: str = "", workstream: str = "default") -> dict[str, str]:
    """Return one bounded set of fields, or no-ready-item; never mutate state."""
    rows = roadmap_rows(root)
    errors = _errors(rows)
    if errors:
        raise ValueError("; ".join(errors))
    by_id = {row["id"]: row for row in rows}

    def eligible(row: dict[str, str]) -> bool:
        return (row["state"] in {"TODO", "IN-PROGRESS"}
                and row.get("deferred", "").lower() in FALSE
                and all(dep in by_id and by_id[dep]["state"] == "DONE"
                        for dep in _dependencies(row)))

    if item:
        if item not in by_id:
            raise ValueError(f"unknown item: {item}")
        chosen = by_id[item]
        if not eligible(chosen):
            raise ValueError(f"item is not eligible: {item}")
    else:
        candidates = [row for row in rows if row.get("workstream") == workstream
                      and workstream and eligible(row)]
        if not candidates:
            return {"workstream": workstream, "next_action": "no-ready-item"}
        chosen = min(candidates, key=lambda row: (
            row["state"] != "IN-PROGRESS",
            int(row["priority"]) if row.get("priority", "") not in EMPTY else float("inf")))
    return {"id": chosen["id"], "item_id": chosen["id"], "item": chosen.get("item", ""),
            "state": chosen["state"], "workstream": chosen.get("workstream", ""),
            "scope": chosen.get("scope", ""), "proof": chosen.get("proof", ""),
            "budget_tokens": chosen.get("budget tokens", ""),
            "next_action": "continue-task" if chosen["state"] == "IN-PROGRESS" else "advance-task"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    next_parser = commands.add_parser("next", help="Select eligible work without changing it")
    next_parser.add_argument("--item", default="")
    next_parser.add_argument("--workstream", default="default")
    commands.add_parser("check", help="Validate roadmap structure")
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            errors = check(args.project_root)
            result = {"ok": not errors, "errors": errors}
        else:
            result = select(args.project_root, args.item, args.workstream)
            errors = []
    except (OSError, UnicodeError, ValueError) as exc:
        errors = [str(exc)]
        result = {"ok": False, "errors": errors}
    print(json.dumps(result, ensure_ascii=False))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
