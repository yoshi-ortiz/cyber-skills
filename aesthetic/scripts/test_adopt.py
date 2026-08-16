"""Tests for folding a companion ledger into the harness ledger.

This class of bug corrupts a user's design ledger without raising anything:
`adopt` reports success either way. Expected values come from what the user
clicked, never from replaying what the implementation does.
"""
import json
import tempfile
import unittest
from pathlib import Path

import bootstrap_harness as bh


def harness(root: Path) -> Path:
    """A minimal ledger on disk -- `adopt` only needs decisions.json + project.json."""
    output = root / "spec" / "design-harness"
    output.mkdir(parents=True)
    decisions = bh.empty_decisions()
    bh.write_json(output / "decisions.json", decisions)
    (output / "DECISIONS.md").write_text(bh.render_decisions_md(decisions), encoding="utf-8")
    bh.write_json(output / "project.json", {"version": bh.VERSION, "state": "draft"})
    return output


def ledger(root: Path, *events: dict) -> Path:
    path = root / "companion-ledger.jsonl"
    path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return path


def element(output: Path, name: str) -> dict:
    for entry in bh.load_decisions(output)["elements"]:
        if entry["element"] == name:
            return entry
    raise AssertionError(f"{name} is not in the ledger")


class SameTimestampPairs(unittest.TestCase):
    """Reaching max stars auto-fires a completed toggle, so real companion UI
    emits rank+verdict at the identical millisecond. The verdict event carries no
    stars of its own and must inherit the rank set moments earlier in the batch,
    not the rank from before the batch."""

    def test_a_rank_then_verdict_pair_keeps_the_new_star_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            path = ledger(
                root,
                {"element": "cover.ring", "stars": 4, "timestamp": 1000},
                {"element": "cover.ring", "verdict": "completed", "timestamp": 1000},
            )
            bh.adopt_companion(root, path)
            entry = element(output, "cover.ring")
            self.assertEqual(entry["stars"], 4)
            self.assertEqual(entry["state"], "completed")

    def test_the_pair_does_not_revert_a_star_recorded_by_an_earlier_adopt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.adopt_companion(root, ledger(
                root, {"element": "cover.ring", "stars": 1, "timestamp": 1}))
            bh.adopt_companion(root, ledger(
                root,
                {"element": "cover.ring", "stars": 5, "timestamp": 1000},
                {"element": "cover.ring", "verdict": "completed", "timestamp": 1000},
            ))
            self.assertEqual(element(output, "cover.ring")["stars"], 5)

    def test_splitting_the_pair_across_two_adopts_gives_the_same_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.adopt_companion(root, ledger(
                root, {"element": "cover.ring", "stars": 4, "timestamp": 1000}))
            bh.adopt_companion(root, ledger(
                root, {"element": "cover.ring", "verdict": "completed", "timestamp": 1000}))
            split = element(output, "cover.ring")

            root2 = Path(tmp) / "other"
            root2.mkdir()
            output2 = harness(root2)
            bh.adopt_companion(root2, ledger(
                root2,
                {"element": "cover.ring", "stars": 4, "timestamp": 1000},
                {"element": "cover.ring", "verdict": "completed", "timestamp": 1000},
            ))
            batched = element(output2, "cover.ring")
            self.assertEqual((split["stars"], split["state"]),
                             (batched["stars"], batched["state"]))

    def test_a_verdict_with_no_prior_star_stays_at_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.adopt_companion(root, ledger(
                root, {"element": "cover.ring", "verdict": "completed", "timestamp": 1000}))
            self.assertEqual(element(output, "cover.ring")["stars"], 0)

    def test_a_later_star_still_wins_over_an_earlier_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.adopt_companion(root, ledger(
                root,
                {"element": "cover.ring", "stars": 5, "timestamp": 1000},
                {"element": "cover.ring", "stars": 2, "timestamp": 2000},
            ))
            self.assertEqual(element(output, "cover.ring")["stars"], 2)

    def test_a_thumbs_event_inherits_the_star_set_in_the_same_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.adopt_companion(root, ledger(
                root,
                {"element": "cover.ring", "stars": 3, "timestamp": 1000},
                {"element": "cover.ring", "sentiment": "like", "timestamp": 1000},
            ))
            entry = element(output, "cover.ring")
            self.assertEqual(entry["stars"], 3)
            self.assertEqual(entry["sentiment"], "like")

    def test_adopting_the_same_ledger_twice_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            events = [
                {"element": "cover.ring", "stars": 4, "timestamp": 1000},
                {"element": "cover.ring", "verdict": "completed", "timestamp": 1000},
            ]
            bh.adopt_companion(root, ledger(root, *events))
            once = bh.load_decisions(output)
            bh.adopt_companion(root, ledger(root, *events))
            self.assertEqual(once, bh.load_decisions(output))


class AlreadyAdoptedHistory(unittest.TestCase):
    """`decide --source user` writes straight to decisions.json and never reaches
    the companion ledger, so it has no position in the chronological replay. If
    adopt replays the whole file every run, an old `proposed` click lands back on
    top of an approval the user gave afterwards -- which downgraded seven
    standing elements in one real run."""

    def test_an_approval_survives_a_re_adopt_of_an_older_proposed_click(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            path = ledger(root, {"element": "cover.solapa.right", "verdict": "proposed",
                                 "stars": 3, "timestamp": 1000})
            bh.adopt_companion(root, path)
            bh.record_decision(root, "cover.solapa.right", "approved", 5,
                               "user: 'la solapa a la derecha'", [], source="user")
            bh.adopt_companion(root, path)
            entry = element(output, "cover.solapa.right")
            self.assertEqual(entry["state"], "approved")
            self.assertEqual(entry["stars"], 5)

    def test_lines_appended_after_the_last_adopt_are_still_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            path = ledger(root, {"element": "cover.solapa.right", "stars": 2, "timestamp": 1000})
            bh.adopt_companion(root, path)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"element": "cover.solapa.right", "stars": 4,
                                         "timestamp": 2000}) + "\n")
                handle.write(json.dumps({"element": "cover.ring", "verdict": "completed",
                                         "timestamp": 3000}) + "\n")
            adopted, _ = bh.adopt_companion(root, path)
            self.assertEqual(adopted, 2)
            self.assertEqual(element(output, "cover.solapa.right")["stars"], 4)
            self.assertEqual(element(output, "cover.ring")["state"], "completed")

    def test_a_second_adopt_of_an_unchanged_ledger_replays_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = ledger(root, {"element": "cover.ring", "stars": 4, "timestamp": 1000})
            harness(root)
            bh.adopt_companion(root, path)
            self.assertEqual(bh.adopt_companion(root, path), (0, 0))

    def test_a_replaced_ledger_at_the_same_path_is_replayed_in_full(self):
        """A companion restart writes a fresh ledger where the old one sat.
        Trusting the stale line count there would silently drop real clicks."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.adopt_companion(root, ledger(
                root, {"element": "cover.ring", "stars": 1, "timestamp": 1000}))
            adopted, _ = bh.adopt_companion(root, ledger(
                root, {"element": "cover.spine", "stars": 5, "timestamp": 2000}))
            self.assertEqual(adopted, 1)
            self.assertEqual(element(output, "cover.spine")["stars"], 5)


class DoctorProbe(unittest.TestCase):
    """companion_doctor strips its probe rows back out, but an adopt racing that
    cleanup used to fold the probe in as a real element -- and adopt never
    removes, so the ghost was permanent."""

    def test_the_probe_element_is_never_adopted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            adopted, skipped = bh.adopt_companion(root, ledger(
                root,
                {"element": bh.PROBE_ELEMENT, "stars": 3, "timestamp": 1000},
                {"element": "cover.ring", "stars": 2, "timestamp": 2000},
            ))
            names = [e["element"] for e in bh.load_decisions(output)["elements"]]
            self.assertEqual(names, ["cover.ring"])
            self.assertEqual((adopted, skipped), (1, 1))


class CompletedIsRendered(unittest.TestCase):
    """DECISIONS.md is binding for any agent resuming the project. An element it
    omits is an element that agent will happily rebuild."""

    def test_a_completed_element_appears_in_the_rendered_ledger(self):
        decisions = dict(bh.empty_decisions(), elements=[{
            "element": "cover.ring", "state": "completed", "stars": 4,
            "evidence": "user clicked done", "supersededBy": None,
        }])
        text = bh.render_decisions_md(decisions)
        self.assertIn("cover.ring", text)
        self.assertIn("## Completed", text)

    def test_completed_is_not_listed_as_standing(self):
        decisions = dict(bh.empty_decisions(), elements=[{
            "element": "cover.ring", "state": "completed", "stars": 4,
            "evidence": "user clicked done", "supersededBy": None,
        }])
        standing = bh.render_decisions_md(decisions).split("## Completed")[0]
        self.assertNotIn("cover.ring", standing)

    def test_every_decision_state_is_rendered_somewhere(self):
        decisions = dict(bh.empty_decisions(), elements=[
            {"element": f"e.{state}", "state": state, "stars": 1,
             "evidence": "x", "supersededBy": None}
            for state in bh.DECISION_STATES
        ])
        text = bh.render_decisions_md(decisions)
        for state in bh.DECISION_STATES:
            self.assertIn(f"e.{state}", text, state)


class CohortIsVisible(unittest.TestCase):
    """A round opens by naming its cohort. `data-dh-cohort` was an attribute
    only -- doctor read it, the user never saw it -- so the screen never said
    which elements this round is asking about and which are left alone."""

    def screen(self, root: Path, attributes: str) -> Path:
        bh.record_decision(root, "cover.ring.kicker", "proposed", 1, "fixture", [])
        bh.record_decision(root, "cover.spine.right", "proposed", 1, "fixture", [])
        session = root / ".superpowers" / "brainstorm" / "s1" / "content"
        session.mkdir(parents=True)
        path = session / "proto.html"
        path.write_text(f"<html><body><div {attributes}></div></body></html>", encoding="utf-8")
        return path

    def test_the_cohort_name_is_rendered_above_the_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness(root)
            path = self.screen(root, 'data-dh-cohort="cover-furniture" '
                                     'data-dh-controls="cover.ring.kicker,cover.spine.right"')
            bh.embed_controls(root, path)
            markup = path.read_text(encoding="utf-8")
            self.assertIn("cover-furniture", markup.split('class="dh-fb"')[0])
            self.assertIn('class="dh-cohort"', markup)
            self.assertIn("2 element(s) to score", markup)

    def test_a_screen_with_no_cohort_renders_no_banner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness(root)
            path = self.screen(root, 'data-dh-controls="cover.ring.kicker"')
            bh.embed_controls(root, path)
            self.assertNotIn('class="dh-cohort"', path.read_text(encoding="utf-8"))

    def test_the_banner_does_not_duplicate_on_re_embed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness(root)
            path = self.screen(root, 'data-dh-cohort="cover-furniture" '
                                     'data-dh-controls="cover.ring.kicker"')
            bh.embed_controls(root, path)
            once = path.read_text(encoding="utf-8")
            bh.embed_controls(root, path)
            self.assertEqual(once, path.read_text(encoding="utf-8"))
            self.assertEqual(once.count('class="dh-cohort"'), 1)


if __name__ == "__main__":
    unittest.main()
