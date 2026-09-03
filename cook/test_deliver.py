#!/usr/bin/env python3
"""The release boundary: reported, never crossed.

Blackbox. The load-bearing case is `test_the_repository_is_untouched`: a report
that quietly commits is worse than no report, so the proof is that the git
state is byte-identical afterwards.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

COOK = Path(__file__).resolve().parent / "cook.py"
REVIEWS = ["doctrine", "architecture", "diff", "checks"]


def git(root: Path, *argv: str) -> str:
    done = subprocess.run(["git", "-C", str(root), *argv],
                          capture_output=True, text=True)
    return done.stdout.strip()


def project(root: Path) -> Path:
    (root / "a.py").write_text("one\n", encoding="utf-8")
    for argv in (("init",), ("add", "a.py"),
                 ("-c", "user.email=t@t", "-c", "user.name=t",
                  "commit", "-m", "first")):
        subprocess.run(["git", "-C", str(root), *argv],
                       capture_output=True, check=True)
    (root / "a.py").write_text("two\n", encoding="utf-8")
    return root


def deliver(root: Path, *extra: str):
    done = subprocess.run(
        [sys.executable, str(COOK), "deliver", "--project-root", str(root), *extra],
        capture_output=True, text=True)
    return done, json.loads(done.stdout or "{}")


class TheBoundaryIsNamedBeforeItIsCrossed(unittest.TestCase):
    def test_every_review_the_row_requires_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            done, result = deliver(project(Path(tmp)))
        self.assertEqual(done.returncode, 1, done.stdout or done.stderr)
        self.assertEqual(sorted(result["reviews"]), sorted(REVIEWS))
        for item in REVIEWS:
            self.assertIn(item, done.stdout)

    def test_confirming_some_reviews_does_not_confirm_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            done, result = deliver(project(Path(tmp)),
                                   "--confirmed", "doctrine",
                                   "--confirmed", "diff")
        self.assertEqual(done.returncode, 1)
        self.assertEqual(sorted(result["outstanding"]), ["architecture", "checks"])

    def test_a_review_cook_does_not_know_is_refused(self):
        """Confirming 'everything' must not silently satisfy the four."""
        with tempfile.TemporaryDirectory() as tmp:
            done, result = deliver(project(Path(tmp)), "--confirmed", "everything")
        self.assertEqual(done.returncode, 2)
        self.assertIn("everything", result["error"])

    def test_all_four_confirmed_reports_ready_and_still_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp))
            argv = [a for item in REVIEWS for a in ("--confirmed", item)]
            done, result = deliver(root, *argv)
        self.assertEqual(done.returncode, 0, done.stdout or done.stderr)
        self.assertEqual(result["outstanding"], [])
        self.assertIn("a.py", result["tree"]["dirty"])


class CookNeverCrossesIt(unittest.TestCase):
    def test_the_repository_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp))
            before = (git(root, "rev-parse", "HEAD"),
                      git(root, "status", "--porcelain"))
            argv = [a for item in REVIEWS for a in ("--confirmed", item)]
            deliver(root, *argv)
            after = (git(root, "rev-parse", "HEAD"),
                     git(root, "status", "--porcelain"))
        self.assertEqual(before, after)

    def test_there_is_no_flag_that_delivers(self):
        """`cook run` refuses a repo project root with no flag to open it. The
        same idiom holds here: the absence is the guarantee."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp))
            for flag in ("--push", "--commit", "--yes"):
                done, _ = deliver(root, flag)
                self.assertEqual(done.returncode, 2, flag)


if __name__ == "__main__":
    unittest.main()
