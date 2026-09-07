#!/usr/bin/env python3
"""Adopt one live Aesthetic turn and return its current domain state."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
TOKENS_QA = REPO_ROOT / "check" / "tokens-qa" / "scripts" / "tokens_qa.py"
RUN_ID = re.compile(r"^[^@\s]+@\d{4}-\d{2}-\d{2}T[^\s]+$")


class AssistantAppError(ValueError):
    pass


def _run(command: list[str], cwd: Path) -> str:
    done = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True)
    if done.returncode:
        raise AssistantAppError((done.stderr or done.stdout).strip())
    return done.stdout


def sync(project_root: Path, decisions: Path, invocation: str,
         turns: list[str]) -> dict:
    """Check the companion, adopt its three queues, then audit the turn once."""
    root = Path(project_root).resolve(strict=True)
    if not RUN_ID.fullmatch(invocation):
        raise AssistantAppError("invocation must use skill@timestamp")

    _run([sys.executable, str(HERE / "companion_doctor.py"), str(root), "--quiet"], root)

    from harness_adoption import adopt_companion
    from harness_ledger import load_decisions
    from brief_workflow import BRIEF_INBOX_FILE, adopt_brief_inbox, load_brief
    from corpus_tags import DEFAULT_INBOX, adopt_inbox, load_tags

    ranked, rank_skipped = (adopt_companion(root, decisions)
                            if Path(decisions).is_file() else (0, 0))
    base = root / ".superpowers" / "brainstorm"
    briefed, brief_skipped = adopt_brief_inbox(root, base / BRIEF_INBOX_FILE)
    tagged, tag_skipped = adopt_inbox(root, root / DEFAULT_INBOX)

    with tempfile.TemporaryDirectory(prefix="aesthetic-turn-") as staging:
        evidence = Path(staging) / "turns.json"
        evidence.write_text(json.dumps({"turns": turns}), encoding="utf-8")
        raw = _run([sys.executable, str(TOKENS_QA), "shot-audit",
                    "--evidence", str(evidence), "--json"], REPO_ROOT)
    envelope = json.loads(raw)
    if not envelope.get("ok"):
        raise AssistantAppError(str(envelope.get("error") or "shot-audit failed"))

    return {
        "invocation": invocation,
        "ranking": {"adopted": ranked, "skipped": rank_skipped,
                    "state": load_decisions(root / "spec" / "design-harness")},
        "brief": {"adopted": briefed, "skipped": brief_skipped,
                  "state": load_brief(root)},
        "corpusTags": {"adopted": tagged, "skipped": tag_skipped,
                       "state": load_tags(root)},
        "feedback": envelope["result"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--companion-ledger", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--turn", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        result = sync(args.project_root, args.companion_ledger,
                      args.invocation, args.turn)
    except (AssistantAppError, OSError, json.JSONDecodeError) as exc:
        print(f"assistant-app: {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
