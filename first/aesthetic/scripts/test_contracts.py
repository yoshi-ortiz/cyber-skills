"""Tests for directory context contracts.

A contract is a CONTEXT.md a directory carries, declaring what it is for, what
belongs in it, and what it costs. The checker is what makes skill development
incremental: you change one directory, check that one directory, move on.
"""
import tempfile
import unittest
from pathlib import Path

import contracts


def make(root: Path, name: str, body: str = "x") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


CONTRACT = """---
purpose: on-demand payload, never auto-loaded
admits: doctrine, examples, failure catalogues
refuses: anything SKILL.md must know before its first command
max_file_bytes: 100
---

Prose below the contract is ignored by the checker.
"""


class MissingContract(unittest.TestCase):
    def test_a_directory_with_no_context_md_is_a_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "thing.md")
            report = contracts.check(root)
            self.assertFalse(report.ok)
            self.assertIn("no CONTEXT.md", report.violations[0])


class Budget(unittest.TestCase):
    def test_files_within_budget_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)
            make(root, "small.md", "y" * 50)
            self.assertTrue(contracts.check(root).ok)

    def test_a_file_over_budget_is_named_with_its_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)
            make(root, "fat.md", "y" * 250)
            report = contracts.check(root)
            self.assertFalse(report.ok)
            self.assertIn("fat.md", report.violations[0])
            self.assertIn("250", report.violations[0])

    def test_the_contract_does_not_audit_itself(self):
        # CONTEXT.md is longer than the budget it sets; that is not a violation.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)      # ~230 bytes, budget is 100
            self.assertTrue(contracts.check(root).ok)


class Completeness(unittest.TestCase):
    def test_a_contract_missing_a_required_field_is_a_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", "---\npurpose: vague\n---\n")
            report = contracts.check(root)
            self.assertFalse(report.ok)
            self.assertTrue(any("admits" in v for v in report.violations))

    def test_a_complete_contract_reports_its_purpose(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)
            self.assertEqual(contracts.check(root).purpose,
                             "on-demand payload, never auto-loaded")


class Incremental(unittest.TestCase):
    """One directory at a time -- checking a dir must not walk into children."""

    def test_a_child_directory_is_not_audited_by_its_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)
            make(root, "child/fat.md", "y" * 250)
            self.assertTrue(contracts.check(root).ok)

    def test_walk_reports_each_directory_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)
            make(root, "child/fat.md", "y" * 250)
            reports = contracts.walk(root)
            self.assertEqual(len(reports), 2)
            self.assertTrue(reports[0].ok)          # root is fine
            self.assertFalse(reports[1].ok)         # child has no contract

    def test_results_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)
            make(root, "a.md", "y" * 250)
            make(root, "b.md", "y" * 250)
            self.assertEqual(contracts.check(root).violations,
                             contracts.check(root).violations)


class HiddenDirectories(unittest.TestCase):
    """The walk must skip a hidden directory AND everything under it.

    Testing only the directory's own name let the walk descend into
    `.git/refs/heads`: that directory is called `heads`, and only its ancestor
    makes it noise. A repository-root run reported 240 directories, nearly all
    of them git internals, which is why the checker was never pointed at the
    root it was needed at.
    """

    def test_a_child_of_a_hidden_directory_is_not_walked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)
            make(root, ".git/refs/heads/main")
            walked = {r.directory for r in contracts.walk(root)}
            self.assertEqual(walked, {root})

    def test_a_child_of_a_dunder_directory_is_not_walked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)
            make(root, "__pycache__/nested/thing.pyc")
            walked = {r.directory for r in contracts.walk(root)}
            self.assertEqual(walked, {root})

    def test_a_hidden_root_still_walks_its_visible_children(self):
        # The skip is relative to the root being checked. Checking a directory
        # that is itself hidden (a `.claude/skills/x` checkout) must not skip
        # everything inside it.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".hidden"
            make(root, "CONTEXT.md", CONTRACT)
            make(root, "child/thing.md")
            walked = {r.directory for r in contracts.walk(root)}
            self.assertEqual(walked, {root, root / "child"})


class Rendering(unittest.TestCase):
    def test_a_nested_directory_renders_its_path_not_just_its_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, "CONTEXT.md", CONTRACT)
            make(root, "assets/spec/thing.md")
            text = contracts.render(contracts.walk(root))
            self.assertIn("assets/spec", text)


if __name__ == "__main__":
    unittest.main()
