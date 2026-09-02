#!/usr/bin/env python3
"""Move a channel branch to the tree `publish.py` generates.

`publish.py` ends at a directory and says so: producing the tree and moving a
branch to it are separate acts, so a bad publish is a directory you delete
rather than a history you rewrite. That second act was never written down, so
it was done by hand, and then it was not done at all -- `alpha` sat four hours
behind `dev` while `kit sync` faithfully installed the stale tree.

This is that act, and nothing more. It publishes, commits the result to the
channel branch, and refuses anything it cannot verify.

    python3 tools/release.py --channel alpha            # commit locally
    python3 tools/release.py --channel alpha --push     # and push it
    python3 tools/release.py --channel alpha --dry-run  # what would change
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*argv: str, cwd: Path = ROOT) -> str:
    done = subprocess.run(("git", *argv), cwd=cwd, capture_output=True, text=True)
    if done.returncode != 0:
        raise SystemExit(f"release: git {' '.join(argv)}: {done.stderr.strip()}")
    return done.stdout.strip()


def blocking_changes(porcelain: str) -> list[str]:
    """Tracked changes only.

    `publish.py` ships what git tracks, so an untracked stray cannot reach a
    published tree. Refusing the release over one only forced a stash-and-pop
    around the release, which is a conflict risk taken on to avoid a file that
    was never going to be published.
    """
    return [line for line in porcelain.splitlines()
            if line.strip() and not line.startswith("??")]


def worktree_holding(listing: str, channel: str) -> str | None:
    """The worktree already holding `channel`, from `worktree list --porcelain`.

    `worktree add --force` will happily check a branch out twice. The second
    checkout leaves the first reporting staged changes nobody made, and a
    commit there silently reverts the release.
    """
    path = ""
    for line in listing.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line == f"branch refs/heads/{channel}":
            return path
    return None


def divergence(counts: str) -> tuple[int, int]:
    """`rev-list --left-right --count channel...origin/channel` as (ahead, behind)."""
    ahead, behind = counts.split()
    return int(ahead), int(behind)


def diff_tree(left: Path, right: Path) -> list[str]:
    """Repo-relative paths that differ between two trees, recursively."""
    changed = []

    def walk(a: Path, b: Path, prefix: str = "") -> None:
        cmp = filecmp.dircmp(a, b)
        for name in cmp.left_only:
            changed.append(f"- {prefix}{name}")
        for name in cmp.right_only:
            changed.append(f"+ {prefix}{name}")
        for name in cmp.diff_files:
            changed.append(f"M {prefix}{name}")
        for name in cmp.common_dirs:
            walk(a / name, b / name, f"{prefix}{name}/")

    walk(left, right)
    return sorted(changed)


def release(channel: str, push: bool, dry_run: bool) -> int:
    dirty = blocking_changes(git("status", "--porcelain"))
    if dirty:
        raise SystemExit("release: tracked changes are uncommitted; commit or "
                         "stash first:\n  " + "\n  ".join(dirty))
    source = git("rev-parse", "--short", "HEAD")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")

    held = worktree_holding(git("worktree", "list", "--porcelain"), channel)
    if held:
        raise SystemExit(
            f"release: {channel} is checked out at {held}, and checking it out "
            f"again would leave that worktree reporting changes nobody made.\n"
            f"  git worktree remove {held}    # or `git worktree prune` if it is gone")

    git("fetch", "origin", channel)
    ahead, behind = divergence(
        git("rev-list", "--left-right", "--count", f"{channel}...origin/{channel}"))
    if behind:
        raise SystemExit(
            f"release: {channel} is {behind} commit(s) behind origin/{channel}. "
            f"Committing on it would push non-fast-forward and leave it diverged.\n"
            f"  git fetch origin {channel} && git branch -f {channel} origin/{channel}")

    with tempfile.TemporaryDirectory(prefix="cyber-skills-release-") as temp:
        out, work = Path(temp) / "tree", Path(temp) / "branch"
        subprocess.run([sys.executable, "tools/publish.py", "--out", str(out),
                        "--channel", channel, "--check"], cwd=ROOT, check=True)

        # A worktree, not a checkout: the release never moves HEAD, so an
        # interrupted run leaves the branch you were working on exactly where
        # it was. `--force` because the branch is usually checked out nowhere.
        git("worktree", "add", "--force", str(work), channel)
        try:
            changed = diff_tree(work, out)
            if not changed:
                print(f"release: {channel} already matches {branch} {source}")
                return 0
            print(f"{len(changed)} path(s) differ:")
            for line in changed[:40]:
                print(f"  {line}")
            if len(changed) > 40:
                print(f"  ... and {len(changed) - 40} more")
            if dry_run:
                return 0

            for item in work.iterdir():
                if item.name == ".git":
                    continue
                shutil.rmtree(item) if item.is_dir() else item.unlink()
            for item in out.iterdir():
                dest = work / item.name
                shutil.copytree(item, dest) if item.is_dir() else shutil.copy2(item, dest)

            git("add", "-A", cwd=work)
            git("commit", "-m", f"publish: {channel} channel from {branch} {source}", cwd=work)
            head = git("rev-parse", "--short", channel)
            print(f"release: {channel} -> {head}")
            if push:
                git("push", "origin", channel, cwd=work)
                print(f"release: pushed {channel} {head}")
            else:
                print(f"release: not pushed; `git push origin {channel}` when ready")
        finally:
            git("worktree", "remove", "--force", str(work))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--channel", default="alpha", choices=("main", "alpha"))
    parser.add_argument("--push", action="store_true", help="push the branch after committing")
    parser.add_argument("--dry-run", action="store_true", help="report the diff and stop")
    args = parser.parse_args(argv)
    return release(args.channel, args.push, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
