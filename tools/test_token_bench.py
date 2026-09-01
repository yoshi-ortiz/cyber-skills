import contextlib
import io
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

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    pkg = root / "pkg"
    for name, disabled in (("a", ""), ("a/b", ""),
                           ("c/d/e", "disable-model-invocation: true\n")):
        skill = pkg / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: visible words\n{disabled}---\n\nBody.\n",
            encoding="utf-8",
        )
    (root / "solo").mkdir()
    (root / "solo" / "SKILL.md").write_text(
        "---\nname: solo\ndescription: visible words\n---\n\nBody.\n",
        encoding="utf-8",
    )

    names = token_bench.discover(pkg)
    assert names == ["a", "a/b", "c/d/e"], names
    assert names == sorted(names)
    assert names == token_bench.discover(pkg)

    rows = token_bench.measure(pkg, names)
    assert all(not r["missing"] for r in rows), rows
    deep = rows[2]
    assert deep["always"] == 0
    assert deep["path"] > 0
    assert sum(r["always"] for r in rows) == 2 * len("visible words")
    assert sum(r["path"] for r in rows) > sum(r["always"] for r in rows)

    summary = token_bench.render_package("pkg", rows)
    assert "3 skills" in summary, summary
    assert "2 model-invoked" in summary, summary

    def run(*argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert token_bench.main(list(argv)) == 0
        return buf.getvalue()

    flows_only = run("--root", str(root), "--flow", "one=solo", "--flow", "two=solo,solo")
    mixed = run("--root", str(root), "--package", f"pkg={pkg}",
                "--flow", "one=solo", "--flow", "two=solo,solo")
    assert "comparison" in flows_only
    assert flows_only.split("comparison", 1)[1] == mixed.split("comparison", 1)[1]
    assert "3 skills" in mixed
