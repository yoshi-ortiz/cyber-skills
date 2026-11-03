#!/usr/bin/env python3
"""Kit cannot promise a harness command that does not exist."""
import tempfile
import unittest
from pathlib import Path

import kit_gate


class KitCitesTheRealHarness(unittest.TestCase):
    def tree(self, skill: str, harness: str | None = None) -> tuple[Path, Path]:
        root = Path(tempfile.mkdtemp())
        (root / "kit").mkdir()
        (root / "kit" / "SKILL.md").write_text(skill)
        script = root / "harness.py"
        if harness is not None:
            script.write_text(harness)
        return root, script

    def test_a_real_command_passes(self):
        root, script = self.tree("run `python3 ~/.harness-core/harness.py sync`")
        self.assertEqual(kit_gate.check(root, script), [])

    def test_an_unshipped_command_fails(self):
        root, script = self.tree("`harness.py domain design`")
        self.assertIn("harness.py domain", kit_gate.check(root, script)[0])

    def test_an_invented_state_file_fails(self):
        root, script = self.tree("picks go to `~/.harness-core.json`")
        self.assertIn("harness-core.json", kit_gate.check(root, script)[0])

    def test_harness_drift_from_the_pin_fails(self):
        root, script = self.tree("ok", 'choices=("sync", "status")')
        self.assertIn("differ from the pin", kit_gate.check(root, script)[0])

    def test_the_repository_passes(self):
        self.assertEqual(kit_gate.check(), [])


if __name__ == "__main__":
    unittest.main()
