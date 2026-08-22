#!/usr/bin/env python3
"""Refuse a published tree that still carries development fog.

`publish.py` builds the tree correctly. This proves it, so the contract
survives someone copying files by hand, a merge that drags `main` sideways,
or a future edit to the fog list that misses a case. A rule the model can
read and skip is not a rule; this one exits non-zero.

    python3 tools/check_publication.py /tmp/published
    python3 tools/check_publication.py            # checks the repo root
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fog import is_fog, reasons

SKIP_DIRS = {".git", "__pycache__"}


def check(tree: Path) -> int:
    found = []
    for path in sorted(tree.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(tree)
        if any(part in SKIP_DIRS or part.startswith(".git") for part in relative.parts):
            continue
        if relative.name == ".DS_Store":
            continue
        if is_fog(relative.as_posix()):
            found.append(relative.as_posix())
    if not found:
        print(f"OK: {tree} carries no development fog.")
        return 0
    why = reasons()
    print(f"FAIL: {len(found)} fog file(s) in {tree}", file=sys.stderr)
    for item in found:
        note = next((text for key, text in why.items()
                     if item == key or item.startswith(key + "/")
                     or Path(item).match(key)), "development state")
        print(f"  {item}\n      {note}", file=sys.stderr)
    print("\nA published tree is what an agent loads. Every file here costs it "
          "context it cannot spend on the work.", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tree", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    return check(args.tree.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
