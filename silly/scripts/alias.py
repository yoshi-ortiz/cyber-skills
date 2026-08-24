#!/usr/bin/env python3
"""Give a skill a second name, without giving it a second copy.

A skill answers to the name in its `SKILL.md`. Wanting `/enciclopedia` to work
therefore means a `SKILL.md` that says `enciclopedia`, which a directory
symlink cannot provide: the file inside a symlinked directory still declares
the old name, so the assistant registers the same command twice and the new
one never appears.

So an alias is a stub. One file, carrying the new name, the manifested
description, and a pointer at the skill that holds the actual instructions.
Nothing is duplicated except the name, which is the only part being changed.

Aliases are written into an installed skills folder, never into a source tree,
and only the ones asked for. A package that shipped every language to everyone
would charge every user for four names they cannot read.

    python3 alias.py list --root ~/.cursor/skills
    python3 alias.py link --root ~/.cursor/skills --lang es
    python3 alias.py unlink --root ~/.cursor/skills
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# Written into every stub. Its presence is what makes removal safe: `unlink`
# deletes a directory only when this key names the skill it points at.
MARKER = "alias_of"


# One `also` entry: the phrase that must appear in the skill's own
# description, and the note an index row may show beside it. `also` never
# installs anything -- see its doctrine in CONTEXT.md -- so it carries no
# command-name charset restriction the way `aliases` does.
Also = tuple[str, str]


def frontmatter(path: Path) -> tuple[dict[str, str], dict[str, str], list[str], list[Also]]:
    """(top-level fields, translations, aliases, also) from one SKILL.md.

    Hand-parsed rather than YAML so this stays standard library only. Three
    nested shapes matter and all are one level deep: a mapping under
    `translations:`, a flat list under `aliases:`, and a `trigger :: note`
    list under `also:`.
    """
    match = re.match(r"\s*---\s*\n(.*?)\n---", path.read_text(encoding="utf-8"), re.S)
    if not match:
        return {}, {}, [], []
    fields: dict[str, str] = {}
    translations: dict[str, str] = {}
    aliases: list[str] = []
    also: list[Also] = []
    block = ""
    for line in match.group(1).splitlines():
        if line.lstrip().startswith("#") or not line.strip():
            continue
        if line[:1].strip():
            key, _, value = line.partition(":")
            block = key.strip()
            fields[block] = value.strip()
        elif block == "translations" and ":" in line:
            code, _, name = line.partition(":")
            translations[code.strip()] = name.strip()
        elif block == "aliases" and line.lstrip().startswith("-"):
            aliases.append(line.lstrip()[1:].strip())
        elif block == "also" and line.lstrip().startswith("-"):
            trigger, _, note = line.lstrip()[1:].partition("::")
            also.append((trigger.strip(), note.strip()))
    return fields, translations, aliases, also


def manifested(root: Path) -> list[tuple[str, str, str, str]]:
    """Every declared second name, as (alias, canonical, kind, description)."""
    found: list[tuple[str, str, str, str]] = []
    for skill in sorted(root.iterdir()):
        entry = skill / "SKILL.md"
        if not entry.is_file():
            continue
        fields, translations, aliases, _also = frontmatter(entry)
        name = fields.get("name") or skill.name
        if fields.get(MARKER):
            continue
        description = fields.get("description", "")
        for code, localized in sorted(translations.items()):
            found.append((localized, name, code, description))
        for playful in aliases:
            found.append((playful, name, "fun", description))
    return found


def quoted(value: str) -> str:
    """A double-quoted YAML scalar.

    A description is prose, and prose contains `: `, which YAML reads as a
    nested mapping and every parser then rejects. The whole file is skipped
    when that happens, so the alias silently does not exist.
    """
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def stub(alias: str, canonical: str, kind: str, description: str) -> str:
    """The whole alias. A name, why it exists, and where the work lives."""
    label = "another language" if kind != "fun" else "a name that is nicer to type"
    return "\n".join([
        "---",
        f"name: {alias}",
        "description: " + quoted(f"The {canonical} skill under {label}. "
                                 f"Say {alias} to run it. {description}"),
        f"{MARKER}: {canonical}",
        "disable-model-invocation: true",
        "---",
        "",
        f"# {alias}",
        "",
        f"Another name for **{canonical}**. Read [{canonical}/SKILL.md]"
        f"(../{canonical}/SKILL.md) and follow it exactly.",
        "",
        "Nothing here changes what that skill does. This file exists so the name",
        "can be typed, and for no other reason.",
        "",
    ])


def wanted(root: Path, languages: list[str], fun: bool) -> list[tuple[str, str, str, str]]:
    return [row for row in manifested(root)
            if (row[2] in languages) or (fun and row[2] == "fun")]


def cmd_list(args: argparse.Namespace) -> int:
    rows = manifested(args.root)
    if not rows:
        print(f"no skill under {args.root} manifests a second name")
        return 0
    width = max(len(alias) for alias, *_ in rows)
    for alias, canonical, kind, _ in rows:
        live = "installed" if (args.root / alias / "SKILL.md").is_file() else "-"
        print(f"{alias:<{width}}  {kind:<4}  {canonical:<16}  {live}")
    return 0


def cmd_link(args: argparse.Namespace) -> int:
    rows = wanted(args.root, args.lang, args.fun)
    if not rows:
        print("nothing to link: name a language with --lang, or pass --fun",
              file=sys.stderr)
        return 1
    for alias, canonical, kind, description in rows:
        target = args.root / alias
        entry = target / "SKILL.md"
        # Overwrite only what this tool wrote. Anything else with that name is
        # someone's real skill, and a second name is never worth losing one.
        ours = entry.is_file() and frontmatter(entry)[0].get(MARKER)
        if target.exists() and not ours:
            print(f"{alias}: {target.name}/ already exists and is not an alias, "
                  f"refusing", file=sys.stderr)
            return 1
        if args.dry_run:
            print(f"would link {alias} -> {canonical}")
            continue
        target.mkdir(parents=True, exist_ok=True)
        entry.write_text(stub(alias, canonical, kind, description), encoding="utf-8")
        print(f"linked {alias} -> {canonical}")
    if not args.dry_run:
        print("\nStart a new chat. Assistants read their skills at session start.")
    return 0


def cmd_unlink(args: argparse.Namespace) -> int:
    removed = 0
    for path in sorted(args.root.iterdir()):
        entry = path / "SKILL.md"
        if not entry.is_file() or not frontmatter(entry)[0].get(MARKER):
            continue
        if args.dry_run:
            print(f"would remove {path.name}")
        else:
            shutil.rmtree(path)
            print(f"removed {path.name}")
        removed += 1
    if not removed:
        print("no aliases installed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, handler, helptext in (
            ("list", cmd_list, "show every manifested second name and whether it is live"),
            ("link", cmd_link, "write the alias stubs for a language or for fun names"),
            ("unlink", cmd_unlink, "remove every alias this tool wrote")):
        command = sub.add_parser(name, help=helptext)
        command.add_argument("--root", type=Path, required=True,
                             help="an installed skills folder, such as ~/.cursor/skills")
        if name != "list":
            command.add_argument("--dry-run", action="store_true")
        if name == "link":
            command.add_argument("--lang", action="append", default=[], metavar="CODE",
                                 help="language to install, repeatable (for example es)")
            command.add_argument("--fun", action="store_true",
                                 help="also install the playful aliases")
        command.set_defaults(handler=handler)

    args = parser.parse_args(argv)
    args.root = args.root.expanduser()
    if not args.root.is_dir():
        print(f"{args.root} is not a directory", file=sys.stderr)
        return 1
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
