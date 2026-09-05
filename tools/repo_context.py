#!/usr/bin/env python3
"""Query bounded Repo-Dev facts without loading the rail's whole history."""
from __future__ import annotations

import argparse
import json
import re
import sys
import subprocess
from pathlib import Path

from skill_discovery import catalog, owner_of

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "first/genesis/scripts"))
import compass

QA = ROOT / "check/tokens-qa/scripts/tokens_qa.py"
LINK = re.compile(r"\[([^]]+)]\([^)]+\)")
BUG_HEADING = re.compile(r"^## (B-\d+)\s+·\s+(.+?)\s+·\s+(.+)$")


def _cell(text: str) -> str:
    text = LINK.sub(r"\1", text)
    return text.replace("`", "").strip()


def roadmap_rows(root: Path) -> list[dict[str, str]]:
    return compass.roadmap_rows(root)


def shot_query(root: Path, verb: str, *args: str) -> tuple[int, dict]:
    """The observer owns feedback and proof; this adapter owns the Item join."""
    done = subprocess.run([sys.executable, str(QA), verb, *args,
                           "--project-root", str(root), "--json"],
                          capture_output=True, text=True, timeout=30)
    envelope = json.loads(done.stdout)
    if done.returncode not in (0, 1):
        raise ValueError(envelope.get("error") or done.stderr or "Shot query failed")
    return done.returncode, envelope.get("result") or {}


def next_feature(root: Path, item: str = "", workstream: str = "default") -> dict:
    errors = check_compass(root)
    if errors:
        raise ValueError("; ".join(errors))
    selected = compass.select(root, item=item, workstream=workstream)
    identity = selected.get("item_id")
    if not identity:
        return selected
    _, history = shot_query(root, "history", "--item-id", identity)
    selected["observations"] = history
    if not selected.get("scope") or not selected.get("proof"):
        selected["next_action"] = "bound-task"
        return selected
    latest = history.get("latest")
    if latest:
        if latest["verdict"] == "failed":
            selected["next_action"] = "apply-correction"
        elif latest["verdict"] == "pending":
            selected["next_action"] = "await-feedback"
        else:
            code, _ = shot_query(root, "gate", latest["path"])
            selected["next_action"] = "close-item" if code == 0 else "verify-proof"
    budget = selected.get("budget_tokens")
    if budget and selected["next_action"] in {"continue-task", "advance-task", "apply-correction"}:
        profiles = history.get("totals_by_profile", {})
        if len(profiles) > 1 or any(b["input"] is None or b["output"] is None for b in profiles.values()):
            selected["next_action"] = "resolve-budget"
        elif sum(b["input"] + b["output"] for b in profiles.values()) >= int(budget):
            selected["next_action"] = "budget-exhausted"
    return selected


def check_compass(root: Path) -> list[str]:
    errors = compass.check(root)
    rows = roadmap_rows(root)
    for row in rows:
        if not row.get("workstream") or row["state"] != "DONE":
            continue
        identity, shot = row["id"], row.get("shot", "")
        if not shot:
            errors.append(f"{identity}: DONE requires a Shot path")
            continue
        path = (root / shot).resolve()
        if not path.is_relative_to(root.resolve() / ".audit/shots"):
            errors.append(f"{identity}: Shot must belong to this project's .audit/shots")
            continue
        code, result = shot_query(root, "gate", str(path))
        _, history = shot_query(root, "history", "--item-id", identity)
        latest = history.get("latest") or {}
        if code or result.get("item_id") != identity or latest.get("shot_id") != result.get("shot_id"):
            errors.append(f"{identity}: latest Shot must be accepted with matching proof and no veto")
    return errors


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
    text = (root / "GOAL.md").read_text(encoding="utf-8")
    text = text.split("## The goal, in one line", 1)[-1]
    paragraphs = re.split(r"\n\s*\n", text.strip())
    goal = next((" ".join(part.split()) for part in paragraphs
                 if part.strip() and not part.startswith("#")), "")
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
    next_cmd = commands.add_parser("next")
    next_cmd.add_argument("--item", default="")
    next_cmd.add_argument("--workstream", default="default")
    commands.add_parser("check")
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
        if args.command == "next":
            result = next_feature(root, args.item, args.workstream)
        elif args.command == "check":
            errors = check_compass(root)
            print(json.dumps({"ok": not errors, "errors": errors}))
            return 1 if errors else 0
        elif args.command == "summary":
            result = summary(root)
        elif args.command == "state":
            result = roadmap_state(root, args.state)
        elif args.command == "item":
            result = item_context(root, args.id)
        elif args.command == "bug":
            result = latest_bug(root) if args.latest else exact_bug(root, args.id)
        else:
            result = module_context(root, args.query)
    except (LookupError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"repo-context: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        _print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
