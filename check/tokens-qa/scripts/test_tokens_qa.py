#!/usr/bin/env python3
"""The four things that can be wrong quietly.

A validator that passes a bad record, a verdict that reads praise into a
correction, a token total that compares across profiles, and a table that drops
a metric. Everything else fails loudly on its own.
"""
import contextlib
import io
import json
import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tokens_qa as qa


FIXTURES = Path(__file__).with_name("shot_contract_fixtures.json")


def shot(**over):
    record = {
        "version": 1, "shot_id": "s1", "scope": "one task",
        "inputs": {"request": "do it", "prompt_hash": qa.sha256("do it"),
                   "corpus_refs": [], "tools": []},
        "compute": {"model": "m", "harness": "h", "started_at": "2026-01-01T00:00:00Z",
                    "duration_ms": 0,
                    "tokens": {"input": 10, "output": 20, "profile": "exact"}},
        "output": {"adapter": "text", "inline": {"text": "done"}},
        "provenance": "inference", "user_feedback": {"status": "pending"},
        "findings": [],
    }
    record.update(over)
    return record


class Validation(unittest.TestCase):
    def test_a_good_record_passes(self):
        self.assertTrue(qa.validate(shot()))

    def test_a_missing_key_names_its_json_path(self):
        bad = shot()
        del bad["compute"]["model"]
        with self.assertRaises(qa.Invalid) as e:
            qa.validate(bad)
        self.assertIn("$.compute.model", str(e.exception))

    def test_output_must_be_exactly_one_of_path_and_inline(self):
        for output in ({"adapter": "t"}, {"adapter": "t", "path": "a", "inline": {}}):
            with self.assertRaises(qa.Invalid):
                qa.validate(shot(output=output))

    def test_an_unlisted_finding_id_is_refused(self):
        with self.assertRaises(qa.Invalid):
            qa.validate(shot(findings=[{"id": "vibes_off", "status": "present"}]))

    def test_multimodal_contract_fixtures_validate_the_same_boundary(self):
        fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
        for fixture in fixtures["valid"]:
            with self.subTest(fixture["name"]):
                self.assertTrue(qa.validate(fixture["record"]))

        base = fixtures["valid"][0]["record"]
        for fixture in fixtures["invalid"]:
            record = copy.deepcopy(base)
            path = fixture.get("replace") or fixture["delete"]
            parent = record
            for key in path[:-1]:
                parent = parent[key]
            if "replace" in fixture:
                parent[path[-1]] = fixture["value"]
            else:
                del parent[path[-1]]
            with self.subTest(fixture["name"]):
                with self.assertRaises(qa.Invalid) as raised:
                    qa.validate(record)
                self.assertIn(fixture["path"], str(raised.exception))


class Verdict(unittest.TestCase):
    def test_praise_with_a_correction_in_it_is_not_acceptance(self):
        # The case this whole tool exists for: "good but fix X" is a failure.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.json"
            path.write_text(json.dumps(shot(version=2)))
            qa.main(["feedback", str(path), "--status", "accepted",
                     "--correction", "good but the split is wrong, fix it"])
            self.assertEqual(qa.verdict(json.loads(path.read_text())), "failed")

    def test_plain_acceptance_is_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.json"
            path.write_text(json.dumps(shot(version=2)))
            qa.main(["feedback", str(path), "--status", "accepted"])
            self.assertEqual(qa.verdict(json.loads(path.read_text())), "accepted")

    def test_silence_stays_pending_and_never_becomes_accepted(self):
        self.assertEqual(qa.verdict(shot()), "pending")

    def test_a_present_hard_veto_is_listed_but_contamination_is_not(self):
        record = shot(findings=[
            {"id": "scope_breach", "status": "present"},
            {"id": "context_contamination", "status": "present"}])
        self.assertEqual(qa.vetoes(record), ["scope_breach"])


class ContextDerail(unittest.TestCase):
    """The veto QA.md names and nothing could ever raise.

    `findings` was written once, as `[]`, and never appended to, so
    `context_derail` reported `none` on every shot ever recorded -- including
    the ones the user rejected for exactly that reason.

    The veto is universal; the context map is the project's. This package
    never learns a folder layout: it classifies whatever it is handed.
    """
    CONTEXTS = {"api": ("src/api/",), "ui": ("src/ui/",)}

    def test_one_context_alone_is_not_a_derail(self):
        self.assertEqual(qa.derail_finding(["src/api/auth.py"], self.CONTEXTS), [])
        self.assertEqual(qa.derail_finding(["src/ui/login.tsx"], self.CONTEXTS), [])
        self.assertEqual(qa.derail_finding([], self.CONTEXTS), [])

    def test_a_path_no_context_claims_is_not_a_derail(self):
        self.assertEqual(qa.derail_finding(["README.md"], self.CONTEXTS), [])

    def test_no_declared_contexts_means_nothing_to_observe(self):
        self.assertEqual(qa.derail_finding(["src/api/a.py", "src/ui/b.tsx"], {}), [])

    def test_both_contexts_in_one_pass_raise_the_veto(self):
        found = qa.derail_finding(["src/api/auth.py", "src/ui/login.tsx"], self.CONTEXTS)
        self.assertEqual([f["id"] for f in found], ["context_derail"])
        self.assertEqual(found[0]["status"], "present")
        # The evidence names the contexts and a path from each, or a reader
        # cannot act on it.
        self.assertIn("api", found[0]["evidence"])
        self.assertIn("ui", found[0]["evidence"])
        self.assertIn("src/api/auth.py", found[0]["evidence"])

    def test_the_veto_reaches_the_report(self):
        record = shot(findings=qa.derail_finding(
            ["src/api/a.py", "src/ui/b.tsx"], self.CONTEXTS))
        self.assertEqual(qa.vetoes(record), ["context_derail"])
        self.assertEqual(qa.metrics(record)["hard_vetoes"], "context_derail")

    def test_a_context_spec_parses_from_the_command_line(self):
        self.assertEqual(qa.parse_contexts(["api=src/api/", "ui=src/ui/,web/"]),
                         {"api": ("src/api/",), "ui": ("src/ui/", "web/")})

    def test_a_malformed_context_spec_is_refused_not_ignored(self):
        with self.assertRaises(qa.Refused):
            qa.parse_contexts(["src/api/"])


class ScopeBreach(unittest.TestCase):
    """The second finding id with a reader and no writer.

    `scope` is the one bounded task a Shot claims. Nothing compared that claim
    against what the pass actually wrote, so a run could name a narrow scope,
    edit half the tree, and still report `hard_vetoes: none`.

    Universal like the derail: the caller declares which paths the bounded task
    was allowed to touch. This package never guesses a layout.
    """

    def test_writing_only_inside_the_declared_scope_is_clean(self):
        self.assertEqual(
            qa.scope_finding(["src/api/a.py", "src/api/b.py"], ("src/api/",)), [])

    def test_no_declared_scope_paths_means_nothing_to_check(self):
        self.assertEqual(qa.scope_finding(["anything.py"], ()), [])

    def test_writing_outside_the_declared_scope_raises_the_veto(self):
        found = qa.scope_finding(["src/api/a.py", "docs/readme.md", "web/app.js"],
                                 ("src/api/",))
        self.assertEqual([f["id"] for f in found], ["scope_breach"])
        self.assertEqual(found[0]["status"], "present")
        # Names what fell outside, or it cannot be acted on.
        self.assertIn("docs/readme.md", found[0]["evidence"])
        self.assertIn("web/app.js", found[0]["evidence"])

    def test_the_veto_reaches_the_report(self):
        record = shot(findings=qa.scope_finding(["out/of/scope.py"], ("src/",)))
        self.assertEqual(qa.vetoes(record), ["scope_breach"])
        self.assertEqual(qa.metrics(record)["hard_vetoes"], "scope_breach")

    def test_both_vetoes_can_stand_on_one_shot(self):
        paths = ["src/api/a.py", "src/ui/b.tsx"]
        found = (qa.derail_finding(paths, {"api": ("src/api/",), "ui": ("src/ui/",)})
                 + qa.scope_finding(paths, ("src/api/",)))
        self.assertEqual(sorted(qa.vetoes(shot(findings=found))),
                         ["context_derail", "scope_breach"])


class RecordPrintsTheTable(unittest.TestCase):
    """`record` printed a path. Reading the shot it just wrote took a second
    command, so the number a person came for was never on screen."""

    def test_recording_prints_the_observation_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            here = Path(tmp)
            req = here / "req.txt"
            req.write_text("draw the thing", encoding="utf-8")
            argv = ["record", "some-skill", "--request", str(req),
                    "--inline", "the output", "--scope", "one-bounded-task"]
            cwd = Path.cwd()
            try:
                import os
                os.chdir(here)
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(qa.main(argv), 0)
            finally:
                os.chdir(cwd)
            printed = out.getvalue()
            self.assertIn("one-bounded-task", printed)
            self.assertIn("hard_vetoes", printed)
            self.assertIn("verdict", printed)
            self.assertIn("+---", printed)   # the ascii table, not a path


class Metrics(unittest.TestCase):
    def test_admitted_context_is_a_field_a_valid_shot_may_carry(self):
        """`metrics` read `inputs.admitted_context`; the contract refused it as
        an unknown field. Two modules in one package, disagreeing, with the
        suite green -- so `context.status` could only ever say not_observed."""
        record = shot()
        record["inputs"]["admitted_context"] = ["first/aesthetic/scripts"]
        qa.validate(record)
        self.assertEqual(qa.metrics(record)["context.status"], "observed")

    def test_admitted_context_with_a_derail_reads_contaminated(self):
        record = shot(findings=[{"id": "context_derail", "status": "present"}])
        record["inputs"]["admitted_context"] = ["first/aesthetic/scripts", "design"]
        self.assertEqual(qa.metrics(record)["context.status"], "contaminated")

    def test_absent_admitted_context_is_not_observed_never_clean(self):
        self.assertEqual(qa.metrics(shot())["context.status"], "not_observed")

    def test_a_null_count_makes_the_total_unavailable(self):
        record = shot()
        record["compute"]["tokens"] = {"input": None, "output": 5, "profile": "unavailable"}
        self.assertEqual(qa.totals(record), (None, "unavailable"))
        self.assertEqual(qa.metrics(record)["tokens.total"], "unavailable")

    def test_an_estimated_total_is_marked_and_an_exact_one_is_not(self):
        self.assertEqual(qa.metrics(shot())["tokens.total"], "30")
        record = shot()
        record["compute"]["tokens"]["profile"] = "utf8_bytes_div4_ceil_v1"
        self.assertEqual(qa.metrics(record)["tokens.total"], "~30")


class Table(unittest.TestCase):
    def test_every_metric_gets_two_physical_rows_and_no_line_wraps(self):
        base = qa.metrics(shot())
        rendered = qa.table(base, base)
        for line in rendered.splitlines():
            self.assertEqual(len(line), len(rendered.splitlines()[0]), line)
        for key in qa.ORDER:
            self.assertIn(f"previous: {key}", rendered)
            self.assertIn(f"new: {key}", rendered)


if __name__ == "__main__":
    unittest.main()
