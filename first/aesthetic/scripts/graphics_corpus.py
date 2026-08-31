#!/usr/bin/env python3
"""Corpus roles that may influence graphics prompt compilation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

STORE = Path("spec/design-harness")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def tagged_references(project_root: Path, aspect: str, stance: str = "pursue",
                      role: str = "reference") -> list[tuple[str, str]]:
    """Paths carrying one aspect, stance, and corpus role."""
    corpus_path = project_root / STORE / "corpus.json"
    tags_path = project_root / STORE / "corpus-tags.json"
    if not corpus_path.exists() or not tags_path.exists():
        return []
    corpus = _read(corpus_path)
    tags = (_read(tags_path) or {}).get("tags") or {}
    by_digest = {str(item.get("sha256")): str(item.get("path"))
                 for item in corpus.get("items", []) if isinstance(item, Mapping)}
    found = []
    for digest, tag in tags.items():
        if (not isinstance(tag, Mapping) or tag.get("stance") != stance
                or tag.get("role", "reference") != role):
            continue
        aspects = tag.get("aspects") or [tag.get("aspect")]
        if aspect not in [str(item) for item in aspects]:
            continue
        path = by_digest.get(str(digest))
        if path:
            found.append((path, str(tag.get("note") or "").strip()))
    return sorted(found)


def refine_references(project_root: Path) -> list[tuple[str, str]]:
    """Near-hit attempts that must be edited or reused before another shot."""
    found = (tagged_references(project_root, "illustration", "refine", "attempt")
             + tagged_references(project_root, "composition", "refine", "attempt"))
    return sorted(set(found))


def prompt_inputs_hash(project_root: Path, manifest: Mapping[str, Any],
                       scene: Mapping[str, Any]) -> str:
    """Hash every authored input that can change generated prompt slices."""
    def optional(name: str) -> Any:
        path = project_root / STORE / name
        return _read(path) if path.exists() else None

    payload = {
        "scene": scene,
        "styleDirective": manifest.get("styleDirective"),
        "outputs": (manifest.get("outputs") or {}).get("prompts"),
        "corpus": optional("corpus.json"),
        "tags": optional("corpus-tags.json"),
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
