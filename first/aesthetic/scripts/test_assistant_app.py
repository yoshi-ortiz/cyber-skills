#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import assistant_app as app
import brief_workflow as brief
from adopt_fixtures import harness, ledger


def project(tmp: str) -> tuple[Path, Path]:
    root = Path(tmp)
    harness(root)
    brief.save_brief_spec(root, brief.default_brief("2026-09-03T10:00:00Z"))
    store = root / "spec" / "design-harness"
    corpus = {"root": "moodboards", "items": [{
        "id": "ref-1", "path": "marks/example.png", "sha256": "a" * 64,
    }]}
    (store / "corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
    inbox = root / ".superpowers" / "brainstorm"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / brief.BRIEF_INBOX_FILE).write_text(json.dumps({
        "eventId": "brief-1", "at": "2026-09-03T10:01:00Z",
        "id": "ships", "answer": "A ranked graphics round.",
    }) + "\n", encoding="utf-8")
    (inbox / "corpus-tags-inbox.jsonl").write_text(json.dumps({
        "at": "2026-09-03T10:02:00Z", "group": "marks",
        "aspects": ["illustration"], "role": "reference",
        "stance": "pursue", "quality": "finished", "note": "Keep the hard edge.",
    }) + "\n", encoding="utf-8")
    return root, ledger(root, {
        "type": "rank", "element": "core.idea", "stars": 4,
        "timestamp": 1,
    })


class AssistantAppSyncTest(unittest.TestCase):
    @patch("assistant_app.subprocess.run")
    def test_one_sync_adopts_all_state_and_calls_tokens_qa_once(self, run) -> None:
        run.side_effect = [
            app.subprocess.CompletedProcess([], 0, "ok\n", ""),
            app.subprocess.CompletedProcess([], 0, json.dumps({
                "ok": True, "code": 0, "error": None, "path": None,
                "result": {"complaints": ["this is frustrating"],
                           "corrections": ["please make it darker"],
                           "restated": [], "candidates": []},
            }) + "\n", ""),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root, decisions = project(tmp)
            result = app.sync(
                root, decisions, "aesthetic@2026-09-03T10:00:00Z",
                ["this is frustrating", "please make it darker"])

        self.assertEqual(run.call_count, 2)
        self.assertEqual(result["invocation"], "aesthetic@2026-09-03T10:00:00Z")
        self.assertEqual(result["ranking"]["adopted"], 1)
        self.assertEqual(result["brief"]["adopted"], 1)
        self.assertEqual(result["corpusTags"]["adopted"], 1)
        self.assertEqual(result["feedback"]["corrections"], ["please make it darker"])
        self.assertEqual(result["ranking"]["state"]["elements"][0]["stars"], 4)
        self.assertEqual(result["brief"]["state"]["answers"][0]["answer"],
                         "A ranked graphics round.")
        self.assertEqual(len(result["corpusTags"]["state"]["tags"]), 1)

    @patch("assistant_app.subprocess.run")
    def test_failed_live_check_changes_nothing(self, run) -> None:
        run.return_value = app.subprocess.CompletedProcess([], 1, "", "server down")
        with tempfile.TemporaryDirectory() as tmp:
            root, decisions = project(tmp)
            before = (root / "spec/design-harness/decisions.json").read_bytes()
            with self.assertRaisesRegex(app.AssistantAppError, "server down"):
                app.sync(root, decisions, "aesthetic@2026-09-03T10:00:00Z", [])
            self.assertEqual(
                (root / "spec/design-harness/decisions.json").read_bytes(), before)
        self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
