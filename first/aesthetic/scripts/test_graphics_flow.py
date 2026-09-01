#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from graphics_flow import (PROOF_KIND, correction_bundles, correction_id,
                          next_action, read_state)
from review_delivery import record_proof
from test_text_to_graphics import _project
from text_to_graphics import (build_svg, compile_slices, export_avge_calls,
                              record_adapter)


def _state(**overrides) -> dict:
    """A loop state with everything done, so each test breaks one thing."""
    state = {
        "sceneErrors": [], "sceneHash": "abc", "corpusRoot": True,
        "corpusRootPath": "moodboards",
        "corpus": True, "tags": True,
        "promptHash": "prompt", "slicesPromptHash": "prompt",
        "slicesHash": "abc", "callsHash": "abc", "adapters": {"avge": "PASS"},
        "refinePending": [],
        "svgHash": "abc", "gateErrors": [],
        "correctionsPending": [], "proofsMissing": [],
    }
    state.update(overrides)
    return state


class FlowTests(unittest.TestCase):
    """One next action from any state, with the reason it fired."""

    def test_a_finished_loop_reports_done(self) -> None:
        """Green AND proven is done. Green alone is not.

        This assertion used to read `done` off a state carrying no proof at
        all, which is the bug: every structural gate passing says the bytes
        are well formed, and says nothing about whether a human can see them.
        """
        self.assertEqual(next_action(_state())["action"], "done")
        self.assertEqual(
            next_action(_state(proofsMissing=[PROOF_KIND]))["action"],
            "verify-delivery")

    def test_an_outstanding_correction_outranks_proving_a_delivery(self) -> None:
        step = next_action(_state(
            correctionsPending=[{"correctionId": "c0ffee", "shotId": "shot-1",
                                 "correction": "the thumbnail is unreadable"}],
            proofsMissing=[PROOF_KIND]))
        self.assertEqual(step["action"], "apply-correction")
        self.assertIn("shot-1", step["reason"])

    def test_a_rejected_artifact_is_repaired_before_it_is_proven(self) -> None:
        step = next_action(_state(
            gateErrors=["road is not closed"],
            correctionsPending=[{"correctionId": "c0ffee", "shotId": "shot-1",
                                 "correction": "the thumbnail is unreadable"}],
            proofsMissing=[PROOF_KIND]))
        self.assertEqual(step["action"], "repair-output")

    def test_an_invalid_scene_outranks_everything_else(self) -> None:
        step = next_action(_state(sceneErrors=["road must be an object"],
                                  corpus=False, svgHash=""))
        self.assertEqual(step["action"], "edit-scene-spec")
        self.assertIn("road must be an object", step["reason"])

    def test_an_unobserved_corpus_comes_before_tagging(self) -> None:
        self.assertEqual(next_action(_state(corpus=False, tags=False))["action"],
                         "observe")

    def test_slices_stale_against_the_scene_hash_recompile(self) -> None:
        step = next_action(_state(slicesHash="older"))
        self.assertEqual(step["action"], "compile")
        self.assertIn("scene changed", step["reason"])

    def test_slices_stale_against_corpus_context_recompile(self) -> None:
        step = next_action(_state(slicesPromptHash="older"))
        self.assertEqual(step["action"], "compile")
        self.assertIn("corpus context changed", step["reason"])

    def test_refine_attempt_blocks_a_fresh_shot(self) -> None:
        step = next_action(_state(refinePending=["attempts/close-but-wrong.png"]))
        self.assertEqual(step["action"], "refine")
        self.assertIn("close-but-wrong.png", step["reason"])

    def test_calls_stale_against_the_scene_hash_re_export(self) -> None:
        self.assertEqual(next_action(_state(callsHash="older"))["action"],
                         "export-avge")

    def test_an_unpreflighted_adapter_is_asked_for_before_drawing(self) -> None:
        self.assertEqual(next_action(_state(adapters={}, svgHash=""))["action"],
                         "preflight")

    def test_a_passing_adapter_draws_through_avge(self) -> None:
        step = next_action(_state(svgHash=""))
        self.assertEqual(step["action"], "run-avge")

    def test_a_blocked_adapter_falls_back_to_the_in_repo_renderer(self) -> None:
        step = next_action(_state(svgHash="", adapters={"avge": "BLOCKED"}))
        self.assertEqual(step["action"], "build")
        self.assertIn("BLOCKED", step["reason"])

    def test_a_failing_gate_names_what_it_caught(self) -> None:
        step = next_action(_state(gateErrors=["road is not closed"]))
        self.assertEqual(step["action"], "repair-output")
        self.assertIn("road is not closed", step["reason"])


    def test_an_svg_drawn_from_an_older_scene_is_redrawn(self) -> None:
        step = next_action(_state(svgHash="older", adapters={"avge": "BLOCKED"}))
        self.assertEqual(step["action"], "build")

    def test_an_svg_with_no_recorded_attempt_is_not_trusted(self) -> None:
        step = next_action(_state(svgHash="", adapters={"avge": "BLOCKED"}))
        self.assertEqual(step["action"], "build")


    def test_a_corpus_root_that_does_not_exist_is_named_not_looped_on(self) -> None:
        step = next_action(_state(corpus=False, corpusRoot=False))
        self.assertEqual(step["action"], "add-corpus")
        self.assertIn("moodboards", step["reason"])


class CorrectionTests(unittest.TestCase):
    """A bundle has no natural identity, so it is given one."""

    def _shot(self, project: Path) -> None:
        shots = project / ".audit" / "shots"
        shots.mkdir(parents=True, exist_ok=True)
        (shots / "s.json").write_text(json.dumps({
            "shot_id": "shot-1",
            "user_feedback": {"correction": "the thumbnail is unreadable",
                              "observed_at": "2026-09-01T02:51:48Z"}}),
            encoding="utf-8")

    def test_the_same_bundle_always_has_the_same_id(self) -> None:
        self.assertEqual(correction_id("shot-1", "2026-09-01T02:51:48Z"),
                         correction_id("shot-1", "2026-09-01T02:51:48Z"))
        self.assertNotEqual(correction_id("shot-1", "2026-09-01T02:51:48Z"),
                            correction_id("shot-2", "2026-09-01T02:51:48Z"))

    def test_an_applied_correction_stops_firing(self) -> None:
        with _project() as project:
            self._shot(project)
            pending = correction_bundles(project)
            self.assertEqual([bundle["shotId"] for bundle in pending], ["shot-1"])
            self.assertEqual(read_state(project)["correctionsPending"], pending)
            support = project / "spec/design-harness" / "support.json"
            payload = json.loads(support.read_text(encoding="utf-8")) \
                if support.exists() else {}
            payload["appliedCorrections"] = [pending[0]["correctionId"]]
            support.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(read_state(project)["correctionsPending"], [])


class ReadStateTests(unittest.TestCase):
    def test_a_project_with_no_corpus_folder_is_told_so(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            store = project / "spec/design-harness"
            store.mkdir(parents=True)
            for name in ("graphics-manifest.json", "scene-spec.json"):
                (store / name).write_text(
                    (Path(__file__).resolve().parents[3] / "spec/design-harness" / name
                     ).read_text(encoding="utf-8"), encoding="utf-8")
            self.assertEqual(next_action(read_state(project))["action"], "add-corpus")

    def test_a_rebuild_records_the_scene_it_was_drawn_from(self) -> None:
        with _project() as project:
            compile_slices(project)
            export_avge_calls(project)
            record_adapter(project, "avge", "BLOCKED", "absent from the MCP config")
            build_svg(project)
            state = read_state(project)
            self.assertEqual(state["svgHash"], state["sceneHash"])
            self.assertEqual(next_action(state)["action"], "verify-delivery")
            image = project / "design" / "review" / "landing.hero.flow.png"
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            record_proof(project, project / "shots/landing.hero.flow.svg",
                         image, PROOF_KIND)
            self.assertEqual(next_action(read_state(project))["action"], "done")

    def test_a_fresh_project_needs_compiling_before_anything_is_drawn(self) -> None:
        with _project() as project:
            step = next_action(read_state(project))
            self.assertIn(step["action"], {"compile", "export-avge"})


if __name__ == "__main__":
    unittest.main()
