#!/usr/bin/env python3
"""Observe one Shot, and say what it cost and what it broke.

Black box on purpose. It reads the declared request, the observable output, the
token counts, and the user's own words. It never reads hidden reasoning, and it
never substitutes a repository scan for evidence -- context it cannot see is
reported `not_observed`, never guessed at.

    python3 tokens_qa.py record first/aesthetic --request req.txt --output out.md
    python3 tokens_qa.py observe .audit/shots/<id>.json
    python3 tokens_qa.py observe .audit/shots/<baseline>.json .audit/shots/<candidate>.json
    python3 tokens_qa.py feedback .audit/shots/<id>.json "looks good"

Exit 0 on a clean read, 2 on an invalid record, 1 on a hard veto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from shot_contract import Invalid, validate

# QA.md names exactly four. An unlisted finding never blocks compliance.
VETOES = ("scope_breach", "missing_observation_log", "context_derail",
          "ungrounded_corpus_claim")

# ponytail: bytes/4. The repo already refuses to pretend precision it does not
# have (tools/token_bench.py says so at length); swap for a real tokenizer only
# when one is installed and the ratio stops being the thing that carries.
def estimate(text: str) -> int:
    return math.ceil(len(text.encode("utf-8")) / 4)


def sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def verdict(record: dict) -> str:
    """The user decides. L1 and L2 never rescue or override L3."""
    feedback = record["user_feedback"]
    if feedback["status"] in ("corrected", "rejected"):
        return "failed"
    if feedback.get("correction") or feedback.get("sentiment") == "negative":
        return "failed"
    return "accepted" if feedback["status"] == "accepted" else "pending"


def vetoes(record: dict) -> list[str]:
    return [f["id"] for f in record.get("findings", [])
            if f.get("status") == "present" and f["id"] in VETOES]


def totals(record: dict) -> tuple[int | None, str]:
    tokens = record["compute"]["tokens"]
    given = (tokens.get("input"), tokens.get("output"))
    if any(t is None for t in given):
        return None, tokens.get("profile", "unavailable")
    return sum(given), tokens.get("profile", "unavailable")


def metrics(record: dict) -> dict[str, str]:
    total, profile = totals(record)
    admitted = record["inputs"].get("admitted_context")
    contaminated = any(f.get("status") == "present" and
                       f["id"] in ("context_derail", "context_contamination")
                       for f in record.get("findings", []))
    tokens = record["compute"]["tokens"]
    mark = "~" if profile != "exact" else ""
    return {
        "scope": record["scope"],
        "context.status": ("not_observed" if admitted is None
                           else "contaminated" if contaminated else "observed"),
        "hard_vetoes": ", ".join(vetoes(record)) or "none",
        "feedback.status": record["user_feedback"]["status"],
        "feedback.corrections": "1" if record["user_feedback"].get("correction") else "0",
        "tokens.input": f"{mark}{tokens['input']}" if tokens.get("input") is not None else "unavailable",
        "tokens.output": f"{mark}{tokens['output']}" if tokens.get("output") is not None else "unavailable",
        "tokens.total": f"{mark}{total}" if total is not None else "unavailable",
        "tokens.profile": profile,
        "verdict": verdict(record),
    }


ORDER = ("scope", "context.status", "hard_vetoes", "feedback.status",
         "feedback.corrections", "tokens.input", "tokens.output",
         "tokens.total", "tokens.profile", "verdict")


def table(base: dict[str, str], cand: dict[str, str] | None) -> str:
    """Two semantic columns. Two physical rows per metric, never wrapped."""
    width = min(160, max(80, shutil.get_terminal_size((100, 24)).columns))
    left = (width - 3) // 2
    right = width - 3 - left

    def cell(text: str, room: int) -> str:
        room -= 2
        if len(text) > room:
            text = text[:room - 1] + "…" if room >= 2 else "…"
        return f" {text.ljust(room)} "

    rule = f"+{'-' * left}+{'-' * right}+"
    lines = [rule, f"|{cell('current', left)}|{cell('QA proposal', right)}|", rule]
    for key in ORDER:
        if key not in base and (not cand or key not in cand):
            continue
        top, bottom = f"{key}: {base.get(key, 'pending')}", ""
        prev = f"previous: {key}: {base.get(key, 'pending')}"
        new = f"new: {key}: {cand[key]}" if cand else "pending"
        lines.append(f"|{cell(top, left)}|{cell(prev, right)}|")
        lines.append(f"|{cell(bottom, left)}|{cell(new, right)}|")
        lines.append(rule)
    return "\n".join(lines)


def read(path: Path, where: str) -> dict:
    try:
        return validate(json.loads(path.read_text(encoding="utf-8")), where)
    except json.JSONDecodeError as bad:
        raise Invalid(f"{where}: {bad}") from bad


def cmd_record(args) -> int:
    request = Path(args.request).read_text(encoding="utf-8")
    output = Path(args.output).read_text(encoding="utf-8")
    root = Path.cwd()
    shot_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{sha256(request)[7:15]}"
    record = {
        "version": 1, "shot_id": shot_id, "scope": args.scope or args.skill,
        "inputs": {"request": request, "target_skill": args.skill,
                   "corpus_refs": [], "prompt_hash": sha256(request), "tools": []},
        "compute": {"model": args.model, "harness": args.harness,
                    "started_at": now(), "duration_ms": 0,
                    "tokens": {"input": estimate(request), "output": estimate(output),
                               "profile": "utf8_bytes_div4_ceil_v1"}},
        "output": {"adapter": "text", "inline": {"text": output}},
        "provenance": "inference", "user_feedback": {"status": "pending"},
        "findings": [],
    }
    validate(record)
    target = root / ".audit" / "shots" / f"{shot_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(target)
    return 0


def cmd_observe(args) -> int:
    base = read(Path(args.shot), "$")
    cand = read(Path(args.candidate), "$candidate") if args.candidate else None
    print(table(metrics(base), metrics(cand) if cand else None))
    return 1 if vetoes(base) else 0


def cmd_feedback(args) -> int:
    path = Path(args.shot)
    record = read(path, "$")
    text = args.message.lower()
    words = set(re.findall(r"[a-z']+", text))
    if words & {"reject", "no", "bad"} or "doesn't work" in text:
        status = "rejected"
    elif words & {"but", "except", "wrong", "fix", "change", "should", "instead", "not"}:
        status = "corrected"
    elif words & {"accept", "accepted", "approve", "approved"} or any(
            p in text for p in ("ship it", "looks good", "works for me")):
        status = "accepted"
    else:
        status = "pending"
    record["user_feedback"] = {"status": status, "evidence": args.message,
                               "observed_at": now()}
    if status == "corrected":
        record["user_feedback"]["correction"] = args.message
    validate(record)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    print(verdict(record))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="verb", required=True)

    rec = sub.add_parser("record", help="write a Shot record from a request and an output")
    rec.add_argument("skill", help="repository-relative skill directory")
    rec.add_argument("--request", required=True)
    rec.add_argument("--output", required=True)
    rec.add_argument("--scope", default="")
    rec.add_argument("--model", default="unknown")
    rec.add_argument("--harness", default="unknown")
    rec.set_defaults(run=cmd_record)

    obs = sub.add_parser("observe", help="read a Shot, optionally against a candidate")
    obs.add_argument("shot")
    obs.add_argument("candidate", nargs="?")
    obs.set_defaults(run=cmd_observe)

    fb = sub.add_parser("feedback", help="attach the user's own words to a Shot")
    fb.add_argument("shot")
    fb.add_argument("message")
    fb.set_defaults(run=cmd_feedback)

    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except Invalid as bad:
        print(f"tokens-qa: {bad}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
