"""Contract tests for the always-loaded aesthetic prompt.

These expectations come from the strongest reference prompt (`frontend-design`)
and from failures captured in this skill's own history. They protect outcomes,
not exact wording, so the prompt can keep getting shorter without losing the loop.
"""
import re
import unittest
from pathlib import Path


PROMPT = (Path(__file__).parents[1] / "SKILL.md").read_text(encoding="utf-8")
MANIFEST = (Path(__file__).parents[1] / "agents" / "openai.yaml").read_text(encoding="utf-8")


class EntryCost(unittest.TestCase):
    def test_prompt_stays_within_the_root_contract_budget(self):
        self.assertLessEqual(len(PROMPT.encode()), 6500)

    def test_agent_entry_point_asks_for_design_quality_not_just_scaffolding(self):
        for idea in ("brief-specific", "critique", "ranked user decisions"):
            self.assertIn(idea, MANIFEST)


class Startup(unittest.TestCase):
    def test_new_and_existing_projects_have_distinct_start_paths(self):
        self.assertRegex(PROMPT, re.compile(r"existing harness", re.I))
        self.assertRegex(PROMPT, re.compile(r"new project", re.I))
        self.assertRegex(PROMPT, re.compile(r"`init`"))
        self.assertRegex(PROMPT, re.compile(r"`doctor`"))


class QualityLoop(unittest.TestCase):
    def test_prompt_requires_a_brief_specific_thesis_and_signature(self):
        for idea in ("subject", "audience", "single job", "thesis", "signature"):
            self.assertIn(idea, PROMPT.lower())

    def test_prompt_requires_a_complete_design_system_not_a_style_vibe(self):
        for decision in ("palette", "typographic", "grid", "hierarchy", "copy"):
            self.assertIn(decision, PROMPT.lower())

    def test_prompt_requires_visual_critique_against_evidence(self):
        self.assertIn("screenshot", PROMPT.lower())
        self.assertIn("same scale", PROMPT.lower())
        self.assertIn("corpus", PROMPT.lower())
        self.assertRegex(PROMPT, re.compile(r"revise.*before", re.I | re.S))

    def test_prompt_names_the_generic_defaults_it_must_not_fall_into(self):
        self.assertIn("generic", PROMPT.lower())
        self.assertIn("default", PROMPT.lower())


if __name__ == "__main__":
    unittest.main()
