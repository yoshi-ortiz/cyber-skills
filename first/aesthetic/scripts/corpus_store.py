#!/usr/bin/env python3
"""Corpus: the reference material a project directs from, either observed or honestly seeded.

A seam because this is the harness's only reader of the outside filesystem. It
walks a folder the user points at, hashes it, and writes what it found; the
other three modules only ever read artifacts the harness itself wrote."""
from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from typing import Any

from harness_store import CORPUS_FILE, KNOWN_BASES, STORE, WorkflowError, _atomic_json, _text

TEXT_SUFFIXES = {".md", ".txt", ".html", ".htm", ".csv", ".json", ".yaml", ".yml"}
IMAGE_SUFFIXES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}


def _kind(path: Path) -> str | None:
    if path.suffix.lower() in IMAGE_SUFFIXES:
        return "image"
    if path.suffix.lower() in TEXT_SUFFIXES:
        return "text"
    return None


def seed_corpus_value(profile: str, subject: str) -> dict[str, Any]:
    """An honest stand-in for a corpus the user has not supplied.

    It holds no items on purpose: nothing here may later be cited as if the
    user had shown it to us."""
    if profile not in KNOWN_BASES:
        raise WorkflowError(f"unknown profile {profile}")
    return {"version": 1, "grounding": "inference", "profile": profile,
            "subject": _text(subject, "subject"), "modalities": [], "items": []}


def seed_corpus(project_root: Path, profile: str, subject: str) -> dict[str, Any]:
    path = Path(project_root) / STORE / CORPUS_FILE
    if path.exists():
        raise WorkflowError("corpus already exists; keep it or run observe, never seed over it")
    result = seed_corpus_value(profile, subject)
    _atomic_json(path, result)
    return result


def observe_corpus(project_root: Path, source_root: Path) -> dict[str, Any]:
    root = Path(source_root).resolve()
    if not root.is_dir():
        raise WorkflowError(f"corpus is not a directory: {root}")
    items = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        kind = _kind(path)
        if kind is None:
            continue
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        item = {
            "id": f"{kind}-{hashlib.sha256((relative + digest).encode()).hexdigest()[:12]}",
            "path": relative, "kind": kind,
            "mediaType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "bytes": path.stat().st_size, "sha256": digest, "inspectPath": str(path),
        }
        if kind == "text":
            item["textExcerpt"] = path.read_text(encoding="utf-8", errors="replace")[:4000]
        items.append(item)
    if not items:
        raise WorkflowError("corpus has no supported image or text material")
    result = {"version": 1, "root": str(root),
              "modalities": sorted({item["kind"] for item in items}), "items": items}
    _atomic_json(Path(project_root) / STORE / CORPUS_FILE, result)
    return result
