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
from dataclasses import dataclass
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
GOVERNED = ("CLAUDE.md", "CONTEXT.md", "SPEC.md", "SKILL_SPEC.md", "ROADMAP.md")
START = re.compile(r"<!--\s*vocabulary:\s*(.*?)\s*-->")
END = re.compile(r"<!--\s*/vocabulary\s*-->")


@dataclass(frozen=True)
class VocabularyTerm:
    name: str
    aliases: tuple[str, ...]
    line: int


def translated(root: Path) -> list[Path]:
    """`README.es.md` is a translation; `README.md` is the source."""
    return sorted(p for p in root.glob("README.*.md")
                  if len(p.name.split(".")) == 3)


def check_translations(root: Path) -> list[str]:
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


def vocabulary(path: Path) -> list[VocabularyTerm]:
    """Parse every canonical term and semantic alias from the root contract."""
    terms: list[VocabularyTerm] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 3 or not cells[0].startswith("**"):
            continue
        name = cells[0].strip("*").strip()
        aliases = tuple(alias.strip() for alias in cells[2].split(",") if alias.strip())
        terms.append(VocabularyTerm(name, aliases, number))
    if not terms:
        raise ValueError(f"{path.name} has no Term | Definition | Aliases to avoid rows")
    duplicate = next((term.name for term in terms
                      if sum(other.name == term.name for other in terms) > 1), None)
    if duplicate:
        raise ValueError(f"{path.name} declares {duplicate!r} more than once")
    return terms


def _prose(line: str) -> str:
    line = re.sub(r"`[^`]*`", "", line)
    line = re.sub(r"https?://\S+", "", line)
    return line


def check_vocabulary(root: Path, paths: tuple[str, ...] = GOVERNED) -> list[str]:
    """Enforce semantic aliases inside explicitly typed Markdown blocks."""
    try:
        terms = vocabulary(root / "UBIQUITOUS_LANGUAGE.md")
    except (OSError, ValueError) as error:
        return [str(error)]
    by_name = {term.name.casefold(): term for term in terms}
    problems: list[str] = []
    blocks = 0
    for relative in paths:
        path = root / relative
        if not path.is_file():
            continue
        active: tuple[VocabularyTerm, ...] = ()
        fenced = False
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            start = START.search(line)
            if start:
                blocks += 1
                requested = tuple(name.strip() for name in start.group(1).split(","))
                unknown = [name for name in requested if name.casefold() not in by_name]
                if unknown:
                    problems.append(
                        f"{relative}:{number}: vocabulary block names unknown canonical "
                        f"term {unknown[0]!r}")
                    active = ()
                else:
                    active = tuple(by_name[name.casefold()] for name in requested)
                fenced = False
                continue
            if END.search(line):
                active = ()
                fenced = False
                continue
            if not active:
                continue
            if line.strip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            prose = _prose(line)
            for term in active:
                for alias in term.aliases:
                    pattern = re.compile(rf"(?<![\w-]){re.escape(alias)}(?![\w-])", re.I)
                    match = pattern.search(prose)
                    if match:
                        problems.append(
                            f"{relative}:{number}: use {term.name!r}, not semantic alias "
                            f"{match.group(0)!r}")
    if not blocks:
        problems.append("no governed Repo-Dev vocabulary blocks found")
    return problems


def check(root: Path) -> list[str]:
    return check_translations(root) + check_vocabulary(root)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    problems = check(root)
    if problems:
        print(f"FAIL: {len(problems)} localised domain term(s)", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(f"OK: translations keep {len(LOANWORDS)} domain term(s) in English, and "
          f"{len(vocabulary(root / 'UBIQUITOUS_LANGUAGE.md'))} Repo-Dev terms are governed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
