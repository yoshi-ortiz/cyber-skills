#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from graphics_tool_research import ToolResearchError, context, validate
from text_to_graphics import compile_slices, main
from test_text_to_graphics import TOOL_RESEARCH, _project


class ToolResearchTests(unittest.TestCase):
    def test_rejected_candidates_cannot_enter_inference_context(self) -> None:
        researched = dict(TOOL_RESEARCH)
        researched["rejectedCandidates"] = [{"name": "blender", "reason": "too broad"}]
        admitted = context(validate(researched))
        self.assertNotIn("rejectedCandidates", admitted)
        self.assertEqual(admitted["selectedNiche"]["name"], "avge")

    def test_common_toolbelt_requires_the_harness_core_pins(self) -> None:
        researched = json.loads(json.dumps(TOOL_RESEARCH))
        researched["common"][0]["version"] = "latest"
        with self.assertRaisesRegex(ToolResearchError, "toolbelt pins"):
            validate(researched)

    def test_atomic_assets_must_belong_to_named_architecture(self) -> None:
        researched = json.loads(json.dumps(TOOL_RESEARCH))
        researched["atomicAssets"][0]["partOf"] = "missing"
        with self.assertRaisesRegex(ToolResearchError, "unknown architecture"):
            validate(researched)

    def test_common_sufficient_research_cannot_smuggle_a_niche_tool(self) -> None:
        researched = json.loads(json.dumps(TOOL_RESEARCH))
        researched["commonSufficient"] = True
        with self.assertRaisesRegex(ToolResearchError, "must be null"):
            validate(researched)

    def test_public_command_records_research_that_compile_admits(self) -> None:
        with _project() as project, tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "evidence.json"
            evidence.write_text(json.dumps(TOOL_RESEARCH), encoding="utf-8")
            self.assertEqual(main(["--project-root", str(project),
                                   "research-tools", "--evidence", str(evidence)]), 0)
            compiled = compile_slices(project)
            tools = compiled["slices"]["tools"]
            self.assertIn("selectedNiche", tools)
            self.assertNotIn("rejectedCandidates", tools)


if __name__ == "__main__":
    unittest.main()
