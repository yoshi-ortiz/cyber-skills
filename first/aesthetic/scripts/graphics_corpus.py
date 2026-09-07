#!/usr/bin/env python3
"""Corpus roles that may influence graphics prompt compilation."""
from __future__ import annotations

import hashlib
import json
import re
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


def derived_measurements(project_root: Path) -> dict[str, Mapping[str, Any]]:
    """Measured colour per corpus path, keyed the way a prompt cites a reference.

    Empty when nothing has been measured, and an empty dict is the honest
    answer: no measurement is not the same as a neutral one, so callers render
    the gap rather than a default.
    """
    path = project_root / STORE / "corpus-derived.json"
    if not path.exists():
        return {}
    payload = _read(path) or {}
    return {str(record.get("path")): record
            for record in (payload.get("images") or {}).values()
            if isinstance(record, Mapping) and record.get("path")}


def _channels(swatch: str) -> tuple[int, int, int]:
    value = swatch.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _swatch_distance(one: str, two: str) -> float:
    return sum((a - b) ** 2 for a, b in zip(_channels(one), _channels(two))) ** 0.5


def _is_screen_grey(swatch: str) -> bool:
    """A mid-tone grey in a screenshot is window chrome, not a design decision.

    Near-white and near-black stay: those are the paper and the contour, which
    the drawing genuinely uses.
    """
    red, green, blue = _channels(swatch)
    high, low = max(red, green, blue), min(red, green, blue)
    saturation = 0.0 if high == 0 else (high - low) / high
    return saturation < 0.12 and 40 < high < 235


def evidenced_palette(project_root: Path, paths: list[str] | None = None,
                      limit: int = 10) -> list[str]:
    """The fills the named references are built from, widest coverage first.

    This is the only list a generated fill may come from. A colour absent here
    is a colour the corpus does not evidence, which `anti-slop.md` forbids.

    Capped, because a list of every colour in every screenshot is a phone book
    rather than a direction, and screen greys are dropped for the same reason.
    """
    measured = derived_measurements(project_root)
    weighted: dict[str, float] = {}
    for path, record in measured.items():
        if paths is not None and path not in paths:
            continue
        for entry in record.get("palette") or []:
            if not isinstance(entry, Mapping):
                continue
            swatch = str(entry.get("hex") or "")
            if not swatch or _is_screen_grey(swatch):
                continue
            weighted[swatch] = weighted.get(swatch, 0.0) + float(
                entry.get("coverage") or 0.0)
    ordered = sorted(weighted.items(), key=lambda pair: (-pair[1], pair[0]))
    # Four references on white are one decision seen four times. Without this
    # the widest-first cap spent most of its slots on near-identical grounds
    # and dropped the accents a drawing is actually built from.
    kept: list[str] = []
    for swatch, _ in ordered:
        if all(_swatch_distance(swatch, chosen) >= 40 for chosen in kept):
            kept.append(swatch)
        if len(kept) >= limit:
            break
    return kept


HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")


def _normalise(swatch: str) -> str:
    value = swatch.lstrip("#").lower()
    if len(value) == 3:
        value = "".join(channel * 2 for channel in value)
    return "#" + value


def palette_audit(project_root: Path, design: Path, tolerance: float = 40.0
                  ) -> dict[str, Any]:
    """How much of a drawn comp's colour the corpus actually evidences.

    A comp is HTML and CSS, so it never passes through the prompt compiler and
    nothing was checking it. Every character round in this project was authored
    with invented hexes while the references sat unread, which is the whole
    complaint this answers.

    `fit` is None when nothing has been measured. No corpus is not a passing
    grade and must not become one.
    """
    text = Path(design).read_text(encoding="utf-8", errors="replace")
    declared = list(dict.fromkeys(_normalise(found) for found in HEX.findall(text)))
    evidence = evidenced_palette(project_root, limit=64)
    if not evidence:
        return {"design": str(design), "evidence": [], "declared": declared,
                "matched": [], "unevidenced": declared, "fit": None}
    matched, unevidenced = [], []
    for swatch in declared:
        nearest = min(evidence, key=lambda have: _swatch_distance(swatch, have))
        distance = _swatch_distance(swatch, nearest)
        record = {"declared": swatch, "nearest": nearest, "distance": round(distance, 1)}
        (matched if distance <= tolerance else unevidenced).append(record)
    return {"design": str(design), "evidence": evidence, "declared": declared,
            "matched": matched, "unevidenced": unevidenced,
            "fit": round(len(matched) / len(declared), 3) if declared else None}


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
        # Measured colour reaches the slices, so a re-measure has to make the
        # compiled prompt stale. Leaving it out let a prompt keep citing hexes
        # that were no longer on disk.
        "derived": optional("corpus-derived.json"),
        "characters": optional("character-observations.json"),
        "toolResearch": optional("graphics-tools.json"),
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
