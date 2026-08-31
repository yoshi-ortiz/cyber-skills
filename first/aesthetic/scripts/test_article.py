"""Tests for the article as a designer reads it.

Split out of `test_rounds.py`, which outgrew its directory's byte budget. These
check the emitted markup and stylesheet, never the source string: two of the
worst defects here were CSS the browser silently discarded while the source
looked correct.
"""
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bootstrap_harness as bh


def live(*rows: tuple) -> dict:
    """A ledger from (element, stars, sentiment, state) tuples."""
    return {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
            "elements": [{"element": e, "stars": s, "sentiment": m, "state": st,
                          "scored": True, "source": "user"}
                         for e, s, m, st in rows]}


class ARoundMustFitInOneSitting(unittest.TestCase):
    """`render_article` refuses an oversized cohort itself, not only the CLI
    path -- so the gate fires for every caller, including a direct call like
    this test's, not just `bootstrap_harness.py article`."""

    def test_render_article_refuses_a_cohort_past_the_limit(self):
        rows = [(f"e{i}", 0, None, "proposed") for i in range(bh.MAX_COHORT_SIZE + 1)]
        decisions = live(*rows)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bh.HarnessError) as caught:
                bh.render_article(Path(tmp), decisions, {row[0] for row in rows},
                                  cohort_name="too-big", language="en", title="Fichas",
                                  asks="Which reads best?")
        self.assertIn(str(bh.MAX_COHORT_SIZE + 1), str(caught.exception))


class TheChartCountsIdeasNotAttempts(unittest.TestCase):
    """The sticky strip drew one bar per element, and a superseded element is
    still `live` for the strip's purposes -- so every redraw kept its own bar
    forever. A ledger of eight ideas drawn four times each read as thirty-two
    separate concerns, and the chart grew without bound.

    The round zone has grouped variants under their incumbent since it was
    written. These check the same grouping now reaches the strip.
    """

    def strip(self, decisions: dict, cohort: set[str] | None = None) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            markup = bh.render_article(Path(tmp), decisions, cohort or set())
        return markup.split("dh-temp dh-temp-sticky")[1].split("</div>")[0]

    def bars(self, decisions: dict, cohort: set[str] | None = None) -> list[str]:
        return re.findall(r'data-el="([^"]+)"', self.strip(decisions, cohort))

    def test_a_supersede_chain_draws_one_bar(self):
        decisions = live(("cover.ring", 1, None, "superseded"),
                         ("cover.ring.v2", 2, None, "superseded"),
                         ("cover.ring.v2.v3", 4, None, "proposed"),
                         ("palette.warm", 3, None, "approved"))
        self.assertEqual(self.bars(decisions),
                         ["cover.ring.v2.v3", "palette.warm"])

    def test_the_standing_drawing_speaks_for_its_lineage(self):
        # Not the ancestor, and not the best-scoring retired attempt: the one
        # that still stands is what the strip must report.
        decisions = live(("cover.ring", 5, None, "superseded"),
                         ("cover.ring.v2", 1, None, "proposed"))
        strip = self.strip(decisions)
        self.assertIn('data-el="cover.ring.v2"', strip)
        self.assertNotIn('data-el="cover.ring"', strip)

    def test_the_bar_carries_how_many_attempts_it_stands_for(self):
        decisions = live(("cover.ring", 1, None, "superseded"),
                         ("cover.ring.v2", 2, None, "superseded"),
                         ("cover.ring.v2.v3", 4, None, "proposed"))
        self.assertIn('data-variants="3"', self.strip(decisions))

    def test_an_idea_drawn_once_carries_no_variant_count(self):
        decisions = live(("palette.warm", 3, None, "approved"))
        self.assertNotIn("data-variants", self.strip(decisions))

    def test_unrelated_ideas_keep_their_own_bars(self):
        decisions = live(("cover.ring", 3, None, "approved"),
                         ("palette.warm", 3, None, "approved"),
                         ("type.display", 3, None, "approved"))
        self.assertEqual(len(self.bars(decisions)), 3)

    def test_this_rounds_ask_speaks_for_its_own_lineage(self):
        # The asked element carries the `?` and the outline. Collapsing it
        # behind an ancestor would hide the one thing being asked about.
        decisions = live(("cover.ring", 5, None, "approved"),
                         ("cover.ring.v2", 0, None, "proposed"))
        strip = self.strip(decisions, {"cover.ring.v2"})
        self.assertIn('data-el="cover.ring.v2"', strip)
        self.assertIn("data-asked", strip)

    def test_the_ledger_is_not_rewritten_by_the_grouping(self):
        # A rendering change must not retire anything. Every element the ledger
        # carried before is still there afterwards, in the same state.
        decisions = live(("cover.ring", 1, None, "superseded"),
                         ("cover.ring.v2", 4, None, "proposed"))
        before = [(e["element"], e["state"]) for e in decisions["elements"]]
        self.strip(decisions)
        after = [(e["element"], e["state"]) for e in decisions["elements"]]
        self.assertEqual(before, after)


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
                                     cohort_name="lomo", language="es", title="Fichas",
                                     asks="Remaches.")

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
        shots = re.findall(r'<div class="dh-shot"([^>]*)>', markup)
        self.assertTrue(shots, "the article rendered no thumbnails at all")
        for attrs in shots:
            self.assertIn("data-el=", attrs,
                          "a thumbnail with no data-el cannot open its slide")

    def test_a_round_cannot_repeat_one_drawing_under_two_names(self):
        decisions = live(("cover.object.first", 0, None, "proposed"),
                         ("cover.object.second", 0, None, "proposed"))
        for entry in decisions["elements"]:
            entry["preview"] = {"path": f"content/{entry['element']}.html",
                                "sha256": "the-same-rendered-drawing"}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bh.HarnessError) as caught:
                bh.render_article(Path(tmp), decisions,
                                  {"cover.object.first", "cover.object.second"},
                                  cohort_name="object", language="en",
                                  asks="Which drawing works better?")
        self.assertIn("same drawing", str(caught.exception).lower())

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
        # Scoped to .dh-swatches specifically -- a later, unrelated
        # `auto-fit,minmax(...)` grid elsewhere in the sheet (e.g. the
        # idea-variant strip) must not be what this regex happens to match.
        swatches = re.search(r"\.dh-swatches\{.*?\}", style, re.S)
        self.assertIsNotNone(swatches, "the .dh-swatches rule went missing")
        floor = re.search(r"repeat\(auto-fit,\s*minmax\((\d+)px", swatches.group(0))
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

    def test_no_provenance_sub_lines_reach_the_reader(self):
        # Provenance is bookkeeping. It stays in the ledger; the card carries
        # the design, not a trace of who proposed it and when.
        self.assertNotIn('<span class="dh-desc dh-sub">', self.article())

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
                                     cohort_name="tab-por-color", language=lang,
                                     title="Fichas",
                                     asks="Does the coloured tab beat the one you liked?")

    def test_the_hero_answers_who_what_which_project_and_what_now(self):
        markup = self.article()
        # "Cyber Yoshi: SKILLS" brands the COMPANION one level up;
        # the article's eyebrow names who is asking for the ranks.
        self.assertIn(">Design Agent<", markup)
        self.assertIn("<h1>Aesthetic ranking</h1>", markup)
        meta = markup.split('class="dh-hero-meta">')[1].split("</div>")[0]
        self.assertIn("Project", meta)
        self.assertIn("Fichas", meta)
        self.assertIn("Designing", meta)
        self.assertIn("tab-por-color", meta)

    def test_designing_uses_the_same_label_style_as_project(self):
        """Project and designing are both key/value rows — same pill label, same weight."""
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>",
                          self.article(), re.S).group(1)
        self.assertNotIn("dh-designing-label", style)
        self.assertNotIn("dh-designing-value", style)
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="round-slug", language="en", title="Fichas", asks="Ask.",
            round_label="Posiciones de página")
        meta = markup.split('class="dh-hero-meta">')[1].split("</div>")[0]
        self.assertIn("Posiciones de página", meta)
        self.assertNotIn("round-slug", meta)

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


class TheCompanionHeaderIsTwoByTwo(unittest.TestCase):
    def test_the_brand_shows_cyber_yoshi_agent_and_connection(self):
        frame = (Path(__file__).parents[1] / "companion" / "frame-template.html").read_text(
            encoding="utf-8")
        style = re.search(r"<style>(.*?)</style>", frame, re.S).group(1)
        self.assertIn("grid-template-columns", style)
        self.assertIn(".dh-brand", style)
        self.assertIn("dh-brand-kind", style)
        self.assertIn("text-transform: uppercase", style)
        self.assertIn("M4 6h16v9H4V6zm-2 11h20v2H2v-2z", style)
        self.assertIn("CYBER YOSHI: SKILLS", frame)
        self.assertIn("dh-brand-left", frame)
        self.assertIn("dh-brand-right", frame)
        self.assertIn("Agent companion", frame)
        self.assertIn('target="_blank"', frame)


class TheSkillKeepsTheUserInformed(unittest.TestCase):
    def test_editorial_output_uses_checked_review_images(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("desktop and narrow widths", skill)
        self.assertIn("review_delivery.py", skill)
        self.assertIn("absolute `image_path`", skill)
        self.assertIn("URL, key, and project-language review request", skill)

    def test_first_reply_gives_the_page_and_key_before_any_status(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        section = skill.split("## Start", 1)[1].split("## Read the user", 1)[0]
        self.assertLess(section.index("🔗 <full URL>"), section.index("👀 <project-language"))
        self.assertLess(section.index("🔑 <value after ?key=>"), section.index("👀 <project-language"))
        self.assertIn("no preamble", section)

    def test_live_status_spans_the_real_run(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        start = skill.split("## Start", 1)[1].split("## Read the user", 1)[0]
        publish = skill.split("## Publish the established article", 1)[1].split(
            "## Continue and critique", 1)[0]
        self.assertIn('--status "<emoji + project-language', start)
        self.assertIn("activity changes", skill)
        self.assertIn("status --project-root . --idle", publish)

    def test_plain_language_contract_is_loaded_before_the_first_update(self):
        root = Path(__file__).resolve().parent.parent
        skill = (root / "SKILL.md").read_text(encoding="utf-8")
        contract = (root / "references" / "user-communication.md").read_text(encoding="utf-8")
        self.assertIn("Read [user-communication.md]", skill)
        for jargon in ("harness", "corpus", "cohort", "ledger", "critical epic", "burndown"):
            self.assertIn(f"| {jargon} |", contract)
        self.assertIn("project language", contract)
        self.assertIn("keep the last\nranking page available", contract)


class TheSkillIsInvokedWithEditorialVerbs(unittest.TestCase):
    def test_context_clues_are_documented(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        for verb in ("observe", "continue", "critique"):
            self.assertIn(f"`{verb}`", skill, f"{verb} is advertised but never documented")
        self.assertNotIn("interpret @", skill,
                         "an old `interpret @` invocation survived in SKILL.md")

    def test_the_slash_description_reads_like_the_arguments(self):
        """The description is what slash-command search shows. Four continue
        sessions opened by dumping harness jargon because this line taught
        'evidence-backed design harness' instead of the verbs the hint lists."""
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        desc = re.search(r"^description:\s*(.*)$", skill, re.M).group(1).lower()
        for jargon in ("harness", "ledger", "knowledge-index",
                       "spec/design-harness", "evidence-backed"):
            self.assertNotIn(jargon, desc, f"slash search still says {jargon!r}")
        for verb in ("continue", "critique"):
            self.assertIn(verb, desc)
        self.assertIn("multimodal corpus", desc)
        self.assertIn("editorial burndown", desc)
        self.assertIn("user sentiment", desc)

    def test_scope_events_are_append_only_and_idempotent(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        section = skill.split("## Scope the editorial burndown", 1)[1].split("## Build", 1)[0]
        self.assertIn("append", section)
        self.assertIn("no-op", section)

    def test_observe_is_the_first_compiler_command(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        body = skill.split("---", 2)[2]
        compiler = re.search(r"editorial_workflow\.py ([a-z-]+)", body)
        self.assertIsNotNone(compiler)
        self.assertEqual(compiler.group(1), "observe")

    def test_the_always_loaded_file_uses_the_established_article(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("`doctor`", skill)
        self.assertNotIn("`stats`", skill)
        self.assertIn("bootstrap_harness.py article --project-root", skill)
        self.assertNotIn("editorial-board.html", skill)


class OpenPutsTheUrlInChat(unittest.TestCase):
    def board(self, tmp: str, url: str = "http://localhost:49830/?key=abc") -> Path:
        root = Path(tmp)
        session = root / ".superpowers" / "brainstorm" / "s1"
        (session / "state").mkdir(parents=True)
        (session / "content").mkdir()
        (session / "state" / "server-info").write_text(
            json.dumps({"type": "server-started", "url": url, "port": 49830}),
            encoding="utf-8")
        return root

    def test_a_standing_board_yields_only_the_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            url = "http://localhost:49830/?key=abc"
            root = self.board(tmp, url)
            self.assertEqual(bh.read_board_url(root), url)

    def test_open_prints_only_the_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            url = "http://localhost:49830/?key=abc"
            root = self.board(tmp, url)
            with patch.object(bh, "board_is_up", return_value=True), \
                 patch.object(bh, "start_companion") as start:
                got = bh.open_board(root)
            start.assert_not_called()
            self.assertEqual(got, url)
            for word in ("ok", "FAIL", "standing", "polish", "doctor", "ledger"):
                self.assertNotIn(word, got)

    def test_open_starts_when_the_board_is_down(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.board(tmp)
            fresh = "http://localhost:49830/?key=fresh"
            with patch.object(bh, "board_is_up", return_value=False), \
                 patch.object(bh, "start_companion", return_value=fresh) as start:
                got = bh.open_board(root)
            start.assert_called_once()
            self.assertEqual(got, fresh)

    def test_open_is_a_verb(self):
        args = bh.parser().parse_args(["open", "--project-root", "."])
        self.assertEqual(args.command, "open")


class TheBottomBarShowsWhatTheAgentIsDoing(unittest.TestCase):
    def markup(self, working: bool = False) -> str:
        return bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.", agent_working=working)

    def test_the_page_carries_no_baked_status(self):
        # The companion frame owns the agent's status. The article is a
        # document, and a status baked at publish time is stale on arrival --
        # so `render_article` no longer accepts one to bake.
        markup = self.markup(working=True)
        self.assertNotIn('class="dh-live"', markup)
        self.assertIn('data-agent-state="active"', markup)

    def test_the_footer_credits_inspiration_not_power(self):
        markup = self.markup()
        self.assertIn("Inspired from Jesse Vincent", markup)
        self.assertNotIn("Powered by Jesse Vincent", markup)


class DoctorCanStayQuiet(unittest.TestCase):
    def test_quiet_swallows_ok_lines(self):
        import companion_doctor as doctor
        self.assertEqual(doctor.line_for("ok", "server answering", quiet=True), "")
        self.assertIn("FAIL", doctor.line_for("fail", "server down", quiet=True))
        self.assertIn("ok", doctor.line_for("ok", "server answering", quiet=False))

class TheSlideshowPutsTheZeroWithTheRanks(unittest.TestCase):
    def test_the_slideshow_clones_row_signals_instead_of_rebuilding_stars(self):
        markup = bh.render_article(
            Path("/tmp"),
            {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
                           "elements": [{"element": "core.idea", "stars": 2, "sentiment": None,
                                         "state": "proposed", "scored": True, "source": "user"}]},
            set(), cohort_name="", language="en", title="F", asks="Ask.")
        script = re.search(r"<script>/\* dh-lightbox \*/(.*?)</script>", markup, re.S).group(1)
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>", markup, re.S).group(1)
        self.assertIn("cloneSignals", script,
                      "the lightbox must clone the row's .dh-signals strip")
        self.assertIn("dh-lb-fb", script,
                      "cloned strips need a .dh-fb shell so scoring CSS applies")
        self.assertNotIn("dh-lb-zero", script,
                         "rebuilt stars drift from the card; clone the row instead")
        self.assertIn(".dh-zone[data-zone]", script,
                      "slideshow navigation must stay inside the row's zone")
        self.assertIn("fitShotInner", script,
                      "HTML comps must be re-scaled in the slideshow cell")
        self.assertIn("createElement('dialog')", script,
                      "the slideshow must use a native dialog for escape and focus")
        opener = script.split("function open")[1]
        self.assertLess(opener.index("showModal();"), opener.index("paint();"),
                        "fit the drawing after the dialog is open, not while it is display:none")
        self.assertIn("dh-lb-shell", script,
                      "slideshow must wrap content so outside clicks can dismiss it")
        self.assertIn("!e.target.closest('.dh-lb-shell')", script,
                      "clicking outside the shell must close the slideshow")
        self.assertIn("dh-lb-foot", script,
                      "scores belong in a footer row, not a side column")
        self.assertIn("dialog.dh-lb .dh-lb-score", style,
                      "slideshow scores must inherit the dark overlay palette")
        self.assertNotIn(".dh-bar", style,
                         "persistent companion status must not cover the review")
        self.assertRegex(style, r"block-size:min\(\d+px,calc\(100dvh - 32px\)\)",
                         "the shell needs a definite height so the drawing cell can size")
        self.assertIn("justify-content:center", style)


class CardThumbnailsScaleOnLoad(unittest.TestCase):
    def test_html_comps_get_a_shot_fit_script_before_the_lightbox(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
        self.assertIn("/* dh-shot-fit */", markup,
                      "card thumbnails need the same scale math as the slideshow")
        fit = markup.index("/* dh-shot-fit */")
        lb = markup.index("/* dh-lightbox */")
        self.assertLess(fit, lb,
                        "shot-fit must run before the lightbox so __dhFitShotInner exists")
        self.assertIn("__dhFitShotInner", markup)
        self.assertIn("ResizeObserver", markup)


class TheSlideshowHeadsItselfWithAName(unittest.TestCase):
    """It headed itself with the dotted id while the card beside it already
    used a real name. Same rule in both places: read the row's own title."""

    def script(self) -> str:
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
        return re.search(r"<script>/\* dh-lightbox \*/(.*?)</script>", markup, re.S).group(1)

    def test_the_header_reads_the_rows_title_not_the_id(self):
        body = self.script()
        self.assertIn(".dh-id", body,
                      "the slideshow must take its heading from the row's name")
        self.assertNotIn("dh-lb-token", body,
                         "machine ids remain bindings, not visible review copy")


class DoneLooksLikeDone(unittest.TestCase):
    def markup(self) -> str:
        return bh.render_article(
            Path("/tmp"),
            live(("core.idea", 5, "like", "completed"),
                               ("core.other", 2, "like", "approved")),
            set(), cohort_name="", language="en", title="F", asks="Ask.")

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

    def test_the_companion_frame_owns_the_brand(self):
        markup = self.markup()
        frame = (Path(__file__).parents[1] / "companion" / "frame-template.html").read_text(
            encoding="utf-8")
        self.assertNotIn("/* dh-brand */", markup)
        self.assertIn("CYBER YOSHI: SKILLS", frame)
        self.assertIn("data-agent-link", frame)
        self.assertIn("data-connection-text", frame)

    def test_the_agent_link_is_omitted_rather_than_invented(self):
        helper = (Path(__file__).parents[1] / "companion" / "helper.js").read_text(
            encoding="utf-8")
        self.assertIn("link.removeAttribute('href')", helper)
        self.assertNotIn("cursor://", helper)

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
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
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


class TheStableCompanionBoundary(unittest.TestCase):
    def test_idle_is_a_state_not_an_absence(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
        self.assertIn('data-agent-state="idle"', markup)
        working = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.", agent_working=True)
        self.assertIn('data-agent-state="active"', working)

    def test_the_agent_name_carries_no_dot(self):
        """Two dots on the right side of the header, reading different things,
        was the ambiguity the name row was meant to remove. The connection
        pill already has one."""
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
        style = re.search(r"<style>/\* dh-article \*/(.*?)</style>", markup, re.S).group(1)
        self.assertNotIn(".dh-brand-agent::before", style)
        self.assertNotIn(".dh-brand-agent[data-state", style)

    def test_status_is_metadata_for_the_stable_frame_not_a_floating_panel(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
        self.assertIn('data-agent-state="idle"', markup)
        self.assertNotIn('class="dh-bar"', markup)
        self.assertNotIn('data-theme-settings', markup)

    def test_project_theme_cannot_restyle_the_review_surface(self):
        markup = bh.render_article(
            Path("/tmp"), live(("core.idea", 2, "like", "proposed")), set(),
            cohort_name="", language="en", title="F", asks="Ask.")
        root = markup.split('class="dh-art"', 1)[1].split('>', 1)[0]
        self.assertNotIn("style=", root)
        self.assertNotIn("Silkscreen", root)

    def test_machine_provenance_stays_out_of_visible_review_copy(self):
        decisions = live(("core.idea", 2, "like", "proposed"))
        decisions["elements"][0].update({
            "description": "Try the quieter hierarchy.",
            "evidence": 'USER: "RANKED"; previous focus: internal trace',
            "implemented": "DOM implementation claim",
        })
        markup = bh.render_article(Path("/tmp"), decisions, {"core.idea"}, cohort_name="",
                                   language="en", title="F", asks="Ask.")
        self.assertIn('data-element="core.idea"', markup)
        self.assertIn("Try the quieter hierarchy.", markup)
        self.assertNotIn('USER: "RANKED"', markup)
        self.assertNotIn("DOM implementation claim", markup)
        self.assertNotIn('<code class="dh-token">core.idea</code>', markup)


class PreviewsUseTheRecordedCanonicalAsset(unittest.TestCase):
    """Recording chooses the comp; rendering never swaps identities."""

    def test_preferred_preview_path_picks_content_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shots = root / "shots"
            shots.mkdir(parents=True)
            content = root / "content"
            content.mkdir()
            png = shots / "pages.inventory.archivador.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n")
            html = content / "pages.inventory.archivador.html"
            html.write_text("<html><body><p>comp</p></body></html>", encoding="utf-8")
            chosen = bh.preferred_preview_path(root, png, "pages.inventory.archivador")
            self.assertEqual(chosen, html)

    def test_render_preview_does_not_silently_replace_the_recorded_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shots = root / "shots"
            shots.mkdir(parents=True)
            content = root / "content"
            content.mkdir()
            png = shots / "x.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n")
            html = content / "x.html"
            html.write_text("<style>.c{color:red}</style><div class='c'>Hi</div>",
                            encoding="utf-8")
            preview = {"path": png.relative_to(root).as_posix(), "sha256": "abc"}
            out = bh.render_preview(root, preview, "x", bh.STRINGS["en"])
            self.assertNotIn("Hi", out)
            self.assertIn("data:image/png;base64", out)

    def test_old_png_records_are_migrated_before_the_article_is_rendered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "spec" / "design-harness"
            output.mkdir(parents=True)
            (root / "shots").mkdir()
            (root / "content").mkdir()
            png = root / "shots" / "x.png"
            png.write_bytes(b"old rendered artifact")
            html = root / "content" / "x.html"
            html.write_text("<html><body>canonical drawing</body></html>", encoding="utf-8")
            decisions = live(("x", 0, None, "proposed"))
            decisions["elements"][0]["evidence"] = "user asked to compare this drawing"
            decisions["elements"][0]["preview"] = {
                "path": "shots/x.png", "sha256": bh.sha256_file(png)}
            bh.write_json(output / "decisions.json", decisions)

            changed = bh.canonicalize_recorded_previews(root, decisions)

            self.assertEqual(changed, 1)
            stored = json.loads((output / "decisions.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["elements"][0]["preview"]["path"], "content/x.html")
            self.assertEqual(stored["elements"][0]["preview"]["sha256"], bh.sha256_file(html))

    def test_html_comp_preview_uses_div_not_span(self):
        raw = ("<html><head><style>body{width:510px;min-height:660px;background:#f00}"
               "p{color:blue}</style></head><body><p>Hi</p></body></html>")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comp = root / "content" / "demo.html"
            comp.parent.mkdir(parents=True)
            comp.write_text(raw, encoding="utf-8")
            out = bh.render_preview(root, {"path": "content/demo.html", "sha256": "x"},
                                    "demo", bh.STRINGS["en"])
            self.assertIn('<div class="dh-shot"', out)
            self.assertIn('<div class="dh-shot-inner"', out)
            self.assertNotIn('<span class="dh-shot-inner"', out)
            self.assertIn('data-comp-w="510.0"', out)
            self.assertIn('data-comp-h="660.0"', out)

    def test_comp_css_is_scoped_and_cannot_shrink_the_frame_body(self):
        raw = ("<html><head><style>body{width:510px;min-height:660px;background:#f00}"
               "p{color:blue}</style></head><body><p>Hi</p></body></html>")
        frag, width, _ = bh.html_comp_fragment(raw)
        self.assertEqual(width, 510.0)
        self.assertIn(bh.COMP_SCOPE_CLASS, frag)
        self.assertNotRegex(frag, r"(?<![\w-])body\s*\{")
        self.assertIn("Hi", frag)

    def test_comp_css_scope_is_unique_per_element_not_shared_globally(self):
        """Two comps sharing a class name (`.title` is a common convention)
        must not let one comp's rule win inside the other comp once both are
        embedded on the same page -- `@scope (.dh-comp-scope)` alone matches
        every comp's wrapper, so a later comp's `.title{font-size:28px}`
        silently overrode an earlier comp's `.title{font-size:16px}`."""
        raw_a = ("<html><head><style>body{inline-size:510px;block-size:660px}"
                  ".title{font-size:16px}</style></head><body><p class='title'>A</p></body></html>")
        raw_b = ("<html><head><style>body{inline-size:510px;block-size:660px}"
                  ".title{font-size:28px}</style></head><body><p class='title'>B</p></body></html>")
        frag_a, _, _ = bh.html_comp_fragment(raw_a, "comp.a")
        frag_b, _, _ = bh.html_comp_fragment(raw_b, "comp.b")
        scope_a = f"{bh.COMP_SCOPE_CLASS}-{bh.comp_scope_id('comp.a')}"
        scope_b = f"{bh.COMP_SCOPE_CLASS}-{bh.comp_scope_id('comp.b')}"
        self.assertNotEqual(scope_a, scope_b)
        self.assertIn(scope_a, frag_a)
        self.assertIn(scope_b, frag_b)
        self.assertIn(f"@scope (.{scope_a})", frag_a)
        self.assertIn(f"@scope (.{scope_b})", frag_b)
        # Neither fragment's <style> block references the OTHER comp's scope
        # class, which is what let their `.title` rules collide site-wide.
        self.assertNotIn(scope_b, frag_a.split("</style>")[0])
        self.assertNotIn(scope_a, frag_b.split("</style>")[0])

    def test_multiple_redraws_of_one_incumbent_render_grouped_not_repeated(self):
        """Two or more variants of ONE idea share a single "before" card
        instead of each getting its own standalone before/after block --
        that's the whole point of allowing more than one redraw per round
        (see MAX_VARIANTS_PER_IDEA)."""
        decisions = live(("art.trama", 2, "like", "proposed"),
                         ("art.trama.limpia", 0, None, "proposed"),
                         ("art.trama.real", 0, None, "proposed"))
        with tempfile.TemporaryDirectory() as tmp:
            markup = bh.render_article(
                Path(tmp), decisions, {"art.trama.limpia", "art.trama.real"},
                cohort_name="trama", language="en", title="T", asks="Which reads better?")
        self.assertEqual(markup.count('class="dh-idea-group"'), 1,
                         "three related proposals must render as ONE group, not three cards")
        self.assertEqual(markup.count('class="dh-versus"'), 0,
                         "a grouped round must not also emit the single-variant wrapper")
        group = re.search(r'<div class="dh-idea-group">(.*?)</div>\s*</section>', markup, re.S)
        self.assertIsNotNone(group)
        chunk = group.group(1)
        # The shared incumbent's row appears exactly once, not once per variant.
        self.assertEqual(chunk.count('data-element="art.trama"'), 1)
        self.assertIn('class="dh-idea-variants"', chunk)
        self.assertEqual(chunk.count('class="dh-idea-variant"'), 2)
        # Each variant is labelled by its own distinguishing suffix, not a
        # generic "Variant A/B" the reader can't map back to an id.
        self.assertIn(">limpia<", chunk)
        self.assertIn(">real<", chunk)

    def test_a_single_redraw_still_renders_the_plain_before_after_card(self):
        """The common case (one idea, one redraw) must render exactly as it
        did before grouping existed -- no group wrapper for a group of one."""
        decisions = live(("art.trama", 2, "like", "proposed"),
                         ("art.trama.limpia", 0, None, "proposed"))
        with tempfile.TemporaryDirectory() as tmp:
            markup = bh.render_article(
                Path(tmp), decisions, {"art.trama.limpia"}, cohort_name="trama",
                language="en", title="T", asks="Better?")
        self.assertEqual(markup.count('class="dh-versus"'), 1)
        self.assertNotIn('class="dh-idea-group"', markup)
        self.assertNotIn('class="dh-idea-variants"', markup)

    def test_versus_rows_survive_nested_divs_inside_html_comps(self):
        """Row extraction must not stop at the first </div> inside a preview."""
        raw = ("<html><head><style>body{width:510px;min-height:660px;background:#f00}"
               "</style></head><body><div class='wrap'><div class='inner'>Hi</div></div>"
               "</body></html>")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comp = root / "content" / "pages.inventory.archivador.posiciones.html"
            comp.parent.mkdir(parents=True)
            comp.write_text(raw, encoding="utf-8")
            decisions = {
                "version": bh.VERSION, "state": "draft", "supersededCount": 0,
                "elements": [
                    {"element": "pages.inventory.archivador.posiciones", "stars": 2,
                     "sentiment": "like", "state": "proposed", "scored": True,
                     "source": "user",
                     "preview": {"path": comp.relative_to(root).as_posix(), "sha256": "abc"}},
                    {"element": "pages.inventory.archivador.posiciones.secuencia", "stars": 0,
                     "sentiment": None, "state": "proposed", "scored": False,
                     "source": "agent",
                     "preview": {"path": comp.relative_to(root).as_posix(), "sha256": "abc"}},
                ],
            }
            markup = bh.render_article(
                root, decisions, {"pages.inventory.archivador.posiciones.secuencia"},
                cohort_name="posiciones", language="es", title="T", asks="Ask.")
            before = re.search(
                r'<div class="dh-fb dh-fb-before"[^>]*data-element="pages\.inventory\.archivador\.posiciones"[^>]*>(.*?)</div>\s*<p class="dh-versus-label"><b class="dh-now">',
                markup, re.S)
            self.assertIsNotNone(before, "the incumbent row must close before the proposal label")
            chunk = before.group(0)
            self.assertIn('<span class="dh-meta">', chunk,
                            "a truncated row loses its title and evidence")
            self.assertIn('<span class="dh-signals">', chunk,
                            "a truncated row loses its scoring strip")
            self.assertIn("Hi", chunk, "the comp preview must still render inside the row")
            proposal = re.search(
                r'id="dh-el-pages\.inventory\.archivador\.posiciones\.secuencia"[^>]*data-scored="no"',
                markup)
            self.assertIsNotNone(proposal, "the proposal row must sit outside the incumbent preview")


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

    def test_comp_logical_page_size_is_not_the_850_default(self):
        raw = ("<html><head><style>body{inline-size:510px;block-size:660px;"
               "background:#e8e4d8}</style></head><body><p>x</p></body></html>")
        _, width, height = bh.html_comp_fragment(raw)
        self.assertEqual(width, 510.0)
        self.assertEqual(height, 660.0)


if __name__ == "__main__":
    unittest.main()


class TheHeaderNamesWhoIsActuallyRunning(unittest.TestCase):
    """R-23/B-015. A real `project.json` carried `companionAgentName` of
    "Claude Code" beside a `companionAgentUrl` of `cursor://...`, because the
    name and the link were resolved from different sources."""

    def project(self, root: Path, **fields) -> Path:
        store = root / "spec" / "design-harness"
        store.mkdir(parents=True, exist_ok=True)
        bh.write_json(store / "project.json", {"version": bh.VERSION, **fields})
        return root

    def test_identity_is_taken_whole_from_one_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.project(Path(tmp), companionAgentName="Cursor",
                                companionAgentUrl="cursor://deeplink")
            with patch.dict("os.environ", {"CLAUDECODE": "1"}, clear=True):
                url, name = bh.resolve_agent("", "", root)
            self.assertEqual(name, "Claude Code")
            self.assertNotIn("cursor://", url)

    def test_an_explicit_flag_still_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.project(Path(tmp), companionAgentName="Cursor")
            with patch.dict("os.environ", {"CLAUDECODE": "1"}, clear=True):
                url, name = bh.resolve_agent("x://y", "Zed", root)
            self.assertEqual((url, name), ("x://y", "Zed"))

    def test_a_stored_identity_is_used_when_nothing_else_speaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.project(Path(tmp), companionAgentName="Cursor",
                                companionAgentUrl="cursor://deeplink")
            with patch.dict("os.environ", {}, clear=True):
                self.assertEqual(bh.resolve_agent("", "", root),
                                 ("cursor://deeplink", "Cursor"))

    def test_an_unknown_host_reports_nothing_rather_than_guessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.project(Path(tmp))
            with patch.dict("os.environ", {}, clear=True):
                self.assertEqual(bh.resolve_agent("", "", root), ("", ""))

    def test_saving_an_identity_without_a_project_is_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            bh.save_companion_agent(Path(tmp), "x://y", "Zed")


class TheBriefIsCreatedSoItCanBeAnswered(unittest.TestCase):
    """R-19/B-016. `brief_workflow` was complete and tested and had never
    rendered, because nothing ever created a brief for it to render."""

    def project(self, root: Path) -> Path:
        store = root / "spec" / "design-harness"
        store.mkdir(parents=True, exist_ok=True)
        bh.write_json(store / "project.json", {"version": bh.VERSION, "language": "es"})
        return root

    def test_a_project_gets_a_brief(self):
        import brief_workflow
        with tempfile.TemporaryDirectory() as tmp:
            root = self.project(Path(tmp))
            self.assertTrue(bh.ensure_brief(root))
            self.assertIsNotNone(brief_workflow.load_brief(root))

    def test_the_brief_speaks_the_project_language(self):
        import brief_workflow
        with tempfile.TemporaryDirectory() as tmp:
            root = self.project(Path(tmp))
            bh.ensure_brief(root)
            prompts = [a["prompt"] for a in brief_workflow.load_brief(root)["answers"]]
            self.assertTrue(any("¿" in p for p in prompts))

    def test_an_existing_brief_is_never_overwritten(self):
        import brief_workflow
        with tempfile.TemporaryDirectory() as tmp:
            root = self.project(Path(tmp))
            bh.ensure_brief(root)
            brief_workflow.answer_brief(root, {
                "eventId": "e1", "at": "2026-08-22T00:00:00-06:00",
                "id": "ships", "answer": "un archivador"})
            self.assertFalse(bh.ensure_brief(root))
            answers = {a["id"]: a["answer"] for a in brief_workflow.load_brief(root)["answers"]}
            self.assertEqual(answers["ships"], "un archivador")

    def test_a_directory_that_is_not_a_project_gets_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(bh.ensure_brief(Path(tmp)))
            self.assertFalse((Path(tmp) / "spec").exists())

    def test_the_brief_reaches_the_article_once_it_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.project(Path(tmp))
            bh.ensure_brief(root)
            markup = bh.render_article(root, live(("cover.a", 3, None, "approved")))
            self.assertIn("dh-brief", markup)


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


class ReRenderingIsNotARound(unittest.TestCase):
    """R-27/B-018. Asking about nothing was refused as a round that proposes
    new ideas over unanswered feedback, leaving no way to regenerate the page
    after a code change."""

    def ledger(self) -> dict:
        return live(("cover.spine", 1, "like", "proposed"))

    def test_an_empty_cohort_is_allowed_despite_polish_debt(self):
        bh.check_round_earns_its_place(self.ledger(), set())

    def test_a_real_round_still_has_to_answer_the_debt(self):
        with self.assertRaises(bh.HarnessError):
            bh.check_round_earns_its_place(self.ledger(), {"type.brand-new"})


class TheAskComesBeforeTheHomework(unittest.TestCase):
    """The brief used to stand above the round. A five-question form over the
    one section that asks for something buried the ask behind homework."""

    def article(self, root: Path) -> str:
        store = root / "spec" / "design-harness"
        store.mkdir(parents=True, exist_ok=True)
        bh.write_json(store / "project.json", {"version": bh.VERSION, "language": "es"})
        bh.ensure_brief(root)
        # `palette.` files under a fundamental foundation, so the article
        # actually emits a zone after the round to be ordered against.
        return bh.render_article(root, live(("palette.a", 3, None, "approved")))

    def test_the_brief_renders_below_the_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = self.article(Path(tmp))
            self.assertLess(markup.index('id="dh-zone-round"'), markup.index('class="dh-brief"'))

    def test_the_brief_renders_above_the_zones_that_follow_the_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = self.article(Path(tmp))
            self.assertLess(markup.index('class="dh-brief"'),
                            markup.index('id="dh-zone-fundamentals"'))

    def test_the_tags_module_sits_beside_the_brief_not_at_the_far_end(self):
        # Both are things the user tells the agent. Splitting them to opposite
        # ends of the page made the reading order say they were different
        # kinds of thing.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markup = self.article(root)
            store = root / "spec" / "design-harness"
            bh.write_json(store / "corpus.json", {
                "version": 1, "root": "/x", "modalities": ["image"],
                "items": [{"id": "image-0", "path": "strong color/a.jpg",
                           "kind": "image", "sha256": f"{0:064x}", "bytes": 1}]})
            markup = bh.render_article(root, live(("palette.a", 3, None, "approved")))
            self.assertLess(markup.index('id="dh-zone-round"'), markup.index('class="dh-tags"'))
            self.assertLess(markup.index('class="dh-tags"'),
                            markup.index('id="dh-zone-fundamentals"'))

    def test_a_project_with_no_brief_still_renders_its_zones(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = bh.render_article(Path(tmp), live(("cover.a", 3, None, "approved")))
            self.assertNotIn('class="dh-brief"', markup)
            self.assertIn('id="dh-zone-round"', markup)
