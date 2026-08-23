#!/usr/bin/env python3
"""The README index is a promise; this is what keeps it one.

Five ways an index rots: a skill ships and nobody adds it, a skill is pulled
back to alpha in `fog.py` while the README still calls it stable, a
translation falls a skill behind, the table groups a skill nowhere or out of
order, or a declared name promises a trigger nothing answers to. Same bug
every time -- the index disagreeing with the repository -- so one gate.

A skill may also declare its own name in another language, in its `SKILL.md`
frontmatter. The gate then insists the translated README uses that name and
that the skill's own description carries it, because a name a reader can say
and the skill will not answer to is worse than no translation.

An `also:` entry adds a second index row for a trigger phrase the
description already documents -- `comandos en espanol` for `silly` -- without
claiming a second name. The anchor still points at the one real skill, and the
trigger still has to appear in that description.

It also refuses the em dash: not a native speaker's clause boundary, unlike a
colon, a full stop, or a pair of commas, so the README uses those instead.

    python3 tools/index_gate.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "silly" / "scripts"))
from fog import ALPHA_SKILLS
# The gate reads a manifest with the same parser that acts on it. A second
# implementation here could disagree with `alias.py`, and a gate that passes
# while the tool fails is the one bug this file exists to prevent.
from alias import frontmatter

# Section index, not section title: translations rename these headings.
STABLE, EXPERIMENTAL = 1, 2
SECTIONS = ("INSTALL", "SKILL PROMPTS", "EXPERIMENTS")

# The index groups skills by the moment a reader needs one, not by channel: a
# person arrives wanting to set something up, plan something, run something,
# or nothing in particular. Labels are English and translations rename them,
# so the gate compares order, never the words.
GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Set up once", ("starter-pack",)),
    ("Plan a project", ("genesis", "knowledge")),
    ("Run a session", ("aesthetic",)),
    ("Odds and ends", ("silly", "ora")),
)


def grouped() -> list[str]:
    """Every grouped skill, in the order the index table must list them."""
    return [name for _, members in GROUPS for name in members]


def skills(root: Path) -> list[str]:
    """Every skill directory in the repo -- a directory with a SKILL.md."""
    return sorted(p.name for p in root.iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


Spec = tuple[dict[str, str], dict[str, str], list[str], list[tuple[str, str]]]


def spec(path: Path) -> Spec:
    """(top-level frontmatter, translations, aliases, also) for one skill."""
    return frontmatter(path)


def second_names(entry: Spec) -> dict[str, str]:
    """Every declared second *name*, as name -> language or `fun`. Not `also`:
    those are not names, and nothing installs them."""
    _, translations, aliases, _also = entry
    return {name: code for code, name in translations.items()} | \
           {name: "fun" for name in aliases}


def also_rows(entry: Spec) -> list[tuple[str, str]]:
    """This skill's declared `(trigger, note)` pairs, in declaration order."""
    return entry[3]


def language(path: Path) -> str:
    """`README.es.md` is Spanish; `README.md` is the original and has no code."""
    parts = path.name.split(".")
    return parts[1] if len(parts) == 3 else ""


def title(heading: str) -> str:
    """A heading without its emoji, so `# 📦 INSTALL` compares as `INSTALL`."""
    return " ".join(re.sub(r"[^A-Za-z ]", " ", heading).split()).upper()


def read_index(readme: Path,
               alias: dict[str, str] | None = None) -> tuple[list[str], dict[str, int]]:
    """(H1 titles, {canonical skill name: index of the H1 it sits under})."""
    alias = alias or {}
    titles: list[str] = []
    placed: dict[str, int] = {}
    for line in readme.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            titles.append(title(line[2:]))
        elif line.startswith("## ") and "/" in line and titles:
            name = re.search(r"/([a-z0-9][a-z0-9-]*)", line)
            if name:
                placed[alias.get(name.group(1), name.group(1))] = len(titles) - 1
    return titles, placed


def languages(readme: Path) -> list[tuple[str, str | None]]:
    """The header's language line, as (label, link or None for a coming-soon)."""
    todo = re.compile(r"coming soon|pr[oó]ximamente|todo|pendiente")
    for line in readme.read_text(encoding="utf-8").splitlines():
        if "README" not in line and "]" not in line:
            continue
        if "|" not in line and "·" not in line:
            continue
        found: list[tuple[str, str | None]] = []
        for segment in re.split(r"\s\|\s|\s·\s", line):
            link = re.search(r"\[([^\]]+)\]\(([^)]+)\)", segment)
            if link:
                found.append((link.group(1), link.group(2)))
            elif todo.search(segment):
                found.append((segment.strip(" *"), None))
        if found:
            return found
    return []


# A skill row in the index, in either shape the README has used. Markdown:
# `| [📦 **/name**](#-name) | ... |`, decoration before the bold marker
# optional. HTML, for a table that joins group headers into one table via
# `colspan`: `<a href="#-name">...`. Group header rows (`<th colspan="2">`,
# or a markdown row with no link) match neither and are correctly skipped.
_INDEX_ROW = re.compile(r"\|\s*\[[^\[\]]*\*\*/([a-z0-9-]+)\*\*"
                        r'|href="#-([a-z0-9-]+)"')


def index_order(readme: Path) -> list[str]:
    """Skill names in the order the `## Index` table lists them."""
    order = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        m = _INDEX_ROW.search(line)
        if m:
            order.append(m.group(1) or m.group(2))
    return order


def gate(root: Path) -> int:
    problems: list[str] = []
    readme = root / "README.md"
    present = skills(root)
    specs = {name: spec(root / name / "SKILL.md") for name in present}

    for path in sorted(root.glob("README*.md")):
        dashes = [n for n, line in enumerate(path.read_text(encoding="utf-8")
                                             .splitlines(), 1) if "—" in line]
        if dashes:
            problems.append(f"{path.name} uses an em dash on line(s) "
                            f"{', '.join(map(str, dashes))}; use a colon, a full "
                            f"stop, or commas")

    for name in present:
        found = [label for label, members in GROUPS if name in members]
        if not found:
            problems.append(f"{name}/ is in no index group; add it to GROUPS in "
                            f"index_gate.py so the table stays a map of the package")
        elif len(found) > 1:
            problems.append(f"{name}/ is in {len(found)} index groups ({found}); "
                            f"a skill belongs to exactly one")
    for name in grouped():
        if name not in present:
            problems.append(f"GROUPS names {name!r}, which is not a skill directory")

    claimed: dict[str, str] = {}
    for name, entry in specs.items():
        description = entry[0].get("description", "")
        for trigger, _note in also_rows(entry):
            if trigger not in description:
                problems.append(
                    f"{name}/SKILL.md offers an also-row for {trigger!r} but its "
                    f"description never says it; the row would promise a trigger "
                    f"that fires nothing")
        for second, code in second_names(entry).items():
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", second):
                problems.append(f"{name}/SKILL.md declares {second!r} as a second "
                                f"name; use lower case, digits, and hyphens only")
            if second not in description:
                problems.append(
                    f"{name}/SKILL.md offers {second!r} as its {code} name but its "
                    f"description never says it; the word would trigger nothing")
            if second in present:
                problems.append(f"{name}/SKILL.md claims {second!r}, which is "
                                f"already a skill directory")
            if second in claimed:
                problems.append(f"{name}/ and {claimed[second]}/ both claim the "
                                f"second name {second!r}")
            claimed[second] = name

    titles, placed = read_index(readme)
    if titles != list(SECTIONS):
        problems.append(f"README.md H1 sections are {titles}, expected {list(SECTIONS)}")

    for path in sorted(root.glob("README*.md")):
        code = language(path)
        want: list[str] = []
        for name in grouped():
            entry = specs.get(name, ({}, {}, [], []))
            want.append(entry[1].get(code, name))
            want.extend(name for _ in also_rows(entry))
        order = index_order(path)
        if order != want:
            problems.append(f"{path.name} indexes {order}, expected {want}: one row "
                            f"per skill, grouped in the order GROUPS declares")

    for name in present:
        section = EXPERIMENTAL if name in ALPHA_SKILLS else STABLE
        where = placed.get(name)
        if where is None:
            problems.append(f"{name}/ has a SKILL.md but no `## /{name}` in README.md")
        elif where != section:
            problems.append(
                f"{name}/ is on the {'alpha' if name in ALPHA_SKILLS else 'main'} "
                f"channel but README.md lists it under {titles[where]!r}, "
                f"expected {SECTIONS[section]!r}")

    for label, link in languages(readme):
        if link is None:
            continue
        target = root / link
        if not target.is_file():
            problems.append(f"header offers {label} but {link} does not exist")
            continue
        if target.name == "README.md":
            continue
        code = language(target)
        aliases = {entry[1][code]: name for name, entry in specs.items()
                   if code in entry[1]}  # translations only; also-rows repeat the same name
        other_titles, other_placed = read_index(target, aliases)
        if len(other_titles) != len(SECTIONS):
            problems.append(f"{link} has {len(other_titles)} H1 sections, expected "
                            f"{len(SECTIONS)}")
        if other_placed != placed:
            problems.append(f"{link} indexes {sorted(other_placed)} in sections "
                            f"{list(other_placed.values())}; README.md indexes "
                            f"{sorted(placed)} in {list(placed.values())}")

    if problems:
        print(f"FAIL: {len(problems)} index problem(s)", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    translated = sum(len(second_names(entry)) for entry in specs.values())
    also_count = sum(len(also_rows(entry)) for entry in specs.values())
    print(f"OK: README indexes {len(present)} skill(s) in {len(GROUPS)} groups on "
          f"the right channel, with {translated} translated name(s) and "
          f"{also_count} also-row(s), and every translation offered matches it.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    return gate(parser.parse_args().root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
