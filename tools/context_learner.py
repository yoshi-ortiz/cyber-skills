#!/usr/bin/env python3
"""Evaluate one reviewed baseline/candidate context experiment without mutation."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

FIELDS = frozenset({
    "version", "reviewed", "task_id", "repository_revision", "arm", "split",
    "model", "harness", "profile", "budget", "bundle_hash", "trace_hash",
    "outcome", "tokens_input", "tokens_output", "required_context_recall",
    "verdict_source",
})


class LearnerError(ValueError):
    pass


def validate(raw: Any, line: int) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != FIELDS:
        raise LearnerError(f"line {line}: reviewed attempt fields do not match version 1")
    if raw["version"] != 1 or raw["reviewed"] is not True:
        raise LearnerError(f"line {line}: attempt must be version 1 and reviewed")
    for key in ("task_id", "repository_revision", "model", "harness", "profile",
                "bundle_hash", "trace_hash", "verdict_source"):
        if not isinstance(raw[key], str) or not raw[key].strip():
            raise LearnerError(f"line {line}: {key} must be non-empty text")
    if raw["arm"] not in ("baseline", "candidate"):
        raise LearnerError(f"line {line}: arm must be baseline or candidate")
    if raw["split"] not in ("train", "heldout"):
        raise LearnerError(f"line {line}: split must be train or heldout")
    if raw["outcome"] not in ("accepted", "mixed", "rejected"):
        raise LearnerError(f"line {line}: invalid outcome")
    for key in ("budget", "tokens_input", "tokens_output"):
        if not isinstance(raw[key], int) or raw[key] < 0:
            raise LearnerError(f"line {line}: {key} must be a non-negative integer")
    recall = raw["required_context_recall"]
    if not isinstance(recall, (int, float)) or not 0 <= recall <= 1:
        raise LearnerError(f"line {line}: required_context_recall must be 0..1")
    return dict(raw)


def load(path: Path) -> list[dict[str, Any]]:
    rows = []
    for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if text.strip():
            try:
                rows.append(validate(json.loads(text), number))
            except json.JSONDecodeError as exc:
                raise LearnerError(f"line {number}: invalid JSON: {exc}") from exc
    if not rows:
        raise LearnerError("reviewed corpus is empty")
    return rows


def _arms(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    tasks: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in rows:
        if row["split"] == split:
            tasks.setdefault(row["task_id"], {}).setdefault(row["arm"], []).append(row)
    if not tasks:
        raise LearnerError(f"{split} split has no tasks")
    pairs = []
    for task, arms in sorted(tasks.items()):
        if set(arms) != {"baseline", "candidate"}:
            raise LearnerError(f"{split} task {task!r} lacks a baseline/candidate arm")
        controls = {(r["model"], r["harness"], r["profile"], r["budget"])
                    for rows_for_arm in arms.values() for r in rows_for_arm}
        if len(controls) != 1:
            raise LearnerError(f"{split} task {task!r} changes model/harness/profile/budget")
        pair = {"task_id": task}
        for arm, attempts in arms.items():
            pair[arm] = {
                "accepted": any(r["outcome"] == "accepted" for r in attempts),
                "attempts": len(attempts),
                "tokens": sum(r["tokens_input"] + r["tokens_output"] for r in attempts),
                "recall": min(float(r["required_context_recall"]) for r in attempts),
            }
        pairs.append(pair)
    return pairs


def _candidate_wins(pair: dict[str, Any]) -> bool:
    base, candidate = pair["baseline"], pair["candidate"]
    return candidate["accepted"] and candidate["recall"] >= base["recall"] and (
        not base["accepted"] or candidate["tokens"] < base["tokens"])


def evaluate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    train, heldout = _arms(rows, "train"), _arms(rows, "heldout")
    wins = sum(_candidate_wins(pair) for pair in train)
    recommendation = "candidate" if wins > len(train) / 2 else "no-change"
    heldout_passed = recommendation == "candidate" and all(
        _candidate_wins(pair) for pair in heldout)
    accepted = [r for r in rows if r["outcome"] == "accepted"]
    by_arm = {}
    for arm in ("baseline", "candidate"):
        arm_rows = [r for r in rows if r["arm"] == arm]
        costs = [r["tokens_input"] + r["tokens_output"] for r in arm_rows
                 if r["outcome"] == "accepted"]
        by_arm[arm] = {"attempts": len(arm_rows), "accepted": len(costs),
                       "median_tokens_per_accepted": statistics.median(costs) if costs else None}
    return {"version": 1, "recommendation": recommendation,
            "heldout_passed": heldout_passed, "train_pairs": len(train),
            "heldout_pairs": len(heldout), "accepted_attempts": len(accepted),
            "arms": by_arm,
            "note": "advisory only; review before changing declarations or budgets"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        report = evaluate(load(args.corpus))
    except (OSError, LearnerError) as exc:
        print(f"context-learner: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["heldout_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
