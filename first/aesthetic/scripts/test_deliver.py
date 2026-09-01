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

    # The stub returns what the REAL verbs return, which is the whole point.
    # This fixture used to hand a URL back from `publish`, and `publish` has
    # never printed one -- it prints "Serving <name>. ...". So the suite was
    # green against a fake that behaved in a way the harness does not, and the
    # URL scrape it was guarding could fail on every real invocation without a
    # single test noticing. `open` is the verb that owns the URL.
    PUBLISH_SAYS = "Serving out.html. Any screen written after this steals the route"

    def test_every_step_runs_in_order(self):
        calls, payload = self.run_with(
            ["", self.PUBLISH_SAYS, "http://localhost:1/?key=abc123", "[]", ""])
        self.assertEqual(calls, [
            ("bootstrap_harness", "article"),
            ("bootstrap_harness", "publish"),
            ("bootstrap_harness", "open"),
            ("review_delivery", "--cohort"),
            ("bootstrap_harness", "status"),
        ])
        self.assertEqual(payload["url"], "http://localhost:1/?key=abc123")
        self.assertEqual(payload["key"], "abc123")

    def test_publish_output_is_never_mistaken_for_a_url(self):
        """The regression this file exists to hold: `publish` says "Serving
        ...", and reading a URL out of that sentence produced a hard failure
        on every single run of the script."""
        calls, payload = self.run_with(
            ["", self.PUBLISH_SAYS, "http://localhost:1/?key=ab99", "[]", ""])
        self.assertIn(("bootstrap_harness", "open"), calls)
        self.assertEqual(payload["key"], "ab99")

    def test_missing_assessments_refuses_before_publishing_a_dead_link(self):
        calls = []

        def fake(argv, project_root):
            calls.append(Path(argv[0]).stem)
            return ""

        with unittest.mock.patch.object(deliver, "step", side_effect=fake):
            with self.assertRaises(deliver.DeliveryError) as refused:
                deliver.deliver(Path("/tmp/p"), "out.html", "a,b", "hero",
                                "How strong?", None, "revisa")
        self.assertIn("cannot act on", str(refused.exception))
        # "before publishing" is the assertion, not a figure of speech: nothing
        # may run at all, or the refusal arrives having already replaced the
        # screen the user is looking at.
        self.assertEqual(calls, [])

    def test_open_without_a_url_is_a_refusal_not_a_reply(self):
        with self.assertRaises(deliver.DeliveryError) as refused:
            self.run_with(["", self.PUBLISH_SAYS,
                           "Waiting for the agent to push a screen...", "", ""])
        self.assertIn("no URL", str(refused.exception))


if __name__ == "__main__":
    unittest.main()
