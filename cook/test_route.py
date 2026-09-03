#!/usr/bin/env python3
"""The route: which skills a Cook round walks, in which order, and whether they
are actually installed.

Blackbox, and the skills root is injected, because a route that only resolves
on the machine that wrote it is not a route.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

COOK = Path(__file__).resolve().parent / "cook.py"
ORDER = ["zoom-out", "diagnosing-bugs", "ponytail-review"]


def install(root: Path, *names: str) -> Path:
    for name in names:
        (root / name).mkdir(parents=True)
        (root / name / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    return root


def route(root: Path):
    done = subprocess.run(
        [sys.executable, str(COOK), "route", "--skills-root", str(root)],
        capture_output=True, text=True)
    return done, json.loads(done.stdout or "{}")


class ARouteThatCannotResolveIsNotARoute(unittest.TestCase):
    def test_every_missing_skill_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            done, result = route(Path(tmp))
        self.assertEqual(done.returncode, 1, done.stdout or done.stderr)
        self.assertEqual(result["unresolved"], ORDER)
        for name in ORDER:
            self.assertIn(name, done.stdout)

    def test_one_missing_skill_does_not_condemn_the_others(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = install(Path(tmp), "zoom-out", "ponytail-review")
            done, result = route(root)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(result["unresolved"], ["diagnosing-bugs"])

    def test_a_directory_without_a_skill_file_has_not_resolved(self):
        """An empty folder with the right name is not an installed skill."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install(root, *ORDER)
            (root / "zoom-out" / "SKILL.md").unlink()
            _, result = route(root)
        self.assertEqual(result["unresolved"], ["zoom-out"])


class TheOrderIsTheProduct(unittest.TestCase):
    def test_a_fully_installed_route_passes_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            done, result = route(install(Path(tmp), *ORDER))
        self.assertEqual(done.returncode, 0, done.stdout or done.stderr)
        self.assertEqual([step["name"] for step in result["route"]], ORDER)

    def test_reviewed_delivery_is_the_terminal_step_and_not_a_skill(self):
        """R-82 puts commit/push at the end of the route as a boundary, not as
        another thing to invoke."""
        with tempfile.TemporaryDirectory() as tmp:
            _, result = route(install(Path(tmp), *ORDER))
        self.assertNotIn("deliver", [step["name"] for step in result["route"]])
        self.assertIn("commit", result["terminal"].lower())


class TheRouterHoldsPointersNotDoctrine(unittest.TestCase):
    """R-82: Cook owns ordering and evidence correlation only. The moment a
    route entry carries the routed skill's rules, they exist in two places."""

    def test_a_step_carries_a_pointer_and_a_purpose_and_nothing_else(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, result = route(install(Path(tmp), *ORDER))
        for step in result["route"]:
            self.assertEqual(set(step), {"name", "purpose", "path", "resolved"})

    def test_a_purpose_is_one_line(self):
        """A paragraph here is doctrine arriving by the back door."""
        with tempfile.TemporaryDirectory() as tmp:
            _, result = route(install(Path(tmp), *ORDER))
        for step in result["route"]:
            self.assertNotIn("\n", step["purpose"])
            self.assertLess(len(step["purpose"]), 120, step["name"])


if __name__ == "__main__":
    unittest.main()
