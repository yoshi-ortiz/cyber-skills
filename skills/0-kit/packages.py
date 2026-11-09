#!/usr/bin/env python3
"""kit: sync the skills listed in PACK.md through the Vercel `skills` CLI.

  packages.py                      install every PACK.md row
  packages.py owner/repo [flags]   same as `add`
  packages.py add owner/repo --skill a b
  packages.py list|update|remove|check|find ...   passed to `skills`

Defaults for add: global (-g), every agent (-a '*'), every skill (--skill '*'),
no prompts (-y). Pass -a, --skill, -y or --all yourself to override. Pass
--project to install into the current project instead of globally. Pass
--dry-run to print the commands without running them.

Flags: https://github.com/vercel-labs/skills/blob/main/docs/commands.md
"""
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).with_name("PACK.md")
MAX_PACK_BYTES = 4096
CLI = ["npx", "--yes", "skills@" + os.environ.get("KIT_SKILLS_VERSION", "latest")]
VERBS = {"add", "list", "ls", "update", "remove", "rm", "check", "find"}
GLOBAL_VERBS = {"list", "ls", "update", "remove", "rm"}
ROW = re.compile(
    r"^\s*[*-]\s+(?:<img[^>]*>\s*)?\[[^\]]+\]\(https://github\.com/([\w.-]+/[\w.-]+?)/?\)\s*(?::\s*(.*))?$"
)
REPO = re.compile(r"[\w.-]+/[\w.-]+")


def has(args, *names):
    return any(a in names or a.split("=")[0] in names for a in args)


def skills_in(args):
    """Names following --skill/-s, up to the next flag."""
    out, on = [], False
    for a in args:
        if a.startswith("-"):
            on = a in ("-s", "--skill")
        elif on:
            out.append(a)
    return out


def run(cmd, dry):
    print("$ " + shlex.join(cmd), flush=True)
    return 0 if dry else subprocess.call(cmd)


def read_pack():
    size = PACK.stat().st_size
    if size > MAX_PACK_BYTES:
        sys.exit(f"PACK.md is {size} bytes, over the {MAX_PACK_BYTES} cap. Trim it; do not raise the cap.")
    rows = []
    for line in PACK.read_text().splitlines():
        m = ROW.match(line)
        if m:
            rows.append((m.group(1), re.split(r"[,\s]+", m.group(2).strip()) if m.group(2) else []))
    return rows


def add_cmd(source, args):
    cmd = CLI + ["add", source]
    everything = has(args, "--all")
    if "--project" in args:
        args = [a for a in args if a != "--project"]
    elif not has(args, "-g", "--global"):
        cmd.append("-g")
    if not everything and not has(args, "-y", "--yes"):
        cmd.append("-y")
    if not everything and not has(args, "-a", "--agent"):
        cmd += ["-a", "*"]
    cmd += args
    if not everything and not has(args, "-s", "--skill"):
        cmd += ["--skill", "*"]
    return cmd


def persist(repo, skills):
    if not REPO.fullmatch(repo):
        print(f"not recorded in PACK.md: {repo} is not owner/repo")
        return
    if any(r == repo for r, _ in read_pack()):
        print(f"already in PACK.md: {repo}")
        return
    row = f"* [{repo}](https://github.com/{repo})" + (": " + ", ".join(skills) if skills else "")
    text = PACK.read_text().rstrip("\n") + "\n" + row + "\n"
    if len(text.encode()) > MAX_PACK_BYTES:
        sys.exit(f"installed, but PACK.md would pass {MAX_PACK_BYTES} bytes; row not recorded.")
    PACK.write_text(text)
    print(f"recorded in PACK.md: {row}")


def main(argv):
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    if not shutil.which("npx"):
        sys.exit("npx not found. Install Node.js first; kit does not install runtimes.")

    if not argv:
        rows = read_pack()
        failed = []
        for repo, skills in rows:
            args = ["--skill", *skills] if skills else []
            if run(add_cmd(repo, args), dry):
                failed.append(repo)
        print(f"\n{len(rows) - len(failed)}/{len(rows)} synced" + (f"; failed: {', '.join(failed)}" if failed else ""))
        return 1 if failed else 0

    verb, rest = (argv[0], argv[1:]) if argv[0] in VERBS else ("add", argv)
    if verb == "add":
        repo = next((a for a in rest if not a.startswith("-")), None)
        if not repo:
            sys.exit("usage: packages.py add owner/repo [--skill a b] [-a agent]")
        i = rest.index(repo)
        code = run(add_cmd(repo, rest[:i] + rest[i + 1:]), dry)
        if code == 0 and not dry and not has(rest, "--all"):
            persist(repo, skills_in(rest))
        return code
    if verb in GLOBAL_VERBS:
        rest = [a for a in rest if a != "--project"] if "--project" in rest else (
            rest if has(rest, "-g", "--global") else ["-g", *rest])
    return run(CLI + [verb, *rest], dry)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
