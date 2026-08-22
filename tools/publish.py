#!/usr/bin/env python3
"""Build the fog-free tree that `main` publishes.

Generating the published tree rather than curating it by hand is the whole
point: a rule that says "remember not to commit the roadmap to main" is a rule
someone forgets on a tired evening. This copies what belongs and skips what
does not, so forgetting is not one of the available outcomes.

    python3 tools/publish.py --out /tmp/published        # inspect it
    python3 tools/publish.py --out /tmp/published --check # and verify it

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
from fog import is_fog

# `.git` only, never a `.git*` prefix -- that silently dropped .gitignore
# from every published tree, so main would have started committing __pycache__.
SKIP_DIRS = {".git", "__pycache__"}


def published_paths(root: Path) -> list[Path]:
    """Every file that belongs in a published tree, repo-relative."""
    keep = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if relative.name == ".DS_Store":
            continue
        if is_fog(relative.as_posix()):
            continue
        keep.append(relative)
    return keep


def publish(root: Path, out: Path) -> tuple[int, int]:
    """Copy the published tree to `out`. Returns (kept, skipped)."""
    every = [p.relative_to(root) for p in sorted(root.rglob("*")) if p.is_file()
             and not any(part in SKIP_DIRS for part in p.relative_to(root).parts)]
    keep = published_paths(root)
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
    parser.add_argument("--check", action="store_true",
                        help="verify the result carries no fog")
    args = parser.parse_args()
    root = args.root.resolve()
    kept, skipped = publish(root, args.out.resolve())
    print(f"Published {kept} file(s) to {args.out}; left {skipped} fog file(s) on dev.")
    if args.check:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from check_publication import check
        return check(args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
