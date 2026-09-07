from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import context_learner as learner


def row(task: str, arm: str, split: str, tokens: int, recall: float = 1.0,
        outcome: str = "accepted") -> dict:
    return {"version": 1, "reviewed": True, "task_id": task,
            "repository_revision": "sha256:repo", "arm": arm, "split": split,
            "model": "model-v1", "harness": "harness-v1", "profile": "bytes/4@v1",
            "budget": 1000, "bundle_hash": "sha256:bundle",
            "trace_hash": "sha256:trace", "outcome": outcome,
            "tokens_input": tokens, "tokens_output": 0,
            "required_context_recall": recall, "verdict_source": "user:event-1"}


class ContextLearnerTest(unittest.TestCase):
    def test_reviewed_pairs_must_improve_heldout_cost_without_recall_loss(self) -> None:
        rows = [row("train", "baseline", "train", 100),
                row("train", "candidate", "train", 80),
                row("heldout", "baseline", "heldout", 120),
                row("heldout", "candidate", "heldout", 90)]
        report = learner.evaluate(rows)
        self.assertEqual(report["recommendation"], "candidate")
        self.assertTrue(report["heldout_passed"])

        rows.insert(0, row("train", "baseline", "train", 20, outcome="rejected"))
        self.assertEqual(learner.evaluate(rows)["arms"]["baseline"]["attempts"], 3)

        rows[-1]["required_context_recall"] = .5
        self.assertFalse(learner.evaluate(rows)["heldout_passed"])

    def test_legacy_attempt_history_is_refused_not_upgraded_by_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "attempts.jsonl"
            path.write_text(json.dumps({"adapter": "iso-svg", "outcome": "accepted"}) + "\n")
            with self.assertRaisesRegex(learner.LearnerError, "fields do not match"):
                learner.load(path)

    def test_experiment_controls_cannot_change_between_arms(self) -> None:
        rows = [row("train", "baseline", "train", 100),
                row("train", "candidate", "train", 80),
                row("heldout", "baseline", "heldout", 120),
                row("heldout", "candidate", "heldout", 90)]
        rows[1]["model"] = "different-model"
        with self.assertRaisesRegex(learner.LearnerError, "changes model"):
            learner.evaluate(rows)


if __name__ == "__main__":
    unittest.main()
