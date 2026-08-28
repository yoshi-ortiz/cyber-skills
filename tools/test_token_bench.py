import tempfile
from pathlib import Path

import token_bench


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for name, disabled in (("model", ""), ("user", "disable-model-invocation: true\n")):
        skill = root / name
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: visible words\n{disabled}---\n\nBody.\n",
            encoding="utf-8",
        )

    rows = token_bench.measure(root, ["model", "user"])
    assert rows[0]["always"] == len("visible words")
    assert rows[0]["model_invoked"] is True
    assert rows[1]["always"] == 0
    assert rows[1]["model_invoked"] is False
    assert token_bench.render("same", rows) == token_bench.render("same", rows)
