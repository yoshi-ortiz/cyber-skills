import urllib.error
import io
import contextlib
#!/usr/bin/env python3
"""Tests for the Food Product loop.

The loop's own first version passed against the broken state it existed to
catch, so the case that matters most here is `test_an_unreadable_page_fails`:
a checker that cannot see the page must say so rather than report a pass.
"""
import json
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import cook
import qa
import screen


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
        parsed = screen.Screen()
        parsed.feed(document)
        return parsed

    def test_the_placeholder_heading_is_read(self):
        parsed = self._parse("<html><body><h1>Brainstorm Companion</h1>"
                             "<p>Waiting for the agent to push a screen...</p></body></html>")
        self.assertIn(cook.PLACEHOLDER_HEADING, parsed.headings)

    def test_a_real_screen_carries_its_own_heading(self):
        parsed = self._parse("<html><body><h1>Cover round</h1>"
                             '<div class="dh-fb" data-element="cover.hero">'
                             '<button data-rank="5">5</button></div></body></html>')
        self.assertNotIn(cook.PLACEHOLDER_HEADING, parsed.headings)
        self.assertEqual(parsed.rankable_elements, {"cover.hero"})

    def test_an_unrelated_button_is_not_a_ranking_control(self):
        parsed = self._parse("<html><body><h1>Landing page</h1>"
                             "<button>Install</button></body></html>")
        self.assertEqual(parsed.rankable_elements, set())

    def test_a_rank_outside_a_decision_row_is_not_rankable(self):
        parsed = self._parse("<html><body><h1>Broken round</h1>"
                             '<button data-rank="5">5</button></body></html>')
        self.assertEqual(parsed.rankable_elements, set())

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


class TheRoundStopsWhatItStarted(unittest.TestCase):
    """A leaked companion is a node process per run, and `clean` deleting the
    tree under a live one leaves it serving a directory that is gone."""

    def pid_file(self, project: Path, pid: int) -> None:
        state = project / cook.COMPANION / "1-1" / "state"
        state.mkdir(parents=True)
        (state / "server.pid").write_text(str(pid), encoding="utf-8")

    def test_every_session_pid_is_signalled(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.pid_file(project, 4242)
            killed = []
            with unittest.mock.patch.object(cook.os, "kill",
                                            lambda pid, sig: killed.append(pid)):
                self.assertEqual(cook.stop_companion(project), [4242])
            self.assertEqual(killed, [4242])

    def test_a_dead_pid_is_not_an_error(self):
        # The server exited on its own. Nothing to stop is a clean stop.
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.pid_file(project, 4242)
            with unittest.mock.patch.object(cook.os, "kill",
                                            side_effect=ProcessLookupError):
                self.assertEqual(cook.stop_companion(project), [])

    def test_a_corrupt_pid_file_is_skipped_rather_than_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.pid_file(project, 0)
            (project / cook.COMPANION / "1-1" / "state" / "server.pid").write_text("nonsense")
            self.assertEqual(cook.stop_companion(project), [])

    def test_no_companion_state_stops_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cook.stop_companion(Path(tmp)), [])


class APreviewMustActuallyDraw(unittest.TestCase):
    """B: the companion served a structurally perfect rankable row whose
    graphic was a white rectangle, and `screen-is-rankable` passed it. A
    proposal the designer cannot see is not a proposal."""

    def _shots(self, document: str) -> dict:
        parsed = screen.Screen()
        parsed.feed(document)
        return parsed.shots

    def test_an_inlined_image_counts_as_drawn(self):
        shots = self._shots('<div class="dh-shot" data-el="a">'
                            '<img src="data:image/png;base64,AAA"></div>')
        self.assertTrue(shots["a"]["drawn"])
        self.assertEqual(shots["a"]["offsite"], [])

    def test_an_empty_shot_is_not_drawn(self):
        shots = self._shots('<div class="dh-shot" data-el="a">'
                            '<span class="dh-shot-missing">sin gráfico</span></div>')
        self.assertFalse(shots["a"]["drawn"])

    def test_a_relative_source_is_offsite_because_the_companion_moves_the_document(self):
        shots = self._shots('<div class="dh-shot" data-el="a">'
                            '<img src="../shots/hero.svg"></div>')
        self.assertEqual(shots["a"]["offsite"], ["../shots/hero.svg"])

    def test_a_shot_does_not_leak_into_the_next_row(self):
        shots = self._shots('<div class="dh-shot" data-el="a">'
                            '<img src="data:image/png;base64,AAA"></div>'
                            '<div class="dh-shot" data-el="b"></div>')
        self.assertTrue(shots["a"]["drawn"])
        self.assertFalse(shots["b"]["drawn"])

class TheStartupRaceIsARetryNotAFailure(unittest.TestCase):
    """`run` starts the companion and fetches immediately. A refused socket
    usually means it is not bound yet, and that used to fail the round."""

    def test_a_refused_socket_is_retried_until_it_answers(self):
        answers = [ConnectionRefusedError(), ConnectionRefusedError(), "<html>ok</html>"]

        def flaky(request, timeout=None):
            head = answers.pop(0)
            if isinstance(head, Exception):
                raise urllib.error.URLError(head)
            return contextlib.closing(io.BytesIO(head.encode()))

        with unittest.mock.patch.object(cook.urllib.request, "urlopen", flaky):
            self.assertIn("ok", cook.served_document("1234", "t"))
        self.assertEqual(answers, [])

    def test_a_server_that_answers_with_an_error_fails_on_the_first_try(self):
        calls = []

        def erroring(request, timeout=None):
            calls.append(1)
            raise urllib.error.HTTPError("u", 500, "boom", {}, None)

        with unittest.mock.patch.object(cook.urllib.request, "urlopen", erroring):
            with self.assertRaises(cook.CookError) as raised:
                cook.served_document("1234", "t")
        self.assertIn("500", str(raised.exception))
        self.assertEqual(len(calls), 1)

    def test_a_socket_refused_past_the_grace_window_still_fails(self):
        def refused(request, timeout=None):
            raise urllib.error.URLError(ConnectionRefusedError())

        with unittest.mock.patch.object(cook, "STARTUP_GRACE", 0), \
             unittest.mock.patch.object(cook.urllib.request, "urlopen", refused):
            with self.assertRaises(cook.CookError):
                cook.served_document("1234", "t")
