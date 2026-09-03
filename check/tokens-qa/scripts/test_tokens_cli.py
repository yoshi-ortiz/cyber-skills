#!/usr/bin/env python3
"""The CLI as a process. Exit codes only mean something when a shell sees them.

Every case here drives `tokens_qa.py` through `subprocess`, so the assertions
are on the real exit status and the real bytes on disk, not on a return value a
future refactor could quietly stop honouring.
"""
import copy
import hashlib
import json
import re
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).with_name("tokens_qa.py"))

V1 = {
    "version": 1, "shot_id": "frozen", "scope": "one task",
    "inputs": {"request": "do it", "prompt_hash": "sha256:00", "corpus_refs": [],
               "tools": []},
    "compute": {"model": "m", "harness": "h", "started_at": "2026-01-01T00:00:00Z",
                "duration_ms": 0,
                "tokens": {"input": 10, "output": 20, "profile": "exact"}},
    "output": {"adapter": "text", "inline": {"text": "done"}},
    "provenance": "inference", "user_feedback": {"status": "pending"},
    "findings": [],
}


def run(*args, cwd=None, env=None):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True,
                          text=True, cwd=cwd, env=env)


def envelope(done):
    return json.loads(done.stdout)


class ShotAudit(unittest.TestCase):
    """Complaints, corrections and restatements are a QA judgement. They belong
    to this package, not to whichever loop happens to be asking."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.addCleanup(self.dir.cleanup)

    def audit(self, *turns):
        path = self.root / "evidence.json"
        path.write_text(json.dumps({"turns": list(turns)}), encoding="utf-8")
        done = run("shot-audit", "--evidence", str(path), "--json")
        return done, json.loads(done.stdout or "{}")

    def test_a_complaint_is_reported_as_one(self):
        done, body = self.audit("this is broken")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(body["result"]["complaints"], ["this is broken"])

    def test_an_instruction_restated_is_reported_as_restated(self):
        _, body = self.audit(
            "i initially requested to take over the claude design website",
            "you did not follow instructions about the claude design website")
        result = body["result"]
        self.assertEqual(len(result["corrections"]), 2)
        self.assertEqual(len(result["restated"]), 1)

    def test_praise_is_neither_a_complaint_nor_a_correction(self):
        _, body = self.audit("that screenshot looks great")
        self.assertEqual(body["result"]["complaints"], [])
        self.assertEqual(body["result"]["corrections"], [])

    def test_the_advisory_candidates_come_back_in_the_same_read(self):
        """One call, so a caller never has to run two commands and correlate
        their answers by hand."""
        _, body = self.audit("looks good")
        self.assertEqual([c["field"] for c in body["result"]["candidates"]],
                         ["status"])

    def test_a_bundle_without_turns_names_its_json_path(self):
        path = self.root / "evidence.json"
        path.write_text(json.dumps({"nope": []}), encoding="utf-8")
        done = run("shot-audit", "--evidence", str(path), "--json")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(json.loads(done.stdout)["path"], "$.turns")


class Recording(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.addCleanup(self.dir.cleanup)
        self.request = self.root / "req.txt"
        self.request.write_text("do the thing", encoding="utf-8")

    def manifest(self, blob=b"\xff\xd8\xff\x00not utf8 \xfe"):
        art = self.root / "art.bin"
        art.write_bytes(blob)
        path = self.root / "manifest.json"
        path.write_text(json.dumps({"adapter": "file", "artifacts": [
            {"role": "deliverable", "path": str(art), "mime": "image/png"}]}),
            encoding="utf-8")
        return path, art, blob

    def test_a_binary_artifact_is_hashed_without_decoding_it(self):
        manifest, art, blob = self.manifest()
        done = run("record", "first/aesthetic", "--request", str(self.request),
                   "--output-manifest", str(manifest), "--json", cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        body = envelope(done)
        record = json.loads(Path(body["result"]["path"]).read_text(encoding="utf-8"))
        artifact = record["output"]["artifacts"][0]
        self.assertEqual(artifact["bytes"], len(blob))
        self.assertEqual(artifact["path"], str(art))
        digest = "sha256:" + hashlib.sha256(blob).hexdigest()
        self.assertEqual(body["result"]["artifacts"][0]["sha256"], digest)

    def test_a_shot_carries_the_invocation_that_produced_it(self):
        """Without a run identity on the record, a Shot cannot be joined back to
        the session, table and feedback that belong to the same round."""
        done = run("record", "first/aesthetic", "--request", str(self.request),
                   "--inline", "the output", "--invocation", "aesthetic@t3",
                   "--json", cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        path = Path(envelope(done)["result"]["path"])
        record = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(record["inputs"]["invocation"], "aesthetic@t3")
        self.assertEqual(record["version"], 2)

    def test_a_shot_recorded_without_an_invocation_is_still_valid(self):
        """Every record already on disk was written without one. Requiring it
        would rewrite history rather than migrate it."""
        done = run("record", "first/aesthetic", "--request", str(self.request),
                   "--inline", "the output", "--json", cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        path = Path(envelope(done)["result"]["path"])
        record = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("invocation", record["inputs"])
        self.assertEqual(run("observe", str(path)).returncode, 0)

    def test_a_recorded_file_is_version_2_on_disk(self):
        done = run("record", "first/aesthetic", "--request", str(self.request),
                   "--inline", "the output", "--json", cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        path = Path(envelope(done)["result"]["path"])
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], 2)

    def test_an_oversized_inline_payload_names_its_json_path(self):
        done = run("record", "first/aesthetic", "--request", str(self.request),
                   "--inline", "x" * 65537, "--json", cwd=self.root)
        self.assertEqual(done.returncode, 2)
        body = envelope(done)
        self.assertEqual(body["path"], "$.output.inline")
        self.assertFalse(body["ok"])

    def test_an_inline_payload_at_the_limit_is_accepted(self):
        done = run("record", "first/aesthetic", "--request", str(self.request),
                   "--inline", "x" * 65536, "--json", cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_a_missing_request_file_is_an_io_failure(self):
        done = run("record", "first/aesthetic", "--request", str(self.root / "nope.txt"),
                   "--inline", "x", "--json", cwd=self.root)
        self.assertEqual(done.returncode, 3)
        self.assertEqual(envelope(done)["path"], None)

    def test_exactly_one_output_flag_is_required(self):
        self.assertEqual(run("record", "s", "--request", str(self.request),
                             cwd=self.root).returncode, 2)
        manifest, _, _ = self.manifest()
        self.assertEqual(run("record", "s", "--request", str(self.request),
                             "--inline", "x", "--output-manifest", str(manifest),
                             cwd=self.root).returncode, 2)

    def test_a_shot_id_collision_refuses_instead_of_overwriting(self):
        shim = self.root / "shim"
        shim.mkdir()
        (shim / "uuid.py").write_text(
            "class _U:\n    hex = 'f' * 32\n\n\ndef uuid4():\n    return _U()\n",
            encoding="utf-8")
        env = dict(os.environ, PYTHONPATH=str(shim))
        first = run("record", "s", "--request", str(self.request), "--inline", "one",
                    "--json", cwd=self.root, env=env)
        self.assertEqual(first.returncode, 0, first.stderr)
        path = Path(envelope(first)["result"]["path"])
        before = path.read_bytes()
        second = run("record", "s", "--request", str(self.request), "--inline", "two",
                     "--json", cwd=self.root, env=env)
        self.assertEqual(second.returncode, 4)
        self.assertEqual(path.read_bytes(), before)

    def test_two_concurrent_records_do_not_corrupt_each_other(self):
        procs = [subprocess.Popen(
            [sys.executable, SCRIPT, "record", "s", "--request", str(self.request),
             "--inline", f"payload {n}", "--json"], cwd=self.root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for n in range(2)]
        out = [p.communicate() for p in procs]
        self.assertEqual([p.returncode for p in procs], [0, 0], out)
        paths = [json.loads(o)["result"]["path"] for o, _ in out]
        self.assertEqual(len(set(paths)), 2)
        for path in paths:
            record = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(record["version"], 2)
        shots = list((self.root / ".audit" / "shots").iterdir())
        self.assertEqual(len(shots), 2, shots)


class Feedback(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.addCleanup(self.dir.cleanup)
        request = self.root / "req.txt"
        request.write_text("do the thing", encoding="utf-8")
        done = run("record", "first/aesthetic", "--request", str(request),
                   "--inline", "the output", "--json", cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.shot = envelope(done)["result"]["path"]

    def feedback_fields(self):
        record = json.loads(Path(self.shot).read_text(encoding="utf-8"))
        return record["user_feedback"]

    def test_a_correction_does_not_set_a_status(self):
        done = run("feedback", self.shot, "--correction", "use the other split",
                   "--json", cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        fields = self.feedback_fields()
        self.assertEqual(fields["correction"], "use the other split")
        self.assertEqual(fields["status"], "pending")
        self.assertNotIn("sentiment", fields)

    def test_a_status_does_not_set_a_sentiment_or_a_correction(self):
        run("feedback", self.shot, "--status", "accepted", cwd=self.root)
        fields = self.feedback_fields()
        self.assertEqual(fields["status"], "accepted")
        self.assertNotIn("sentiment", fields)
        self.assertNotIn("correction", fields)

    def test_a_sentiment_does_not_set_a_status(self):
        run("feedback", self.shot, "--sentiment", "negative", cwd=self.root)
        fields = self.feedback_fields()
        self.assertEqual(fields["sentiment"], "negative")
        self.assertEqual(fields["status"], "pending")

    def test_a_rank_sets_only_a_rank(self):
        run("feedback", self.shot, "--rank", "3", cwd=self.root)
        fields = self.feedback_fields()
        self.assertEqual(fields["rank"], 3)
        self.assertEqual(set(fields), {"status", "rank"})

    def test_no_flags_at_all_is_an_argument_failure(self):
        done = run("feedback", self.shot, "--json", cwd=self.root)
        self.assertEqual(done.returncode, 2)
        self.assertEqual(self.feedback_fields(), {"status": "pending"})

    def test_evidence_and_observed_at_survive_a_later_flag(self):
        path = Path(self.shot)
        record = json.loads(path.read_text(encoding="utf-8"))
        record["user_feedback"] = {"status": "pending",
                                   "evidence": "the split is wrong, fix it",
                                   "observed_at": "2026-01-01T00:00:00Z"}
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
        before = self.feedback_fields()
        self.assertIn("evidence", before)
        run("feedback", self.shot, "--rank", "1", cwd=self.root)
        after = self.feedback_fields()
        self.assertEqual(after["evidence"], before["evidence"])
        self.assertEqual(after["observed_at"], before["observed_at"])

    def test_a_v1_file_refuses_the_write_and_keeps_its_bytes(self):
        path = self.root / "v1.json"
        path.write_text(json.dumps(V1, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
        before = path.read_bytes()
        done = run("feedback", str(path), "--status", "accepted", "--json",
                   cwd=self.root)
        self.assertEqual(done.returncode, 2)
        self.assertEqual(path.read_bytes(), before)
        self.assertIn("record", envelope(done)["error"])

    def test_a_v1_file_still_reads(self):
        path = self.root / "v1.json"
        path.write_text(json.dumps(V1), encoding="utf-8")
        done = run("observe", str(path), cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)


class ReadOnly(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.addCleanup(self.dir.cleanup)

    def shot(self, name):
        path = self.root / name
        record = copy.deepcopy(V1)
        record.update(version=2, shot_id=name)
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return path

    def test_observe_does_not_modify_either_record(self):
        base, cand = self.shot("a.json"), self.shot("b.json")
        before = (base.read_bytes(), cand.read_bytes())
        done = run("observe", str(base), str(cand), cwd=self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual((base.read_bytes(), cand.read_bytes()), before)

    def test_compare_requires_both_records(self):
        base = self.shot("a.json")
        self.assertEqual(run("compare", str(base), cwd=self.root).returncode, 2)
        cand = self.shot("b.json")
        self.assertEqual(run("compare", str(base), str(cand),
                             cwd=self.root).returncode, 0)

    def test_a_missing_record_is_an_io_failure(self):
        done = run("observe", str(self.root / "gone.json"), "--json", cwd=self.root)
        self.assertEqual(done.returncode, 3)
        self.assertFalse(envelope(done)["ok"])

    def test_malformed_json_is_a_schema_failure_without_a_traceback(self):
        path = self.root / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        done = run("observe", str(path), "--json", cwd=self.root)
        self.assertEqual(done.returncode, 2)
        self.assertNotIn("Traceback", done.stderr)

    def test_an_invalid_record_names_its_json_path(self):
        path = self.root / "bad.json"
        record = copy.deepcopy(V1)
        record["version"] = 2
        del record["compute"]["model"]
        path.write_text(json.dumps(record), encoding="utf-8")
        done = run("observe", str(path), "--json", cwd=self.root)
        self.assertEqual(done.returncode, 2)
        self.assertEqual(envelope(done)["path"], "$.compute.model")


class AssessFeedback(unittest.TestCase):
    def test_it_advises_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps(
                {"turns": ["thanks", "fix the header spacing"]}), encoding="utf-8")
            done = run("assess-feedback", "--evidence", str(evidence), "--json",
                       cwd=root)
            self.assertEqual(done.returncode, 0, done.stderr)
            candidates = envelope(done)["result"]["candidates"]
            self.assertEqual([c["field"] for c in candidates], ["correction"])
            self.assertEqual(sorted(p.name for p in root.iterdir()),
                             ["evidence.json"])

    def test_it_runs_from_the_repository_root(self):
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "e.json"
            evidence.write_text(json.dumps({"turns": ["ship it"]}), encoding="utf-8")
            done = run("assess-feedback", "--evidence", str(evidence), "--json",
                       cwd=root)
            self.assertEqual(done.returncode, 0, done.stderr)
            body = envelope(done)
            self.assertTrue(body["ok"])
            self.assertEqual(body["result"]["candidates"][0]["value"], "accepted")

    def test_a_turns_list_that_is_not_strings_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "e.json"
            evidence.write_text(json.dumps({"turns": [{"text": "hi"}]}),
                                encoding="utf-8")
            done = run("assess-feedback", "--evidence", str(evidence), "--json",
                       cwd=tmp)
            self.assertEqual(done.returncode, 2)
            self.assertEqual(envelope(done)["path"], "$.turns")


class RemovedFlagsDoNotSilentlyAlias(unittest.TestCase):
    """`--output` is an unambiguous prefix of `--output-manifest`, so argparse
    expanded it and parsed the user's markdown as a manifest. Both READMEs
    documented that command for a while."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name)
        (self.root / "req.txt").write_text("hello", encoding="utf-8")
        (self.root / "out.md").write_text("# not a manifest", encoding="utf-8")

    def test_the_removed_flag_names_its_replacements(self):
        done = run("record", "s", "--request", "req.txt", "--output", "out.md",
                   "--json", cwd=self.root)
        self.assertEqual(done.returncode, 2)
        error = envelope(done)["error"]
        self.assertIn("--output was removed", error)
        self.assertIn("--inline", error)
        self.assertIn("--output-manifest", error)

    def test_no_current_flag_is_a_prefix_of_another_on_the_same_verb(self):
        source = (Path(__file__).resolve().parent / "tokens_qa.py").read_text()
        verbs = dict(re.findall(r'(\w+)\s*=\s*sub\.add_parser\("([\w-]+)"', source))
        for var, verb in verbs.items():
            flags = set(re.findall(r'%s\.add_argument\("(--[\w-]+)"' % var, source))
            flags.discard("--output")
            for a in flags:
                for b in flags:
                    if a != b and b.startswith(a):
                        self.fail(f"{verb}: {a} silently abbreviates {b}")


if __name__ == "__main__":
    unittest.main()
