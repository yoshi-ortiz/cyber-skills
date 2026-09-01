#!/usr/bin/env python3
"""The order is the product. These assert it, and assert the refusals.

`deliver` exists because two of its four steps used to get dropped. A test that
only checked the happy path would not notice them being dropped again.
"""
import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deliver


class Order(unittest.TestCase):
    def run_with(self, outputs, **kwargs):
        calls = []

        def fake(argv, project_root):
            calls.append((Path(argv[0]).stem, argv[1] if len(argv) > 1 else ""))
            return outputs.pop(0)

        with unittest.mock.patch.object(deliver, "step", side_effect=fake):
            payload = deliver.deliver(
                Path("/tmp/p"), "out.html", "a,b", "hero", "How strong?",
                kwargs.get("assessments", "/tmp/a.json"), "revisa")
        return calls, payload

    def test_all_four_steps_run_in_order(self):
        calls, payload = self.run_with(
            ["", "http://localhost:1/?key=abc123", "[]", ""])
        self.assertEqual(calls, [
            ("bootstrap_harness", "article"),
            ("bootstrap_harness", "publish"),
            ("review_delivery", "--cohort"),
            ("bootstrap_harness", "status"),
        ])
        self.assertEqual(payload["url"], "http://localhost:1/?key=abc123")
        self.assertEqual(payload["key"], "abc123")

    def test_missing_assessments_refuses_before_publishing_a_dead_link(self):
        with self.assertRaises(deliver.DeliveryError) as refused:
            self.run_with(["", "http://localhost:1/?key=abc", "", ""],
                          assessments=None)
        self.assertIn("cannot act on", str(refused.exception))

    def test_publish_without_a_url_is_a_refusal_not_a_reply(self):
        with self.assertRaises(deliver.DeliveryError) as refused:
            self.run_with(["", "Waiting for the agent to push a screen...", "", ""])
        self.assertIn("no URL", str(refused.exception))


if __name__ == "__main__":
    unittest.main()
