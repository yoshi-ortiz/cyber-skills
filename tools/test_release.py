#!/usr/bin/env python3
"""One check on the part of `release.py` that can be wrong quietly.

The git half fails loudly; `diff_tree` is the half that can report "already
matches" over a real difference and let a stale channel look current, which is
the exact failure this tool exists to prevent.
"""
import tempfile
import unittest
from pathlib import Path

import release


class DiffTree(unittest.TestCase):
    def trees(self, left: dict[str, str], right: dict[str, str]):
        base = Path(tempfile.mkdtemp())
        for name, files in (("a", left), ("b", right)):
            for path, body in files.items():
                target = base / name / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body)
            (base / name).mkdir(exist_ok=True)
        return base / "a", base / "b"

    def test_identical_trees_report_nothing(self):
        a, b = self.trees({"x.md": "same", "d/y.md": "same"},
                          {"x.md": "same", "d/y.md": "same"})
        self.assertEqual(release.diff_tree(a, b), [])

    def test_nested_difference_is_found(self):
        a, b = self.trees({"d/y.md": "old"}, {"d/y.md": "new"})
        self.assertEqual(release.diff_tree(a, b), ["M d/y.md"])

    def test_added_and_removed_are_signed(self):
        a, b = self.trees({"gone.md": "x"}, {"new.md": "y"})
        self.assertEqual(release.diff_tree(a, b), ["+ new.md", "- gone.md"])


class OnlyTrackedChangesBlockARelease(unittest.TestCase):
    """publish.py ships what git tracks, so an untracked stray cannot reach a
    published tree and has no business refusing the release that would have
    excluded it anyway."""

    def test_untracked_files_do_not_block(self):
        self.assertEqual(release.blocking_changes("?? TODOS.md\n?? notes.md\n"), [])

    def test_a_tracked_edit_still_blocks(self):
        self.assertEqual(release.blocking_changes(" M tools/fog.py\n"), [" M tools/fog.py"])

    def test_a_staged_add_still_blocks(self):
        self.assertEqual(release.blocking_changes("A  new.py\n?? stray.md\n"), ["A  new.py"])


class AChannelCheckedOutElsewhereIsRefused(unittest.TestCase):
    """`worktree add --force` on a branch another worktree holds leaves that
    worktree reporting staged changes nobody made, and a commit there silently
    reverts the release."""

    LISTING = ("worktree /repo\nHEAD aaa\nbranch refs/heads/dev\n\n"
               "worktree /private/tmp/main-wt\nHEAD bbb\nbranch refs/heads/main\n\n"
               "worktree /repo/detached\nHEAD ccc\ndetached\n")

    def test_it_names_the_worktree_already_holding_the_channel(self):
        self.assertEqual(release.worktree_holding(self.LISTING, "main"),
                         "/private/tmp/main-wt")

    def test_a_channel_nobody_holds_is_free(self):
        self.assertIsNone(release.worktree_holding(self.LISTING, "alpha"))

    def test_a_detached_worktree_holds_no_branch(self):
        self.assertIsNone(release.worktree_holding(self.LISTING, "ccc"))


class AStaleChannelIsRefusedBeforeItDiverges(unittest.TestCase):
    """Committing on a channel that is behind its remote makes a push that
    cannot fast-forward, and release has already moved the branch by then."""

    def test_behind_is_refused(self):
        self.assertEqual(release.divergence("0\t1"), (0, 1))

    def test_level_is_fine(self):
        self.assertEqual(release.divergence("0\t0"), (0, 0))

    def test_ahead_only_is_fine(self):
        self.assertEqual(release.divergence("3\t0"), (3, 0))


if __name__ == "__main__":
    unittest.main()
