#!/usr/bin/env python3
"""The preview carries the whole trace, and reaches no network to be built."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "first" / "aesthetic" / "scripts"))
import direction_context as dc
import trace_preview as tp


def embedded(html: str) -> tuple[dict, str]:
    """The payload, parsed, and the raw text it was parsed from."""
    start = html.index("const DATA = ") + len("const DATA = ")
    value, end = json.JSONDecoder().raw_decode(html[start:])
    return value, html[start:start + end]


def test() -> None:
    import editorial_workflow as ew

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ew.seed_corpus(root, "art-direction", "a landing hero")
        html = tp.build(root, "proposal")

    data, blob = embedded(html)
    assert "__DATA__" not in html
    assert data["cdn"].startswith("https://cdn.jsdelivr.net/npm/@huggingface/transformers@")

    # Every row can be tokenized, or the exact column is a lie by omission.
    for chunk in data["trace"]["chunks"]:
        assert chunk["key"] in data["texts"], chunk["key"]

    # The page shows the deterministic trace, byte for byte, and never its own.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ew.seed_corpus(root, "art-direction", "a landing hero")
        assert data["trace"] == json.loads(json.dumps(
            {k: v for k, v in dc.compile_pass(root, "proposal").items()}))

    # `</` closes a script element whatever the JSON says, and doctrine is
    # markdown people write. The parsed payload still holds it; the page must not.
    assert "</" in json.dumps(data["texts"]), "fixture no longer covers the case"
    assert "</" not in blob

    tags()
    print("OK")


def tags() -> None:
    """The review vocabulary, and the three signals staying independent."""
    for bad, why in [
        ({"key": "a", "signal": "weight", "value": "3"}, "signal"),
        ({"key": "a", "signal": "utility", "value": "great"}, "utility"),
        ({"key": "", "signal": "utility", "value": "useful"}, "key"),
    ]:
        try:
            tp.validate_tag(bad)
        except ValueError as exc:
            assert why in str(exc), (bad, str(exc))
        else:
            raise AssertionError(f"{bad} was accepted")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        key = "doctrine:references/loop.md"
        for signal, value in [("utility", "wasted"), ("contamination", "derail"),
                              ("utility", "useful"), ("group", "Repo-Dev")]:
            tp.append_tag(root, tp.validate_tag(
                {"key": key, "signal": signal, "value": value}))

        # One line per interaction. Four clicks are four rows, including the
        # two that scored the same signal twice.
        path = root / tp.INBOX
        assert len(path.read_text().strip().splitlines()) == 4

        # Latest state per signal, and no signal touched by another. The second
        # utility click must not have cleared the contamination judgement.
        state = tp.adopt(root)
        assert state[key] == {"utility": "useful", "contamination": "derail",
                              "group": "Repo-Dev"}, state

        # A corrupt line is skipped, never fatal: the inbox is append-only and
        # a half-written line must not cost a maintainer their whole review.
        with path.open("a") as handle:
            handle.write("{not json\n")
        assert tp.adopt(root)[key]["utility"] == "useful"


if __name__ == "__main__":
    test()
