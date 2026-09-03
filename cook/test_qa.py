#!/usr/bin/env python3
"""Tests for the read-back: what the user said, versus what the round changed."""
import json
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import qa

MARKER = "Base directory for this skill: /skills/aesthetic"


def said(text: str, stamp: str = "t1") -> dict:
    return {"type": "user", "timestamp": stamp,
            "message": {"content": [{"type": "text", "text": text}]}}


def written(folder, *rows: dict, name: str = "session.jsonl") -> Path:
    path = Path(folder) / name
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return path


def run_of(folder, *rows: dict) -> Path:
    """A transcript always opens with the skill payload, as a real one does."""
    return written(folder, said(MARKER, "t0"), *rows)


class TheRoundIsReadBackAgainstWhatTheUserSaid(unittest.TestCase):
    """`doctor` cannot see a designer calling the round broken."""

    def test_skill_payload_replayed_as_a_user_turn_is_not_the_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = run_of(tmp, said("Base directory for this skill: /x\n\n# A"),
                          said("this is broken"))
            self.assertEqual(qa.user_turns(qa.entries(path)), ["this is broken"])

    def test_a_sentence_typed_into_a_slash_command_is_still_the_user_talking(self):
        """The user's own words arrive inside <command-args>; the turn opens
        with <command-message>, which used to discard the whole thing."""
        with tempfile.TemporaryDirectory() as tmp:
            path = run_of(tmp, said(
                "<command-message>cook</command-message>\n"
                "<command-name>/cook</command-name>\n"
                "<command-args>you should fix the thumbnail</command-args>"))
            self.assertEqual(qa.user_turns(qa.entries(path)),
                             ["you should fix the thumbnail"])

    def test_an_answer_given_through_a_question_tool_still_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = run_of(tmp, {"type": "user", "message": {"content": [{
                "type": "tool_result",
                "content": 'The user answered: "Which one?"="all of it is wrong"'}]}})
            self.assertEqual(qa.user_turns(qa.entries(path)), ["all of it is wrong"])

    def test_a_repeated_answer_is_not_two_complaints(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = run_of(tmp, said("broken"), said("broken"))
            self.assertEqual(qa.user_turns(qa.entries(path)), ["broken"])

    def test_a_project_with_no_ledger_is_still_checked(self):
        """Universal half: any project, no design ledger, nothing changed."""
        with tempfile.TemporaryDirectory() as tmp:
            path = run_of(tmp, said("it is all broken"))
            with unittest.mock.patch.object(qa, "session_transcripts", return_value=[path]), \
                 unittest.mock.patch.object(qa, "tracked_changes", return_value=[]):
                result = qa.feedback(Path(tmp))
            self.assertFalse(result["passed"])
            self.assertIn("edited nothing", result["errors"][0])

    def test_complaints_with_nothing_rejected_are_a_missed_shot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "spec" / "design-harness").mkdir(parents=True)
            (root / "spec" / "design-harness" / "decisions.json").write_text(
                json.dumps({"elements": [{"element": "hero", "state": "proposed"}]}),
                encoding="utf-8")
            path = run_of(root, said("it is all broken"))
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


class TheReadIsScopedToTheLatestSkillRun(unittest.TestCase):
    """Complaints from before the latest invocation are about another round."""

    def test_the_skill_directory_names_the_skill(self):
        rows = [said("Base directory for this skill: /s/aesthetic\\n\\n# X")]
        self.assertEqual(qa.latest_run(rows), ("aesthetic", "t1", 0))

    def test_a_transcript_with_no_skill_is_not_evidence(self):
        self.assertEqual(qa.latest_run([said("hi")])[0], "")

    def test_complaints_before_the_skill_ran_are_out_of_scope(self):
        rows = [said("the old thing is broken", "t1"),
                said("Base directory for this skill: /s/aesthetic", "t2"),
                said("looks fine", "t3")]
        self.assertEqual(qa.user_turns(rows, after="t2"), ["looks fine"])

    def test_a_session_that_ran_no_skill_is_skipped_for_an_older_one_that_did(self):
        with tempfile.TemporaryDirectory() as tmp:
            idle = written(tmp, said("just chatting"), name="idle.jsonl")
            real = written(tmp, said("Base directory for this skill: /s/genesis"),
                           name="real.jsonl")
            with unittest.mock.patch.object(qa, "session_transcripts",
                                            return_value=[idle, real]):
                path = qa.resolve_transcript(Path(tmp), None)
            self.assertEqual(path, real)
            self.assertEqual(qa.latest_run(qa.entries(path))[0], "genesis")

    def test_only_the_latest_runs_turns_are_evidence(self):
        """The FIRST marker reads a dead round's verdict onto the live one."""
        with tempfile.TemporaryDirectory() as tmp:
            path = written(tmp, said(MARKER, "t1"), said("the old run is broken", "t2"),
                           said(MARKER, "t3"), said("looks good", "t4"))
            bundle = qa.normalized_evidence(path)
            self.assertEqual(bundle["turns"], ["looks good"])
            self.assertEqual(set(bundle), {"transcript", "skill", "invoked_at",
                                           "turns", "artifacts"})

    def test_a_transcript_is_never_read_whole(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = written(tmp, *[said("filler") for _ in range(5000)],
                           said(MARKER, "z1"), said("looks good", "z2"))
            with unittest.mock.patch.object(
                    qa, "entries",
                    side_effect=AssertionError("the whole transcript was loaded")):
                self.assertEqual(qa.normalized_evidence(path)["turns"], ["looks good"])
            self.assertEqual(len(list(qa.stream_run(path))), 1)


class CookAsksTokensQaThroughItsPublicCli(unittest.TestCase):
    def test_a_nonzero_exit_names_the_code_rather_than_tracing_back(self):
        done = subprocess.CompletedProcess([], 5, "", "adapter blew up")
        with unittest.mock.patch.object(subprocess, "run", return_value=done):
            with self.assertRaises(qa.CookError) as caught:
                qa.assess_feedback({"turns": ["looks good"]})
        self.assertIn("5", str(caught.exception))

    def test_advisory_candidates_are_warnings_not_a_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = run_of(tmp, said("looks good"))
            with unittest.mock.patch.object(qa, "tracked_changes", return_value=["a.py"]):
                result = qa.feedback(Path(tmp), path)
        self.assertTrue(result["passed"])
        self.assertTrue(result["warnings"])
        self.assertNotIn("rejected", result)

    def test_cook_runs_from_the_repository_root(self):
        """The old sys.path hack reached into a private module, and the
        directory cook ran from decided whether that resolved."""
        repo = Path(qa.__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            log = run_of(tmp, said("looks good"))
            done = subprocess.run(
                [sys.executable, str(repo / "cook" / "cook.py"), "feedback",
                 "--project-root", tmp, "--session", str(log)],
                capture_output=True, text=True, cwd=repo)
        self.assertEqual(done.returncode, 0, done.stderr or done.stdout)
        self.assertEqual(json.loads(done.stdout)["skill"], "aesthetic")


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
    """"It's broken" is a symptom. "I asked for X" is still outstanding."""

    # The patterns themselves now live in tokens-qa, the universal QA boundary,
    # and are tested there. What is left here is what cook still owns: a round
    # that heard one and changed nothing.

    def test_corrections_alone_fail_a_round_that_changed_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = run_of(tmp, said("i asked for the rails to be css"))
            with unittest.mock.patch.object(qa, "session_transcripts", return_value=[path]), \
                 unittest.mock.patch.object(qa, "tracked_changes", return_value=[]):
                result = qa.feedback(Path(tmp))
            self.assertFalse(result["passed"])
            self.assertEqual(len(result["corrections"]), 1)

    def test_a_restated_instruction_fails_however_many_files_moved(self):
        """A run that churns a dozen files while ignoring what was asked is the
        exact shot this check exists to catch, so `changed` cannot rescue it."""
        with tempfile.TemporaryDirectory() as tmp:
            path = run_of(tmp,
                          said("i asked for the rails on the claude design site to be css"),
                          said("you did not follow instructions about the claude "
                               "design site rails"))
            with unittest.mock.patch.object(qa, "tracked_changes",
                                            return_value=["a.py"] * 13):
                result = qa.feedback(Path(tmp), path)
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["restated"]), 1)
