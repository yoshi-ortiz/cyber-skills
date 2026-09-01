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


if __name__ == "__main__":
    unittest.main()
