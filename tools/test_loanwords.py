#!/usr/bin/env python3
"""A gate that cannot fail is not a gate."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loanwords import check_translations, check_vocabulary, vocabulary


def case(**files: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, text in files.items():
            (root / name.replace("_", ".")).write_text(text, encoding="utf-8")
        return len(check_translations(root))


def test() -> None:
    # the English source is never checked: it is where the terms come from
    assert case(README_md="Una habilidad y un agente.") == 0

    # a translation keeping the English terms passes
    assert case(README_es_md="Instala una skill nueva y el agent la carga.") == 0

    # the two the gate exists for
    assert case(README_es_md="Una habilidad.") == 1
    assert case(README_es_md="Un agente.") == 1
    # both at once are two problems, not one
    assert case(README_es_md="Una habilidad y un agente.") == 2

    # plurals, in both Spanish forms
    assert case(README_es_md="Las habilidades.") == 1
    assert case(README_es_md="Los agentes.") == 1
    # and capitalised, as a heading would be
    assert case(README_es_md="# PROMPTS DE HABILIDAD") == 1

    # every translation is checked, not just the first
    assert case(README_es_md="Una habilidad.", README_ja_md="Una habilidad.") == 2

    # a word that merely contains a banned one is not a hit
    assert case(README_es_md="La deshabilidad no existe pero inhabilitar si.") == 0

    # ordinary words stay legal: this gate is not a style checker
    assert case(README_es_md="Tu asistente lee las instrucciones.") == 0

    print("OK")


def vocabulary_test() -> None:
    contract = """# Language
| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Item** | One roadmap row | Task, ticket, story |
| **Root cause** | Engineering finding | Fix, patch |
"""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "UBIQUITOUS_LANGUAGE.md").write_text(contract)
        terms = vocabulary(root / "UBIQUITOUS_LANGUAGE.md")
        assert [(term.name, term.aliases) for term in terms] == [
            ("Item", ("Task", "ticket", "story")),
            ("Root cause", ("Fix", "patch")),
        ]

        (root / "CLAUDE.md").write_text(
            "<!-- vocabulary: Item -->\nThis task is active.\n<!-- /vocabulary -->\n")
        problems = check_vocabulary(root, paths=("CLAUDE.md",))
        assert len(problems) == 1
        assert "CLAUDE.md:2" in problems[0]
        assert "task" in problems[0]
        assert "Item" in problems[0]

        # Only explicitly typed semantic blocks are governed. Code-like content
        # and substrings remain literal rather than prose vocabulary.
        (root / "CLAUDE.md").write_text(
            """This task is historical explanation.
<!-- vocabulary: Item -->
This item is active; `task` is a CLI value and taskmaster is another word.
```
task --json
```
<!-- /vocabulary -->
""")
        assert check_vocabulary(root, paths=("CLAUDE.md",)) == []

        (root / "BUGS.md").write_text("This task was renamed.\n")
        (root / "first/aesthetic").mkdir(parents=True)
        (root / "first/aesthetic/UBIQUITOUS_LANGUAGE.md").write_text(
            "A task in another semantic context.\n")
        assert check_vocabulary(root, paths=("CLAUDE.md",)) == []

        (root / "CLAUDE.md").write_text(
            "<!-- vocabulary: Missing term -->\ntext\n<!-- /vocabulary -->\n")
        assert "unknown canonical term" in check_vocabulary(
            root, paths=("CLAUDE.md",))[0]


if __name__ == "__main__":
    test()
    vocabulary_test()
