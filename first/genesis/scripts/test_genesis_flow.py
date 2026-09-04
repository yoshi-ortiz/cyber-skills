#!/usr/bin/env python3
"""Tests for Genesis flow state evaluation and action gating."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genesis_flow import FLOW, SKILL_MD, main, next_action, read_state, topology


def state(*absent: str) -> dict:
    """A state whose canonical files are all present except the ones named."""
    return {"present": {path: path not in absent for path in topology()},
            "totalTasks": 2, "inProgressCount": 1, "todoCount": 1,
            "doneCount": 0, "unprovenDone": []}


class DoctrineTests(unittest.TestCase):
    """SKILL.md is canonical; this module may not name a path it dropped."""

    def test_topology_reads_the_skill_table(self) -> None:
        canon = topology()
        self.assertIn("docs/REQUIREMENTS.md", canon)
        self.assertIn("docs/SPEC/", canon)
        self.assertIn("docs/adr/", canon)
        self.assertIn("ROADMAP.md", canon)
        # Prose, not topology: a cell that is not a path stays out.
        self.assertTrue(all(path.endswith((".md", "/")) for path in canon))

    def test_every_flow_path_is_doctrine(self) -> None:
        canon = topology()
        for action, paths, _condition, _explanation in FLOW:
            for path in paths:
                self.assertIn(path, canon,
                              f"{action} reads {path}, which SKILL.md no longer lists")

    def test_missing_doctrine_yields_no_topology(self) -> None:
        self.assertEqual(topology(SKILL_MD.parent / "no-such-file.md"), {})


class GenesisFlowTests(unittest.TestCase):
    def test_missing_requirements_triggers_interview(self) -> None:
        action = next_action(state("docs/REQUIREMENTS.md"))
        self.assertEqual(action["action"], "interview")
        self.assertIn("docs/REQUIREMENTS.md", action["reason"])

    def test_requirements_without_specs_triggers_promote_spec(self) -> None:
        action = next_action(state("docs/SPEC/"))
        self.assertEqual(action["action"], "promote-spec")
        self.assertIn("docs/SPEC/", action["reason"])

    def test_specs_without_glossary_triggers_declare_glossary(self) -> None:
        action = next_action(state("docs/GLOSSARY.md"))
        self.assertEqual(action["action"], "declare-glossary")
        self.assertIn("docs/GLOSSARY.md", action["reason"])

    def test_missing_roadmap_triggers_sync_roadmap(self) -> None:
        broken = state("ROADMAP.md")
        broken["totalTasks"] = 0
        action = next_action(broken)
        self.assertEqual(action["action"], "sync-roadmap")
        self.assertIn("ROADMAP.md", action["reason"])

    def test_unadvanced_tasks_trigger_advance_task(self) -> None:
        stalled = state()
        stalled.update(totalTasks=5, inProgressCount=0, todoCount=5)
        action = next_action(stalled)
        self.assertEqual(action["action"], "advance-task")
        self.assertIn("IN-PROGRESS", action["reason"])

    def test_unproven_done_triggers_verify_proof(self) -> None:
        unproven = state()
        unproven.update(doneCount=1, unprovenDone=["R-01 initial skeleton"])
        action = next_action(unproven)
        self.assertEqual(action["action"], "verify-proof")
        self.assertIn("R-01 initial skeleton", action["reason"])

    def test_fully_proven_project_reports_done(self) -> None:
        self.assertEqual(next_action(state())["action"], "done")

    def test_adr_absence_is_not_a_gap(self) -> None:
        """The doctrine makes a record conditional, so a project with none is fine."""
        self.assertEqual(next_action(state("docs/adr/"))["action"], "done")

    def test_read_state_on_disk(self) -> None:
        with tempfile.TemporaryDirectory(prefix="genesis-flow-test-") as temp:
            root = Path(temp)
            st = read_state(root)
            self.assertFalse(st["present"]["docs/REQUIREMENTS.md"])
            self.assertFalse(st["present"]["docs/SPEC/"])

            docs = root / "docs"
            docs.mkdir(parents=True)
            (docs / "REQUIREMENTS.md").write_text("User wants a parser.", encoding="utf-8")
            st = read_state(root)
            self.assertTrue(st["present"]["docs/REQUIREMENTS.md"])
            self.assertFalse(st["present"]["docs/SPEC/"])

            spec_dir = docs / "SPEC"
            spec_dir.mkdir()
            (spec_dir / "PARSER.md").write_text("# Parser Spec\nContract details.", encoding="utf-8")
            st = read_state(root)
            self.assertTrue(st["present"]["docs/SPEC/"])
            self.assertFalse(st["present"]["docs/GLOSSARY.md"])

            (docs / "GLOSSARY.md").write_text("| Term | Meaning |\n| Parser | Token reader |", encoding="utf-8")
            st = read_state(root)
            self.assertTrue(st["present"]["docs/GLOSSARY.md"])
            self.assertFalse(st["present"]["ROADMAP.md"])

            (root / "ROADMAP.md").write_text(
                "| id | State | Item |\n| --- | --- | --- |\n| R-1 | `IN-PROGRESS` | Build parser |\n",
                encoding="utf-8",
            )
            st = read_state(root)
            self.assertTrue(st["present"]["ROADMAP.md"])
            self.assertEqual(st["totalTasks"], 1)
            self.assertEqual(st["inProgressCount"], 1)
            self.assertEqual(next_action(st)["action"], "done")

    def test_cli_json_and_check_flags(self) -> None:
        with tempfile.TemporaryDirectory(prefix="genesis-cli-test-") as temp:
            root = Path(temp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["--project-root", str(root), "--json", "--check"])
            # Fails check because empty dir has action "interview"
            self.assertEqual(code, 1)
            output = json.loads(buf.getvalue())
            self.assertEqual(output["nextAction"], "interview")


if __name__ == "__main__":
    unittest.main()
