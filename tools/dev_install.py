#!/usr/bin/env python3
"""Point the installed skills at this checkout, so edits are live.

`kit sync` installs copies cloned from GitHub. Editing through the installed
path then edits a copy the next sync overwrites, which is B-027: work lost
with a clean `git status` and every gate green. Symlinking instead makes the
installed path and the source the same bytes.

    python3 tools/dev_install.py --dry-run
    python3 tools/dev_install.py
    python3 tools/dev_install.py --undo      # back to whatever kit sync last put there

Re-run after any `kit sync`, which replaces symlinks with copies again.

A copy that matches a published channel byte for byte is what sync put there,
not an edit, even though publication rewrites it away from `dev`. And a skill
that sync never installed has no per-agent link, so the store link alone
leaves it invisible; missing agent links are added the way `npx skills` does.
"""
from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_discovery import catalog

ROOT = Path(__file__).resolve().parent.parent
STORE = Path.home() / ".agents" / "skills"
AGENTS = [Path.home() / ".claude" / "skills"]
CHANNELS = ("alpha", "main", "origin/alpha", "origin/main")

# `cook` is fog and ships on no channel, so `discover` skips it. An owner
# working in this checkout still wants to invoke it.
EXTRA = {"cook": "cook"}


def targets(root: Path) -> dict[str, Path]:
    found = {record.name: root.resolve() / record.path for record in catalog(root)}
    found.update({name: root / rel for name, rel in EXTRA.items()})
    return dict(sorted(found.items()))


def published(rel: str, root: Path = ROOT) -> list[bytes]:
    """Every channel's bytes for one repo path; empty where a channel lacks it."""
    out = []
    for ref in CHANNELS:
        shown = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{rel}"],
                               capture_output=True)
        if shown.returncode == 0:
            out.append(shown.stdout)
    return out


def edited(copy: Path, source: Path, released=lambda rel: []) -> list[str]:
    """Files present in both that differ, so a copy carrying real edits is not
    deleted silently. Files only on one side are the fog split, and a file
    equal to a released version is what sync installed; neither is an edit."""
    out: list[str] = []

    def walk(cmp_: filecmp.dircmp, prefix: str) -> None:
        out.extend(f"{prefix}{name}" for name in cmp_.diff_files
                   if (copy / prefix / name).read_bytes() not in released(f"{prefix}{name}"))
        for name, sub in cmp_.subdirs.items():
            walk(sub, f"{prefix}{name}/")

    walk(filecmp.dircmp(copy, source), "")
    return out


def link_agents(names, store: Path, agents: list[Path], dry_run: bool) -> None:
    """Give each agent a relative link to the store entry it is missing."""
    for agent in agents:
        if not agent.is_dir():
            continue
        for name in names:
            entry = agent / name
            if entry.exists() or entry.is_symlink():
                continue
            print(f"  agent  {agent.parent.name}/{name}")
            if not dry_run:
                entry.symlink_to(os.path.relpath(store / name, agent))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--undo", action="store_true", help="remove the symlinks")
    parser.add_argument("--force", action="store_true",
                        help="replace a copy even when it carries edits")
    args = parser.parse_args(argv)

    if not STORE.is_dir():
        print(f"dev-install: no skill store at {STORE}; run kit sync first")
        return 1

    risky: list[str] = []
    for name, source in targets(ROOT).items():
        installed = STORE / name
        if args.undo:
            if installed.is_symlink():
                print(f"  unlink {name}")
                if not args.dry_run:
                    installed.unlink()
            continue
        if installed.is_symlink() and installed.resolve() == source:
            print(f"  ok     {name}")
            continue
        if installed.is_dir() and not installed.is_symlink():
            rel = source.relative_to(ROOT.resolve()).as_posix()
            changed = edited(installed, source,
                             lambda path: published(f"{rel}/{path}"))
            if changed and not args.force:
                risky.append(f"{name}: {', '.join(changed[:3])}")
                continue
        print(f"  link   {name} -> {source}")
        if args.dry_run:
            continue
        if installed.is_symlink() or installed.is_file():
            installed.unlink()
        elif installed.is_dir():
            shutil.rmtree(installed)
        installed.symlink_to(source)

    if not args.undo:
        link_agents(targets(ROOT), STORE, AGENTS, args.dry_run)
    if risky:
        print("\ndev-install: these installed copies differ from the checkout, so\n"
              "replacing them would discard edits made through the installed path:")
        for line in risky:
            print(f"  {line}")
        print("Diff them, then re-run with --force.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
