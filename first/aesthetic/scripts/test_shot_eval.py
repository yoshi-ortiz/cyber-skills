#!/usr/bin/env python3
"""The rejected landing round, kept as a fixture so it cannot be re-shipped.

The user rejected this Shot. Epic 3 exists to answer it, and the answer is
only meaningful if the failure it started from stays legible. These tests
pin what was wrong: the round recorded a text summary, carried no artifact
anyone could look at, and still has to read as failed.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "check" / "tokens-qa" / "scripts"))
import feedback as advisory  # noqa: E402
import shot_io  # noqa: E402
import shot_view  # noqa: E402

BASELINE = REPO / ".audit" / "shots" / "20260901T025137Z-a7052318.json"
DIGEST = "a481fa5ac9900b7bcca3bc6748b052857156f8cfea72fe806c0340e4a3f9126f"


class TheRejectedRoundStaysRejected(unittest.TestCase):
    def setUp(self):
        if not BASELINE.is_file():
            self.skipTest(f"{BASELINE} is absent")
        self.record = shot_io.read_shot(BASELINE)

    def test_the_baseline_is_byte_identical(self):
        self.assertEqual(hashlib.sha256(BASELINE.read_bytes()).hexdigest(), DIGEST)

    def test_the_verdict_is_failed(self):
        self.assertEqual(shot_view.verdict(self.record), "failed")

    def test_a_v1_record_still_reads(self):
        self.assertEqual(json.loads(BASELINE.read_text())["version"], 1)
        self.assertEqual(self.record["version"], 2)

    def test_the_exact_words_survive_migration(self):
        said = self.record["user_feedback"]["correction"]
        self.assertIn("did not impove the graphics round or the thumbnail", said)
        self.assertIn("output is useless", said)

    def test_it_carries_no_artifact_anyone_could_look_at(self):
        self.assertNotIn("artifacts", self.record["output"])
        self.assertEqual(self.record["output"]["adapter"], "text")

    def test_the_correction_bundle_names_no_visual_evidence(self):
        self.assertEqual(advisory.correction_bundle(self.record)["artifacts"], [])


class ACandidateMustDoBetter(unittest.TestCase):
    """What Epic 3's Shot has to clear. Failing here means the round repeated
    the mistake rather than answered it."""

    def candidate(self, **over):
        base = {
            "version": 2, "shot_id": "candidate", "scope": "landing hero",
            "inputs": {"prompt_hash": "sha256:x", "tools": []},
            "compute": {"model": "m", "harness": "h", "started_at": "2026-09-01T00:00:00Z",
                        "duration_ms": 1,
                        "tokens": {"input": None, "output": None, "profile": "unavailable"}},
            "output": {"adapter": "graphic", "artifacts": [
                {"role": "deliverable", "path": "design/review/hero.png",
                 "mime": "image/png", "bytes": 1, "sha256": "sha256:a"},
                {"role": "deliverable", "path": "design/review/thumb.png",
                 "mime": "image/png", "bytes": 1, "sha256": "sha256:b"}]},
            "provenance": "procedural", "user_feedback": {"status": "pending"},
        }
        base.update(over)
        return shot_io.validate(base)

    def test_a_candidate_declares_real_artifacts(self):
        artifacts = self.candidate()["output"]["artifacts"]
        self.assertEqual(len(artifacts), 2)
        self.assertTrue(all(a["sha256"] for a in artifacts))

    def test_machine_proof_never_promotes_it(self):
        self.assertEqual(shot_view.verdict(self.candidate()), "pending")

    def test_only_an_explicit_accept_promotes_it(self):
        accepted = self.candidate(user_feedback={"status": "accepted"})
        self.assertEqual(shot_view.verdict(accepted), "accepted")

    def test_a_correction_beats_any_amount_of_proof(self):
        sent_back = self.candidate(
            user_feedback={"status": "pending", "correction": "the crop is still wrong"})
        self.assertEqual(shot_view.verdict(sent_back), "failed")


if __name__ == "__main__":
    unittest.main()
