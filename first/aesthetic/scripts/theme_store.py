#!/usr/bin/env python3
"""Theme: the colour and type values a project renders with, and the contrast floor they must clear.

A seam because this is the only module that reasons about pixels rather than
documents. Relative luminance, the 4.5:1 and 3:1 floors, and the last-safe
fallback are a self-contained rule set, and they get to be wrong on their own
terms without touching art direction, scope, or corpus."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from harness_store import STORE, THEME_FILE, WorkflowError, _atomic_json, _read_json, _text

DEFAULT_THEME = {
    "bg": "#f5f5f7",
    "ink": "#1d1d1f",
    "accent": "#0066cc",
    "font": "system-ui, sans-serif",
}


def _rgb(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"#([0-9a-fA-F]{6})", str(value).strip())
    if not match:
        return None
    raw = match.group(1)
    return tuple(int(raw[index:index + 2], 16) for index in (0, 2, 4))


def contrast(first: str, second: str) -> float:
    def luminance(value: str) -> float:
        rgb = _rgb(value)
        if rgb is None:
            raise WorkflowError(f"color must be six-digit hex: {value}")
        channels = []
        for channel in rgb:
            scaled = channel / 255
            channels.append(scaled / 12.92 if scaled <= .04045 else ((scaled + .055) / 1.055) ** 2.4)
        return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]
    a, b = luminance(first), luminance(second)
    return (max(a, b) + .05) / (min(a, b) + .05)


def validate_theme_elements(candidate: Mapping[str, Any], safe: Mapping[str, Any] | None = None) -> dict[str, Any]:
    previous = dict(DEFAULT_THEME)
    previous.update({key: value for key, value in (safe or {}).items() if key in previous})
    active = dict(previous)
    errors: list[dict[str, Any]] = []
    requested = {key: candidate.get(key, previous[key]) for key in previous}
    if _rgb(str(requested["bg"])) is None:
        errors.append({"element": "bg", "message": "background must be six-digit hex"})
    else:
        active["bg"] = str(requested["bg"])
    ink_ratio = contrast(str(requested["ink"]), active["bg"]) if _rgb(str(requested["ink"])) else 0
    if ink_ratio < 4.5:
        errors.append({"element": "ink", "message": "text contrast is below 4.5:1",
                       "contrast": round(ink_ratio, 2)})
    else:
        active["ink"] = str(requested["ink"])
    accent_ratio = contrast(str(requested["accent"]), active["bg"]) if _rgb(str(requested["accent"])) else 0
    if accent_ratio < 3:
        errors.append({"element": "accent", "message": "control contrast is below 3:1",
                       "contrast": round(accent_ratio, 2)})
    else:
        active["accent"] = str(requested["accent"])
    font = str(requested["font"]).strip()
    if not font or len(font) > 200 or not re.fullmatch(r"[A-Za-z0-9 ,.'\"_-]+", font):
        errors.append({"element": "font", "message": "font stack is not a safe CSS value"})
    else:
        active["font"] = font
    if contrast(active["ink"], active["bg"]) < 4.5:
        active["bg"] = previous["bg"]
        errors.append({"element": "bg", "message": "background conflicts with the last safe ink"})
    return {"active": active, "errors": errors}


def _theme_spec(project_root: Path) -> dict[str, Any]:
    path = Path(project_root) / STORE / THEME_FILE
    if not path.exists():
        return {"version": 1, "selected": None, "followArtDirection": False, "themes": []}
    value = _read_json(path)
    if not isinstance(value, Mapping) or not isinstance(value.get("themes"), list):
        raise WorkflowError("theme.json has an invalid shape")
    return dict(value)


def save_theme(project_root: Path, mode: str, identifier: str,
               elements: Mapping[str, Any], name: str = "") -> dict[str, Any]:
    if mode not in {"current", "new"}:
        raise WorkflowError("theme save mode must be current or new")
    identifier = _text(identifier, "theme id")
    spec = _theme_spec(project_root)
    by_id = {theme.get("id"): dict(theme) for theme in spec["themes"] if isinstance(theme, Mapping)}
    target_id = spec.get("selected") if mode == "current" and spec.get("selected") else identifier
    if mode == "new" and identifier in by_id:
        raise WorkflowError(f"theme {identifier} already exists")
    prior = by_id.get(target_id, {}).get("elements") or DEFAULT_THEME
    checked = validate_theme_elements(elements, prior)
    by_id[target_id] = {
        "id": target_id,
        "name": name.strip() or by_id.get(target_id, {}).get("name") or target_id,
        "elements": checked["active"],
        "issues": checked["errors"],
    }
    result = {
        "version": 1,
        "selected": target_id,
        "followArtDirection": bool(spec.get("followArtDirection", False)),
        "themes": sorted(by_id.values(), key=lambda item: item["id"]),
    }
    _atomic_json(Path(project_root) / STORE / THEME_FILE, result)
    return result


def set_follow_art_direction(project_root: Path, enabled: bool) -> dict[str, Any]:
    spec = _theme_spec(project_root)
    spec["followArtDirection"] = bool(enabled)
    _atomic_json(Path(project_root) / STORE / THEME_FILE, spec)
    return spec


def selected_theme(project_root: Path) -> dict[str, Any] | None:
    spec = _theme_spec(project_root)
    selected = spec.get("selected")
    for theme in spec["themes"]:
        if theme.get("id") == selected:
            return {"followArtDirection": bool(spec.get("followArtDirection")), **theme}
    return None
