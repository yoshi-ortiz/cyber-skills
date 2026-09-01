"""Tests for the preview surfaces: slideshow, thumbnails, canonical assets.

Split out of `test_article.py` for its directory's byte budget.
"""
import json
import re
import tempfile
import unittest
from pathlib import Path

import bootstrap_harness as bh
from article_fixtures import live


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
