"""Tests for the host behaviour around the article.

The companion frame, the skill's own status reporting, the brief it asks for
and the header naming who is running. Split out of `test_article.py` for its
directory's byte budget.
"""
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bootstrap_harness as bh
from article_fixtures import live


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
        self.assertIn("deliver.py", skill)
        self.assertIn("review image\npath", skill)
        # Prose can no longer drop the review images, because prose no longer
        # orders them. `deliver` runs review_delivery and refuses without it.
        deliver = (Path(__file__).resolve().parent / "deliver.py").read_text(encoding="utf-8")
        self.assertIn("review_delivery.py", deliver)
        self.assertIn("cannot act on", deliver)

    def test_first_reply_gives_the_page_and_key_before_any_status(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        section = skill.split("## Start", 1)[1].split("## Read the user", 1)[0]
        self.assertLess(section.index("🔗 <full URL>"), section.index("👀 <user-language"))
        self.assertLess(section.index("🔑 <value after ?key=>"), section.index("👀 <user-language"))
        self.assertIn("no preamble", section)

    def test_live_status_spans_the_real_run(self):
        skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        start = skill.split("## Start", 1)[1].split("## Read the user", 1)[0]
        publish = skill.split("## Publish the established article", 1)[1].split(
            "## Continue and critique", 1)[0]
        self.assertIn('--status "<emoji + user-language', start)
        self.assertIn("activity changes", skill)
        self.assertIn("--idle-text", publish)
        deliver = (Path(__file__).resolve().parent / "deliver.py").read_text(encoding="utf-8")
        self.assertIn('"status", "--idle"', deliver)

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
        self.assertIn("deliver.py --project-root", skill)
        self.assertNotIn("editorial-board.html", skill)


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
