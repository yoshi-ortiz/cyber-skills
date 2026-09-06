#!/usr/bin/env python3
import contextlib
import hashlib
import json
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from graphics_flow import next_action, read_state
from text_to_graphics import (build_svg, compile_slices, export_avge_calls,
                              gate_outputs, GraphicsError, prompt_inputs_hash,
                              record_adapter, run_clear_shot, run_moodboard,
                              validate_scene)

ROOT = Path(__file__).resolve().parents[3]
STORE = "spec/design-harness"
HARNESS_FILES = ("graphics-manifest.json", "scene-spec.json",
                 "corpus.json", "corpus-tags.json", "corpus-derived.json",
                 "cast.json")

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


def _reviewed_intent(project: Path) -> None:
    constraints = [{"id": "done", "text": "One readable 16:9 moodboard.",
                    "priority": "criterion", "sourceRef": "brief-events:7"}]
    digest = hashlib.sha256(json.dumps(
        constraints, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    (project / STORE / "reviewed-intent.json").write_text(json.dumps({
        "version": 1, "reviewed": True,
        "invocation": "aesthetic/moodboard-generation",
        "source": {"kind": "user", "ref": "brief-events:7", "digest": digest},
        "review": {"source": "user", "at": "2026-09-05T12:00:00Z"},
        "constraints": constraints}), encoding="utf-8")


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
                             if "clear layout" in item["path"])
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

    def test_character_observations_split_build_from_avoid(self) -> None:
        """A counterevidence entry must read as a boundary, not an instruction.

        Folding 'avoid' prose into the same list as 'build it this way' is how
        a generator ends up quoting the register it was told to steer clear of.
        """
        with _project(**{
            "character-observations": {
                "version": 1,
                "observations": [
                    {"id": "ears", "source": "a.png", "box": [0, 0, 1, 1],
                     "read": "long provenance essay about the ear",
                     "rule": "One circle sits proud of the head silhouette."},
                    {"id": "realism", "stance": "avoid",
                     "source": "best ugly shot, good layout.png", "box": [0, 0, 1, 1],
                     "read": "long provenance essay about proportion",
                     "rule": "Never realistic human proportion."},
                ],
            },
        }) as project:
            style = compile_slices(project)["slices"]["style"]
            self.assertIn("One circle sits proud", style)
            self.assertIn("Never draw figures in this register:", style)
            self.assertIn("Never realistic human proportion.", style)
            # The boundary trails the build list, not the other way round.
            self.assertLess(style.index("One circle sits proud"),
                            style.index("Never draw figures in this register:"))
            # Neither the provenance nor the source filename may travel. Naming
            # an avoid-tagged file in a style prompt summons the register.
            self.assertNotIn("long provenance essay", style)
            self.assertNotIn("best ugly shot", style)

    def test_no_observations_file_compiles_with_no_construction_section(self) -> None:
        with _project() as project:
            style = compile_slices(project)["slices"]["style"]
            self.assertNotIn("How this corpus builds a figure", style)

class MoodboardRuntimeGateTests(unittest.TestCase):
    def test_missing_proof_stops_the_expensive_runner(self) -> None:
        with _project() as project:
            _reviewed_intent(project)
            with unittest.mock.patch("graphics_generation.subprocess.run") as invoked:
                with self.assertRaisesRegex(ValueError, "generation blocked"):
                    run_moodboard(project)
            invoked.assert_not_called()

    def test_matching_observed_proof_permits_exactly_one_runner_call(self) -> None:
        import direction_context as dc

        with _project() as project:
            _reviewed_intent(project)
            trace = dc.compile_pass(project, "generation", proof=("golden-rules",),
                                    require_reviewed=True)
            artifact = project / "proof.txt"
            artifact.write_text("golden rules passed", encoding="utf-8")
            proof = project / "proof.json"
            proof.write_text(json.dumps({"version": 1, "check": "golden-rules",
                "status": "passed", "invocation": "aesthetic/moodboard-generation",
                "intentDigest": trace["identity"], "observedAt": "2026-09-05T12:01:00Z",
                "artifact": "proof.txt",
                "artifactSha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}),
                encoding="utf-8")
            completed = unittest.mock.Mock(returncode=0, stdout="ok", stderr="")
            with unittest.mock.patch("graphics_generation.subprocess.run",
                                     return_value=completed) as invoked:
                result = run_moodboard(project, proof=proof)
            invoked.assert_called_once()
            self.assertEqual(result["proofGate"]["state"], "passed")
            self.assertEqual(result["contextIdentity"], trace["identity"])


class EmptySpaceGateTests(unittest.TestCase):
    """An empty room is one of the recorded failures. The gate owns it now."""

    def test_a_space_with_no_boss_fails_the_gate(self) -> None:
        with _project() as project:
            cast_path = project / STORE / "cast.json"
            cast = json.loads(cast_path.read_text())
            cast["figures"].pop("/check")
            cast_path.write_text(json.dumps(cast), encoding="utf-8")
            build_svg(project)
            result = gate_outputs(project)
            self.assertFalse(result["passed"])
            self.assertTrue(any("nobody in them" in e for e in result["errors"]))
            self.assertIn("check", " ".join(result["errors"]))

    def test_text_no_billboard_declares_fails_the_gate(self) -> None:
        """A generator invented signage. This renderer may not."""
        with _project() as project:
            build_svg(project)
            manifest = json.loads((project / STORE / "graphics-manifest.json").read_text())
            svg = project / str((manifest.get("outputs") or {}).get("vector"))
            svg.write_text(svg.read_text().replace("</svg>",
                           '<text x="5" y="5">qa tests</text></svg>'), encoding="utf-8")
            result = gate_outputs(project)
            self.assertFalse(result["passed"])
            self.assertTrue(any("no billboard declares" in e for e in result["errors"]))


class DeterministicPromptTests(unittest.TestCase):
    """The hand-written prompt stated the billboard text twice and disagreed
    with itself on three of six, so the generator invented a third answer."""

    def _prompt(self, project) -> str:
        from graphics_slices import deterministic_prompt

        result = deterministic_prompt(project)
        return Path(result["deterministic"]).read_text(encoding="utf-8")

    def test_each_billboard_string_appears_exactly_once(self) -> None:
        with _project() as project:
            scene = json.loads((project / STORE / "scene-spec.json").read_text())
            text = self._prompt(project)
            for want in scene["billboards"].values():
                self.assertEqual(text.count(f'"{want}"'), 1, want)

    def test_billboards_come_from_the_scene_and_keep_the_slash(self) -> None:
        """The old prompt dropped the slash while demanding it be kept."""
        with _project() as project:
            scene = json.loads((project / STORE / "scene-spec.json").read_text())
            text = self._prompt(project)
            for space, want in scene["billboards"].items():
                self.assertIn(f'- {space}: "{want}"', text)
                self.assertTrue(want.startswith("/"), want)

    def test_editing_the_scene_moves_the_prompt(self) -> None:
        """A generated prompt cannot drift from its source. That was the bug."""
        with _project() as project:
            path = project / STORE / "scene-spec.json"
            scene = json.loads(path.read_text())
            scene["billboards"]["/fix"] = "/fix TRIAGE"
            path.write_text(json.dumps(scene), encoding="utf-8")
            text = self._prompt(project)
            self.assertIn('"/fix TRIAGE"', text)
            self.assertNotIn('"/fix REPAIR"', text)

    def test_known_failures_reach_the_prompt_as_constraints(self) -> None:
        with _project(**{"known-failures": {
            "version": 1,
            "failures": [{"id": "open-road", "seenIn": "a.png",
                          "defect": "road did not close",
                          "constraint": "The road is ONE closed curve."}],
        }}) as project:
            text = self._prompt(project)
            self.assertIn("ALREADY REJECTED", text)
            self.assertIn("The road is ONE closed curve.", text)
            self.assertIn("road did not close", text)

    def test_audit_only_observations_never_reach_the_generator(self) -> None:
        """An entry with no `rule` is provenance for a reader, not an
        instruction for an image model."""
        with _project(**{"character-observations": {
            "version": 1,
            "observations": [
                {"id": "eyes", "read": "long provenance essay",
                 "rule": "Eyes are large white ovals."},
                {"id": "meta", "read": "notes about how tagging works"},
            ],
        }}) as project:
            text = self._prompt(project)
            self.assertIn("Eyes are large white ovals.", text)
            self.assertNotIn("notes about how tagging works", text)
            self.assertNotIn("long provenance essay", text)

    def test_shot_corrections_are_not_forwarded_to_the_image_model(self) -> None:
        """Corrections aimed at other adapters are contamination here."""
        with _project() as project:
            shots = project / ".audit" / "shots"
            shots.mkdir(parents=True)
            (shots / "x.json").write_text(json.dumps({
                "version": 2, "shot_id": "x",
                "user_feedback": {"correction": "the companion app thumbnails"},
            }), encoding="utf-8")
            self.assertNotIn("companion app thumbnails", self._prompt(project))


class ClearShotPromptTests(unittest.TestCase):
    def _prompt(self, project: Path) -> str:
        from graphics_slices import clear_shot_prompt

        result = clear_shot_prompt(project)
        return Path(result["clearShotPrompt"]).read_text(encoding="utf-8")

    def test_prompt_treats_the_clear_shot_as_style_and_composition(self) -> None:
        with _project() as project:
            text = self._prompt(project)
            self.assertIn("clear layout, good cartoon.png", text)
            self.assertIn("Keep its composition and cartoon register", text)
            self.assertIn("cartoon/Pasted 2026-08-28 at 5.53.02 p.m..png", text)

    def test_prompt_contains_exact_scene_text_once_and_no_avoid_reference(self) -> None:
        with _project() as project:
            scene = json.loads((project / STORE / "scene-spec.json").read_text())
            text = self._prompt(project)
            for want in scene["billboards"].values():
                self.assertEqual(text.count(f'"{want}"'), 1, want)
            self.assertNotIn("best ugly shot", text)
            self.assertNotIn("qa tests", text)
            self.assertNotIn("clean code", text)

    def test_prompt_uses_failure_constraints_without_the_failure_essay(self) -> None:
        with _project(**{"known-failures": {
            "version": 1,
            "failures": [{"id": "open-road", "seenIn": "bad.png",
                          "defect": "the old road stopped",
                          "constraint": "Draw one closed road."}],
        }}) as project:
            text = self._prompt(project)
            self.assertIn("Draw one closed road.", text)
            self.assertNotIn("bad.png", text)
            self.assertNotIn("the old road stopped", text)

    def test_prompt_is_bounded_for_an_image_model(self) -> None:
        with _project() as project:
            text = self._prompt(project)
            self.assertLessEqual(len(text.encode("utf-8")), 12000)
            self.assertNotIn("Generated by", text)
            self.assertNotIn("Do not hand-edit", text)

    def test_dry_run_hands_the_clear_prompt_to_agy_without_running_it(self) -> None:
        with _project() as project:
            result = run_clear_shot(project, dry_run=True)
            self.assertEqual(result["adapter"], "agy")
            self.assertEqual(result["outcome"], "pending")
            self.assertIn("--output-format json", result["command"])
            self.assertIn("clear-shot-prompt.txt", result["prompt"])
            self.assertIn("clear-shot-", result["output"])


class SliceSeparationTests(unittest.TestCase):
    """Each slice carries one concern, and a changed input goes stale."""
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
