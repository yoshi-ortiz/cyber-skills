#!/usr/bin/env python3
"""The design-harness store: where artifacts live and how they are written.

This is the seam under the four workflow modules. Art direction, editorial
scope, theme, and corpus each own a different artifact in `spec/design-harness`,
but they all need the same store path, the same failure type, and the same
crash-safe write. Holding those here is what lets the four stay independent of
each other instead of importing through a common parent."""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


STORE = Path("spec/design-harness")
CORPUS_FILE = "corpus.json"
EDITORIAL_FILE = "editorial.json"
EVENTS_FILE = "editorial-events.jsonl"
THEME_FILE = "theme.json"
DECISIONS_FILE = "decisions.json"
ART_DIRECTION_FILE = "art-direction.json"
VAGUE_LABEL = re.compile(r"\b(clean|modern|bold|editorial|premium)\b", re.I)
# A premise is inference, so it must cite doctrine that exists outside this run.
KNOWN_BASES = {
    "graphic-design-fundamentals", "aesthetics-philosophy", "art-history", "golden-rules",
    "frontend-layout", "art-direction", "motion", "composition",
    "physical-space", "product-design", "copywriting", "mockup-layering",
}


class WorkflowError(ValueError):
    pass


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _atomic_json(path: Path, value: Any) -> None:
    _atomic_text(path, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError(f"missing required artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"invalid JSON in {path}: {exc}") from exc


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"{label} must be non-empty text")
    return value.strip()
