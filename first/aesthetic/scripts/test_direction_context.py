from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import brief_workflow as bw
import direction_context as dc
import editorial_workflow as ew


class CompactDirectionContextTest(unittest.TestCase):
    def test_absent_feedback_stays_empty_instead_of_becoming_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ew.seed_corpus(root, "art-direction", "a landing hero")
            value = dc.inference_context(root)
            self.assertEqual(value["briefConstraints"], [])
            self.assertEqual(value["preferences"]["elements"], [])

    def test_stale_or_missing_brief_constraints_are_rejected(self) -> None:
        brief = bw.default_brief("2026-08-28T00:00:00Z")
        brief["answers"][-1]["answer"] = "Rooms must not be copied."
        with self.assertRaisesRegex(dc.DirectionContextError, "briefConstraints"):
            dc.validate_brief_constraints([], brief)
        current = dc.validate_brief_constraints([{
            "id": "fixed", "answer": "Rooms must not be copied.",
            "impact": "Room imagery is omitted from the composition."
        }], brief)
        self.assertEqual(current[0]["id"], "fixed")



def _project(tmp: str) -> Path:
    root = Path(tmp)
    ew.seed_corpus(root, "art-direction", "a landing hero")
    return root


def _decisions(root: Path, elements: list[dict]) -> None:
    path = root / dc.STORE / "decisions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"elements": elements}), encoding="utf-8")


REJECTED_LONG_SHOT = {
    "element": "landing.hero.flow", "source": "user", "scored": True, "stars": 1,
    "sentiment": "dislike", "state": "discarded",
    "preview": "design/landing-flow-hero.html",
    "evidence": "the long shot reads as an empty room at thumbnail size",
}


class TokenCostTest(unittest.TestCase):
    def test_a_byte_ratio_never_claims_to_be_an_exact_count(self) -> None:
        tokens, exact = dc.count("x" * 40)
        self.assertEqual(tokens, 10)
        self.assertFalse(exact)

    def test_an_unnamed_profile_is_refused_rather_than_guessed(self) -> None:
        with self.assertRaisesRegex(dc.DirectionContextError, "unknown tokenizer profile"):
            dc.count("x", "gpt-whatever")


class CompilePassTest(unittest.TestCase):
    def test_the_same_project_compiles_to_the_same_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp)
            _decisions(root, [REJECTED_LONG_SHOT])
            first = dc.compile_pass(root, "proposal")
            second = dc.compile_pass(root, "proposal")
            self.assertEqual(json.dumps(first, sort_keys=True),
                             json.dumps(second, sort_keys=True))

    def test_corrections_are_admitted_before_doctrine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp)
            _decisions(root, [REJECTED_LONG_SHOT])
            order = [row["priority"] for row in dc.compile_pass(root, "proposal")["chunks"]]
            self.assertEqual(order, sorted(order, key=dc.PRIORITIES.index))

    def test_a_full_budget_drops_optional_doctrine_and_keeps_the_correction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp)
            _decisions(root, [REJECTED_LONG_SHOT])
            trace = dc.compile_pass(root, "proposal", budget=60)
            kept = {row["key"] for row in trace["chunks"] if row["admitted"]}
            dropped = [row for row in trace["chunks"] if not row["admitted"]]
            self.assertIn("correction:landing.hero.flow", kept)
            self.assertTrue(dropped)
            self.assertTrue(all(row["priority"] == "doctrine"
                                or row["key"] == "skill:SKILL.md" for row in dropped))
            self.assertIn("budget full", dropped[0]["reason"])

    def test_doctrine_is_spent_in_the_order_the_skill_tells_you_to_read_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace = dc.compile_pass(_project(tmp), "proposal")
            doctrine = [row["key"].removeprefix("doctrine:references/")
                        for row in trace["chunks"] if row["priority"] == "doctrine"]
            named = [name for name in doctrine if name in dc.DOCTRINE_ORDER]
            self.assertEqual(named, list(dc.DOCTRINE_ORDER))
            self.assertNotIn("CONTEXT.md", doctrine)

    def test_a_correction_too_large_to_fit_raises_instead_of_being_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp)
            _decisions(root, [REJECTED_LONG_SHOT])
            with self.assertRaisesRegex(dc.DirectionContextError, "never dropped"):
                dc.compile_pass(root, "proposal", budget=1)

    def test_the_rejected_landing_hero_long_shot_survives_without_its_scene(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp)
            _decisions(root, [REJECTED_LONG_SHOT])
            bundle = dc.compile_pass(root, "proposal", budget=200)["bundle"]
            self.assertIn("landing.hero.flow: rejected by the user", bundle)
            self.assertIn("empty room at thumbnail size", bundle)
            self.assertNotIn("landing-flow-hero.html", bundle)

    def test_repo_dev_rail_documents_have_no_route_into_a_design_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp)
            (root / "ROADMAP.md").write_text("R-99 | TODO | burndown row", encoding="utf-8")
            (root / "BUGS.md").write_text("root cause: a regression", encoding="utf-8")
            bundle = dc.compile_pass(root, "proposal")["bundle"]
            self.assertNotIn("burndown row", bundle)
            self.assertNotIn("root cause", bundle)


class CorrectionBundleTest(unittest.TestCase):
    def test_a_bounded_correction_bundle_outranks_optional_doctrine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp)
            shots = root / ".audit" / "shots"
            shots.mkdir(parents=True)
            (shots / "s.json").write_text(json.dumps({
                "shot_id": "shot-1",
                "user_feedback": {"correction": "the thumbnail is unreadable",
                                  "observed_at": "2026-09-01T02:51:48Z"}}),
                encoding="utf-8")

            trace = dc.compile_pass(root, "proposal", budget=200)

            self.assertEqual(trace["chunks"][0]["priority"], "correction")
            admitted = [row["key"] for row in trace["chunks"] if row["admitted"]]
            self.assertIn("correction:shot:shot-1", admitted)
            self.assertIn("the thumbnail is unreadable", trace["bundle"])
            self.assertTrue(any(row["priority"] == "doctrine" and not row["admitted"]
                                for row in trace["chunks"]))


class ProofGateTest(unittest.TestCase):
    def test_an_expensive_pass_waits_for_its_cheapest_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _project(tmp)
            with self.assertRaisesRegex(dc.DirectionContextError, "gated on golden-rules"):
                dc.compile_pass(root, "generation")
            passed = dc.compile_pass(root, "generation", proof=("golden-rules",))
            self.assertEqual(passed["proofGate"]["state"], "passed")
            forced = dc.compile_pass(root, "generation", force=True)
            self.assertEqual(forced["proofGate"]["state"], "forced")

    def test_a_cheap_pass_declares_no_gate_rather_than_a_silent_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = dc.compile_pass(_project(tmp), "intent")["proofGate"]
            self.assertEqual(gate, {"requires": None, "state": "not required"})


class AttemptRecordTest(unittest.TestCase):
    def test_an_outcome_outside_the_vocabulary_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(dc.DirectionContextError, "outcome must be"):
                dc.record_attempt(Path(tmp), {"outcome": "great"})

    def test_reviewed_attempts_append_rather_than_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dc.record_attempt(root, {"task": "hero", "outcome": "rejected"})
            path = dc.record_attempt(root, {"task": "hero", "outcome": "accepted"})
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual([json.loads(line)["outcome"] for line in lines],
                             ["rejected", "accepted"])


if __name__ == "__main__":
    unittest.main()
