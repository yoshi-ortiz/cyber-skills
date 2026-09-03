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
            "direction_context.py",
            "deliver.py --project-root",
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

    def test_small_models_get_a_mechanical_graphics_and_language_route(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        communication = (ROOT / "references/user-communication.md").read_text(
            encoding="utf-8")
        self.assertLess(skill.index("text_to_graphics.py"),
                        skill.index("editorial_workflow.py observe"))
        self.assertIn("project-authored publishing copy", skill)
        self.assertIn("project.json.language", communication)
        self.assertIn("never\nchooses the language of chat", communication)

    def test_each_loop_step_uses_the_live_adapter_and_one_invocation(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("assistant_app.py", skill)
        self.assertIn("before every loop step", skill.lower())
        self.assertLess(skill.index("assistant_app.py"),
                        skill.index("direction_context.py"))
        self.assertIn("--invocation <skill@timestamp>", skill)


if __name__ == "__main__":
    unittest.main()
