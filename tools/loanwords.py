#!/usr/bin/env python3
"""Domain words a translation must leave in English.

An agent ecosystem names some things in English everywhere the reader will
meet them again: the CLI flag is `--skill`, the file on disk is `SKILL.md`,
the folder is `~/.claude/skills/`, and the app's own settings screen says
"skills" too. Translating that noun hands the reader a word no interface will
ever echo back and that they cannot search for. They then have to learn the
English term anyway, having first learned a synonym for it.

So `skill` stays `skill` in Spanish prose, and `una habilidad` is a defect.
This is narrower than it sounds. It covers the handful of nouns that name
parts of the machinery, not ordinary words: `asistente` for "assistant" is
fine, because no flag, path, or screen says "assistant" back at the reader.

Only translations are checked. `README.md` is the source and cannot fail.

    python3 tools/loanwords.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# term that must survive -> what a translator reaches for instead. Plurals are
# generated, so list the singular: `habilidad` also catches `habilidades`.
LOANWORDS: dict[str, tuple[str, ...]] = {
    "skill": ("habilidad", "destreza"),
    "agent": ("agente",),
    "prompt": ("indicación", "indicacion"),
    "token": ("ficha",),
}

# Spanish pluralises with -s or -es, and `\b` is accent-aware on str patterns.
_PLURAL = r"(?:e?s)?\b"


def translated(root: Path) -> list[Path]:
    """`README.es.md` is a translation; `README.md` is the source."""
    return sorted(p for p in root.glob("README.*.md")
                  if len(p.name.split(".")) == 3)


def check(root: Path) -> list[str]:
    """One problem per localised domain term found, with its line number."""
    problems: list[str] = []
    for path in translated(root):
        lines = path.read_text(encoding="utf-8").splitlines()
        for keep, avoid in LOANWORDS.items():
            for word in avoid:
                pattern = re.compile(rf"\b{re.escape(word)}{_PLURAL}", re.I)
                hits = [n for n, line in enumerate(lines, 1) if pattern.search(line)]
                if hits:
                    shown = ", ".join(map(str, hits[:8]))
                    more = f" and {len(hits) - 8} more" if len(hits) > 8 else ""
                    problems.append(
                        f"{path.name} translates {keep!r} as {word!r} on line(s) "
                        f"{shown}{more}; keep the English term, it is what the "
                        f"flag, the file, and the app all say")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    problems = check(parser.parse_args().root.resolve())
    if problems:
        print(f"FAIL: {len(problems)} localised domain term(s)", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(f"OK: every translation keeps {len(LOANWORDS)} domain term(s) in English.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
