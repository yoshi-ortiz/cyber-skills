"""Tests for the article as a designer reads it.

Split out of `test_rounds.py`, which outgrew its directory's byte budget. These
check the emitted markup and stylesheet, never the source string: two of the
worst defects here were CSS the browser silently discarded while the source
looked correct.
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


class TheArticleAsRendered(unittest.TestCase):
    """Checks against the emitted markup. A rule that reads correctly in the
    source and is dropped by the CSS parser is the defect, not the source."""

    def article(self) -> str:
        decisions = live(("cover.spine", 2, "like", "proposed"),
                         ("cover.spine.remaches", 0, None, "proposed"),
                         ("type.brackets", 4, "like", "approved"))
        # Provenance is what the invisible table lays out, so the fixture has to
        # carry some -- without it the layout tests pass by rendering nothing.
        for entry in decisions["elements"]:
            entry["description"] = "pestana de archivador con paso por rol"
            entry["evidence"] = "cover.spine gusto a 2 estrellas, el dibujo no llegaba"
            entry["implemented"] = "se removieron los grupos opacity=0.13 y la barra de lomo"
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
            self.assertIn("data-el=", attrs)

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

    def test_provenance_lines_are_laid_out_as_one_invisible_table(self):
        """`PROPUESTO` and `IMPLEMENTADO` must share a label column.

        As independent flex rows each value began wherever its own label ended
        -- nine characters against twelve -- so the two values started at
        different x and their wrapped lines hung at different indents. The meta
        block is one grid: labels in a `max-content` column, values on a single
        edge, and every wrapped line inherits that edge because the value is a
        block-level grid cell rather than an inline run after the label.
        """
        markup = self.article()
        style = re.search(r"<style>/\* dh-controls \*/(.*?)</style>", markup, re.S).group(1)
        meta = re.search(r"\.dh-fb \.dh-meta\{([^}]*)\}", style)
        self.assertIsNotNone(meta, "the meta block lost its layout rule")
        self.assertIn("display:grid", meta.group(1),
                      "independent rows cannot share a label column")
        self.assertIn("max-content", meta.group(1),
                      "the label column must size to the longest label")
        sub = re.search(r"\.dh-fb \.dh-sub\{([^}]*)\}", style)
        self.assertIn("display:contents", sub.group(1),
                      "the sub-line must not generate a box, or its label and value "
                      "are trapped in a row of their own instead of joining the grid")

    def test_every_provenance_value_has_its_own_element(self):
        # A bare text node cannot be placed in a grid column. Without this the
        # value falls back to an anonymous item and the table silently un-aligns.
        markup = self.article()
        opened = markup.count('<span class="dh-desc dh-sub">')
        self.assertTrue(opened, "the article rendered no provenance lines")
        # Anchor on each opening tag and look at what immediately follows the
        # label. A loose `.*?` here matched across two sub-lines and let an
        # unwrapped value pass.
        wrapped = re.findall(r'<span class="dh-desc dh-sub"><b>[^<]*</b><span>', markup)
        self.assertEqual(len(wrapped), opened,
                         f"{opened - len(wrapped)} provenance value(s) are bare text nodes; "
                         "a text node cannot be placed in a grid column, so the table "
                         "silently un-aligns")

    def test_the_spacing_scale_is_declared_before_it_is_used(self):
        markup = self.article()
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>", markup, re.S).group(1)
        used = set(re.findall(r"var\((--s\d)\)", style))
        declared = set(re.findall(r"(--s\d):", style))
        self.assertTrue(used, "the article stopped using the spacing scale")
        self.assertLessEqual(used, declared,
                             "a var() with no declaration silently computes to 0")

class TheArticleSpeaksToADesigner(unittest.TestCase):
    """The reader is a graphic designer, not whoever built the harness.

    Every label here was rewritten to say what the reader must DO. These tests
    pin the words, because the page's whole job is to be understood by someone
    who has never seen the ledger.
    """

    def article(self, lang: str = "en") -> str:
        # One element per zone, or the empty zones never render and the test
        # passes by not looking at them.
        def entry(element, stars, sentiment, state="proposed", source="user"):
            return {"element": element, "stars": stars, "sentiment": sentiment,
                    "state": state, "scored": source == "user", "source": source}
        decisions = {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
                     "elements": [
                         entry("core.idea", 2, "like"),                      # fundamentals
                         entry("core.idea.redraw", 0, None, source="agent"),  # the round
                         entry("composition.grid", 2, "like"),                # on development
                         entry("voice.shouty", 1, "dislike")]}                # rejected
        with tempfile.TemporaryDirectory() as tmp:
            return bh.render_article(Path(tmp), decisions, {"core.idea.redraw"},
                                     "tab-por-color", lang, None, "Fichas",
                                     "Does the coloured tab beat the one you liked?")

    def test_the_hero_answers_who_what_which_project_and_what_now(self):
        markup = self.article()
        self.assertIn(">Cyber Yoshi: SKILLS<", markup)
        self.assertIn("<h1>Aesthetic ranking</h1>", markup)
        project = markup.split('class="dh-project">')[1].split("</p>")[0]
        self.assertIn("Project", project)
        self.assertIn("Fichas", project)
        designing = markup.split('class="dh-designing">')[1].split("</p>")[0]
        self.assertIn("Designing", designing)
        self.assertIn("tab-por-color", designing)

    def test_the_lede_tells_the_designer_what_to_do_next(self):
        # Scoring is half the job; going back to the chat is the other half,
        # and nothing else on the page says so.
        lede = self.article().split('class="dh-lede">')[1].split("</p>")[0]
        for phrase in ("score", "agent chat", "critique"):
            self.assertIn(phrase, lede.lower(), f"the lede must mention {phrase}")

    def test_the_zones_are_named_for_a_designer(self):
        markup = self.article()
        for heading in ("Design round", "Critical components",
                        "On development", "Rejected"):
            self.assertIn(f"<h2>{heading}</h2>", markup,
                          f"expected a section headed {heading!r}")
        self.assertNotIn("Antipatterns", markup)
        self.assertNotIn("Backlog", markup)

    def test_the_round_question_is_the_protagonist_not_a_footnote(self):
        markup = self.article()
        self.assertIn('class="dh-ask"', markup,
                      "the round's question must not be filed as a grey note")
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>", markup, re.S).group(1)
        rule = re.search(r"\.dh-ask\{([^}]*)\}", style).group(1)
        self.assertIn("clamp(", rule, "the question is set large")
        header = re.search(r'\.dh-zone\[data-zone="round"\] > header\{([^}]*)\}', style)
        self.assertIn("text-align:center", header.group(1))

    def test_counts_are_designs_not_elements(self):
        self.assertIn("designs</p>", self.article())

    def test_the_sticky_bar_names_the_page(self):
        self.assertIn('class="dh-toc-title">Aesthetic ranking', self.article())

    def test_group_headings_carry_two_different_ranks(self):
        # In the critical components the group IS the subject and reads big; in
        # the development backlog it is a folder label and stays small.
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.article(), re.S).group(1)
        big = re.search(r'\.dh-zone\[data-zone="fundamentals"\] \.dh-group\{([^}]*)\}', style)
        small = re.search(r'\.dh-zone\[data-zone="backlog"\] \.dh-group\{([^}]*)\}', style)
        self.assertIsNotNone(big, "critical-component groups lost their big heading")
        self.assertIsNotNone(small, "development groups lost their small heading")
        self.assertIn("clamp(", big.group(1))
        self.assertIn("font-size:13px", small.group(1))

    def test_the_confirmation_fires_on_the_ledger_not_on_the_click(self):
        """"Preference saved" must mean the ledger agreed.

        Flashing it on mousedown would promise something the companion has not
        recorded -- and a dropped socket is exactly when the user most needs to
        know their score did not save.
        """
        markup = self.article()
        self.assertIn('data-saved="Preference saved"', markup,
                      "the confirmation string must reach the page; the article "
                      "strips the controls wrapper, so it rides on the article root")
        script = re.search(r"<script>/\* dh-rehydrate \*/(.*?)</script>", markup, re.S).group(1)
        self.assertIn("function flashSaved", script)
        paint = script.split("function paint(row,s,live){", 1)[1][:120]
        self.assertIn("if(live)flashSaved(row)", paint,
                      "the confirmation must be raised by paint(), and only for a live "
                      "signal -- `dh-state` is the bootstrap the server sends on connect, "
                      "so flashing on it announced every row as saved on every page load")
        self.assertIn("applyState(one,true)", script,
                      "a real user signal is the only thing that flashes")
        # and never from a raw click handler
        for handler in re.findall(r"addEventListener\('click'.*?\n", script):
            self.assertNotIn("flashSaved", handler)

    def test_every_language_defines_the_new_keys(self):
        for key in ("brand", "project-label", "designing", "saved",
                    "designs", "round-heading"):
            for lang, words in bh.STRINGS.items():
                self.assertIn(key, words, f"{lang} is missing {key!r}")

    def test_spanish_renders_the_same_structure(self):
        markup = self.article("es")
        self.assertIn("<h1>Aesthetic ranking</h1>", markup)   # product name, untranslated
        self.assertIn("<h2>Ronda de diseño</h2>", markup)
        self.assertIn("<h2>Componentes críticos</h2>", markup)
        self.assertIn('data-saved="Preferencia guardada"', markup)

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

    def test_the_id_is_still_emitted_as_a_tag(self):
        # It stays the ledger's key and the thing to quote back to the agent.
        markup = bh.render_feedback_controls(
            {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
             "elements": [{"element": "cover.object", "stars": 2, "sentiment": None,
                           "state": "proposed", "scored": True, "source": "user",
                           "description": "un objeto grande"}]},
            None, None, None, "es")
        self.assertIn('<code class="dh-token">cover.object</code>', markup)
        self.assertIn('class="dh-id">Un objeto grande<', markup)

class TheArticleFitsItsContainer(unittest.TestCase):
    """The same row renders in a 1180px article and in a companion pane a third
    that wide, so the layout responds to its CONTAINER, not to the viewport."""

    def style(self) -> str:
        markup = bh.render_article(
            Path("/tmp"), {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
                           "elements": [{"element": "core.idea", "stars": 2,
                                         "sentiment": "like", "state": "proposed",
                                         "scored": True, "source": "user"}]},
            set(), "", "en", None, "Fichas", "Ask.")
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

class TheSkillIsInvokedWithFourVerbs(unittest.TestCase):
    def test_the_argument_hint_matches_the_documented_verbs(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('argument-hint: "continue | critique | prototype | observe @/art-folder"',
                      skill)
        for verb in ("continue", "critique", "prototype", "observe"):
            self.assertIn(f"- **{verb}", skill,
                          f"{verb} is advertised but never documented")
        self.assertNotIn("interpret @", skill,
                         "an old `interpret @` invocation survived in SKILL.md")

class TheSlideshowPutsTheZeroWithTheRanks(unittest.TestCase):
    def test_zero_sits_in_the_star_row_not_the_verdict_row(self):
        # A zero is a rank. In the verdict row it read as a fourth verdict.
        markup = bh.render_article(
            Path("/tmp"), {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
                           "elements": [{"element": "core.idea", "stars": 2, "sentiment": None,
                                         "state": "proposed", "scored": True, "source": "user"}]},
            set(), "", "en", None, "F", "Ask.")
        script = re.search(r"<script>/\* dh-lightbox \*/(.*?)</script>", markup, re.S).group(1)
        stars_block = script.split("dh-lb-acts")[0]
        self.assertIn("dh-lb-zero", stars_block,
                      "the zero must be emitted with the stars")
        self.assertNotIn('data-rank="0"', script.split("dh-lb-acts")[1],
                         "the zero must not also sit in the verdict row")


class TheSlideshowHeadsItselfWithAName(unittest.TestCase):
    """It headed itself with the dotted id while the card beside it already
    used a real name. Same rule in both places: read the row's own title."""

    def script(self) -> str:
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")),
            set(), "", "en", None, "F", "Ask.")
        return re.search(r"<script>/\* dh-lightbox \*/(.*?)</script>", markup, re.S).group(1)

    def test_the_header_reads_the_rows_title_not_the_id(self):
        body = self.script()
        self.assertIn(".dh-id", body,
                      "the slideshow must take its heading from the row's name")
        self.assertIn("dh-lb-token", body,
                      "the id still ships, demoted under the name")


class DoneLooksLikeDone(unittest.TestCase):
    def markup(self) -> str:
        return bh.render_article(
            Path("/tmp"), live(("core.idea", 5, "like", "completed"),
                               ("core.other", 2, "like", "approved")),
            set(), "", "en", None, "F", "Ask.")

    def test_the_finish_flag_is_a_glyph_not_a_hex_escape(self):
        # This file learned it once already: a CSS hex escape came back out of
        # the browser as literal text. It did it again -- `\1F3C1` computed to
        # "\1 F3C1" and drew that string instead of a flag.
        style = re.search(r"<style>/\* dh-controls \*/(.*?)</style>",
                          self.markup(), re.S).group(1)
        rule = re.search(r"\[data-verdict\]\.on > span::after\{([^}]*)\}", style)
        self.assertIsNotNone(rule, "completed lost its finish flag")
        self.assertIn("\U0001F3C1", rule.group(1))
        self.assertNotIn("\\1F3C1", rule.group(1))

    def test_the_companions_brand_bar_is_hidden(self):
        # The companion draws its own brand above our page; the credit already
        # sits in our footer, so the bar is a second louder copy. Hidden from
        # here because patching another skill's server gets overwritten.
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.markup(), re.S).group(1)
        self.assertRegex(style, r"\.brand\{display:none\}")

    def test_only_completed_work_reads_as_finished(self):
        # A thumb up is not a finish. `approved` said "approved", which read as
        # done to anyone who had merely liked something.
        markup = self.markup()
        labels = re.findall(r'<span class="dh-state">([^<]*)</span>', markup)
        self.assertIn("completed", labels)
        self.assertIn("on shape", labels)
        self.assertNotIn("approved", labels)


class TheSlideshowFitsItsCell(unittest.TestCase):
    def test_the_drawing_is_bounded_on_both_axes(self):
        """`block-size:100%` alone let the height grow while the width clamped,
        so a tall window stretched the page to a 0.28 aspect. Measured: 1238px
        of drawing inside a 540px frame, hanging off both edges."""
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")),
            set(), "", "en", None, "F", "Ask.")
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>", markup, re.S).group(1)
        rule = re.search(r"\.dh-lb-art \.dh-shot\{([^}]*)\}", style).group(1)
        self.assertIn("100cqh", rule, "height must be capped by the cell")
        self.assertIn("100cqw", rule, "and by the height its width allows")
        self.assertNotIn("vh", rule, "never size the drawing off the viewport")
        art = re.search(r"\.dh-lb-art\{([^}]*)\}", style).group(1)
        self.assertIn("container-type:size", art,
                      "container units need the cell declared as the container")


class TheTextOutranksTheControls(unittest.TestCase):
    def test_the_controls_wrap_before_the_text_loses_its_measure(self):
        """The strip is 360px of fixed touch targets and was winning the space
        fight: at an 802px row the description got 282px and its provenance
        column 196px, so it wrapped every four words. The breakpoint has to ask
        "does the text still have a measure?", not "is the row narrow?" -- 96px
        of thumbnail plus 360px of controls leaves under 30ch until ~980px."""
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")),
            set(), "", "en", None, "F", "Ask.")
        style = re.search(r"<style>/\* dh-controls \*/(.*?)</style>", markup, re.S).group(1)
        widths = [int(w) for w in re.findall(
            r"@container dh-row \(max-width: (\d+)px\)", style)]
        self.assertTrue(widths, "the row lost its container queries")
        self.assertGreaterEqual(
            max(widths), 900,
            "the controls must drop to their own row well before the text is "
            f"crushed; widest breakpoint is only {max(widths)}px")


class TheBarReportsTheAgent(unittest.TestCase):
    def test_idle_is_a_state_not_an_absence(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")),
            set(), "", "en", None, "F", "Ask.")
        self.assertIn('data-state="idle"', markup)
        working = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")),
            set(), "", "en", None, "F", "Ask.", "Redrawing the cover")
        self.assertIn('data-state="working"', working)
        self.assertIn("Redrawing the cover", working)

    def test_the_bar_does_not_report_a_todo_count(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")),
            set(), "", "en", None, "F", "Ask.")
        bar = markup.split('class="dh-bar"')[1].split("</aside>")[0]
        self.assertNotIn("left to score", bar,
                         "the bar reports the agent, not a to-do tally")


class TheStickyBarReadsTopDown(unittest.TestCase):
    def test_title_then_legend_then_chart_then_sections(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")),
            set(), "", "en", None, "F", "Ask.")
        nav = markup.split('class="dh-toc"')[1].split("</nav>")[0]
        order = [nav.index(x) for x in
                 ('dh-toc-title', 'dh-key', 'dh-temp', '<ol>')]
        self.assertEqual(order, sorted(order),
                         "legend belongs above the chart it explains, and the "
                         "chart above the sections it indexes")


if __name__ == "__main__":
    unittest.main()
