#!/usr/bin/env python3
"""Cold Repo-Dev entry returns bounded facts, not whole documents."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import repo_context


class RepoContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "ROADMAP.md").write_text("""# Roadmap
| ID | Core controller | State | Item | Bugs | Module | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| R-43 | [`manifest_gate.py`](tools/manifest_gate.py) | ⚪ `TODO` | Index origins | — | [`tools/`](tools/) | — |
| R-50 | [`context.py`](first/aesthetic/context.py) | 🟡 `IN-PROGRESS` | Compile context | — | [`first/aesthetic/`](first/aesthetic/) | R-43 |
| R-62 | controller | 🟡 `IN-PROGRESS` | Food Product | [B-026](BUGS.md) | aesthetic | R-50 |
""", encoding="utf-8")
        (self.root / "GOAL.md").write_text("""# Goal
Spend less context while preserving proof.

| Item | Prototype | Answers | Row |
| --- | --- | --- | --- |
| manifest | Discover origins | Does every source arrive? | R-43 |
""", encoding="utf-8")
        (self.root / "BUGS.md").write_text("""# Bugs
## B-026 · Old bug · fixed
**Root cause.** Old cause.

## B-027 · Installed copy loses edits · open (needs a human)
**Symptom.** Work disappears.

**Root cause.** The installed path is a copy.
""", encoding="utf-8")
        skill = self.root / "first" / "genesis"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: genesis\ndescription: Plans work.\n---\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_state_query_returns_only_exact_state(self) -> None:
        rows = repo_context.roadmap_state(self.root, "IN-PROGRESS")
        self.assertEqual([row["id"] for row in rows], ["R-50", "R-62"])

    def test_exact_item_carries_roadmap_and_goal_evidence(self) -> None:
        result = repo_context.item_context(self.root, "R-43")
        self.assertEqual(result["roadmap"]["id"], "R-43")
        self.assertEqual(result["roadmap"]["state"], "TODO")
        self.assertEqual(result["roadmap"]["module"], "tools/")
        self.assertEqual(result["goal"], ["manifest | Discover origins | Does every source arrive? | R-43"])

    def test_latest_bug_uses_document_order_and_preserves_status(self) -> None:
        bug = repo_context.latest_bug(self.root)
        self.assertEqual(bug["id"], "B-027")
        self.assertEqual(bug["status"], "open (needs a human)")
        self.assertIn("The installed path is a copy.", bug["body"])

    def test_module_query_consumes_catalog_ownership(self) -> None:
        by_name = repo_context.module_context(self.root, "genesis")
        by_path = repo_context.module_context(
            self.root, "first/genesis/references/architecture.md")
        self.assertEqual(by_name, by_path)
        self.assertEqual(by_name["family"], "first")
        self.assertEqual(by_name["channel"], "alpha")
        self.assertEqual(by_name["path"], "first/genesis")

    def test_missing_exact_item_fails_clearly(self) -> None:
        with self.assertRaisesRegex(LookupError, "R-99"):
            repo_context.item_context(self.root, "R-99")


if __name__ == "__main__":
    unittest.main()
