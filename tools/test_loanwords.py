#!/usr/bin/env python3
"""A gate that cannot fail is not a gate."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loanwords import check


def case(**files: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, text in files.items():
            (root / name.replace("_", ".")).write_text(text, encoding="utf-8")
        return len(check(root))


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


if __name__ == "__main__":
    test()
