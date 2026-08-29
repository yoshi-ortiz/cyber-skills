#!/usr/bin/env python3
"""Build the fog-free tree that `main` publishes.

Generating the published tree rather than curating it by hand is the whole
point: a rule that says "remember not to commit the roadmap to main" is a rule
someone forgets on a tired evening. This copies what belongs and skips what
does not, so forgetting is not one of the available outcomes.

    python3 tools/publish.py --out /tmp/published        # inspect it
    python3 tools/publish.py --out /tmp/published --check # and verify it
    python3 tools/publish.py --out /tmp/alpha --channel alpha --check

Nothing here touches git. Producing the tree and moving a branch to it are
separate acts, so a bad publish is a directory you delete rather than a
history you rewrite.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fog import is_fog, walk


def published_paths(root: Path, channel: str = "main") -> list[Path]:
    """Every file that belongs in a published tree, repo-relative."""
    return [relative for relative in walk(root)
            if not is_fog(relative.as_posix(), channel)]


def publish(root: Path, out: Path, channel: str = "main") -> tuple[int, int]:
    """Copy the published tree to `out`. Returns (kept, skipped)."""
    every = walk(root)
    keep = published_paths(root, channel)
    if out.exists():
        shutil.rmtree(out)
    for relative in keep:
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
    return (len(keep), len(every) - len(keep))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--channel", default="main", choices=("main", "alpha"),
                        help="main drops alpha skills; alpha carries them")
    parser.add_argument("--check", action="store_true",
                        help="verify the result carries no fog")
    args = parser.parse_args()
    root = args.root.resolve()
    kept, skipped = publish(root, args.out.resolve(), args.channel)
    print(f"Published {kept} file(s) to {args.out} on the {args.channel} channel; "
          f"left {skipped} file(s) on dev.")
    if args.check:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from check_publication import check
        return check(args.out.resolve(), args.channel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
