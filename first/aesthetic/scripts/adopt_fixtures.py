"""Shared on-disk fixtures for the `adopt` and article test modules.

Not named `test_*.py` on purpose: `unittest discover -p 'test_*.py'` must not
collect it, and `ArticleFixture` is a mixin, not a TestCase.
"""
import json
from pathlib import Path

import bootstrap_harness as bh


def harness(root: Path) -> Path:
    """A minimal ledger on disk -- `adopt` only needs decisions.json + project.json."""
    output = root / "spec" / "design-harness"
    output.mkdir(parents=True)
    decisions = bh.empty_decisions()
    bh.write_json(output / "decisions.json", decisions)
    (output / "DECISIONS.md").write_text(bh.render_decisions_md(decisions), encoding="utf-8")
    bh.write_json(output / "project.json", {"version": bh.VERSION, "state": "draft"})
    return output


def ledger(root: Path, *events: dict) -> Path:
    path = root / "companion-ledger.jsonl"
    path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return path


def element(output: Path, name: str) -> dict:
    for entry in bh.load_decisions(output)["elements"]:
        if entry["element"] == name:
            return entry
    raise AssertionError(f"{name} is not in the ledger")

class ArticleFixture:
    """The one ledger every article test renders from."""

    def system(self, root: Path) -> dict:
        harness(root)
        bh.record_decision(root, "palette.family", "approved", 1, "user picked it", [])
        bh.describe_element(root, "palette.family", None, None, {
            "colors": [{"name": "menta", "value": "#b2ffc2", "role": "grupo"}]})
        bh.record_decision(root, "type.display", "approved", 1, "chosen face", [])
        bh.describe_element(root, "type.display", None, None, {
            "fonts": [{"name": "Matriz 5x7", "stack": "monospace", "use": "display"}]})
        bh.record_decision(root, "cover.weak", "proposed", 1, "backlog item", [])
        # A rank above 1 has to come from a click, so the fixture clicks.
        bh.adopt_companion(root, ledger(root, {
            "element": "cover.strong", "stars": 4, "text": "user liked it", "timestamp": 1}))
        bh.record_decision(root, "cover.bad", "rejected", 1, "user said no", [])
        return bh.load_decisions(root / "spec" / "design-harness")
