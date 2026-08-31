#!/usr/bin/env python3
"""Tests for the read-back: what the user said, versus what the round changed."""
import json
import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import qa


class TheRoundIsReadBackAgainstWhatTheUserSaid(unittest.TestCase):
    """`doctor` cannot see a designer calling the round broken; that lives in
    the transcript and the ledger."""

    def _transcript(self, folder: Path, *entries: dict) -> Path:
        """A transcript always opens with the skill payload, as a real one does."""
        rows = (self._said("Base directory for this skill: /skills/aesthetic"),) + entries
        path = folder / "session.jsonl"
        path.write_text("\n".join(json.dumps(e) for e in rows), encoding="utf-8")
        return path

    def _said(self, text: str) -> dict:
        return {"type": "user", "timestamp": "2026-01-01T00:00:00Z",
                "message": {"content": [{"type": "text", "text": text}]}}

    def test_skill_payload_replayed_as_a_user_turn_is_not_the_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._transcript(
                Path(tmp),
                self._said("Base directory for this skill: /x\n\n# Aesthetic"),
                self._said("this is broken"))
            self.assertEqual(qa.user_turns(qa.entries(path)), ["this is broken"])

    def test_an_answer_given_through_a_question_tool_still_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._transcript(Path(tmp), {
                "type": "user",
                "message": {"content": [{
                    "type": "tool_result",
                    "content": 'The user answered: "Which one?"="all of it is wrong"'}]}})
            self.assertEqual(qa.user_turns(qa.entries(path)), ["all of it is wrong"])

    def test_a_repeated_answer_is_not_two_complaints(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._transcript(Path(tmp), self._said("broken"), self._said("broken"))
            self.assertEqual(qa.user_turns(qa.entries(path)), ["broken"])

    def test_a_project_with_no_ledger_is_still_checked(self):
        """Universal half: any project, no design ledger, nothing changed."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._transcript(root, self._said("it is all broken"))
            with unittest.mock.patch.object(qa, "session_transcripts", return_value=[path]), \
                 unittest.mock.patch.object(qa, "tracked_changes", return_value=[]):
                result = qa.feedback(root)
            self.assertFalse(result["passed"])
            self.assertIn("edited nothing", result["errors"][0])


    def test_complaints_with_nothing_rejected_are_a_missed_shot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "spec" / "design-harness").mkdir(parents=True)
            (root / "spec" / "design-harness" / "decisions.json").write_text(
                json.dumps({"elements": [{"element": "hero", "state": "proposed"}]}),
                encoding="utf-8")
            path = self._transcript(root, self._said("it is all broken"))
            with unittest.mock.patch.object(qa, "session_transcripts", return_value=[path]), \
                 unittest.mock.patch.object(qa, "tracked_changes", return_value=[]):
                result = qa.feedback(root)
            self.assertFalse(result["passed"])
            self.assertIn("edited nothing", result["errors"][0])


    def test_no_transcript_is_refused_rather_than_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with unittest.mock.patch.object(qa, "session_transcripts", return_value=[]):
                with self.assertRaises(qa.CookError):
                    qa.feedback(Path(tmp))


class TheReadIsScopedToTheSkillRun(unittest.TestCase):
    """Complaints from before a skill was invoked are about something else, and
    a transcript that never ran one is not evidence about a skill."""

    def _rows(self, *texts: tuple[str, str]) -> list[dict]:
        return [{"type": "user", "timestamp": stamp,
                 "message": {"content": [{"type": "text", "text": text}]}}
                for stamp, text in texts]

    def test_the_skill_directory_names_the_skill(self):
        rows = self._rows(("t1", "Base directory for this skill: /s/aesthetic\\n\\n# X"))
        self.assertEqual(qa.skill_run(rows), ("aesthetic", "t1"))

    def test_a_transcript_with_no_skill_is_not_evidence(self):
        self.assertEqual(qa.skill_run(self._rows(("t1", "hi")))[0], "")

    def test_complaints_before_the_skill_ran_are_out_of_scope(self):
        rows = self._rows(("t1", "the old thing is broken"),
                          ("t2", "Base directory for this skill: /s/aesthetic"),
                          ("t3", "looks fine"))
        self.assertEqual(qa.user_turns(rows, after="t2"), ["looks fine"])

    def test_a_session_that_ran_no_skill_is_skipped_for_an_older_one_that_did(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            idle = root / "idle.jsonl"
            idle.write_text(json.dumps(self._rows(("t1", "just chatting"))[0]),
                            encoding="utf-8")
            real = root / "real.jsonl"
            real.write_text(json.dumps(
                self._rows(("t1", "Base directory for this skill: /s/genesis"))[0]),
                encoding="utf-8")
            with unittest.mock.patch.object(qa, "session_transcripts",
                                            return_value=[idle, real]):
                path, rows = qa.resolve_transcript(root, None)
            self.assertEqual(path, real)
            self.assertEqual(qa.skill_run(rows)[0], "genesis")


class ACommittedFixStillCounts(unittest.TestCase):
    """`git status --porcelain` empties the moment the agent commits, and a
    correctly handled round then failed as 'changed nothing'."""

    def test_commits_since_the_run_started_count_as_change(self):
        calls = []

        def fake(argv, **kwargs):
            calls.append(argv[3:])
            porcelain = argv[3] == "status"
            return subprocess.CompletedProcess(
                argv, 0, "" if porcelain else "abc123 fix the thing\n", "")

        with unittest.mock.patch.object(subprocess, "run", side_effect=fake):
            changed = qa.tracked_changes(Path("/x"), since="2026-01-01T00:00:00Z")
        self.assertEqual(changed, ["abc123 fix the thing"])
        self.assertIn(["log", "--oneline", "--since=2026-01-01T00:00:00Z"], calls)


class ACorrectionIsStrongerThanAComplaint(unittest.TestCase):
    """"It's broken" is a symptom. "I asked for X" is a requirement still
    outstanding, and this session shipped four rounds without acting on one."""

    def test_an_unmet_instruction_is_a_correction(self):
        said = ["i initially requested to take over the design website",
                "you did not create a css layout"]
        for text in said:
            self.assertTrue(any(p.search(text) for p in qa.CORRECTION), text)

    def test_plain_praise_is_not_a_correction(self):
        self.assertFalse(any(p.search("that screenshot looks great")
                             for p in qa.CORRECTION))

    def test_an_instruction_restated_is_one_that_did_not_land(self):
        said = ["i initially requested to take over the claude design website",
                "you did not follow instructions about the claude design website"]
        self.assertEqual(qa.repeated(said), [said[1]])

    def test_two_unrelated_corrections_are_not_a_restatement(self):
        said = ["i asked for a css layout on the rails",
                "you did not translate the companion copy properly"]
        self.assertEqual(qa.repeated(said), [])

    def test_corrections_alone_fail_a_round_that_changed_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._t(root, "i asked for the rails to be css")
            with unittest.mock.patch.object(qa, "session_transcripts", return_value=[path]), \
                 unittest.mock.patch.object(qa, "tracked_changes", return_value=[]):
                result = qa.feedback(root)
            self.assertFalse(result["passed"])
            self.assertEqual(len(result["corrections"]), 1)

    def _t(self, folder, *texts):
        rows = [{"type": "user", "timestamp": "t0", "message": {"content": [
            {"type": "text", "text": "Base directory for this skill: /s/aesthetic"}]}}]
        rows += [{"type": "user", "timestamp": "t1", "message": {"content": [
            {"type": "text", "text": t}]}} for t in texts]
        path = folder / "s.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        return path
