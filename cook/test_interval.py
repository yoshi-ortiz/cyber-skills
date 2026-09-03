#!/usr/bin/env python3
"""The invocation interval: what the run touched, not what was already dirty.

Blackbox. Every case drives `cook/cook.py` as a process, because the exit code
is the whole product here -- a round that passed on somebody else's uncommitted
work returned 0, and every gate in this repository reads exit codes.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

COOK = Path(__file__).resolve().parent / "cook.py"
MARKER = "Base directory for this skill: /skills/aesthetic"


def stamp(offset: int) -> str:
    """An ISO timestamp `offset` seconds from now, the shape a transcript uses."""
    return (datetime.now(timezone.utc)
            + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%SZ")


def said(text: str, at: str) -> dict:
    return {"type": "user", "timestamp": at,
            "message": {"content": [{"type": "text", "text": text}]}}


def repo(root: Path) -> None:
    """A real git repository with one commit, so `status` has a baseline."""
    for argv in (("init",), ("add", "old.txt"),
                 ("-c", "user.email=t@t", "-c", "user.name=t",
                  "commit", "-m", "first")):
        subprocess.run(["git", "-C", str(root), *argv],
                       capture_output=True, check=True)


def transcript(root: Path, *rows: dict) -> Path:
    path = root / "session.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return path


def feedback(root: Path, log: Path, *extra: str):
    done = subprocess.run(
        [sys.executable, str(COOK), "feedback", "--project-root", str(root),
         "--session", str(log), *extra], capture_output=True, text=True)
    return done, json.loads(done.stdout or "{}")


class TheWorkingTreeIsScopedToTheRun(unittest.TestCase):
    """`git status --porcelain` carries no clock, so an already-dirty tree read
    as 'the run changed something' and rescued a round that changed nothing."""

    def test_a_tree_dirtied_before_the_run_is_not_evidence_the_run_acted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "old.txt").write_text("one", encoding="utf-8")
            repo(root)
            (root / "old.txt").write_text("dirty before the run", encoding="utf-8")
            log = transcript(root, said(MARKER, stamp(5)),
                             said("this is broken", stamp(6)))
            done, result = feedback(root, log)
        self.assertEqual(done.returncode, 1, done.stdout or done.stderr)
        self.assertEqual(result["changed"], [])
        self.assertIn("edited nothing", result["errors"][0])

    def test_a_file_touched_after_the_run_began_still_counts(self):
        """The scope must not become 'nothing ever counts'."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "old.txt").write_text("one", encoding="utf-8")
            repo(root)
            log = transcript(root, said(MARKER, stamp(-5)),
                             said("this is broken", stamp(-4)))
            (root / "old.txt").write_text("edited by the run", encoding="utf-8")
            done, result = feedback(root, log)
        self.assertEqual(done.returncode, 0, done.stdout or done.stderr)
        self.assertIn("old.txt", result["changed"])


class AnEarlierRunIsAddressableAndBounded(unittest.TestCase):
    """One transcript holds many runs. Selecting only the latest leaves every
    earlier round unauditable, and an unbounded window reads the next round's
    verdict onto this one."""

    def two_runs(self, tmp: str):
        """A clean project, and a transcript beside it holding two runs: the
        first complained about and unanswered, the second praised."""
        root = Path(tmp) / "project"
        root.mkdir()
        (root / "old.txt").write_text("one", encoding="utf-8")
        repo(root)
        self.first, self.second = stamp(-30), stamp(-10)
        log = transcript(Path(tmp),
                         said(MARKER, self.first),
                         said("this is broken", stamp(-29)),
                         said(MARKER, self.second),
                         said("looks good", stamp(-9)))
        return root, log

    def test_the_latest_run_does_not_inherit_the_earlier_runs_complaint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, log = self.two_runs(tmp)
            done, result = feedback(root, log)
        self.assertEqual(done.returncode, 0, done.stdout or done.stderr)
        self.assertEqual(result["complaints"], [])
        self.assertEqual(result["run_id"], f"aesthetic@{self.second}")

    def test_an_earlier_run_can_be_audited_by_its_own_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, log = self.two_runs(tmp)
            run = f"aesthetic@{self.first}"
            done, result = feedback(root, log, "--invocation", run)
        self.assertEqual(done.returncode, 1, done.stdout or done.stderr)
        self.assertEqual(result["run_id"], run)
        self.assertEqual(result["complaints"], ["this is broken"])

    def test_an_earlier_run_stops_where_the_next_one_starts(self):
        """Praise given to the second round is not evidence about the first."""
        with tempfile.TemporaryDirectory() as tmp:
            root, log = self.two_runs(tmp)
            _, result = feedback(root, log, "--invocation",
                                 f"aesthetic@{self.first}")
        self.assertNotIn("looks good", result["complaints"])
        self.assertEqual(result["userTurns"], 1)

    def test_an_invocation_that_is_not_in_the_transcript_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, log = self.two_runs(tmp)
            done, result = feedback(root, log, "--invocation", "aesthetic@nope")
        self.assertEqual(done.returncode, 2, done.stdout or done.stderr)
        self.assertIn("aesthetic@nope", result["error"])


if __name__ == "__main__":
    unittest.main()
