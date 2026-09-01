#!/usr/bin/env python3
"""The four things that can be wrong quietly.

A validator that passes a bad record, a verdict that reads praise into a
correction, a token total that compares across profiles, and a table that drops
a metric. Everything else fails loudly on its own.
"""
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
            path.write_text(json.dumps(shot()))
            qa.main(["feedback", str(path), "good but the split is wrong, fix it"])
            self.assertEqual(qa.verdict(json.loads(path.read_text())), "failed")

    def test_plain_acceptance_is_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.json"
            path.write_text(json.dumps(shot()))
            qa.main(["feedback", str(path), "looks good, ship it"])
            self.assertEqual(qa.verdict(json.loads(path.read_text())), "accepted")

    def test_silence_stays_pending_and_never_becomes_accepted(self):
        self.assertEqual(qa.verdict(shot()), "pending")

    def test_a_present_hard_veto_is_listed_but_contamination_is_not(self):
        record = shot(findings=[
            {"id": "scope_breach", "status": "present"},
            {"id": "context_contamination", "status": "present"}])
        self.assertEqual(qa.vetoes(record), ["scope_breach"])


class Metrics(unittest.TestCase):
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
