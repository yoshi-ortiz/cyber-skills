"""Tests for the two things a round has to get right before anyone sees it.

Both of these were rules written in prose that every session drifted past, and
the ledger recorded the cost: eighteen elements the user liked and scored 1-2
sat untouched while eleven fresh siblings were proposed on top of them, and the
mean score FELL to 1.56. A rule the model can read and skip is not a rule, so
each one here is a refusal with a test behind it.

The article's own invariants are checked the same way -- against generated
markup, never against the source string, because two of the worst defects so
far were CSS the browser silently discarded while the source looked correct.
"""
import re
import tempfile
import unittest
from pathlib import Path

import bootstrap_harness as bh


def live(*rows: tuple) -> dict:
    """A ledger from (element, stars, sentiment, state) tuples."""
    return {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
            "elements": [{"element": e, "stars": s, "sentiment": m, "state": st,
                          "scored": True, "source": "user"}
                         for e, s, m, st in rows]}


class RoundsThatDoNotEarnTheirPlace(unittest.TestCase):
    """`article` refuses before it renders, so the screen is never the thing
    that has to explain why a round was pointless."""

    def test_new_ideas_over_unanswered_feedback_are_refused(self):
        decisions = live(("cover.spine", 2, "like", "proposed"),
                         ("type.silkscreen", 0, None, "proposed"))
        with self.assertRaises(bh.HarnessError) as caught:
            bh.check_round_earns_its_place(decisions, {"type.silkscreen"})
        message = str(caught.exception)
        self.assertIn("cover.spine", message,
                      "the refusal has to NAME the work that is waiting, or the "
                      "agent cannot act on it without another round trip")

    def test_redrawing_a_liked_low_element_is_allowed(self):
        # The whole point: `<parent>.<slug>` is how a polish pass is proposed,
        # and it must pass without a flag or the rule teaches the wrong lesson.
        decisions = live(("cover.spine", 2, "like", "proposed"),
                         ("cover.spine.remaches", 0, None, "proposed"))
        bh.check_round_earns_its_place(decisions, {"cover.spine.remaches"})

    def test_re_asking_the_element_itself_is_allowed(self):
        decisions = live(("cover.spine", 2, "like", "proposed"))
        bh.check_round_earns_its_place(decisions, {"cover.spine"})

    def test_nothing_waiting_means_nothing_to_refuse(self):
        # A project with no liked-and-low work is free to explore.
        decisions = live(("cover.spine", 5, "like", "proposed"),
                         ("type.silkscreen", 0, None, "proposed"))
        bh.check_round_earns_its_place(decisions, {"type.silkscreen"})

    def test_a_high_score_with_a_thumb_up_is_not_polish_work(self):
        # 3 stars is not "the drawing is not there yet". Only 1-2 is.
        decisions = live(("cover.spine", 3, "like", "proposed"),
                         ("type.silkscreen", 0, None, "proposed"))
        bh.check_round_earns_its_place(decisions, {"type.silkscreen"})

    def test_two_redraws_of_one_element_are_wallpaper(self):
        decisions = live(("art.trama", 2, "like", "proposed"),
                         ("art.trama.limpia", 0, None, "proposed"),
                         ("art.trama.real", 0, None, "proposed"))
        with self.assertRaises(bh.HarnessError) as caught:
            bh.check_round_earns_its_place(
                decisions, {"art.trama.limpia", "art.trama.real"})
        self.assertIn("art.trama", str(caught.exception))

    def test_one_redraw_each_of_two_elements_is_a_round_not_wallpaper(self):
        decisions = live(("art.trama", 2, "like", "proposed"),
                         ("cover.spine", 2, "like", "proposed"),
                         ("art.trama.limpia", 0, None, "proposed"),
                         ("cover.spine.remaches", 0, None, "proposed"))
        bh.check_round_earns_its_place(
            decisions, {"art.trama.limpia", "cover.spine.remaches"})

class AnAgentPlaceholderIsNotAScore(unittest.TestCase):
    """`decide --source agent --stars 1` used to write `scored: True`.

    The row then painted a gold star on a proposal the user had never seen,
    suppressed the "sin puntuar" marker, and made a brand-new round read as one
    already judged badly. `anti-slop.md` says the rank reflects the user, not
    the agent -- so the placeholder must be visible as a starting position and
    never as a judgement.
    """

    def harness(self, root: Path) -> Path:
        output = root / "spec" / "design-harness"
        output.mkdir(parents=True)
        bh.write_json(output / "decisions.json", bh.empty_decisions())
        bh.write_json(output / "project.json", {"version": bh.VERSION, "state": "draft"})
        (output / "DECISIONS.md").write_text("", encoding="utf-8")
        return output

    def test_an_agent_decision_is_not_recorded_as_scored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.harness(root)
            bh.record_decision(root, "x.agent", "proposed", 1, "evidencia", [],
                               source="agent")
            entry = bh.load_decisions(output)["elements"][0]
            self.assertFalse(entry["scored"],
                             "an agent placeholder recorded as scored becomes a rank "
                             "the user never set")

    def test_a_user_decision_is_recorded_as_scored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.harness(root)
            bh.record_decision(root, "x.user", "proposed", 3, "evidencia", [],
                               source="user")
            self.assertTrue(bh.load_decisions(output)["elements"][0]["scored"])

    def test_the_user_ranking_it_later_turns_it_into_a_real_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.harness(root)
            bh.record_decision(root, "x", "proposed", 1, "evidencia", [], source="agent")
            bh.record_decision(root, "x", "proposed", 4, "me gusta", [], source="user")
            entry = bh.load_decisions(output)["elements"][0]
            self.assertEqual((entry["stars"], entry["scored"], entry["source"]),
                             (4, True, "user"))

    def test_re_proposing_as_the_agent_still_does_not_score_it(self):
        # The second `decide` for the same id takes the UPDATE path, which had
        # its own `scored = True` and would have quietly re-scored the row.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.harness(root)
            bh.record_decision(root, "x", "proposed", 1, "primera", [], source="agent")
            bh.record_decision(root, "x", "proposed", 1, "segunda", [], source="agent")
            entry = bh.load_decisions(output)["elements"][0]
            self.assertFalse(entry["scored"])

    def test_the_row_paints_no_star_the_user_did_not_set(self):
        # Legacy rows carry scored=True from before the write path was fixed,
        # so the ROW must decide from who ranked it, not from the stale flag.
        decisions = {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
                     "elements": [
                         {"element": "a.placeholder", "stars": 1, "sentiment": None,
                          "state": "proposed", "scored": True, "source": "agent"},
                         {"element": "b.ranked", "stars": 3, "sentiment": "like",
                          "state": "proposed", "scored": True, "source": "user"}]}
        markup = bh.render_feedback_controls(decisions, None, None, None, "es")
        for element, expected in (("a.placeholder", 0), ("b.ranked", 3)):
            row = re.search(r'<div class="dh-fb" data-element="%s".*?\n</div>'
                            % re.escape(element), markup, re.S).group(0)
            lit = len(re.findall(r'<span data-rank="\d" [^>]*class="on"', row))
            self.assertEqual(lit, expected,
                             f"{element} painted {lit} star(s), expected {expected}")
            self.assertRegex(row, r'data-stars="%d"' % expected)
            # And it must SAY so. Without the marker an agent placeholder just
            # looks like a row someone scored zero.
            marked = "puntuar" in row.lower() or "unscored" in row.lower()
            self.assertEqual(marked, expected == 0,
                             f"{element} should{'' if expected == 0 else ' not'} carry "
                             "the unscored marker")

class PublishSurvivesACompanionRestart(unittest.TestCase):
    """The companion restarts into a new session directory, so any caller that
    names a path is guessing. Refusing left a correct screen unpublishable and
    the user on a stale page."""

    def test_a_screen_written_elsewhere_is_moved_not_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            served = root / ".superpowers" / "brainstorm" / "1-1" / "content"
            served.mkdir(parents=True)
            stray = root / "elsewhere.html"
            stray.write_text("<p>screen</p>", encoding="utf-8")
            out = bh.publish_screen(root, stray)
            self.assertEqual(out.parent.resolve(), served.resolve())
            self.assertTrue((served / "elsewhere.html").is_file())

    def test_the_published_screen_is_the_newest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            served = root / ".superpowers" / "brainstorm" / "1-1" / "content"
            served.mkdir(parents=True)
            (served / "old.html").write_text("old", encoding="utf-8")
            stray = root / "new.html"
            stray.write_text("new", encoding="utf-8")
            bh.publish_screen(root, stray)
            newest = max(served.glob("*.html"), key=lambda p: p.stat().st_mtime)
            self.assertEqual(newest.name, "new.html")

class PreviewsMustBeVisible(unittest.TestCase):
    """The gate that replaces hand-authored SVG with something checkable.

    A preview used to be markup the model wrote blind. One session shipped a
    comp wrapped in a nested `opacity="0.13"` and the whole of the NEXT round
    was spent repairing it rather than improving the design -- the user's score
    was the first time anyone found out. A rendered comp can be measured, so it
    is, and the failure cannot reach the ledger.

    Synthetic images, so these run with no browser and no network.
    """

    def setUp(self):
        try:
            from PIL import Image, ImageDraw  # noqa: F401
        except ImportError:
            self.skipTest("Pillow is not installed; the gate degrades to a no-op")
        self.tmp = Path(tempfile.mkdtemp())

    def page(self, name, ink=None, ground=(255, 215, 229), step=26, height=12):
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (510, 660), ground)
        if ink:
            draw = ImageDraw.Draw(image)
            for y in range(60, 600, step):
                draw.rectangle([40, y, 470, y + height], fill=ink)
        path = self.tmp / name
        image.save(path)
        return path

    def test_a_comp_faded_to_thirteen_percent_is_refused(self):
        # #111 at 13% over #ffd7e5 -- the exact defect, in its own numbers.
        faded = self.page("faded.png", ink=(232, 199, 214))
        with self.assertRaises(bh.HarnessError) as caught:
            bh.check_preview_legible(faded)
        self.assertIn("contrast", str(caught.exception).lower())

    def test_a_blank_page_is_refused(self):
        with self.assertRaises(bh.HarnessError):
            bh.check_preview_legible(self.page("blank.png"))

    def test_a_sparse_but_legible_comp_passes(self):
        # Refusing this would make the gate worse than the bug: a restrained
        # cover is a design, not an error.
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (510, 660), (255, 215, 229))
        draw = ImageDraw.Draw(image)
        draw.rectangle([40, 300, 470, 304], fill=(17, 17, 17))
        draw.rectangle([40, 330, 300, 360], fill=(17, 17, 17))
        path = self.tmp / "sparse.png"
        image.save(path)
        bh.check_preview_legible(path)

    def test_a_pastel_pairing_from_the_corpus_passes(self):
        # mint on yellow -- both real corpus colours, low luminance contrast.
        # The gate must not mistake a soft palette for an invisible one.
        bh.check_preview_legible(
            self.page("mint.png", ink=(178, 255, 194), ground=(255, 235, 8), height=20))

    def test_recording_a_blank_png_preview_is_refused(self):
        # The gate has to sit on `decide --preview`, not only on `shoot`, or a
        # hand-made PNG walks straight past it into the ledger.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "shots").mkdir()
            blank = self.page("x.png")
            target = root / "shots" / "x.png"
            target.write_bytes(blank.read_bytes())
            with self.assertRaises(bh.HarnessError):
                bh.preview_reference(root, "shots/x.png")

    def test_a_letterboxed_render_is_cropped_back_to_the_comp(self):
        """QuickLook returns a SQUARE thumbnail with the page anchored top-left.

        A letter-shaped comp came back as 171x221 of drawing inside 510x510 of
        white -- 85% empty -- and the article then fitted that whole square into
        a 96px portrait frame, so the comp rendered about 32px across and read
        as a blank card. Cropping restores its own aspect.
        """
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (510, 510), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle([3, 3, 173, 223], fill=(255, 215, 229))   # the comp, inset
        # QuickLook pads with white and anchors the page top-left, so the
        # corner pixel is the letterbox and not the comp's own ground.
        draw.rectangle([23, 23, 153, 43], fill=(17, 17, 17))     # some ink on it
        path = self.tmp / "letterboxed.png"
        image.save(path)
        bh.trim_to_content(path, 510)
        with Image.open(path) as out:
            width, height = out.size
        self.assertEqual(width, 510, "the crop must scale back to the target width")
        self.assertAlmostEqual(width / height, 171 / 221, places=1,
                               msg="the comp's own aspect must survive the crop")

    def test_the_renderer_actually_calls_the_crop(self):
        # The crop is correct in isolation and useless if the render path stops
        # calling it -- which is a whole class of half-change this repo has
        # shipped before. Driving qlmanage from a unit test is not worth it, so
        # assert the wiring directly.
        import inspect
        source = inspect.getsource(bh.render_html_preview)
        self.assertIn("trim_to_content", source,
                      "the fallback renderer must crop its letterboxed output")

    def test_cropping_a_full_bleed_render_changes_nothing(self):
        # Chrome output has no margin: its bounding box is the whole image, so
        # the crop must be a no-op rather than shaving a row of pixels.
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (510, 660), (255, 215, 229))
        ImageDraw.Draw(image).rectangle([0, 0, 509, 40], fill=(17, 17, 17))
        path = self.tmp / "fullbleed.png"
        image.save(path)
        bh.trim_to_content(path, 510)
        with Image.open(path) as out:
            self.assertEqual(out.size, (510, 660))

    def test_the_measurement_is_reported_as_numbers(self):
        # The refusal quotes a figure so a borderline comp can be argued about
        # against evidence rather than against an opinion.
        ink = bh.preview_ink(self.page("dense.png", ink=(17, 17, 17), step=24, height=16))
        self.assertGreater(ink["coverage"], 0.2)
        self.assertGreater(ink["contrast"], bh.MIN_INK_CONTRAST)


if __name__ == "__main__":
    unittest.main()
