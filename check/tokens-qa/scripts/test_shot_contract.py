#!/usr/bin/env python3
"""What v2 has to keep true.

Every v1 record on disk still reads, the migration loses nothing and invents
nothing, and an unknown field names the exact place it was found.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shot_contract as sc


FIXTURES = json.loads(
    Path(__file__).with_name("shot_contract_fixtures.json").read_text(encoding="utf-8"))
VALID = [fixture["record"] for fixture in FIXTURES["valid"]]


class Compatibility(unittest.TestCase):
    def test_every_v1_fixture_migrates_and_validates(self):
        for fixture in FIXTURES["valid"]:
            with self.subTest(fixture["name"]):
                record = sc.validate(fixture["record"])
                self.assertEqual(record["version"], sc.CURRENT_VERSION)

    def test_every_invalid_fixture_still_fails_at_its_declared_path(self):
        base = VALID[0]
        for fixture in FIXTURES["invalid"]:
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
                with self.assertRaises(sc.Invalid) as raised:
                    sc.validate(record)
                self.assertIn(fixture["path"], str(raised.exception))


class Migration(unittest.TestCase):
    def test_a_v1_path_becomes_exactly_one_deliverable_artifact(self):
        output = sc.migrate(VALID[1])["output"]
        self.assertEqual(output["adapter"], "graphic")
        self.assertNotIn("path", output)
        self.assertEqual(output["artifacts"], [{
            "role": "deliverable",
            "path": "shots/hero.png",
            "mime": "image/png",
            "bytes": 2048,
        }])

    def test_an_absent_bytes_is_omitted_and_never_null(self):
        for record in (VALID[2], VALID[3]):
            artifact = sc.migrate(record)["output"]["artifacts"][0]
            with self.subTest(record["shot_id"]):
                self.assertNotIn("bytes", artifact)
                self.assertEqual(artifact["role"], "deliverable")

    def test_an_inline_output_keeps_inline_and_gains_no_artifacts(self):
        output = sc.migrate(VALID[0])["output"]
        self.assertEqual(output["inline"], {"text": "Shipped."})
        self.assertNotIn("artifacts", output)

    def test_a_v1_corpus_ref_string_becomes_a_descriptor(self):
        refs = sc.migrate(VALID[1])["inputs"]["corpus_refs"]
        self.assertEqual(refs, [{"path": "corpus/reference.png"},
                                {"path": "corpus/avoid.jpg"}])

    def test_a_descriptor_that_is_already_an_object_passes_through(self):
        record = copy.deepcopy(VALID[1])
        record["inputs"]["corpus_refs"] = [{"path": "a.png", "role": "avoid"}]
        self.assertEqual(sc.migrate(record)["inputs"]["corpus_refs"],
                         [{"path": "a.png", "role": "avoid"}])

    def test_migrate_does_not_mutate_its_argument(self):
        record = copy.deepcopy(VALID[1])
        before = copy.deepcopy(record)
        sc.migrate(record)
        self.assertEqual(record, before)

    def test_migrating_an_already_v2_record_is_a_no_op(self):
        once = sc.migrate(VALID[1])
        self.assertEqual(sc.migrate(once), once)

    def test_an_unsupported_version_is_refused(self):
        record = copy.deepcopy(VALID[0])
        record["version"] = 3
        with self.assertRaises(sc.Invalid) as raised:
            sc.migrate(record)
        self.assertIn("$.version: unsupported version", str(raised.exception))


class Strictness(unittest.TestCase):
    def test_an_unknown_nested_field_names_its_exact_path(self):
        record = copy.deepcopy(VALID[0])
        record["compute"]["tokens"]["surprise"] = True
        with self.assertRaises(sc.Invalid) as raised:
            sc.validate(record)
        self.assertEqual(str(raised.exception),
                         "$.compute.tokens.surprise: unknown field")

    def test_an_unknown_artifact_field_names_its_index(self):
        record = sc.migrate(VALID[1])
        record["output"]["artifacts"][0]["surprise"] = True
        with self.assertRaises(sc.Invalid) as raised:
            sc.validate_v2(record)
        self.assertIn("$.output.artifacts[0].surprise", str(raised.exception))

    def test_an_unknown_gate_field_names_its_gate(self):
        record = copy.deepcopy(VALID[0])
        record["gates"] = {"l1": {"status": "pass", "surprise": True}}
        with self.assertRaises(sc.Invalid) as raised:
            sc.validate(record)
        self.assertIn("$.gates.l1.surprise", str(raised.exception))

    def test_the_cli_written_feedback_fields_are_admitted(self):
        record = copy.deepcopy(VALID[0])
        record["user_feedback"] = {"status": "corrected", "correction": "fix it",
                                   "evidence": "fix it",
                                   "observed_at": "2026-09-01T02:51:48Z"}
        self.assertTrue(sc.validate(record))

    def test_optional_passes_and_gates_are_admitted(self):
        record = copy.deepcopy(VALID[0])
        record["compute"]["passes"] = [{"name": "compile", "tokens_input": 4000}]
        record["gates"] = {"l1": {"status": "pass", "name": "graphics_flow.status"},
                           "l2": {"status": "skip", "reason": "no browser"}}
        self.assertTrue(sc.validate(record))


if __name__ == "__main__":
    unittest.main()
