"""Exercise the standalone public functions and CLI against project files."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import compass


class CompassTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, body):
        (self.root / "ROADMAP.md").write_text(body, encoding="utf-8")

    def table(self, rows):
        self.write("| ID | State | Workstream | Depends on | Priority | Deferred | Item | Scope | Proof | Budget tokens |\n"
                   "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n" + rows)

    def cli(self, *args, status=0):
        before = {path.relative_to(self.root): path.read_bytes()
                  for path in self.root.rglob("*") if path.is_file()}
        proc = subprocess.run([sys.executable, str(Path(compass.__file__).resolve()),
                               "--project-root", str(self.root), *args],
                              cwd=self.root, capture_output=True, text=True)
        self.assertEqual(proc.returncode, status, proc.stderr + proc.stdout)
        self.assertEqual(before, {path.relative_to(self.root): path.read_bytes()
                                 for path in self.root.rglob("*") if path.is_file()})
        return json.loads(proc.stdout)

    def test_selection_orders_priority_then_document_and_bounds_context(self):
        self.table("| prerequisite | DONE | default | | | | Setup | | | |\n"
                   "| later | TODO | default | prerequisite | 4 | | Later | | | |\n"
                   "| quick | TODO | default | prerequisite | 1 | false | Quick win | src/ | test command | 800 |\n"
                   "| tie | TODO | default | | 1 | | Another | | | |\n"
                   "| deferred | TODO | default | | 0 | true | Wait | | | |\n"
                   "| dependency | TODO | default | later | 0 | | Wait | | | |\n")
        result = self.cli("next")
        self.assertEqual(result, {"id": "quick", "item_id": "quick", "item": "Quick win", "state": "TODO",
                                 "workstream": "default", "scope": "src/", "proof": "test command",
                                 "budget_tokens": "800", "next_action": "advance-task"})
        self.assertEqual(self.cli("check"), {"ok": True, "errors": []})

    def test_continue_active_and_allow_explicit_user_choice(self):
        self.table("| active | IN-PROGRESS | default | | 9 | | Work | | | |\n"
                   "| quick | TODO | default | | 0 | | Quick | | | |\n"
                   "| other | IN-PROGRESS | docs | | | | Docs | | | |\n")
        self.assertEqual(self.cli("next")["next_action"], "continue-task")
        self.assertEqual(self.cli("next")["id"], "active")
        self.assertEqual(self.cli("next", "--item", "quick")["id"], "quick")
        self.assertEqual(self.cli("next", "--workstream", "docs")["id"], "other")

    def test_legacy_rows_headers_links_emoji_and_escaped_pipe(self):
        self.write("| Item | State | ID | Depends on |\n| --- | --- | --- | --- |\n"
                   "| Section | | | |\n"
                   "| Old \\| feature | ⚪ `TODO` | [feature.alpha](somewhere.md) | — |\n"
                   "| Prose | TODO | legacy | MVP release |\n"
                   "```markdown\n| ID | State |\n| --- | --- |\n| example | BAD |\n```\n")
        rows = compass.roadmap_rows(self.root)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"item": "Old | feature", "state": "TODO",
                                   "id": "feature.alpha", "depends on": "—"})
        self.assertEqual(self.cli("check")["errors"], [])
        self.assertEqual(self.cli("next")["next_action"], "no-ready-item")
        self.assertEqual(self.cli("next", "--item", "feature.alpha")["id"], "feature.alpha")
        self.assertIn("not eligible", self.cli("next", "--item", "legacy", status=1)["errors"][0])

    def test_structural_errors_fail_check_and_selection(self):
        cases = [
            ("| x | TODO | default | | | |\n| x | TODO | | | | |\n", "duplicate ID"),
            ("| | TODO | default | | | |\n", "empty ID"),
            ("| x | MAYBE | default | | | |\n", "invalid state"),
            ("| x | TODO | default | absent | | |\n", "unresolved dependency"),
            ("| x | TODO | default | y | | |\n| y | TODO | default | x | | |\n", "dependency cycle"),
            ("| x | DONE | default | x | | |\n", "dependency cycle"),
            ("| x | IN-PROGRESS | default | | | |\n| y | IN-PROGRESS | default | | | |\n", "multiple IN-PROGRESS"),
            ("| x | IN-PROGRESS | default | y | | |\n| y | TODO | other | | | |\n", "not DONE"),
            ("| x | TODO | default | | urgent | |\n", "priority"),
            ("| x | TODO | default | | | maybe |\n", "deferred"),
            ("| x | TODO | default | | | | Title | | | -5 |\n", "budget tokens"),
        ]
        for rows, message in cases:
            with self.subTest(message=message):
                self.table(rows)
                self.assertTrue(any(message in error for error in compass.check(self.root)))
                self.assertFalse(self.cli("check", status=1)["ok"])
                self.assertFalse(self.cli("next", status=1)["ok"])

    def test_explicit_selection_obeys_state_deferral_and_dependencies(self):
        self.table("| done | DONE | default | | | |\n"
                   "| blocked | BLOCKED | default | | | |\n"
                   "| deferred | TODO | default | | | true |\n"
                   "| waiting | TODO | default | blocked | | |\n"
                   "| ready | TODO | default | done | | |\n")
        for identity in ("done", "blocked", "deferred", "waiting", "missing"):
            with self.subTest(identity=identity):
                self.assertFalse(self.cli("next", "--item", identity, status=1)["ok"])
        self.assertEqual(self.cli("next")["id"], "ready")

    def test_multiple_dependencies_can_reference_legacy_done(self):
        self.table("| old | DONE | | prose retained | | |\n"
                   "| new | DONE | default | | | |\n"
                   "| feature with spaces | TODO | default | old; new | | |\n")
        self.assertEqual(self.cli("next")["id"], "feature with spaces")

    def test_missing_invalid_encoding_empty_and_no_ready_project(self):
        self.assertFalse(self.cli("check", status=1)["ok"])
        self.assertFalse(self.cli("next", status=1)["ok"])
        (self.root / "ROADMAP.md").write_bytes(b"\xff")
        self.assertFalse(self.cli("check", status=1)["ok"])
        self.write("# No planned work\n")
        self.assertEqual(self.cli("check")["errors"], [])
        self.assertEqual(self.cli("next")["next_action"], "no-ready-item")
        self.table("| finished | DONE | default | | | |\n")
        self.assertEqual(self.cli("next")["next_action"], "no-ready-item")

    def test_standalone_copy_needs_no_skill_installation_or_shot_reader(self):
        copied = self.root / "compass.py"
        copied.write_bytes(Path(compass.__file__).read_bytes())
        self.table("| feature | TODO | default | | | |\n")
        shots = self.root / ".audit" / "shots"
        shots.mkdir(parents=True)
        (shots / "unrelated.json").write_text("invalid JSON", encoding="utf-8")
        proc = subprocess.run([sys.executable, "-I", str(copied), "--project-root",
                               str(self.root), "next"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["id"], "feature")


if __name__ == "__main__":
    unittest.main()
