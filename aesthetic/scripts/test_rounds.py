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


class TheArticleAsRendered(unittest.TestCase):
    """Checks against the emitted markup. A rule that reads correctly in the
    source and is dropped by the CSS parser is the defect, not the source."""

    def article(self) -> str:
        decisions = live(("cover.spine", 2, "like", "proposed"),
                         ("cover.spine.remaches", 0, None, "proposed"),
                         ("type.brackets", 4, "like", "approved"))
        with tempfile.TemporaryDirectory() as tmp:
            return bh.render_article(Path(tmp), decisions, {"cover.spine.remaches"},
                                     "lomo", "es", None, "Fichas", "Remaches.")

    def test_every_stylesheet_comment_is_closed(self):
        # Two separate half-changes shipped because an unclosed `/*` swallowed
        # the rules after it: the row gap and the group heading both silently
        # kept their old values while the source said otherwise.
        markup = self.article()
        for block in re.findall(r"<style>(.*?)</style>", markup, re.S):
            self.assertEqual(block.count("/*"), block.count("*/"),
                             "an unbalanced comment discards every rule that follows it")

    def test_no_rule_after_a_comment_is_orphaned_prose(self):
        markup = self.article()
        for block in re.findall(r"<style>(.*?)</style>", markup, re.S):
            stripped = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
            for line in stripped.splitlines():
                line = line.strip()
                if not line or line.startswith("@") or line.startswith("}"):
                    continue
                self.assertFalse(
                    line.endswith("*/"),
                    f"orphaned comment tail outside a comment: {line!r}")

    def test_every_thumbnail_names_its_element(self):
        # The slideshow addresses a slide by id. A thumbnail without one is a
        # picture that leads nowhere -- which is what all 95 of them were.
        markup = self.article()
        shots = re.findall(r'<span class="dh-shot"([^>]*)>', markup)
        self.assertTrue(shots, "the article rendered no thumbnails at all")
        for attrs in shots:
            self.assertIn("data-el=", attrs,
                          "a thumbnail with no data-el cannot open its slide")

    def test_the_lightbox_holds_no_state_of_its_own(self):
        # Every control in the slideshow must click the row's real control.
        # A second write path is how the JS and Python rules drifted apart.
        markup = self.article()
        script = re.search(r"<script>/\* dh-lightbox \*/(.*?)</script>", markup, re.S)
        self.assertIsNotNone(script, "the lightbox script was not emitted")
        body = script.group(1)
        self.assertIn("data-proxy", body)
        for forbidden in ("fetch(", "WebSocket", "localStorage"):
            self.assertNotIn(forbidden, body,
                             f"the lightbox must not talk to {forbidden} itself; "
                             "it proxies the row and the companion does the writing")

    def test_no_hover_rule_paints_a_row_with_a_transparent_base(self):
        """The inverted-zone trap, for the fourth time in this file's history.

        A row inside the round zone paints its OWN light ground and keeps its
        own dark ink. Any background here mixed toward `transparent` lets the
        inverted section show through, and the row becomes dark text on a
        near-black card -- which is exactly what hovering a proposal did. Mix
        toward `var(--dh-bg)` instead: that stays opaque and is correct on both
        grounds.
        """
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.article(), re.S).group(1)
        flat = re.sub(r"/\*.*?\*/", "", style, flags=re.S)
        for rule in re.findall(r"([^{}]*:hover[^{}]*)\{([^}]*)\}", flat):
            selector, body = rule
            if ".dh-fb" not in selector:
                continue
            background = re.search(r"background(?:-color)?\s*:\s*([^;]*)", body)
            if not background:
                continue
            self.assertNotIn(
                "transparent", background.group(1),
                f"{selector.strip()} mixes toward transparent; inside the inverted "
                "round zone that paints the row's ink onto the zone's dark ground")

    def test_the_strip_bars_carry_no_native_title(self):
        # The strip draws its own tooltip. A `title` makes the browser draw a
        # SECOND one, in the OS font, at its own position -- two overlapping
        # labels covering the key row underneath the sticky bar.
        markup = self.article()
        bars = re.findall(r"<a class=\"dh-t[^\"]*\"([^>]*)>", markup)
        self.assertTrue(bars, "the article rendered no strip bars")
        for attrs in bars:
            self.assertNotIn("title=", attrs.replace("aria-label=", ""))
            self.assertIn("data-tip=", attrs)

    def test_the_swatch_column_is_never_narrower_than_its_controls(self):
        # The scoring strip is five 30px stars, a zero and three verdict
        # buttons: 216px of touch targets that cannot shrink. A column narrower
        # than that overflows its own card, which is how the strip came to sit
        # broken across three ragged lines.
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.article(), re.S).group(1)
        floor = re.search(r"repeat\(auto-fit,\s*minmax\((\d+)px", style)
        self.assertIsNotNone(floor, "the swatch grid stopped declaring a column floor")
        self.assertGreaterEqual(int(floor.group(1)), 240)

    def test_the_spacing_scale_is_declared_before_it_is_used(self):
        markup = self.article()
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>", markup, re.S).group(1)
        used = set(re.findall(r"var\((--s\d)\)", style))
        declared = set(re.findall(r"(--s\d):", style))
        self.assertTrue(used, "the article stopped using the spacing scale")
        self.assertLessEqual(used, declared,
                             "a var() with no declaration silently computes to 0")


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

    def test_the_measurement_is_reported_as_numbers(self):
        # The refusal quotes a figure so a borderline comp can be argued about
        # against evidence rather than against an opinion.
        ink = bh.preview_ink(self.page("dense.png", ink=(17, 17, 17), step=24, height=16))
        self.assertGreater(ink["coverage"], 0.2)
        self.assertGreater(ink["contrast"], bh.MIN_INK_CONTRAST)


if __name__ == "__main__":
    unittest.main()
