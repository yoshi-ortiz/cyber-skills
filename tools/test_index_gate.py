#!/usr/bin/env python3
"""A gate that cannot fail is not a gate."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from index_gate import gate, grouped

HEADER = "🇬🇧 [English](README.md) | 🇪🇸 [Espanol](README.es.md) | 🇯🇵 Nihongo (coming soon)\n"

# One row per skill, in the order GROUPS declares. The gate reads the order,
# never the group headings, so the fixture needs no headings at all.
INDEX = ("## Index\n\n| | |\n| --- | --- |\n"
         + "".join(f"| [**/{name}** 🎨](#-{name}) | row |\n" for name in grouped())
         + "\n")
BODY = (INDEX + "# 📦 INSTALL\n\n"
        "# ✨ SKILL PROMPTS\n\n## 🎒 /kit\n\n## 🇪🇸 /ora\n\n"
        "## 🔬 /build-context-token-vectors\n\n## 🎨 /aesthetic\n\n"
        "# 🧪 EXPERIMENTS\n\n## 🧬 /genesis\n\n## 📚 /knowledge\n\n"
        "## 🃏 /silly\n")

MANIFEST = ("---\nname: knowledge\ndescription: Distils sources, and answers to "
            "enciclopedia.\ntranslations:\n  es: enciclopedia\n---\n")


# One row per skill, in the order GROUPS declares. Nested under workflow families.
SKILL_HOME: dict[str, tuple[str, ...]] = {
    "kit": (),
    "silly": ("kit",),
    "ora": ("kit", "spanish"),
    "genesis": ("first",),
    "knowledge": ("first",),
    "aesthetic": ("first",),
    "build-context-token-vectors": ("check",),
}


def skill_dir(root: Path, name: str) -> Path:
    return root.joinpath(*SKILL_HOME[name], name)


def build(root: Path, readme: str, translation: str | None,
          manifest: str = MANIFEST) -> None:
    for name in grouped():
        path = skill_dir(root, name)
        path.mkdir(parents=True, exist_ok=True)
        (path / "SKILL.md").write_text(
            manifest if name == "knowledge" else f"---\nname: {name}\n---\n")
    (root / "README.md").write_text(readme)
    if translation is not None:
        (root / "README.es.md").write_text(translation)


def case(readme: str, translation: str | None = None,
         manifest: str = MANIFEST) -> int:
    """Defaults to a Spanish README that matches, so each case varies one thing."""
    if translation is None:
        translation = (HEADER + BODY.replace("/knowledge", "/enciclopedia")
                       if manifest is MANIFEST else HEADER + BODY)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build(root, readme, translation, manifest)
        return gate(root)


def test() -> None:
    assert case(HEADER + BODY) == 0

    # genesis, knowledge, silly are alpha: an EXPERIMENTS section removed
    # leaves them with no home, which must fail
    assert case(HEADER + BODY.replace("\n# 🧪 EXPERIMENTS\n", "")) == 1
    # a skill missing from the index
    assert case(HEADER + BODY.replace("## 🇪🇸 /ora\n", "")) == 1
    # an em dash anywhere in a README
    assert case(HEADER + BODY.replace("## 🃏 /silly", "## 🃏 /silly — fun")) == 1
    # a translation offered but never written
    assert case(HEADER + BODY, translation="") == 1
    # a translation that fell a skill behind
    assert case(HEADER + BODY,
                translation=HEADER + BODY.replace("/knowledge", "/enciclopedia")
                                         .replace("## 🇪🇸 /ora\n", "")) == 1

    # the index table out of the order GROUPS declares
    rows = [f"| [**/{name}** 🎨](#-{name}) | row |\n" for name in grouped()]
    swapped = "".join([rows[1], rows[0]] + rows[2:])
    assert case(HEADER + BODY.replace("".join(rows), swapped)) == 1

    # an HTML index table (group headers joined via colspan) is read the same
    def html_row(name: str) -> str:
        return (f'<tr><td><a href="#-{name}"><strong>/{name}</strong></a>'
                f"</td><td>row</td></tr>\n")

    html_index = ("## Index\n\n<table>\n"
                  + "".join(html_row(name) for name in grouped())
                  + "</table>\n\n")
    assert case(HEADER + html_index + BODY[len(INDEX):]) == 0
    html_swapped = "".join(
        html_row(n) for n in [grouped()[1], grouped()[0]] + grouped()[2:])
    bad_html_index = "## Index\n\n<table>\n" + html_swapped + "</table>\n\n"
    assert case(HEADER + bad_html_index + BODY[len(INDEX):]) == 1

    # a group header's own link -- no leading slash, no <strong> -- is not
    # mistaken for that skill's row and does not get counted twice
    with_header = ("## Index\n\n<table>\n"
                   f'<tr><th colspan="2"><a href="#-{grouped()[0]}">Title</a></th></tr>\n'
                   + "".join(html_row(name) for name in grouped())
                   + "</table>\n\n")
    assert case(HEADER + with_header + BODY[len(INDEX):]) == 0

    # the Spanish README indexing the skill under its English name anyway
    assert case(HEADER + BODY, translation=HEADER + BODY) == 1

    # a declared name the skill's own description never says: it triggers nothing
    assert case(HEADER + BODY.replace("/knowledge", "/enciclopedia"),
                manifest="---\nname: knowledge\ndescription: Distils sources."
                         "\ntranslations:\n  es: enciclopedia\n---\n") == 1
    # a declared name that collides with a real skill directory
    assert case(HEADER + BODY,
                translation=HEADER + BODY,
                manifest="---\nname: knowledge\ndescription: Also called ora."
                         "\ntranslations:\n  es: ora\n---\n") == 1
    # a declared name that is not a usable command
    assert case(HEADER + BODY.replace("/knowledge", "/enciclopedia"),
                manifest="---\nname: knowledge\ndescription: Also Enciclopedia!"
                         "\ntranslations:\n  es: Enciclopedia!\n---\n") == 1

    # an `also` row: a second index row for a trigger the skill's own
    # description already documents. Not a name, so it repeats the skill's
    # own anchor rather than claiming a new one.
    also_manifest = ("---\nname: knowledge\ndescription: Distils sources, and "
                     "documents reads the docs as a trigger.\nalso:\n"
                     "  - reads the docs :: An extra index row\n---\n")
    also_row = "| [**/knowledge** 🎨](#-knowledge) also |\n"
    with_also = HEADER + BODY.replace(
        "| [**/knowledge** 🎨](#-knowledge) | row |\n",
        "| [**/knowledge** 🎨](#-knowledge) | row |\n" + also_row)
    # present in both README.md and README.es.md: passes
    assert case(with_also, translation=with_also, manifest=also_manifest) == 0
    # present only in README.md: the translation fell behind, fails
    assert case(with_also, translation=HEADER + BODY, manifest=also_manifest) == 1
    # the also-row's trigger is not in the skill's own description: fails
    assert case(with_also, translation=with_also,
                manifest="---\nname: knowledge\ndescription: Distils sources."
                         "\nalso:\n  - reads the docs :: An extra index row\n---\n") == 1

    # a shipped alias directory is not a skill: it has a SKILL.md, but
    # `alias_of` means it wears another skill's name and needs no group,
    # no index row, and no section of its own
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build(root, HEADER + BODY, HEADER + BODY.replace("/knowledge",
                                                         "/enciclopedia"))
        (root / "old-name").mkdir()
        (root / "old-name" / "SKILL.md").write_text(
            "---\nname: old-name\nalias_of: ora\n---\n")
        assert gate(root) == 0

    # an unquoted `: ` in frontmatter is a nested mapping to YAML, so a real
    # parser skips the file and the skill silently does not exist
    assert case(HEADER + BODY,
                translation=HEADER + BODY,
                manifest="---\nname: knowledge\n"
                         "description: Distils sources: docs, specs, notes.\n---\n") == 1
    # quoted is fine
    assert case(HEADER + BODY,
                translation=HEADER + BODY,
                manifest='---\nname: knowledge\n'
                         'description: "Distils sources: docs, specs, notes."\n---\n') == 0

    print("OK")


if __name__ == "__main__":
    test()
