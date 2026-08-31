"""Structural contracts for the skill's public workflow."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillWorkflowTest(unittest.TestCase):
    def test_skill_routes_inference_back_to_the_established_article(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        positions = [skill.index(term) for term in (
            "editorial_workflow.py observe",
            "editorial_workflow.py preferences",
            "bootstrap_harness.py article",
            "bootstrap_harness.py publish",
        )]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("editorial-board.html", skill)
        self.assertNotIn("Backlog, Doing, Review, and Done", skill)

    def test_every_local_markdown_link_resolves(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", skill)
        self.assertTrue(links)
        for link in links:
            self.assertTrue((ROOT / link).is_file(), link)

    def test_frontmatter_names_sentiment_and_editorial_burndown(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        self.assertIn("multimodal corpus", frontmatter)
        self.assertIn("user sentiment", frontmatter)
        self.assertIn("editorial burndown", frontmatter)

    def test_rank_and_sentiment_are_never_collapsed(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Never collapse", skill)
        self.assertIn("low stars", skill)
        self.assertIn("high stars", skill)

    def test_asset_contract_forbids_invented_vectors(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Never invent SVG paths", skill)
        self.assertIn("asset-sourcing.md", skill)


if __name__ == "__main__":
    unittest.main()
