#!/usr/bin/env python3
"""What a `SKILL.md` frontmatter has to hold to be worth anything.

Two failures, both silent, both shipped at least once.

A value carrying an unquoted `: ` is a nested mapping to YAML. A real parser
does not guess, it skips the whole file, and the skill then does not exist as
far as any agent is concerned. This repository's own reader is flat and would
never notice, which is exactly how it shipped.

A declared second name or trigger that the skill's own description never says
is a word nothing answers to. An agent picks a skill by reading descriptions,
so a name absent from every description has never been heard of, however many
files declare it.

Called by `index_gate.py`, which owns the index itself.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "silly" / "scripts"))
from alias import frontmatter

NAME = re.compile(r"[a-z0-9][a-z0-9-]*")


def check(root: Path, present: list[str]) -> list[str]:
    """Every frontmatter problem across the repo's skills, aliases included."""
    problems: list[str] = []
    claimed: dict[str, str] = {}

    for entry in sorted(root.glob("*/SKILL.md")):
        name = entry.parent.name
        fields, translations, aliases, also = frontmatter(entry)
        description = fields.get("description", "")

        for key, value in fields.items():
            if ": " in value and not value.startswith(('"', "'")):
                problems.append(
                    f"{name}/SKILL.md has an unquoted `: ` in `{key}`; YAML reads "
                    f"that as a nested mapping and skips the file, so the skill "
                    f"stops existing. Wrap the value in double quotes.")

        for trigger, _note in also:
            if trigger not in description:
                problems.append(
                    f"{name}/SKILL.md offers an also-row for {trigger!r} but its "
                    f"description never says it; the row promises a trigger that "
                    f"fires nothing")

        second = {n: code for code, n in translations.items()}
        second.update({n: "fun" for n in aliases})
        for word, code in second.items():
            if not NAME.fullmatch(word):
                problems.append(f"{name}/SKILL.md declares {word!r} as a second "
                                f"name; lower case, digits, and hyphens only")
            if word not in description:
                problems.append(
                    f"{name}/SKILL.md offers {word!r} as its {code} name but its "
                    f"description never says it; the word would trigger nothing")
            if word in present:
                problems.append(f"{name}/SKILL.md claims {word!r}, which is "
                                f"already a skill directory")
            if word in claimed:
                problems.append(f"{name}/ and {claimed[word]}/ both claim the "
                                f"second name {word!r}")
            claimed[word] = name

    return problems


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    present = sorted(p.name for p in root.iterdir()
                     if p.is_dir() and (p / "SKILL.md").is_file()
                     and not frontmatter(p / "SKILL.md")[0].get("alias_of"))
    problems = check(root, present)
    if problems:
        print(f"FAIL: {len(problems)} frontmatter problem(s)", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(f"OK: {len(present)} skill(s) declare usable frontmatter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
