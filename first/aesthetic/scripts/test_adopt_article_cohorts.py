"""Tests for the article's rounds: cohort scope, specimens, zone placement.

Everything here is about which elements land in which zone of the rendered
article, and how a round and its specimens survive the inverted ground.
"""
import re
import tempfile
import unittest
from pathlib import Path

import bootstrap_harness as bh
from adopt_fixtures import ArticleFixture, ledger


class TheArticleIsADesignSystem(ArticleFixture, unittest.TestCase):
    def one_folder(self, root: Path) -> dict:
        """Three foundations under ONE parent item.

        The foundation-span check and `check_round_stays_in_scope` used to be
        indistinguishable in these tests, because the fixture cohort spanned
        three foundations AND three parent items -- so whichever check ran
        first was the one being tested. Everything here sits under `folder`,
        which reaches the foundation check with scope already satisfied.
        """
        self.system(root)
        for element in ("folder.type.display", "folder.palette.warm",
                        "folder.voice.labels"):
            bh.record_decision(root, element, "proposed", 1, "fixture", [])
        return bh.load_decisions(root / "spec" / "design-harness")

    SCATTERED = {"folder.type.display", "folder.palette.warm", "folder.voice.labels"}

    def test_a_cohort_spanning_many_foundations_is_refused(self):
        """Three elements from three foundations under a name claiming a shared
        surface is a batch of errands. The page cannot say what it asks, so the
        agent ends up explaining the round in prose instead."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions = self.one_folder(root)
            with self.assertRaises(bh.HarnessError) as caught:
                bh.render_article(root, decisions, self.SCATTERED)
            self.assertIn("one surface or one problem", str(caught.exception))

    def test_stating_what_they_share_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions = self.one_folder(root)
            markup = bh.render_article(root, decisions, self.SCATTERED,
                                       asks="Everything the folder says out loud.")
            self.assertIn("Everything the folder says out loud.", markup)

    def test_asks_does_not_buy_a_round_out_of_its_parent_item(self):
        """`--asks` answers the foundation-span check: it explains a round that
        needs explaining. It must not answer scope, because no sentence turns
        two objects into one round -- that is how a long run ends up spread
        across every surface in the ledger."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.system(root)
            bh.record_decision(root, "voice.labels", "proposed", 1, "fixture", [])
            decisions = bh.load_decisions(root / "spec" / "design-harness")
            with self.assertRaises(bh.HarnessError) as caught:
                bh.render_article(root, decisions,
                                  {"type.display", "cover.weak", "voice.labels"},
                                  asks="Everything the cover says out loud.")
            self.assertIn("parent items", str(caught.exception))

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
            markup = bh.render_article(root, self.system(root))
            style = markup.split("<style>/* dh-article */")[1].split("</style>")[0]
            self.assertNotIn("#fff5", style)
            self.assertIn("var(--dh-bg", style)

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
