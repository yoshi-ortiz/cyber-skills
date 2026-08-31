#!/usr/bin/env python3
"""Capture a source as an OKF 0.2 concept file, and gate the bundle it lands in.

Two jobs, and the split is the point. `new` does what is deterministic --
fetch, timestamp, attribute, refuse to clobber -- and hands the prose to
whoever runs it. `check` does what is mechanical -- frontmatter, `type`, index
completeness -- so nobody has to remember the conformance rules.

The distillation itself is not here and never will be. A script that summarised
a page would be inventing the one part of a knowledge file that has to be read
by something that understands it.

    python3 okf.py new https://example.com/docs --root docs/knowledge
    python3 okf.py check --root docs/knowledge
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# OKF reserves these; they carry no frontmatter requirement.
RESERVED = ("index.md", "log.md")

USER_AGENT = "okf.py (+https://github.com/yoshi-ortiz/cyber-skills)"


def now() -> str:
    """Local time with its offset, so a timestamp says where it was taken."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def fetch(resource: str) -> tuple[str, str | None]:
    """(text, last-modified). A local path is read; anything else is fetched."""
    path = Path(resource)
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace"), None
    request = urllib.request.Request(resource, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return raw, response.headers.get("Last-Modified")


def to_text(raw: str) -> str:
    """Strip markup down to something readable. Crude on purpose.

    A real HTML-to-markdown converter is a dependency, and this output is read
    once by whoever writes the concept file, never stored. Good enough beats
    installed.
    """
    if "<" not in raw:
        return raw
    text = re.sub(r"(?is)<(script|style|nav|footer|svg)\b.*?</\1>", " ", raw)
    text = re.sub(r"(?is)<br\s*/?>|</(p|div|li|h[1-6]|tr)>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(
        line.strip() for line in text.splitlines())).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "concept"


def stub(resource: str, kind: str, title: str, by: str,
         last_modified: str | None) -> str:
    """The frontmatter a distilled file starts from, and a body that says so."""
    source = [f"  - resource: {resource}", f"    title: {title}"]
    if last_modified:
        source.append(f"    last_modified: {last_modified}")
    return "\n".join([
        "---",
        f"type: {kind}",
        f"title: {title}",
        "description: TODO one sentence, then set status to stable",
        "status: draft",
        f"resource: {resource}",
        "generated:",
        f"  by: {by}",
        f"  at: {now()}",
        "sources:",
        *source,
        "---",
        "",
        f"# {title}",
        "",
        "TODO. Replace this with the distilled concept: what it is, the shape",
        "that matters here, the failure modes, and the version the claims hold",
        "for. The extract printed by `okf.py new` is raw material, not a body.",
        "",
    ])


def cmd_new(args: argparse.Namespace) -> int:
    root = args.root
    root.mkdir(parents=True, exist_ok=True)
    title = args.title or Path(args.resource.rstrip("/")).name or args.resource
    target = root / f"{slugify(args.slug or title)}.md"
    if target.exists() and not args.force:
        print(f"{target} exists; pass --force to rewrite its frontmatter",
              file=sys.stderr)
        return 1
    try:
        raw, last_modified = fetch(args.resource)
    except (urllib.error.URLError, OSError) as error:
        print(f"could not read {args.resource}: {error}", file=sys.stderr)
        return 1
    target.write_text(stub(args.resource, args.type, title, args.by,
                           last_modified), encoding="utf-8")
    print(f"wrote {target}\n", file=sys.stderr)
    print(to_text(raw))
    return 0


def frontmatter(text: str) -> dict[str, str] | None:
    """Top-level `key: value` pairs, or None when there is no block to read.

    Nested blocks are skipped rather than parsed: conformance turns on `type`,
    which is always top level, and a YAML dependency would put this script
    outside what a stdlib-only repository ships.
    """
    match = re.match(r"\s*---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
    if not match:
        return None
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line[:1].strip() and ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def concepts(root: Path, ignore: tuple[str, ...] = ()) -> list[Path]:
    """Every file the bundle is judged on: not reserved, not explicitly ignored.

    `--ignore` exists because a bundle often shares a directory with a file
    that answers to something else entirely -- a directory contract, a licence,
    a repository's own convention. Naming those in the caller keeps this script
    from carrying a list of one project's filenames.
    """
    return sorted(p for p in root.rglob("*.md")
                  if p.name not in RESERVED
                  and not any(p.match(pattern) for pattern in ignore))


def cmd_check(args: argparse.Namespace) -> int:
    root = args.root
    if not root.is_dir():
        print(f"{root} is not a directory", file=sys.stderr)
        return 1
    problems: list[str] = []
    ignore = tuple(args.ignore)
    files = concepts(root, ignore)

    for path in files:
        fields = frontmatter(path.read_text(encoding="utf-8"))
        name = path.relative_to(root)
        if fields is None:
            problems.append(f"{name}: no frontmatter block")
        elif not fields.get("type"):
            problems.append(f"{name}: frontmatter declares no `type`")

    index = root / "index.md"
    if not files:
        pass
    elif not index.is_file():
        problems.append("index.md is missing; a bundle with no door is a pile")
    else:
        body = index.read_text(encoding="utf-8")
        linked = set(re.findall(r"\]\(([^)#]+\.md)\)", body))
        for path in files:
            if str(path.relative_to(root)) not in linked:
                problems.append(f"{path.relative_to(root)}: not listed in index.md")
        for link in sorted(linked):
            if any(Path(link).match(pattern) for pattern in ignore):
                continue
            if not (root / link).is_file():
                problems.append(f"index.md links {link}, which does not exist")

    if problems:
        print(f"FAIL: {len(problems)} problem(s) in {root}", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(f"OK: {len(files)} concept(s) in {root} conform to OKF 0.2 "
          f"and are indexed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="capture a URL or file as a concept stub")
    new.add_argument("resource", help="URL, or a path to a local file")
    new.add_argument("--root", type=Path, required=True,
                     help="knowledge directory in the target project")
    new.add_argument("--type", default="Reference", help="OKF `type` (default: Reference)")
    new.add_argument("--title", help="display name (default: from the resource)")
    new.add_argument("--slug", help="filename stem (default: from the title)")
    new.add_argument("--by", default="agent/unknown",
                     help="actor, as <producer>/<version> or human:<id>")
    new.add_argument("--force", action="store_true",
                     help="rewrite the frontmatter of an existing file")
    new.set_defaults(handler=cmd_new)

    check = sub.add_parser("check", help="gate a knowledge directory")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--ignore", action="append", default=[], metavar="GLOB",
                       help="basename pattern to exclude, repeatable "
                            "(for example --ignore CONTEXT.md)")
    check.set_defaults(handler=cmd_check)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
