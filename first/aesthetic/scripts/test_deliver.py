#!/usr/bin/env python3
"""The order is the product. These assert it, and assert the refusals.

`deliver` exists because two of its four steps used to get dropped. A test that
only checked the happy path would not notice them being dropped again.
"""
import contextlib
import io
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


PAYLOAD = {"url": "http://localhost:1/?key=abc123", "key": "abc123",
           "ask": "How strong?", "images": {"images": []}}
ARGV = ["--project-root", "/tmp/p", "--out", "out.html", "--cohort", "a,b",
        "--round-label", "hero", "--asks", "How strong?",
        "--assessments", "/tmp/a.json", "--idle-text", "revisa"]


class ShotRecord(unittest.TestCase):
    """A round the QA tool never saw cannot be assessed. Recording is not
    part of the delivery, though: it happens after the payload is printed,
    and it may not turn a delivered round into a failed one."""

    def test_a_delivered_round_is_recorded_as_a_shot(self):
        with unittest.mock.patch.object(deliver, "deliver", return_value=PAYLOAD), \
             unittest.mock.patch.object(deliver, "record_shot") as recorded, \
             contextlib.redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(deliver.main(ARGV), 0)
        recorded.assert_called_once()
        self.assertIn("key=abc123", printed.getvalue())

    def test_a_failed_recording_does_not_fail_the_delivery(self):
        with unittest.mock.patch.object(deliver, "deliver", return_value=PAYLOAD), \
             unittest.mock.patch.object(deliver, "record_shot",
                                        side_effect=OSError("no such tool")), \
             contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(deliver.main(ARGV), 0)


if __name__ == "__main__":
    unittest.main()
