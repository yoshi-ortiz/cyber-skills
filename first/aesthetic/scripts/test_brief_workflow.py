"""Tests for the project brief.

The brief is the only surface where the USER writes prose the skill keeps, so
the things that matter are the ones that lose writing: a retry that appends a
second copy, a save that drops an answer, or a corrupt spec that takes the
whole article down with it.
"""
import json
import tempfile
import unittest
from pathlib import Path

import brief_workflow as bw
from editorial_workflow import STORE, WorkflowError

AT = "2026-08-22T00:00:00Z"


def html_of(text: str) -> str:
    """Prompts carry accents and question marks, so compare escaped."""
    from html import escape
    return escape(text)


def started(root: Path, language: str | None = None) -> dict:
    return bw.save_brief_spec(root, bw.default_brief(AT, language))


class AnEmptyBriefIsStillABrief(unittest.TestCase):
    def test_start_writes_every_prompt_unanswered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = started(root)
            self.assertEqual(bw.brief_progress(spec), (0, len(spec["answers"])))
            self.assertTrue(all(item["answer"] == "" for item in spec["answers"]))
            self.assertTrue((root / STORE / bw.BRIEF_FILE).exists())

    def test_start_creates_the_event_log_so_the_first_answer_has_somewhere_to_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            self.assertTrue((root / STORE / bw.BRIEF_EVENTS_FILE).exists())

    def test_a_project_with_no_brief_renders_nothing(self):
        # Not an empty section, and not an error: an older project simply has
        # no brief, exactly as an older project has no burndown.
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(bw.render_brief(Path(tmp)), "")
            self.assertIsNone(bw.load_brief(Path(tmp)))


class AnsweringIsIdempotent(unittest.TestCase):
    """A retried answer must not append a second copy. The event id is the
    caller's promise that two deliveries are one intent."""

    def event(self, identifier="e1", key="ships", answer="A print programme."):
        return {"eventId": identifier, "at": AT, "id": key, "answer": answer}

    def test_the_first_answer_lands_and_the_replay_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            self.assertTrue(bw.answer_brief(root, self.event()))
            path = root / STORE / bw.BRIEF_EVENTS_FILE
            after_first = path.read_bytes()
            self.assertFalse(bw.answer_brief(root, self.event()))
            self.assertEqual(path.read_bytes(), after_first,
                             "a replayed answer must not write anything at all")
            self.assertEqual(len(bw.load_brief_events(root)), 1)

    def test_the_answer_reaches_the_spec_not_only_the_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            bw.answer_brief(root, self.event())
            spec = bw.load_brief(root)
            stored = next(i for i in spec["answers"] if i["id"] == "ships")
            self.assertEqual(stored["answer"], "A print programme.")
            self.assertEqual(bw.brief_progress(spec), (1, len(spec["answers"])))

    def test_rewriting_an_answer_keeps_both_events_as_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            bw.answer_brief(root, self.event("e1", answer="First take."))
            bw.answer_brief(root, self.event("e2", answer="Sharper take."))
            self.assertEqual(len(bw.load_brief_events(root)), 2,
                             "the log is the change history, so a rewrite appends")
            spec = bw.load_brief(root)
            stored = next(i for i in spec["answers"] if i["id"] == "ships")
            self.assertEqual(stored["answer"], "Sharper take.",
                             "the spec always holds the CURRENT answer")

    def test_an_unknown_prompt_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            with self.assertRaises(WorkflowError):
                bw.answer_brief(root, self.event(key="not-a-prompt"))

    def test_answering_before_starting_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(WorkflowError) as caught:
                bw.answer_brief(Path(tmp), self.event())
            self.assertIn("brief start", str(caught.exception))


class TheBrowsersAnswersAreAdopted(unittest.TestCase):
    """The companion queues what the user typed and validates almost nothing,
    exactly as it does for scoring. Python owns the schema, so adopting is
    where a malformed answer is refused."""

    def inbox(self, root: Path, *lines: str) -> Path:
        path = root / "brief-inbox.jsonl"
        path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        return path

    def test_a_queued_answer_reaches_the_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            box = self.inbox(root, json.dumps(
                {"eventId": "b1", "at": AT, "id": "ships", "answer": "A print programme."}))
            self.assertEqual(bw.adopt_brief_inbox(root, box), (1, 0))
            spec = bw.load_brief(root)
            self.assertEqual(next(i for i in spec["answers"]
                                  if i["id"] == "ships")["answer"], "A print programme.")

    def test_adopting_twice_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            box = self.inbox(root, json.dumps(
                {"eventId": "b1", "at": AT, "id": "ships", "answer": "Once."}))
            self.assertEqual(bw.adopt_brief_inbox(root, box), (1, 0))
            before = (root / STORE / bw.BRIEF_EVENTS_FILE).read_bytes()
            self.assertEqual(bw.adopt_brief_inbox(root, box), (0, 1))
            self.assertEqual((root / STORE / bw.BRIEF_EVENTS_FILE).read_bytes(), before)

    def test_a_bad_line_is_skipped_without_losing_the_good_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            box = self.inbox(
                root,
                "{ not json",
                json.dumps({"eventId": "b1", "at": AT, "id": "ships", "answer": "Good."}),
                json.dumps({"eventId": "b2", "at": AT, "id": "nope", "answer": "Unknown id."}))
            self.assertEqual(bw.adopt_brief_inbox(root, box), (1, 2))
            self.assertEqual(bw.brief_progress(bw.load_brief(root))[0], 1)

    def test_an_absent_inbox_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            self.assertEqual(bw.adopt_brief_inbox(root, root / "nothing.jsonl"), (0, 0))


class TheBriefRefusesWhatWouldCorruptIt(unittest.TestCase):
    def test_a_non_object_brief_is_refused(self):
        with self.assertRaises(WorkflowError):
            bw.validate_brief_spec(["not", "an", "object"])

    def test_an_empty_answer_list_is_refused(self):
        with self.assertRaises(WorkflowError):
            bw.validate_brief_spec({"startedAt": AT, "answers": []})

    def test_duplicate_prompt_ids_are_refused(self):
        with self.assertRaises(WorkflowError):
            bw.validate_brief_spec({"startedAt": AT, "answers": [
                {"id": "ships", "prompt": "a", "answer": ""},
                {"id": "ships", "prompt": "b", "answer": ""}]})

    def test_an_oversized_answer_is_refused_with_its_length(self):
        with self.assertRaises(WorkflowError) as caught:
            bw.validate_brief_spec({"startedAt": AT, "answers": [
                {"id": "ships", "prompt": "a", "answer": "x" * (bw.MAX_ANSWER_CHARS + 1)}]})
        self.assertIn(str(bw.MAX_ANSWER_CHARS), str(caught.exception))

    def test_a_corrupt_brief_renders_nothing_rather_than_breaking_the_article(self):
        # render_brief is called from render_article. A project whose brief
        # got hand-edited into invalid JSON must lose the section, not the page.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            (root / STORE / bw.BRIEF_FILE).write_text("{ not json", encoding="utf-8")
            self.assertEqual(bw.render_brief(root), "")


class TheBriefReadsAsAManifesto(unittest.TestCase):
    def test_the_prompts_follow_the_projects_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = started(root, "es")
            prompts = " ".join(i["prompt"] for i in spec["answers"])
            self.assertIn("entregar", prompts)
            self.assertNotIn("shipping", prompts)

    def test_an_unknown_language_falls_back_instead_of_failing(self):
        self.assertEqual(bw.prompts_for("qq"), bw.PROMPTS["en"])
        self.assertEqual(bw.prompts_for(None), bw.PROMPTS["en"])

    def test_answers_are_escaped_into_the_markup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            bw.answer_brief(root, {"eventId": "e1", "at": AT, "id": "ships",
                                   "answer": "<script>alert(1)</script>"})
            markup = bw.render_brief(root)
            self.assertNotIn("<script>alert", markup)
            self.assertIn("&lt;script&gt;", markup)

    def test_an_incomplete_brief_opens_itself(self):
        # The one thing on the page a user can act on without waiting for a
        # render should not be behind a click while it is still unfinished.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root)
            self.assertRegex(bw.render_brief(root), r'<details class="dh-brief" open>')

    def test_a_finished_brief_collapses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = started(root)
            for index, item in enumerate(spec["answers"]):
                bw.answer_brief(root, {"eventId": f"e{index}", "at": AT,
                                       "id": item["id"], "answer": "Answered."})
            markup = bw.render_brief(root)
            self.assertIn('<details class="dh-brief">', markup)
            self.assertNotIn("dh-brief\" open", markup)

    def test_rendered_words_come_from_the_caller_so_the_page_speaks_one_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root, "es")
            markup = bw.render_brief(root, {
                "brief-title": "Resumen del proyecto",
                "brief-count": "{answered} de {total} respondidas",
                "brief-now": "Ahora", "brief-more": "{count} más después de esta"})
            self.assertIn("Resumen del proyecto", markup)
            self.assertIn("0 de 5 respondidas", markup)
            self.assertIn("4 más después de esta", markup)
            self.assertNotIn("Project brief", markup)
            self.assertNotIn("more after this", markup)


class OnlyOneQuestionIsAskedAtATime(unittest.TestCase):
    """Five prompts on screen at once is a form, and a form gets skimmed and
    filled with the shortest thing that dismisses it."""

    def test_a_fresh_brief_shows_exactly_one_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = started(root)
            markup = bw.render_brief(root)
            self.assertEqual(markup.count('class="dh-brief-question"'), 1)
            self.assertIn(html_of(spec["answers"][0]["prompt"]), markup)
            for later in spec["answers"][1:]:
                self.assertNotIn(html_of(later["prompt"]), markup,
                                 "a prompt the user has not reached yet must not be shown")

    def test_the_question_advances_as_answers_land(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = started(root)
            first, second = spec["answers"][0], spec["answers"][1]
            bw.answer_brief(root, {"eventId": "e1", "at": AT,
                                   "id": first["id"], "answer": "A print programme."})
            markup = bw.render_brief(root)
            self.assertEqual(markup.count('class="dh-brief-question"'), 1)
            self.assertIn(html_of(second["prompt"]), markup)
            self.assertIn("A print programme.", markup,
                          "what was already said stays visible as the manifesto so far")

    def test_the_remaining_count_is_shown_and_shrinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = started(root)
            self.assertIn("4 more after this", bw.render_brief(root))
            bw.answer_brief(root, {"eventId": "e1", "at": AT,
                                   "id": spec["answers"][0]["id"], "answer": "Said."})
            self.assertIn("3 more after this", bw.render_brief(root))

    def test_the_last_question_promises_no_more(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = started(root)
            for index, item in enumerate(spec["answers"][:-1]):
                bw.answer_brief(root, {"eventId": f"e{index}", "at": AT,
                                       "id": item["id"], "answer": "Said."})
            markup = bw.render_brief(root)
            self.assertEqual(markup.count('class="dh-brief-question"'), 1)
            self.assertNotIn("more after this", markup)

    def test_a_finished_brief_asks_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = started(root)
            for index, item in enumerate(spec["answers"]):
                bw.answer_brief(root, {"eventId": f"e{index}", "at": AT,
                                       "id": item["id"], "answer": "Said."})
            markup = bw.render_brief(root)
            self.assertNotIn('class="dh-brief-question"', markup)
            self.assertIsNone(bw.next_unanswered(bw.load_brief(root)))


class TheArticleCarriesTheBrief(unittest.TestCase):
    def test_render_article_emits_the_brief_section(self):
        import bootstrap_harness as bh
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            started(root, "es")
            bw.answer_brief(root, {"eventId": "e1", "at": AT, "id": "ships",
                                   "answer": "Un programa impreso."})
            decisions = {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
                         "elements": [{"element": "core.idea", "stars": 2,
                                       "sentiment": "like", "state": "proposed",
                                       "scored": True, "source": "user"}]}
            markup = bh.render_article(root, decisions, set(), cohort_name="",
                                       language="es", title="T", asks="Ask.")
            self.assertIn('class="dh-brief"', markup)
            self.assertIn("Un programa impreso.", markup)
            self.assertIn("Resumen del proyecto", markup,
                          "the section must speak the article's language")

    def test_an_article_without_a_brief_is_unchanged(self):
        import bootstrap_harness as bh
        with tempfile.TemporaryDirectory() as tmp:
            decisions = {"version": bh.VERSION, "state": "draft", "supersededCount": 0,
                         "elements": [{"element": "core.idea", "stars": 2,
                                       "sentiment": "like", "state": "proposed",
                                       "scored": True, "source": "user"}]}
            markup = bh.render_article(Path(tmp), decisions, set(), cohort_name="",
                                       language="en", title="T", asks="Ask.")
            self.assertNotIn("dh-brief", markup)


if __name__ == "__main__":
    unittest.main()
