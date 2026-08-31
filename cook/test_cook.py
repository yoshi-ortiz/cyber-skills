#!/usr/bin/env python3
"""Tests for the dogfood loop.

The loop's own first version passed against the broken state it existed to
catch, so the case that matters most here is `test_an_unreadable_page_fails`:
a checker that cannot see the page must say so rather than report a pass.
"""
import tempfile
import unittest
from pathlib import Path

import cook


class TheRepositoryIsNotAProjectRoot(unittest.TestCase):
    """No flag opens this. Skill package and shot tests stay separate trees."""

    def test_the_repository_root_is_refused(self):
        with self.assertRaises(cook.CookError) as caught:
            cook.check_not_the_repo(cook.REPO)
        self.assertIn("contamination", str(caught.exception))

    def test_a_directory_inside_the_repository_is_refused(self):
        with self.assertRaises(cook.CookError):
            cook.check_not_the_repo(cook.REPO / "spec" / "design-harness")

    def test_a_scratch_tree_outside_the_repository_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cook.check_not_the_repo(Path(tmp))


class AScreenIsToldFromTheShell(unittest.TestCase):
    """Parsed structure, never a substring of the document."""

    def _parse(self, document: str) -> cook.Screen:
        parsed = cook.Screen()
        parsed.feed(document)
        return parsed

    def test_the_placeholder_heading_is_read(self):
        parsed = self._parse("<html><body><h1>Brainstorm Companion</h1>"
                             "<p>Waiting for the agent to push a screen...</p></body></html>")
        self.assertIn(cook.PLACEHOLDER_HEADING, parsed.headings)

    def test_a_real_screen_carries_its_own_heading(self):
        parsed = self._parse("<html><body><h1>Cover round</h1>"
                             "<form><button>5</button></form></body></html>")
        self.assertNotIn(cook.PLACEHOLDER_HEADING, parsed.headings)
        self.assertTrue(parsed.tags & {"form", "input", "button"})

    def test_an_unreadable_page_has_no_heading_to_stand_on(self):
        # The redirect shim at `/?key=`: a title, a script, and no heading.
        # Reading this document is how the first version went green.
        parsed = self._parse('<html><head><title>Opening</title></head>'
                             '<body><script>location.replace("/")</script></body></html>')
        self.assertEqual(parsed.headings, [])


class NoScreenIsNoPass(unittest.TestCase):

    def test_an_empty_content_directory_yields_no_screens(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / cook.COMPANION / "1-1" / "state").mkdir(parents=True)
            self.assertEqual(cook.screens_on_disk(project), [])

    def test_a_published_screen_is_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            content = project / cook.COMPANION / "1-1" / "content"
            content.mkdir(parents=True)
            (content / "screen.html").write_text("<h1>x</h1>", encoding="utf-8")
            self.assertEqual([p.name for p in cook.screens_on_disk(project)],
                             ["screen.html"])

    def test_missing_companion_state_is_an_error_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(cook.CookError):
                cook.companion_address(Path(tmp))


if __name__ == "__main__":
    unittest.main()
