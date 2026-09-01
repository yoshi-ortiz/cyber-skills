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
from article_fixtures import live


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
