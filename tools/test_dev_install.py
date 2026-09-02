#!/usr/bin/env python3
"""The guard that stops a dev install from discarding work.

Replacing an installed copy with a symlink deletes that copy. If someone
edited through the installed path (B-027), those bytes are the only copy.
"""
import tempfile
import unittest
from pathlib import Path

import dev_install


class EditsInAnInstalledCopyAreNoticed(unittest.TestCase):
    def pair(self, copy_files, source_files):
        base = Path(tempfile.mkdtemp())
        for name, files in (("copy", copy_files), ("source", source_files)):
            for rel, body in files.items():
                target = base / name / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body)
        return base / "copy", base / "source"

    def test_identical_trees_report_nothing(self):
        copy, source = self.pair({"SKILL.md": "same", "scripts/a.py": "same"},
                                 {"SKILL.md": "same", "scripts/a.py": "same"})
        self.assertEqual(dev_install.edited(copy, source), [])

    def test_an_edited_file_is_named_with_its_path(self):
        copy, source = self.pair({"scripts/a.py": "edited in the copy"},
                                 {"scripts/a.py": "original"})
        self.assertEqual(dev_install.edited(copy, source), ["scripts/a.py"])

    def test_fog_only_files_are_not_edits(self):
        copy, source = self.pair({"SKILL.md": "same"},
                                 {"SKILL.md": "same", "AGENTS.md": "dev only",
                                  "scripts/test_x.py": "dev only"})
        self.assertEqual(dev_install.edited(copy, source), [])

    def test_cook_is_installable_even_though_discover_skips_it(self):
        self.assertIn("cook", dev_install.targets(dev_install.ROOT))


if __name__ == "__main__":
    unittest.main()
