#!/usr/bin/env python3
import contextlib
import json
import tempfile
import unittest
from pathlib import Path

from graphics_flow import next_action, read_state
from text_to_graphics import (build_svg, compile_slices, export_avge_calls,
                              gate_outputs, GraphicsError, prompt_inputs_hash,
                              record_adapter, run_moodboard, validate_scene)

ROOT = Path(__file__).resolve().parents[3]
STORE = "spec/design-harness"
HARNESS_FILES = ("graphics-manifest.json", "scene-spec.json",
                 "corpus.json", "corpus-tags.json")

TOOL_RESEARCH = {
    "version": 1, "domain": "editorial developer-tool graphics",
    "stack": ["HTML", "CSS", "SVG", "Python"],
    "common": [
        {"name": "playwright-mcp", "version": "@playwright/mcp@0.0.80",
         "command": "playwright-mcp", "source": "https://github.com/microsoft/playwright-mcp",
         "license": "Apache-2.0", "runtime": "Node 18+",
         "security": "workspace roots only", "evidence": "command preflight passed"},
        {"name": "svgmaker-mcp", "version": "@genwave/svgmaker-mcp@2.1.0",
         "command": "svgmaker-mcp", "source": "https://github.com/GenWaveLLC/svgmaker-mcp",
         "license": "MIT", "runtime": "Node 20.9+ and API key",
         "security": "hosted API receives supplied inputs", "evidence": "command preflight passed"},
    ],
    "commonSufficient": False,
    "whyCommonInsufficient": "The scene needs deterministic isometric topology.",
    "selectedNiche": {"name": "avge", "version": "0.5.14", "command": "avge-engine",
        "source": "installed MCP tool inventory", "license": "not observed",
        "runtime": "Python 3.12", "security": "local project storage",
        "evidence": "isometric_box and attach were observed"},
    "customGeneration": True,
    "architecture": [{"name": "isometric-loop", "purpose": "closed route and rooms"}],
    "atomicAssets": [{"name": "road", "partOf": "isometric-loop", "output": "road polyline"}],
}


def _scene() -> dict:
    return json.loads((ROOT / STORE / "scene-spec.json").read_text(encoding="utf-8"))


@contextlib.contextmanager
def _project(**overrides: dict):
    """A throwaway project root holding only this loop's harness state."""
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        store = project / STORE
        store.mkdir(parents=True)
        for name in HARNESS_FILES:
            source = ROOT / STORE / name
            if source.exists():
                (store / name).write_text(source.read_text(encoding="utf-8"),
                                          encoding="utf-8")
        (store / "graphics-tools.json").write_text(json.dumps(TOOL_RESEARCH),
                                                    encoding="utf-8")
        inventory = ROOT / "moodboards/storytelling/rooms-inventory.md"
        if inventory.exists():
            target = project / "moodboards/storytelling/rooms-inventory.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(inventory.read_text(encoding="utf-8"), encoding="utf-8")
        for name, payload in overrides.items():
            (store / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
        yield project


FOREIGN_SCENE = {
    "version": 1,
    "element": "docs.nav.cycle",
    "layout": "isometric-x",
    "road": {"shape": "loop", "direction": "clockwise",
             "sequence": ["/read", "/try", "/ask", "/read"]},
    "positions": {
        "north": {"x": 0.30, "y": 0.05, "width": 0.40, "depth": 0.30, "height": 0.05},
        "south-west": {"x": 0.05, "y": 0.60, "width": 0.35, "depth": 0.30, "height": 0.05},
        "south-east": {"x": 0.60, "y": 0.60, "width": 0.35, "depth": 0.30, "height": 0.05},
        "middle": {"x": 0.42, "y": 0.42, "width": 0.16, "depth": 0.12, "height": 0.03},
    },
    "mainRooms": [
        {"id": "/read", "position": "north", "palette": ["ink"]},
        {"id": "/try", "position": "south-west", "palette": ["clay"]},
        {"id": "/ask", "position": "south-east", "palette": ["moss"]},
    ],
    "kiosks": [{"id": "/hub", "position": "middle", "palette": "paper"}],
    "billboards": {"/read": "/read DOCS", "/try": "/try RUN",
                   "/ask": "/ask HELP", "/hub": "/hub INDEX"},
}


class SceneValidationTests(unittest.TestCase):
    def test_the_landing_hero_scene_is_valid(self) -> None:
        self.assertEqual(validate_scene(_scene()), [])

    def test_a_scene_sharing_no_name_with_the_hero_is_valid(self) -> None:
        self.assertEqual(validate_scene(FOREIGN_SCENE), [])

    def test_a_road_that_does_not_close_is_rejected(self) -> None:
        scene = json.loads(json.dumps(FOREIGN_SCENE))
        scene["road"]["sequence"] = ["/read", "/try", "/ask"]
        self.assertIn("road.sequence must return to its first space",
                      validate_scene(scene))

    def test_a_road_naming_an_undeclared_space_is_rejected(self) -> None:
        scene = json.loads(json.dumps(FOREIGN_SCENE))
        scene["road"]["sequence"] = ["/read", "/nope", "/ask", "/read"]
        self.assertIn("road.sequence names undeclared spaces: /nope",
                      validate_scene(scene))

    def test_a_space_with_no_declared_position_is_rejected(self) -> None:
        scene = json.loads(json.dumps(FOREIGN_SCENE))
        del scene["positions"]["north"]
        self.assertIn("/read sits at undeclared position 'north'",
                      validate_scene(scene))


class CompileTests(unittest.TestCase):
    def test_geometry_and_style_stay_separate(self) -> None:
        with _project() as project:
            result = compile_slices(project)
            payload = json.loads((project / result["compiled"]).read_text(encoding="utf-8"))
            self.assertNotEqual(payload["slices"]["geometry"], payload["slices"]["style"])
            self.assertIn("GEOMETRY ONLY", payload["slices"]["geometry"])


class CorpusDrivenPromptTests(unittest.TestCase):
    """Goal 4. Tagging a reference must change the next prompt."""

    def test_style_cites_pursue_illustration_and_never_an_avoid_reference(self) -> None:
        with _project() as project:
            compile_slices(project)
            style = (project / "moodboards/llm-shots/prompts/slices/style.txt"
                     ).read_text(encoding="utf-8")
            self.assertIn("isometric cartoon/", style)
            self.assertNotIn("best ugly shot", style)

    def test_retagging_a_reference_changes_the_style_slice(self) -> None:
        with _project() as project:
            compile_slices(project)
            before = (project / "moodboards/llm-shots/prompts/slices/style.txt"
                      ).read_text(encoding="utf-8")
            tags_path = project / STORE / "corpus-tags.json"
            tags = json.loads(tags_path.read_text(encoding="utf-8"))
            for tag in tags["tags"].values():
                if tag.get("stance") == "pursue":
                    tag["stance"] = "avoid"
            tags_path.write_text(json.dumps(tags), encoding="utf-8")
            compile_slices(project)
            after = (project / "moodboards/llm-shots/prompts/slices/style.txt"
                     ).read_text(encoding="utf-8")
            self.assertNotEqual(before, after)

    def test_refine_attempt_is_separate_and_never_used_as_a_fresh_shot_reference(self) -> None:
        with _project() as project:
            corpus = json.loads((project / STORE / "corpus.json").read_text())
            tags_path = project / STORE / "corpus-tags.json"
            tags = json.loads(tags_path.read_text())
            candidate = next(item for item in corpus["items"]
                             if item["path"].endswith("clear layout.png"))
            tags["tags"][candidate["sha256"]].update({
                "stance": "refine", "role": "attempt",
                "note": "keep the crossing; enlarge the rooms",
            })
            tags_path.write_text(json.dumps(tags), encoding="utf-8")
            result = compile_slices(project)
            slices = result["slices"]
            self.assertNotIn(candidate["path"], slices["style"])
            self.assertNotIn(candidate["path"], slices["moodboard"])
            self.assertIn(candidate["path"], slices["refine"])
            self.assertIn("enlarge the rooms", slices["refine"])

            with self.assertRaisesRegex(GraphicsError, "before spending a fresh"):
                run_moodboard(project, dry_run=True)

    def test_prompt_input_hash_changes_when_a_tag_changes(self) -> None:
        with _project() as project:
            manifest = json.loads((project / STORE / "graphics-manifest.json").read_text())
            scene = json.loads((project / STORE / "scene-spec.json").read_text())
            before = prompt_inputs_hash(project, manifest, scene)
            tags_path = project / STORE / "corpus-tags.json"
            tags = json.loads(tags_path.read_text())
            next(iter(tags["tags"].values()))["stance"] = "avoid"
            tags_path.write_text(json.dumps(tags), encoding="utf-8")
            self.assertNotEqual(before, prompt_inputs_hash(project, manifest, scene))

    def test_inventory_is_its_own_slice_and_never_enters_style_or_geometry(self) -> None:
        with _project() as project:
            result = compile_slices(project)
            payload = json.loads((project / result["compiled"]).read_text(encoding="utf-8"))
            inventory = payload["slices"]["inventory"]
            self.assertIn("Acid Rockstar", inventory)
            self.assertNotIn("Acid Rockstar", payload["slices"]["style"])
            self.assertNotIn("Acid Rockstar", payload["slices"]["geometry"])
            self.assertNotIn("Acid Rockstar", payload["slices"]["moodboard"])


class ExportTests(unittest.TestCase):
    def test_every_space_becomes_a_box_and_a_billboard(self) -> None:
        with _project() as project:
            result = export_avge_calls(project)
            payload = json.loads((project / "moodboards/llm-shots/prompts/slices"
                                  / "avge-calls.json").read_text(encoding="utf-8"))
            self.assertEqual(result["callCount"], len(payload["calls"]))
            patterns = [call["pattern"] for call in payload["calls"]]
            self.assertEqual(patterns.count("isometric_box"), 6)
            self.assertIn("create_line_pattern", patterns)


class ProjectAgnosticTests(unittest.TestCase):
    def test_a_foreign_scene_compiles_and_exports(self) -> None:
        with _project(**{"scene-spec": FOREIGN_SCENE}) as project:
            compile_slices(project)
            result = export_avge_calls(project)
            payload = json.loads((project / result["avgeCalls"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["element"], "docs.nav.cycle")
            patterns = [call["pattern"] for call in payload["calls"]]
            self.assertEqual(patterns.count("isometric_box"), 4)
            self.assertEqual(patterns.count("attach"), 4)
            prefixes = {call["params"]["new_prefix"] for call in payload["calls"]
                        if call["pattern"] == "isometric_box"}
            self.assertEqual(prefixes, {"read", "try", "ask", "hub"})


class AdapterVerdictTests(unittest.TestCase):
    def test_a_recorded_verdict_routes_the_next_action(self) -> None:
        with _project() as project:
            self.assertEqual(next_action(read_state(project))["action"] != "run-avge",
                             True)
            compile_slices(project)
            export_avge_calls(project)
            record_adapter(project, "avge", "PASS", "tool list returned isometric_box")
            self.assertEqual(next_action(read_state(project))["action"], "run-avge")

    def test_a_blocked_verdict_routes_to_the_in_repo_renderer(self) -> None:
        with _project() as project:
            compile_slices(project)
            export_avge_calls(project)
            record_adapter(project, "avge", "BLOCKED", "not in the MCP config")
            self.assertEqual(next_action(read_state(project))["action"], "build")

    def test_an_unknown_verdict_is_refused(self) -> None:
        with _project() as project:
            with self.assertRaises(ValueError):
                record_adapter(project, "avge", "probably fine", "vibes")


class FallbackRendererTests(unittest.TestCase):
    def test_build_draws_a_gate_passing_scene_with_no_adapter(self) -> None:
        with _project() as project:
            compile_slices(project)
            build_svg(project)
            result = gate_outputs(project)
            self.assertTrue(result["passed"], result["errors"])


class GateTests(unittest.TestCase):
    def test_a_broken_road_is_caught(self) -> None:
        with _project() as project:
            compile_slices(project)
            build_svg(project)
            svg = project / "shots/landing.hero.flow.svg"
            text = svg.read_text(encoding="utf-8")
            head, _, tail = text.partition('<polyline id="road" points="')
            svg.write_text(head + '<polyline id="road" points="0,0 900,0 900,500 0,500 '
                           + tail.partition('"')[2], encoding="utf-8")
            result = gate_outputs(project)
            self.assertFalse(result["passed"])
            self.assertTrue(any(check["id"] == "road-topology" and not check["passed"]
                                for check in result["checks"]))

    def test_gate_fails_without_svg(self) -> None:
        with _project() as project:
            result = gate_outputs(project)
            self.assertFalse(result["passed"])
            self.assertTrue(any(check["id"] == "svg-exists" and not check["passed"]
                                for check in result["checks"]))


if __name__ == "__main__":
    unittest.main()
