"""Tests for rendering the ledger as an article: material, zones, chart.

The article has to show the material -- the palette as colour, the faces as
type -- and keep its four zones and its navigation distinguishable.
"""
import re
import tempfile
import unittest
from pathlib import Path

import bootstrap_harness as bh
from adopt_fixtures import ArticleFixture, ledger


class TheArticleIsADesignSystem(ArticleFixture, unittest.TestCase):
    """A foundation heading with one scoring row under it is a list. The section
    has to show the material -- the palette as colour, the faces as type -- and
    the four zones have to be distinguishable, or the user re-reads decisions
    they already made looking for the three that matter."""

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
