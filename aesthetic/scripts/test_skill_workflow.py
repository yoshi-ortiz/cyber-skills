"""Structural contracts for the skill's public workflow."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillWorkflowTest(unittest.TestCase):
    def test_skill_routes_the_full_corpus_through_the_editorial_compiler(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        positions = [skill.index(term) for term in (
            "editorial_workflow.py observe",
            "Ground and rank",
            "editorial_workflow.py publish",
            "Editorial board",
        )]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("INDEX.md present", skill)
        self.assertNotIn("Observing a text corpus stops at IA", skill)

    def test_every_local_markdown_link_resolves(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", skill)
        self.assertTrue(links)
        for link in links:
            self.assertTrue((ROOT / link).is_file(), link)

    def test_frontmatter_names_the_new_default_workflow(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        self.assertIn("multimodal corpus", frontmatter)
        self.assertIn("editorial board", frontmatter)


if __name__ == "__main__":
    unittest.main()
