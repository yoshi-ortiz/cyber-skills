#!/usr/bin/env python3
"""Eval: did any rank the USER set actually reach the ledger?

The question this skill exists to answer. A session where this returns zero has
produced nothing, however many screens were made.
"""

import json
import sys
from pathlib import Path


def main() -> int:
    project = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    ledger = project / "spec" / "design-harness" / "decisions.json"
    if not ledger.is_file():
        print("FAIL  no ledger")
        return 1

    elements = json.loads(ledger.read_text())["elements"]
    user = [e for e in elements if e.get("source") == "user"]
    agent = [e for e in elements if e.get("source") != "user"]
    overrank = [e for e in agent if e.get("stars", 0) > 1]

    print(f"user-set  : {len(user)}")
    print(f"agent-set : {len(agent)}")
    for entry in sorted(user, key=lambda x: -x["stars"])[:5]:
        print(f"  {entry['stars']}* {entry['state']:9s} {entry['element']}")

    bad = 0
    if not user:
        print("FAIL  no user-set rank in the ledger -- feedback was never captured")
        bad += 1
    if overrank:
        names = ", ".join(e["element"] for e in overrank[:5])
        print(f"FAIL  {len(overrank)} agent-set rank(s) above the cap: {names}")
        bad += 1
    print("PASS  user feedback is reaching the ledger" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
