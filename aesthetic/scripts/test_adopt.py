"""Tests for folding a companion ledger into the harness ledger.

This class of bug corrupts a user's design ledger without raising anything:
`adopt` reports success either way. Expected values come from what the user
clicked, never from replaying what the implementation does.
"""
import json
import re
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


class WithdrawingAThumb(unittest.TestCase):
    """Taking a thumb back is a signal, not the absence of one. The companion
    sends `"sentiment": null` and 18 such events were already sitting in one
    real ledger -- one element un-liked twelve times -- while `stats` still
    counted every withdrawn like. `sentiment=None` meant BOTH "leave it alone"
    and "clear it", so it could only ever mean the first."""

    def liked(self, root: Path) -> Path:
        output = harness(root)
        bh.adopt_companion(root, ledger(root, {
            "type": "sentiment", "element": "palette.role-groups-three",
            "sentiment": "like", "stars": 2, "timestamp": 1000}))
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


class TheArticleIsADesignSystem(unittest.TestCase):
    """A foundation heading with one scoring row under it is a list. The section
    has to show the material -- the palette as colour, the faces as type -- and
    the four zones have to be distinguishable, or the user re-reads decisions
    they already made looking for the three that matter."""

    def system(self, root: Path) -> dict:
        harness(root)
        bh.record_decision(root, "palette.family", "approved", 1, "user picked it", [])
        bh.describe_element(root, "palette.family", None, None, {
            "colors": [{"name": "menta", "value": "#b2ffc2", "role": "grupo"}]})
        bh.record_decision(root, "type.display", "approved", 1, "chosen face", [])
        bh.describe_element(root, "type.display", None, None, {
            "fonts": [{"name": "Matriz 5x7", "stack": "monospace", "use": "display"}]})
        bh.record_decision(root, "cover.weak", "proposed", 1, "backlog item", [])
        # A rank above 1 has to come from a click, so the fixture clicks.
        bh.adopt_companion(root, ledger(root, {
            "element": "cover.strong", "stars": 4, "text": "user liked it", "timestamp": 1}))
        bh.record_decision(root, "cover.bad", "rejected", 1, "user said no", [])
        return bh.load_decisions(root / "spec" / "design-harness")

    def test_the_palette_section_shows_the_actual_colour(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            self.assertIn("#b2ffc2", markup)
            self.assertIn("dh-swatches", markup)

    def test_the_typography_section_names_the_face(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            self.assertIn("Matriz 5x7", markup)
            self.assertIn("dh-faces", markup)

    def test_a_face_itemises_its_variants_and_what_each_is_for(self):
        """A name and one sample line is a caption. It cannot say which weight
        sets a heading and which sets a caption, which is most of what a type
        system actually decides."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            bh.describe_element(root, "type.display", None, None, {"fonts": [{
                "name": "Matriz 5x7", "stack": "ui-monospace", "use": "display",
                "variants": [
                    {"weight": 700, "size": "32px", "use": "titular", "sample": "EN VIVO"},
                    {"weight": 400, "size": "13px", "use": "pie", "sample": "nota al pie"}]}]})
            markup = bh.render_article(root, bh.load_decisions(root / "spec" / "design-harness"))
            self.assertIn("ui-monospace", markup)          # the stack that renders
            for word in ("titular", "pie", "700", "400", "32px", "13px"):
                self.assertIn(word, markup, word)
            self.assertEqual(markup.count('class="dh-variants"'), 1)
            # each variant renders AT its own weight, not merely described
            self.assertIn("font-weight:700", markup)

    def test_a_variant_must_say_what_it_is_for(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            with self.assertRaises(bh.HarnessError):
                bh.describe_element(root, "type.display", None, None, {"fonts": [{
                    "name": "X", "variants": [{"weight": 700}]}]})

    def test_a_face_with_no_variants_still_renders(self):
        """Older ledgers carry {name, stack, use, sample} and must not break."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            self.assertIn('class="dh-variants"', markup)
            self.assertIn("Matriz 5x7", markup)

    def test_the_toc_lists_every_zone_shown_and_marks_one_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"cover.strong"})
            self.assertIn('class="dh-toc"', markup)
            for zone in bh.ZONES:
                self.assertIn(f'href="#dh-zone-{zone}"', markup)
                self.assertIn(f'id="dh-zone-{zone}"', markup)
            self.assertIn("aria-current", markup)

    def test_typography_and_palette_land_in_fundamentals_whatever_their_state(self):
        """A type system is judged as a system. Scattering half of it into a
        backlog because it is still `proposed` makes the pairings unrankable."""
        for state in ("proposed", "approved", "completed"):
            for element_id in ("type.display", "palette.family", "core.thesis"):
                entry = {"element": element_id, "state": state, "stars": 1, "sentiment": None}
                self.assertEqual(bh.zone_of(entry, set()), "fundamentals",
                                 f"{element_id} @ {state}")

    def test_the_round_link_is_the_only_call_to_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"cover.strong"})
            toc = markup.split('class="dh-toc"')[1].split("</nav>")[0]
            self.assertEqual(toc.count("data-cta"), 1)
            cta = toc.split("<li>")[1]
            self.assertIn('href="#dh-zone-round"', cta)

    def test_the_antipattern_link_carries_an_inheriting_icon(self):
        """Emoji ignore `color`, so a bin glyph could never invert with the
        active pill or take the bar's ink."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            toc = markup.split('class="dh-toc"')[1].split("</nav>")[0]
            self.assertIn("<svg", toc)
            self.assertIn("currentColor", toc)

    def test_a_zone_with_enough_groups_gets_a_second_level_of_navigation(self):
        """Three groups is where scrolling past everything to reach one surface
        stops being acceptable -- and it is the length, not the zone's name,
        that decides. The critical components hit five foundations in the real
        project and had no way in at all."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            bh.record_decision(root, "voice.labels", "proposed", 1, "fixture", [])
            bh.record_decision(root, "motion.reveal", "proposed", 1, "fixture", [])
            decisions = bh.load_decisions(root / "spec" / "design-harness")
            markup = bh.render_article(root, decisions)
            backlog = markup.split('id="dh-zone-backlog"')[1].split("</section>")[0]
            self.assertIn('class="dh-subnav"', backlog)
            self.assertIn('href="#dh-backlog-composition"', backlog)
            self.assertIn('id="dh-backlog-composition"', backlog)

    def test_a_short_zone_gets_no_second_level(self):
        """A zone earns a second sticky bar only when it has three or more
        groups to navigate between; two sticky bars over a short list is
        chrome for its own sake."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            block = markup.split('id="dh-zone-fundamentals"')[1].split("</section>")[0]
            self.assertNotIn('class="dh-subnav"', block)

    def test_the_status_strip_is_a_clickable_index_in_the_sticky_bar(self):
        """A chart nobody can act on is decoration. Every bar is the element it
        stands for, and its target has to exist."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"cover.strong"})
            nav = markup.split('class="dh-toc"')[1].split("</nav>")[0]
            self.assertIn("dh-temp-sticky", nav)
            targets = re.findall(r'href="#(dh-el-[^"]+)"', nav)
            self.assertTrue(targets)
            for target in targets:
                self.assertIn(f'id="{target}"', markup)

    def test_only_completed_work_is_solid_green(self):
        """A top score says the drawing is beautiful, not that the question is
        closed. Sharing one green made the handful of finished things
        unfindable."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            bh.adopt_companion(root, ledger(
                root,
                {"element": "cover.strong", "stars": 5, "timestamp": 3},
                {"element": "palette.family", "stars": 5, "verdict": "completed", "timestamp": 4}))
            decisions = bh.load_decisions(root / "spec" / "design-harness")
            markup = bh.render_article(root, decisions)
            done = re.search(r'class="dh-tdone" href="#dh-el-([^"]+)"', markup)
            high = re.search(r'class="dh-thigh" href="#dh-el-([^"]+)"', markup)
            self.assertEqual(done.group(1), "palette.family")
            self.assertEqual(high.group(1), "cover.strong")

    def test_the_rounds_own_bars_are_marked_with_a_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"cover.strong"})
            asked = re.search(r'href="#dh-el-cover\.strong"[^>]*data-asked="1"[^>]*>'
                              r'<span>\?</span>', markup)
            self.assertIsNotNone(asked)
            # One strip, in the sticky bar. Two of them a hundred pixels apart
            # read as a rendering fault, not as emphasis.
            self.assertEqual(markup.count('data-asked="1"'), 1)
            self.assertEqual(markup.count('class="dh-temp dh-temp-sticky"'), 1)

    def test_every_bar_carries_a_tooltip_naming_the_element(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            # A bar identifies its element by id so the chart can build a real
            # preview card from the row's own drawing, and names it in words for
            # assistive tech. It must NOT carry `title`: the browser then draws a
            # second tooltip, in the OS font, on top of the key row.
            self.assertIn('data-el="palette.family', markup)
            self.assertIn("data-name=", markup)
            self.assertNotIn('title="palette.family', markup)

    def test_a_missing_translation_falls_back_instead_of_crashing(self):
        """Falling back only on an unknown LANGUAGE left a gap: forget one
        translation and the user's own language is the one that crashes while
        English renders fine."""
        bh.STRINGS["xx"] = {"zone-round": "Ronda XX"}
        try:
            words = bh.strings_for("xx")
            self.assertEqual(words["zone-round"], "Ronda XX")
            self.assertEqual(words["key-done"], bh.STRINGS["en"]["key-done"])
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                markup = bh.render_article(root, self.system(root), language="xx")
                self.assertIn("Ronda XX", markup)
        finally:
            del bh.STRINGS["xx"]

    def test_every_language_defines_every_key_the_article_uses(self):
        missing = {lang: sorted(set(bh.STRINGS["en"]) - set(words))
                   for lang, words in bh.STRINGS.items() if lang != "en"}
        self.assertEqual({k: v for k, v in missing.items() if v}, {})

    def test_the_hero_says_who_is_asking_what_page_and_which_project(self):
        """A designer opening this page needs, in order: who is asking, what
        this page is, which project, and what is on the table right now.

        A kebab-case cohort id set at 68px is a machine label wearing a
        headline's clothes -- it belongs on the `Designing` line, never as h1.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"cover.strong"},
                                       cohort_name="cover-furniture-redraw",
                                       title="Fichas de performance")
            eyebrow = markup.split('class="dh-eyebrow">')[1].split("</p>")[0]
            h1 = markup.split("<h1>")[1].split("</h1>")[0]
            meta = markup.split('class="dh-hero-meta">')[1].split("</div>")[0]
            self.assertEqual(eyebrow, "Design Agent")
            self.assertEqual(h1, "Aesthetic ranking")
            self.assertIn("Fichas de performance", meta)
            self.assertNotIn("cover-furniture-redraw", h1)
            self.assertIn("cover-furniture-redraw", meta)

    def test_a_proposal_is_shown_beside_what_it_replaces(self):
        """"Is this good?" has no answer. "Is this better than what stands?"
        does -- and without the pair the user cannot score the round at all."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            bh.record_decision(root, "cover.strong.redraw", "proposed", 1, "new pass", [])
            decisions = bh.load_decisions(root / "spec" / "design-harness")
            markup = bh.render_article(root, decisions, {"cover.strong.redraw"})
            block = markup.split('class="dh-versus"')[1].split("</div></div>")[0]
            self.assertLess(block.index('data-element="cover.strong"'),
                            block.index('data-element="cover.strong.redraw"'))
            self.assertIn("dh-fb-before", block)

    def test_the_incumbent_is_the_longest_matching_prefix(self):
        known = {"cover.ring", "cover.ring.kicker", "unrelated"}
        self.assertEqual(bh.incumbent_of("cover.ring.kicker.arco", known), "cover.ring.kicker")
        self.assertEqual(bh.incumbent_of("cover.ring.other", known), "cover.ring")
        self.assertEqual(bh.incumbent_of("brand.new.thing", known), "")

    def test_a_proposal_with_no_incumbent_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"cover.strong"})
            self.assertIn(bh.STRINGS["en"]["brand-new"], markup)

    def test_the_strip_keeps_score_order_and_sinks_antipatterns(self):
        """A bar's POSITION says how that work compares, so the round's bars
        stay where their score puts them -- the ? and the outline make them
        findable in place."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"cover.weak"})
            nav = markup.split('class="dh-temp dh-temp-sticky"')[1].split("</div>")[0]
            classes = re.findall(r'<a class="([^"]+)"', nav)
            self.assertEqual(classes[-1], "dh-tanti")
            # cover.weak is in the round at 1 star; cover.strong outranks it and
            # must still come first.
            order = re.findall(r'href="#dh-el-([^"]+)"', nav)
            self.assertLess(order.index("cover.strong"), order.index("cover.weak"))

    def test_the_key_reads_from_this_round_to_set_aside(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            key = markup.split('class="dh-key"')[1].split("</p>")[0]
            labels = re.findall(r'</[ib]>([^<]+)</span>', key)
            words = bh.STRINGS["en"]
            self.assertEqual(labels, [words["key-asked"], words["key-done"], words["key-open"],
                                      words["key-weak"], words["key-unscored"], words["key-anti"]])

    def test_the_chart_shows_the_drawing_not_a_dotted_id(self):
        """`family.tab.spine-step.grupo-color -- 1/5 -- proposed` is a namespace,
        a fraction and a lifecycle word. A designer needs the DRAWING and its
        name, which a CSS `content:` tooltip cannot hold -- so the chart builds
        a real card, and a click opens the same slideshow a thumbnail does."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            self.assertIn("dh-chartcard", markup)
            self.assertNotIn("content:attr(data-tip)", markup)
            script = re.search(r"<script>/\* dh-lightbox \*/(.*?)</script>",
                               markup, re.S).group(1)
            self.assertIn(".dh-temp a[data-el]", script,
                          "a bar must open the slideshow, not scroll to a row")
            self.assertIn("__dhOpenSlide", script,
                          "the chart and the thumbnails must share one opener")

    def test_a_cohort_spanning_many_foundations_is_refused(self):
        """Three elements from three foundations under a name claiming a shared
        surface is a batch of errands. The page cannot say what it asks, so the
        agent ends up explaining the round in prose instead."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            bh.record_decision(root, "voice.labels", "proposed", 1, "fixture", [])
            decisions = bh.load_decisions(root / "spec" / "design-harness")
            scattered = {"type.display", "cover.weak", "voice.labels"}
            with self.assertRaises(bh.HarnessError) as caught:
                bh.render_article(root, decisions, scattered)
            self.assertIn("one surface or one problem", str(caught.exception))

    def test_stating_what_they_share_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            bh.record_decision(root, "voice.labels", "proposed", 1, "fixture", [])
            decisions = bh.load_decisions(root / "spec" / "design-harness")
            markup = bh.render_article(root, decisions,
                                       {"type.display", "cover.weak", "voice.labels"},
                                       asks="Everything the cover says out loud.")
            self.assertIn("Everything the cover says out loud.", markup)

    def test_a_single_domain_cohort_needs_no_sentence_and_names_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"type.display"})
            block = markup.split('id="dh-zone-round"')[1].split("</header>")[0]
            self.assertIn(bh.STRINGS["en"]["typography"], block)

    def test_a_specimen_follows_its_element_into_the_round(self):
        """The specimen IS the thing being judged. Keeping specimens out of the
        round to dodge a styling bug lost the picture for exactly the element
        being asked about."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"type.display"})
            block = markup.split('id="dh-zone-round"')[1].split("</section>")[0]
            self.assertIn("dh-faces", block)
            self.assertIn("Matriz 5x7", block)

    def test_specimen_surfaces_do_not_assume_a_light_ground(self):
        """On the round's inverted ground a transparent card with an
        ink-derived border had no back and no edge: the sample floated on black
        with its controls adrift."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            style = markup.split("<style>/* dh-article */")[1].split("</style>")[0]
            for selector in (".dh-faces .dh-face{", ".dh-swatches li{"):
                block = style.split(selector)[1].split("}")[0]
                self.assertIn("currentColor", block, selector)
            # Nothing inside a specimen may derive its colour from the page
            # ink: a specimen can appear in the inverted round, where ink-on-ink
            # is invisible. The article ROOT setting the ground is correct.
            for rule in (".dh-swatches .dh-vals{", ".dh-swatches .dh-vals code{",
                         ".dh-swatches .dh-vals > span{",
                         ".dh-face-head code{", ".dh-variants code{"):
                block = style.split(rule)[1].split("}")[0]
                self.assertNotIn("--dh-ink", block, rule)

    def test_the_inverted_round_re_derives_the_rule_token(self):
        """Anything rendered there borrows --dh-rule; ink-derived it is
        invisible on ink."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"cover.strong"})
            style = markup.split("<style>/* dh-article */")[1].split("</style>")[0]
            block = style.split('.dh-zone[data-zone="round"]{')[1].split("}")[0]
            self.assertIn("--dh-rule:", block)
            self.assertIn("var(--dh-bg", block.split("--dh-rule:")[1])

    def test_nothing_bleeds_outside_the_article(self):
        """The article does not own the viewport: the companion nests it in a
        padded wrapper inside an overflow-x:auto pane. A negative margin made
        that pane scrollable, and it sat scrolled -- clipping the headline and
        the left edge of every card."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), {"cover.strong"})
            style = markup.split("<style>/* dh-article */")[1].split("</style>")[0]
            offenders = [line.strip() for line in style.splitlines()
                         if re.search(r"margin[^:]*:[^;}]*(-\d|calc\(-)", line)
                         or "margin-inline:-" in line]
            self.assertEqual(offenders, [])

    def test_specimen_controls_take_the_zone_foreground(self):
        """A row paints its own light ground and sets ink to match. Stripped of
        that ground, its controls must inherit -- otherwise currentColor is
        still ink and the strip is ink on ink in the inverted round."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            style = markup.split("<style>/* dh-article */")[1].split("</style>")[0]
            block = style.split(".dh-spec-score .dh-fb.dh-fb{")[1].split("}")[0]
            self.assertIn("color:inherit", block)
            # and the overrides must outrank the controls sheet that follows
            for rule in (".dh-spec-score .dh-fb .dh-stars > *{",
                         ".dh-spec-score .dh-fb [data-sentiment]"):
                self.assertIn(rule, style)

    def test_swatch_captions_do_not_dim_the_controls_below_them(self):
        """`.dh-swatches span` also matched every span in the nested scoring
        strip, dimming currentColor again at each level until a star was ink at
        ten percent."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            style = markup.split("<style>/* dh-article */")[1].split("</style>")[0]
            self.assertNotIn(".dh-swatches span{", style)
            self.assertIn(".dh-swatches .dh-vals > span{", style)

    def test_the_long_zone_folds_and_shows_its_work_while_folded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            bh.record_decision(root, "voice.labels", "proposed", 1, "fixture", [])
            decisions = bh.load_decisions(root / "spec" / "design-harness")
            markup = bh.render_article(root, decisions)
            backlog = markup.split('id="dh-zone-backlog"')[1].split("</section>")[0]
            self.assertIn('<details class="dh-acc"', backlog)
            self.assertIn("dh-acc-thumbs", backlog)
            self.assertEqual(backlog.count("<details"), backlog.count("</details>"))
            # the round must never fold: it is the ask
            self.assertNotIn("dh-acc", markup.split('id="dh-zone-round"')[1]
                             .split("</section>")[0])

    def test_the_second_bar_sticks_below_the_measured_first(self):
        """47px was typed when the bar was one row tall. It grew a strip and a
        key, and the sub-nav went on sticking underneath it."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            style = markup.split("<style>/* dh-article */")[1].split("</style>")[0]
            block = style.split(".dh-subnav{")[1].split("}")[0]
            self.assertIn("var(--dh-toc-h", block)
            self.assertIn("--dh-toc-h", markup)  # the script that measures it

    def test_the_fold_marker_is_a_glyph_not_an_escape(self):
        """The hex escape came back out of the browser as U+0015 and drew the
        literal text "B8" beside every group."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            self.assertIn('content:"▸"', markup)
            self.assertNotIn("25B8", markup)

    def test_antipatterns_sit_last_and_muted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            sections = re.findall(r'<section class="dh-zone" id="dh-zone-(\w+)"', markup)
            self.assertEqual(sections[-1], "antipattern")
            style = markup.split("<style>/* dh-article */")[1].split("</style>")[0]
            muted = style.split('.dh-zone[data-zone="antipattern"]{')[1].split("}")[0]
            # The GROUND goes quiet, not the contents: dimming the rows made the
            # stars and thumbs unreadable, and those are the only way a
            # rejection gets undone.
            self.assertIn("background:", muted)
            self.assertNotIn("opacity:", muted)
            self.assertNotIn("filter:", muted)

    def test_each_element_lands_in_exactly_one_zone(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions = self.system(root)
            cohort = {"cover.strong"}
            seen = {}
            for entry in decisions["elements"]:
                if entry["state"] in bh.GROUP_OF:
                    seen[entry["element"]] = bh.zone_of(entry, cohort)
            self.assertEqual(seen["cover.strong"], "round")
            self.assertEqual(seen["palette.family"], "fundamentals")
            self.assertEqual(seen["cover.weak"], "backlog")
            self.assertEqual(seen["cover.bad"], "antipattern")

    def test_a_disliked_element_is_an_antipattern_whatever_its_state(self):
        entry = {"element": "x.y", "state": "proposed", "stars": 3, "sentiment": "dislike"}
        self.assertEqual(bh.zone_of(entry, set()), "antipattern")

    def test_a_thumbed_up_element_is_never_an_antipattern(self):
        """A thumb up says the direction is right. Filing it under antipatterns
        told the next agent to stop pursuing an idea the user endorsed."""
        for state in ("rejected", "superseded", "proposed", "approved"):
            entry = {"element": "x.y", "state": state, "stars": 2, "sentiment": "like"}
            self.assertNotEqual(bh.zone_of(entry, set()), "antipattern", state)

    def test_superseded_work_the_user_liked_is_held_not_condemned(self):
        entry = {"element": "x.y", "state": "superseded", "stars": 4, "sentiment": "like"}
        self.assertEqual(bh.zone_of(entry, set()), "backlog")

    def test_no_thumbed_up_element_reaches_the_antipattern_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            bh.adopt_companion(root, ledger(root, {
                "element": "cover.bad", "sentiment": "like", "timestamp": 9}))
            decisions = bh.load_decisions(root / "spec" / "design-harness")
            markup = bh.render_article(root, decisions)
            anti = markup.split('id="dh-zone-antipattern"')
            if len(anti) > 1:
                self.assertNotIn('data-element="cover.bad"', anti[1])
            liked = {e["element"] for e in decisions["elements"]
                     if e.get("sentiment") == "like" and e["state"] in bh.GROUP_OF}
            for name in liked:
                self.assertNotEqual(bh.zone_of(
                    next(e for e in decisions["elements"] if e["element"] == name), set()),
                    "antipattern", name)

    def test_rows_run_best_score_first_inside_a_foundation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            backlog = markup.split('id="dh-zone-backlog"')[1]
            self.assertLess(backlog.index('data-element="cover.strong"'),
                            backlog.index('data-element="cover.weak"'))

    def test_the_round_zone_renders_even_when_the_cohort_is_empty(self):
        """An empty round is a fact worth stating: it means nothing is being
        asked, which is exactly the failure doctor now catches."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root))
            self.assertIn('data-zone="round"', markup)
            self.assertIn("dh-empty", markup)

    def test_the_article_imposes_no_palette_of_its_own(self):
        """Chrome in a competing palette corrupts the judgement it collects."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = bh.render_article(root, self.system(root), theme={"bg": "#FDF6E3"})
            style = markup.split("<style>/* dh-article */")[1].split("</style>")[0]
            self.assertNotIn("#fff5", style)
            self.assertIn("var(--dh-bg", style)
            self.assertIn("--dh-bg: #FDF6E3", markup)

    def test_every_element_stays_scoreable_in_the_article(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions = self.system(root)
            markup = bh.render_article(root, decisions)
            for entry in decisions["elements"]:
                if entry["state"] in bh.GROUP_OF:
                    self.assertIn(f'data-element="{entry["element"]}"', markup)


if __name__ == "__main__":
    unittest.main()
