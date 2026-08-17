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
        paint = script.split("function paint(row,s){", 1)[1][:120]
        self.assertIn("flashSaved(row)", paint,
                      "the confirmation must be raised by paint(), which only runs "
                      "when the companion echoes the write back")
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
