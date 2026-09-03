#!/usr/bin/env python3
"""The order is the product. These assert it, and assert the refusals.

`deliver` exists because two of its four steps used to get dropped. A test that
only checked the happy path would not notice them being dropped again.
"""
import contextlib
import io
import json
import sys
import tempfile
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
                Path("/tmp/p"), "out.html", "a,b,c", "hero", "How strong?",
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
                deliver.deliver(Path("/tmp/p"), "out.html", "a,b,c", "hero",
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
ARGV = ["--project-root", "/tmp/p", "--out", "out.html", "--cohort", "a,b,c",
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

    def test_the_live_state_invocation_joins_the_recorded_shot(self):
        run_id = "aesthetic@2026-09-03T10:00:00Z"
        with unittest.mock.patch.object(deliver, "deliver", return_value=PAYLOAD), \
             unittest.mock.patch.object(deliver, "record_shot") as recorded, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(deliver.main(ARGV + ["--invocation", run_id]), 0)
        recorded.assert_called_once_with(PAYLOAD, "hero", "How strong?", run_id)


class HandAuthoredSvgIsRefused(unittest.TestCase):
    """`shoot` refuses a comp that draws its own <svg>, but delivery never
    routes through `shoot`, so a cohort of invented paths shipped to a user
    with the rule intact and unenforced. An element the user already reacted
    to is settled and stays deliverable."""

    COHORT = "hero.a,hero.b,hero.c"   # a legal round, so only the SVG rule is under test

    def _project(self, tmp, sentiment):
        root = Path(tmp)
        store = root / "spec" / "design-harness"
        store.mkdir(parents=True)
        (root / "comp.html").write_text(
            "<html><svg><path d='M0 0'/></svg></html>", encoding="utf-8")
        (root / "clean.html").write_text(
            "<html><div class='shape'></div></html>", encoding="utf-8")
        entry = lambda name, preview: {
            "element": name, "sentiment": sentiment if name == "hero.a" else None,
            "scored": False, "preview": {"path": preview, "sha256": ""}}
        (store / "decisions.json").write_text(json.dumps({"version": 1, "elements": [
            entry("hero.a", "comp.html"),
            entry("hero.b", "clean.html"),
            entry("hero.c", "clean.html")]}), encoding="utf-8")
        return root

    def test_a_fresh_proposal_that_hand_authors_svg_never_reaches_the_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, None)
            with unittest.mock.patch.object(deliver, "step") as ran:
                with self.assertRaises(deliver.DeliveryError) as refused:
                    deliver.deliver(root, "out.html", self.COHORT, "r", "a?",
                                    "assessments.json", "idle")
            self.assertIn("hand-author", str(refused.exception))
            self.assertIn("hero.a", str(refused.exception))
            ran.assert_not_called()  # refused before the live screen is touched

    def test_an_element_the_user_already_thumbed_stays_deliverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, "like")

            def fake(argv, project_root):
                return ("http://x/?key=a" if argv[1:2] == ["open"] else "[]")

            with unittest.mock.patch.object(deliver, "step", side_effect=fake):
                payload = deliver.deliver(root, "out.html", self.COHORT, "r", "a?",
                                          "assessments.json", "idle")
            self.assertEqual(payload["key"], "a")


class ACohortOfOneIsNotARound(unittest.TestCase):
    """SKILL.md has always said "a 3-6 element cohort". Nothing enforced it.

    Three rounds shipped a single unscored proposal and all three were rejected
    on sight: a lone proposal asks "do you like this?", which is not a design
    question a user can answer with a rank. The rule existed; the guard did not.
    """

    def _ledger(self, tmp, elements):
        root = Path(tmp)
        store = root / "spec" / "design-harness"
        store.mkdir(parents=True)
        (store / "decisions.json").write_text(json.dumps(
            {"version": 1, "elements": elements}), encoding="utf-8")
        return root

    def _entry(self, name, scored):
        return {"element": name, "scored": scored, "sentiment": None,
                "preview": {"path": "c.html", "sha256": ""}}

    def test_two_fresh_proposals_are_refused_as_a_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._ledger(tmp, [self._entry("hero.a", False),
                                      self._entry("hero.b", False)])
            with unittest.mock.patch.object(deliver, "step") as ran:
                with self.assertRaises(deliver.DeliveryError) as refused:
                    deliver.deliver(root, "out.html", "hero.a,hero.b", "r", "a?",
                                    "assessments.json", "idle")
            self.assertIn("3", str(refused.exception))
            ran.assert_not_called()

    def test_three_fresh_proposals_are_a_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._ledger(tmp, [self._entry("hero.a", False),
                                      self._entry("hero.b", False),
                                      self._entry("hero.c", False)])

            def fake(argv, project_root):
                return ("http://x/?key=a" if argv[1:2] == ["open"] else "[]")

            with unittest.mock.patch.object(deliver, "step", side_effect=fake):
                deliver.deliver(root, "out.html", "hero.a,hero.b,hero.c", "r", "a?",
                                "assessments.json", "idle")

    def test_re_asking_about_something_already_ranked_is_not_a_fresh_round(self):
        """A continuation carries a scored element, and re-asking about one
        settled thing is a legitimate round of one."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._ledger(tmp, [self._entry("hero.a", True)])

            def fake(argv, project_root):
                return ("http://x/?key=a" if argv[1:2] == ["open"] else "[]")

            with unittest.mock.patch.object(deliver, "step", side_effect=fake):
                deliver.deliver(root, "out.html", "hero.a", "r", "a?",
                                "assessments.json", "idle")


if __name__ == "__main__":
    unittest.main()
