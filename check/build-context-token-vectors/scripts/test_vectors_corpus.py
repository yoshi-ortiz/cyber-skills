#!/usr/bin/env python3
"""Corpus facts are measured once when installed skills are loaded."""
from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path

sys.modules.setdefault("numpy", types.SimpleNamespace(ndarray=object))
sys.modules.setdefault("evoc", types.SimpleNamespace(EVoC=object))
sys.modules.setdefault("model2vec", types.SimpleNamespace(StaticModel=object))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vectors


class CorpusTest(unittest.TestCase):
    def test_loaded_record_carries_utf8_body_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "ora"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: ora\n---\n\nseñal", encoding="utf-8")
            records = vectors.load(Path(tmp))

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, "ora")
        self.assertEqual(records[0].body, "señal")
        self.assertEqual(records[0].body_bytes, len("señal".encode("utf-8")))


if __name__ == "__main__":
    unittest.main()
