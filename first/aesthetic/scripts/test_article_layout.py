"""Tests for how the article lays itself out on the screen.

Cards, chips, headers, the frame it sits in and the stylesheet that holds it
there. Split out of `test_article.py` for its directory's byte budget.
"""
import re
import tempfile
import unittest
from pathlib import Path

import bootstrap_harness as bh
from article_fixtures import live


class TheCardNamesTheDesignNotTheToken(unittest.TestCase):
    """A designer should not have to parse a namespace to know what they score."""

    def test_a_title_wins_when_one_is_given(self):
        self.assertEqual(
            bh.display_name({"element": "a.b.c", "title": "Pestaña de rol"}),
            "Pestaña de rol")

    def test_the_description_beats_a_humanised_id(self):
        # "El objeto de portada dibujado grande" against "Sin colision".
        name = bh.display_name({
            "element": "cover.object.character-drawn.dentro-de-margen.sin-colision",
            "description": "el objeto de portada dibujado grande, reubicado bajo el anillo"})
        self.assertEqual(name, "El objeto de portada dibujado grande")

    def test_a_redraw_never_shares_its_parents_name(self):
        # The round view puts parent and redraw side by side as before/after.
        # Two identical titles over two different drawings is worse than the id.
        described = "el objeto de portada dibujado grande, reubicado"
        names = bh.display_names([
            {"element": "cover.object", "description": described},
            {"element": "cover.object.sin-colision", "description": described}])
        self.assertNotEqual(names["cover.object"], names["cover.object.sin-colision"])
        self.assertIn("sin colision", names["cover.object.sin-colision"])

    def test_the_id_stays_a_binding_not_visible_copy(self):
        markup = bh.render_feedback_controls(
            {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
             "elements": [{"element": "cover.object", "stars": 2, "sentiment": None,
                           "state": "proposed", "scored": True, "source": "user",
                           "description": "un objeto grande"}]},
            None, None, None, "es")
        self.assertNotIn('<code class="dh-token">', markup)
        self.assertIn('data-element="cover.object"', markup)
        self.assertIn('class="dh-id">Un objeto grande<', markup)

    def a_row(self, bookmarked) -> str:
        return bh.render_feedback_controls(
            {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
             "elements": [{"element": "cover.object", "stars": 2, "sentiment": None,
                           "state": "proposed", "scored": True, "source": "user",
                           "bookmarked": bookmarked}]},
            None, None, None, "en")

    def test_a_bookmarked_element_renders_the_control_lit(self):
        markup = self.a_row(True)
        self.assertIn("data-bookmark", markup)
        # A 4th independent signal, not folded into an existing one -- must
        # never share a class with sentiment/verdict's own `.on` markers.
        match = re.search(r'<span data-bookmark[^>]*>', markup)
        self.assertIsNotNone(match)
        self.assertIn('class="on"', match.group(0))

    def test_an_unbookmarked_element_renders_the_control_unlit(self):
        markup = self.a_row(False)
        match = re.search(r'<span data-bookmark[^>]*>', markup)
        self.assertIsNotNone(match)
        self.assertNotIn('class="on"', match.group(0))

    def test_an_element_missing_the_field_entirely_defaults_unlit(self):
        # Ledgers written before this feature existed have no "bookmarked"
        # key at all -- must read as unbookmarked, not crash.
        markup = bh.render_feedback_controls(
            {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
             "elements": [{"element": "cover.object", "stars": 2, "sentiment": None,
                           "state": "proposed", "scored": True, "source": "user"}]},
            None, None, None, "en")
        match = re.search(r'<span data-bookmark[^>]*>', markup)
        self.assertIsNotNone(match)
        self.assertNotIn('class="on"', match.group(0))


class TheArticleFitsItsContainer(unittest.TestCase):
    """The same row renders in a 1180px article and in a companion pane a third
    that wide, so the layout responds to its CONTAINER, not to the viewport."""

    def style(self) -> str:
        markup = bh.render_article(
            Path("/tmp"),
            {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
                           "elements": [{"element": "core.idea", "stars": 2,
                                         "sentiment": "like", "state": "proposed",
                                         "scored": True, "source": "user"}]},
            set(), cohort_name="", language="en", title="Fichas", asks="Ask.")
        return markup

    def test_the_container_is_an_ancestor_never_the_row_itself(self):
        # An element cannot respond to its own container query. The first
        # attempt put `container-type` on `.dh-fb` and silently did nothing --
        # the controls kept overflowing a narrow row by 220px.
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.style(), re.S).group(1)
        zone = re.search(r"\.dh-zone\{([^}]*)\}", style).group(1)
        self.assertIn("container-type:inline-size", zone)
        self.assertIn("container-name:dh-row", zone)

    def test_the_narrow_rules_outrank_the_legacy_media_query(self):
        """A legacy `@media (max-width:780px)` sets the same property on
        `.dh-fb.dh-fb` further down the sheet, so a container rule that only
        ties on specificity loses to it by source order."""
        markup = self.style()
        style = re.search(r"<style>/\* dh-controls \*/(.*?)</style>", markup, re.S).group(1)
        for block in re.findall(r"@container dh-row \([^)]*\)\{(.*?)\n\}", style, re.S):
            if "grid-template-columns" in block:
                self.assertIn(".dh-fb.dh-fb.dh-fb", block,
                              "a container rule must outrank the legacy media query")


class TheTwoChipsAreNotTheSameThing(unittest.TestCase):
    """Status and id were two grey pills of the same size saying unrelated
    things. One is a lifecycle state; the other is the string you quote back to
    the agent."""

    def style(self) -> str:
        markup = bh.render_feedback_controls(
            {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
             "elements": [{"element": "core.idea", "stars": 2, "sentiment": None,
                           "state": "proposed", "scored": True, "source": "user"}]},
            None, None, None, "en")
        return re.search(r"<style>/\* dh-controls \*/(.*?)</style>", markup, re.S).group(1)

    def test_the_id_is_not_a_badge(self):
        rule = re.search(r"\.dh-fb \.dh-token\{([^}]*)\}", self.style()).group(1)
        self.assertIn("background:none", rule)
        self.assertIn("padding:0", rule)

    def test_the_status_carries_its_lifecycle_as_colour(self):
        style = self.style()
        for group in ("developing", "rejected"):
            self.assertRegex(
                style, r'\.dh-fb\[data-group="%s"\] \.dh-state\{' % group,
                f"{group} rows must not look identical to every other state")


class TheRoundHeaderNamesTheObject(unittest.TestCase):
    def test_a_slug_like_objeto_becomes_the_object_name(self):
        decisions = live(("cover.object.character-drawn", 1, None, "proposed"))
        decisions["elements"][0]["description"] = (
            "El objeto de portada es el micrófono de Open Mic, dibujado como personaje")
        with tempfile.TemporaryDirectory() as tmp:
            markup = bh.render_article(
                Path(tmp), decisions, {"cover.object.character-drawn"},
                cohort_name="objeto", language="es", title="Performance Ejecutivo",
                asks="¿Se lee como personaje?")
            tag = markup.split('class="dh-tag">')[1].split("</p>")[0]
            self.assertIn("Micrófono", tag)
            self.assertNotEqual(tag.lower(), "objeto")

    def test_the_round_shows_one_topic_not_two(self):
        decisions = live(
            ("cover.object.character-drawn", 1, None, "proposed"),
            ("cover.layout.two-column", 2, "like", "proposed"))
        with tempfile.TemporaryDirectory() as tmp:
            markup = bh.render_article(
                Path(tmp), decisions,
                {"cover.object.character-drawn", "cover.layout.two-column"},
                cohort_name="objeto", language="es")
            domain = markup.split('class="dh-domain">')[1].split("</p>")[0]
            self.assertEqual(domain.count("<span>"), 1,
                             "two foundation pills stacked topics the round does not have")

    def test_the_round_icon_matches_the_primary_foundation(self):
        decisions = live(("artsource.pixel.trama", 1, None, "proposed"))
        with tempfile.TemporaryDirectory() as tmp:
            markup = bh.render_article(
                Path(tmp), decisions, {"artsource.pixel.trama"}, cohort_name="objeto",
                language="es")
            round_zone = markup.split('id="dh-zone-round"')[1].split("</section>")[0]
            self.assertIn("dh-round-icon", round_zone)
            self.assertIn("<circle cx=\"9\" cy=\"8\" r=\"2\"/>", round_zone,
                          "illustration rounds use the drawing icon, not the core target")


class TheTextOutranksTheControls(unittest.TestCase):
    def test_the_controls_wrap_before_the_text_loses_its_measure(self):
        """The strip is 360px of fixed touch targets and was winning the space
        fight: at an 802px row the description got 282px and its provenance
        column 196px, so it wrapped every four words. The breakpoint has to ask
        "does the text still have a measure?", not "is the row narrow?" -- 96px
        of thumbnail plus 360px of controls leaves under 30ch until ~980px."""
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
        style = re.search(r"<style>/\* dh-controls \*/(.*?)</style>", markup, re.S).group(1)
        widths = [int(w) for w in re.findall(
            r"@container dh-row \(max-width: (\d+)px\)", style)]
        self.assertTrue(widths, "the row lost its container queries")
        self.assertGreaterEqual(
            max(widths), 900,
            "the controls must drop to their own row well before the text is "
            f"crushed; widest breakpoint is only {max(widths)}px")


class TheArticleDoesNotOverflowTheFrame(unittest.TestCase):
    def test_wide_charts_scroll_and_the_article_stays_full_width(self):
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          bh.render_article(Path("/tmp"),
                                            live(("core.idea", 2, "like", "proposed")),
                                            set(), cohort_name="", language="en",
                                            title="F", asks="Ask."),
                          re.S).group(1)
        self.assertIn("inline-size:100%", style)
        self.assertIn("overflow-x:auto", style.replace(" ", ""))


class SupersededRowsStayReadable(unittest.TestCase):
    def test_rejected_opacity_is_scoped_to_the_antipattern_zone(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
        style = re.search(r"<style>/\* dh-controls \*/(.*?)</style>", markup, re.S).group(1)
        self.assertIn('.dh-zone[data-zone="antipattern"] .dh-fb[data-group="rejected"]{opacity:.62}',
                      style)
        for rule in style.split("}"):
            if '.dh-fb[data-group="rejected"]' in rule and "opacity:.62" in rule:
                self.assertIn("antipattern", rule,
                              "rejected opacity must only apply inside antipattern zone")


class TheFrameOwnsTheAgentLink(unittest.TestCase):
    def test_the_article_has_no_second_agent_navigation_surface(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.",
            agent_url="https://agent.test/chat")
        self.assertIn('data-agent-url="https://agent.test/chat"', markup)
        self.assertNotIn('class="dh-bar"', markup)


class TheStickyBarReadsTopDown(unittest.TestCase):
    def test_title_then_legend_then_chart_then_sections(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
        nav = markup.split('class="dh-toc"')[1].split("</nav>")[0]
        order = [nav.index(x) for x in
                 ('dh-toc-title', 'dh-key', 'dh-temp', '<ol>')]
        self.assertEqual(order, sorted(order),
                         "legend belongs above the chart it explains, and the "
                         "chart above the sections it indexes")


class TheScreenSaysWhatEncodingItIs(unittest.TestCase):
    """R-29. The article is a fragment, so its encoding rode on whoever served
    it. Opened from disk, every Spanish accent became mojibake."""

    def test_the_article_declares_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = bh.render_article(Path(tmp), live(("cover.a", 3, None, "approved")))
            self.assertIn('<meta charset="utf-8">', markup)

    def test_the_declaration_leads_the_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = bh.render_article(Path(tmp), live(("cover.a", 3, None, "approved")))
            self.assertLess(markup.index("charset"), markup.index("<style>"))


class ChromeFixesV34(unittest.TestCase):
    def markup(self, **kwargs) -> str:
        opts = dict(language="en", title="F", asks="Ask.",
                    agent_name="Composer", agent_url="cursor://agent")
        opts.update(kwargs)
        return bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language=opts.pop("language"), title=opts.pop("title"),
            asks=opts.pop("asks"), **opts)

    def test_saved_pill_uses_the_project_accent(self):
        style = re.search(r"<style>/\* dh-controls \*/(.*?)</style>",
                          self.markup(), re.S).group(1)
        saved = re.search(r"\.dh-fb \.dh-saved\{([^}]*)\}", style).group(1)
        self.assertIn("--dh-accent", saved)
        self.assertNotIn("#1c8b4b", saved)
        cheer = re.search(r"\.dh-fb \.dh-saved\[data-cheer\]\{([^}]*)\}",
                          self.markup())
        article = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                            self.markup(), re.S).group(1)
        cheer = re.search(r"\.dh-fb \.dh-saved\[data-cheer\]\{([^}]*)\}", article)
        self.assertIsNotNone(cheer)
        self.assertNotIn("#126435", cheer.group(1))

    def test_connected_label_uses_the_status_color(self):
        frame = (Path(__file__).parents[1] / "companion" / "frame-template.html").read_text(
            encoding="utf-8")
        rule = re.search(r"\.status\s*\{([^}]*)\}", frame, re.S)
        self.assertIsNotNone(rule)
        self.assertIn("--status-color", rule.group(1))

    def test_agent_line_splits_app_and_model(self):
        markup = self.markup()
        self.assertIn('data-agent-app="Cursor"', markup)
        self.assertIn('data-agent-model="Composer"', markup)
        self.assertIn('data-agent-label="Cursor Composer"', markup)
        self.assertNotIn("Cursor | Composer", markup)
        helper = (Path(__file__).parents[1] / "companion" / "helper.js").read_text(
            encoding="utf-8")
        self.assertIn("[data-agent-app]", helper)
        self.assertIn("[data-agent-model]", helper)

    def test_connected_uses_regular_weight(self):
        frame = (Path(__file__).parents[1] / "companion" / "frame-template.html").read_text(
            encoding="utf-8")
        rule = re.search(r"\.status\s*\{([^}]*)\}", frame, re.S)
        self.assertIsNotNone(rule)
        weight = re.search(r"font-weight:\s*(\d+)", rule.group(1))
        self.assertIsNotNone(weight)
        self.assertLess(int(weight.group(1)), 500)

    def test_toc_kills_leaked_comp_bullets(self):
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.markup(), re.S).group(1)
        self.assertIn(".dh-toc li::before", style)
        self.assertIn(".main{scroll-behavior:smooth}", style.replace(" ", ""))

    def test_review_has_no_covering_corner_chip(self):
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.markup(), re.S).group(1)
        self.assertNotIn(".dh-bar", style)

    def test_the_lightbox_declares_the_spacing_scale_it_uses(self):
        """The dialog is appended to `document.body`, NOT inside `.dh-art`,
        so it inherits none of the `--s1..--s6` declared there. Without a
        redeclaration every `var(--sN)` in the lightbox resolves to nothing:
        the shell computes `padding:0` and every zone gap collapses, which is
        how the slideshow spent several rounds looking cluttered while the
        spacing edits meant to fix it were being silently discarded."""
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.markup(), re.S).group(1)
        dialog = re.search(r"dialog\.dh-lb\{([^}]*)\}", style).group(1)
        for token in ("--s1:", "--s2:", "--s3:", "--s4:"):
            self.assertIn(token, dialog.replace(" ", ""),
                          f"the lightbox uses {token[:-1]} but never declares it, so it "
                          "resolves to nothing and the spacing silently disappears")

    def test_lightbox_centers_score_and_strip(self):
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.markup(), re.S).group(1)
        strip = re.search(r"\.dh-lb-strip\{([^}]*)\}", style).group(1)
        self.assertIn("justify-content:center", strip.replace(" ", ""))
        score = re.search(r"\.dh-lb-score-wrap\{([^}]*)\}", style).group(1)
        self.assertIn("justify-content:center", score.replace(" ", ""))
        # The COPY is deliberately not centred. Centring three stacked lines of
        # different lengths gives each a different left edge, which read as
        # debris under the drawing instead of a paragraph about it. It gets a
        # measure and a start edge; only the controls stay centred.
        copy = re.search(r"\.dh-lb-copy\{([^}]*)\}", style).group(1).replace(" ", "")
        self.assertIn("text-align:start", copy)
        self.assertRegex(copy, r"inline-size:min\(\d+ch,100%\)")

    def test_the_article_ships_no_live_status_script(self):
        self.assertNotIn("/* dh-live */", self.markup())

    def test_lightbox_hides_the_companion_header(self):
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.markup(), re.S).group(1)
        self.assertIn("html:has(dialog.dh-lb[open]) .header", style)
        signals = re.search(
            r"\.dh-lb-score-wrap \.dh-lb-score \.dh-signals\{([^}]*)\}",
            style).group(1)
        self.assertIn("nowrap", signals)
        shot = re.search(r"\.dh-lb-art \.dh-shot\{([^}]*)\}", style).group(1)
        self.assertIn("position:relative", shot.replace(" ", ""))
        script = re.search(r"<script>/\* dh-shot-fit \*/(.*?)</script>",
                           self.markup(), re.S).group(1)
        self.assertIn("Math.min(w/cw,h/ch)", script.replace(" ", ""))

    def test_preparing_round_is_static(self):
        working = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), {"core.idea"},
            cohort_name="", language="en", title="F", asks="Does this beat what stands?",
            agent_working=True)
        self.assertIn('data-preparing="1"', working)
        self.assertIn("class=\"dh-prep\"", working)
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          working, re.S).group(1)
        prep = re.search(
            r"\[data-preparing\] > :not\(\.dh-prep\)\{([^}]*)\}", style)
        self.assertIsNotNone(prep)
        # The rows must NOT be dimmed. They stayed fully clickable the whole
        # time the old `opacity:.72` was here -- nothing sets pointer-events,
        # disabled or inert while preparing, and clicks are sent, stored and
        # echoed normally. Dimming only told the user that the one thing they
        # could usefully do during a long inference was unavailable.
        self.assertNotIn("opacity", prep.group(1),
                         "a live control must not be styled as a disabled one")
        self.assertIn("transition:none", prep.group(1).replace(" ", ""))
        overlay = re.search(
            r"\[data-preparing\] \.dh-prep\{([^}]*)\}", style).group(1)
        compact = overlay.replace(" ", "")
        self.assertIn("position:absolute", compact)
        self.assertIn("inset:12px12pxauto", compact)
        self.assertNotIn("opacity:.72", overlay)

    def test_the_ask_has_a_readable_measure(self):
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.markup(), re.S).group(1)
        rule = re.search(r"\.dh-ask\{([^}]*)\}", style).group(1)
        self.assertNotIn("30ch", rule)
        self.assertIn("62ch", rule)

    def test_comp_element_selectors_cannot_style_the_toc(self):
        raw = ("<html><head><style>li::before{content:'·'}*{margin:0;padding:0}"
               "body{width:510px;background:#e8e4d8}</style></head>"
               "<body><ul><li>x</li></ul></body></html>")
        frag, _, _ = bh.html_comp_fragment(raw)
        compact = re.sub(r"\s+", "", frag)
        self.assertIn("@scope", frag)
        self.assertIn(bh.COMP_SCOPE_CLASS, frag)
        # Host size/paint must bind to :scope. `.dh-comp-scope { width }`
        # inside `@scope (.dh-comp-scope)` never matches the host, so the
        # drawing rendered as an empty white rectangle.
        self.assertIn(":scope{width:510px;background:#e8e4d8}", compact)
        self.assertNotIn(f".{bh.COMP_SCOPE_CLASS}{{width:510px", compact)

    def test_a_components_width_is_never_read_as_the_page_width(self):
        """B: a landing comp declared `.brand-mark{width:34px}` before any
        page size, so the preview scaled the whole page to a 34px artboard and
        the designer got a magnified corner of the logo instead of the page.
        A component width must not be mistaken for the page."""
        raw = ("<html><head><style>.brand-mark{width:34px}"
               ".site-nav{min-height:78px}"
               ".shell{width:min(1440px,100%)}</style></head>"
               "<body><p>x</p></body></html>")
        _, width, height = bh.html_comp_fragment(raw)
        self.assertEqual(width, 850.0)
        self.assertEqual(height, 1100.0)

    def test_a_page_level_rule_still_wins_at_any_size(self):
        """The floor guards the fallback only. A comp that deliberately sizes
        its page small on `body` keeps that size."""
        raw = ("<html><head><style>.chip{width:44px}"
               "body{width:300px;min-height:200px}</style></head>"
               "<body><p>x</p></body></html>")
        _, width, height = bh.html_comp_fragment(raw)
        self.assertEqual(width, 300.0)
        self.assertEqual(height, 200.0)

    def test_an_artboard_sized_wrapper_is_still_found_without_a_page_rule(self):
        """Comps that size a `.sheet` wrapper rather than `body` must keep
        working -- the floor only skips component-scale declarations."""
        raw = ("<html><head><style>.badge{width:28px}"
               ".sheet{width:816px;min-height:1056px}</style></head>"
               "<body><p>x</p></body></html>")
        _, width, height = bh.html_comp_fragment(raw)
        self.assertEqual(width, 816.0)
        self.assertEqual(height, 1056.0)

    def test_comp_logical_page_size_is_not_the_850_default(self):
        raw = ("<html><head><style>body{inline-size:510px;block-size:660px;"
               "background:#e8e4d8}</style></head><body><p>x</p></body></html>")
        _, width, height = bh.html_comp_fragment(raw)
        self.assertEqual(width, 510.0)
        self.assertEqual(height, 660.0)


if __name__ == "__main__":
    unittest.main()
