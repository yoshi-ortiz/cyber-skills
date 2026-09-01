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
from adopt_fixtures import element, harness, ledger


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


class SentimentDoesNotCreateARank(unittest.TestCase):
    def test_thumb_only_feedback_keeps_an_agent_proposal_unscored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.record_decision(root, "core.idea", "proposed", 0,
                               "agent proposal", [], source="agent", sentiment=None)
            bh.adopt_companion(root, ledger(root, {
                "type": "sentiment", "element": "core.idea", "sentiment": "like",
                "timestamp": 1000,
            }))
            entry = element(output, "core.idea")
            self.assertEqual(entry["sentiment"], "like")
            self.assertFalse(entry["scored"])
            self.assertEqual(entry["source"], "user")

    def test_legacy_thumb_event_carrying_zero_still_does_not_create_a_rank(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.record_decision(root, "core.idea", "proposed", 0,
                               "agent proposal", [], source="agent", sentiment=None)
            bh.adopt_companion(root, ledger(root, {
                "type": "sentiment", "element": "core.idea", "sentiment": "like",
                "stars": 0, "timestamp": 1000,
            }))
            entry = element(output, "core.idea")
            self.assertFalse(entry["scored"])
            self.assertEqual(bh.ledger_stats(bh.load_decisions(output))["userSet"], 0)

    def test_sentiment_does_not_resurrect_a_rejected_element(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.record_decision(root, "voice.celebratory", "rejected", 0,
                               "agent proposal", [], source="agent", sentiment=None)
            bh.adopt_companion(root, ledger(root, {
                "type": "sentiment", "element": "voice.celebratory",
                "sentiment": "dislike", "timestamp": 1000,
            }))
            entry = element(output, "voice.celebratory")
            self.assertEqual(entry["state"], "rejected")
            self.assertEqual(entry["sentiment"], "dislike")


class BookmarkOnlyEventsAdopt(unittest.TestCase):
    """A bookmark-only companion event carries no stars, sentiment, or
    verdict -- before this feature it would have been silently dropped by
    the same skip rule that used to swallow bare sentiment withdrawals."""

    def test_a_bookmark_only_event_is_not_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.record_decision(root, "core.idea", "proposed", 0,
                               "agent proposal", [], source="agent", sentiment=None)
            adopted, skipped = bh.adopt_companion(root, ledger(root, {
                "type": "bookmark", "element": "core.idea", "bookmark": True,
                "timestamp": 1000,
            }))
            self.assertEqual((adopted, skipped), (1, 0))
            entry = element(output, "core.idea")
            self.assertTrue(entry["bookmarked"])
            self.assertFalse(entry["scored"], "a bookmark click is not a rank")

    def test_a_bookmark_event_does_not_disturb_a_standing_rank(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = harness(root)
            bh.record_decision(root, "core.idea", "proposed", 4,
                               "user liked it", [], source="user", sentiment="like")
            bh.adopt_companion(root, ledger(root, {
                "type": "bookmark", "element": "core.idea", "bookmark": True,
                "timestamp": 2000,
            }))
            entry = element(output, "core.idea")
            self.assertTrue(entry["bookmarked"])
            self.assertEqual(entry["stars"], 4)
            self.assertEqual(entry["sentiment"], "like")


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


class WithdrawingAThumb(unittest.TestCase):
    """Taking a thumb back is a signal, not the absence of one. The companion
    sends `"sentiment": null` and 18 such events were already sitting in one
    real ledger -- one element un-liked twelve times -- while `stats` still
    counted every withdrawn like. `sentiment=None` meant BOTH "leave it alone"
    and "clear it", so it could only ever mean the first."""

    def liked(self, root: Path) -> Path:
        output = harness(root)
        bh.adopt_companion(root, ledger(root,
            {"type": "rank", "element": "palette.role-groups-three",
             "stars": 2, "timestamp": 900},
            {"type": "sentiment", "element": "palette.role-groups-three",
             "sentiment": "like", "timestamp": 1000}))
        return output

    def test_a_withdrawal_clears_the_stored_sentiment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.liked(root)
            bh.adopt_companion(root, ledger(root, {
                "type": "sentiment", "element": "palette.role-groups-three",
                "choice": "palette.role-groups-three", "sentiment": None,
                "stars": 2, "text": "palette.role-groups-three", "timestamp": 2000}))
            self.assertIsNone(element(output, "palette.role-groups-three")["sentiment"])

    def test_a_withdrawal_leaves_the_star_rank_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.liked(root)
            bh.adopt_companion(root, ledger(root, {
                "type": "sentiment", "element": "palette.role-groups-three",
                "sentiment": None, "stars": 2, "timestamp": 2000}))
            self.assertEqual(element(output, "palette.role-groups-three")["stars"], 2)

    def test_an_event_with_no_sentiment_key_does_not_clear_it(self):
        """The correction must not overshoot: a plain star click carries no
        sentiment key at all and has never meant 'take the thumb back'."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.liked(root)
            bh.adopt_companion(root, ledger(root, {
                "element": "palette.role-groups-three", "stars": 5, "timestamp": 2000}))
            entry = element(output, "palette.role-groups-three")
            self.assertEqual(entry["sentiment"], "like")
            self.assertEqual(entry["stars"], 5)

    def test_a_bare_withdrawal_carrying_no_stars_is_still_adopted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.liked(root)
            adopted, skipped = bh.adopt_companion(root, ledger(root, {
                "type": "sentiment", "element": "palette.role-groups-three",
                "sentiment": None, "timestamp": 2000}))
            self.assertEqual((adopted, skipped), (1, 0))
            self.assertIsNone(element(output, "palette.role-groups-three")["sentiment"])

    def test_stats_stops_counting_a_withdrawn_like(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.liked(root)
            self.assertEqual(bh.ledger_stats(bh.load_decisions(output))["likes"], 1)
            bh.adopt_companion(root, ledger(root, {
                "type": "sentiment", "element": "palette.role-groups-three",
                "sentiment": None, "stars": 2, "timestamp": 2000}))
            self.assertEqual(bh.ledger_stats(bh.load_decisions(output))["likes"], 0)

    def test_decide_without_a_sentiment_argument_keeps_the_existing_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.liked(root)
            bh.record_decision(root, "palette.role-groups-three", "proposed", 1,
                               "agent re-records", [])
            self.assertEqual(element(output, "palette.role-groups-three")["sentiment"], "like")


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


class RecordingAWinKeepsTheRank(unittest.TestCase):
    """`decide --supersedes` records the supersede on the WINNER, and the winner
    is always the element the user just ranked -- so writing it ran the agent
    path, capped at 1 star with source=agent, and destroyed the click that
    decided the contest. A real 3-star user rank came back as agent 1-star, and
    adopt would not restore it: it had already consumed that click."""

    def contest(self, root: Path) -> Path:
        output = harness(root)
        bh.record_decision(root, "cover.ring.kicker", "proposed", 1, "flat label", [])
        bh.adopt_companion(root, ledger(root, {
            "element": "cover.ring.kicker.antetitulo-arco", "stars": 3,
            "text": "user: 'el antetitulo sobre el arco'", "timestamp": 1000}))
        return output

    def test_retiring_the_loser_leaves_the_winner_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.contest(root)
            before = element(output, "cover.ring.kicker.antetitulo-arco")
            bh.retire_element(root, "cover.ring.kicker",
                              "cover.ring.kicker.antetitulo-arco",
                              "user: 3 estrellas contra 1")
            self.assertEqual(element(output, "cover.ring.kicker.antetitulo-arco"), before)

    def test_the_loser_is_marked_superseded_by_the_winner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.contest(root)
            bh.retire_element(root, "cover.ring.kicker",
                              "cover.ring.kicker.antetitulo-arco", "user: gana el arco")
            loser = element(output, "cover.ring.kicker")
            self.assertEqual(loser["state"], "superseded")
            self.assertEqual(loser["supersededBy"], "cover.ring.kicker.antetitulo-arco")

    def test_the_winners_user_stars_and_source_survive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.contest(root)
            bh.retire_element(root, "cover.ring.kicker",
                              "cover.ring.kicker.antetitulo-arco", "user: gana el arco")
            winner = element(output, "cover.ring.kicker.antetitulo-arco")
            self.assertEqual(winner["stars"], 3)
            self.assertEqual(winner["source"], "user")

    def test_re_retiring_the_same_pair_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.contest(root)
            args = ("cover.ring.kicker", "cover.ring.kicker.antetitulo-arco", "user: gana")
            bh.retire_element(root, *args)
            once = bh.load_decisions(output)
            bh.retire_element(root, *args)
            self.assertEqual(once, bh.load_decisions(output))

    def test_an_element_cannot_supersede_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.contest(root)
            with self.assertRaises(bh.HarnessError):
                bh.retire_element(root, "cover.ring.kicker", "cover.ring.kicker", "x")


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

    def test_an_embedded_screen_carries_the_foundation_headings(self):
        """embed lifts bare rows out of the generated wrapper, so headings
        rendered there never reached the page the user actually scores."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness(root)
            path = self.screen(root, 'data-dh-controls="cover.ring.kicker,cover.spine.right"')
            bh.record_decision(root, "palette.family-from-cards", "proposed", 1, "fixture", [])
            path.write_text('<html><body><div data-dh-controls="cover.ring.kicker,'
                            'palette.family-from-cards"></div></body></html>', encoding="utf-8")
            bh.embed_controls(root, path)
            markup = path.read_text(encoding="utf-8")
            self.assertIn('data-group="palette"', markup)
            self.assertIn('data-group="composition"', markup)
            # Foundations render in reading order, not in the order typed.
            self.assertLess(markup.index('data-group="palette"'),
                            markup.index('data-group="composition"'))

    def test_a_foundation_heads_its_section_once_per_screen(self):
        """Sixteen placeholders on one screen printed "Composition & layout"
        four times, which reads as noise rather than as a design system."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness(root)
            path = self.screen(root, 'data-dh-controls="cover.ring.kicker"')
            path.write_text('<html><body>'
                            '<div data-dh-controls="cover.ring.kicker"></div>'
                            '<div data-dh-controls="cover.spine.right"></div>'
                            '</body></html>', encoding="utf-8")
            bh.embed_controls(root, path)
            markup = path.read_text(encoding="utf-8")
            self.assertEqual(markup.count('data-group="composition"'), 1)
            # Both rows still render -- only the repeated heading is dropped.
            self.assertIn('data-element="cover.ring.kicker"', markup)
            self.assertIn('data-element="cover.spine.right"', markup)

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
