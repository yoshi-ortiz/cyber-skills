#!/usr/bin/env python3
"""Validate project tool research before the graphics loop compiles a prompt."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

STORE = Path("spec/design-harness")
FILE = "graphics-tools.json"
COMMON = {
    "playwright-mcp": "@playwright/mcp@0.0.80",
    "svgmaker-mcp": "@genwave/svgmaker-mcp@2.1.0",
}
FIELDS = ("name", "version", "command", "source", "license", "runtime",
          "security", "evidence")


class ToolResearchError(ValueError):
    pass


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ToolResearchError(f"{path} must be non-empty text")
    return value.strip()


def _record(value: Any, path: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ToolResearchError(f"{path} must be an object")
    return {field: _text(value.get(field), f"{path}.{field}") for field in FIELDS}


def _plan(value: Any, path: str, fields: tuple[str, ...]) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ToolResearchError(f"{path} must contain at least one item")
    rows = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ToolResearchError(f"{path}[{index}] must be an object")
        rows.append({field: _text(item.get(field), f"{path}[{index}].{field}")
                     for field in fields})
    return rows


def validate(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping) or raw.get("version") != 1:
        raise ToolResearchError("graphics tool research must be a version 1 object")
    stack = raw.get("stack")
    if not isinstance(stack, list) or not stack:
        raise ToolResearchError("stack must contain at least one named technology")
    common = [_record(item, f"common[{index}]")
              for index, item in enumerate(raw.get("common") or [])]
    pins = {item["name"]: item["version"] for item in common}
    if pins != COMMON:
        raise ToolResearchError("common must match the harness-core graphics toolbelt pins")
    sufficient = raw.get("commonSufficient")
    if not isinstance(sufficient, bool):
        raise ToolResearchError("commonSufficient must be true or false")
    selected = raw.get("selectedNiche")
    if sufficient and selected is not None:
        raise ToolResearchError("selectedNiche must be null when the common toolbelt is sufficient")
    if not sufficient:
        selected = _record(selected, "selectedNiche")
    custom = raw.get("customGeneration") is True
    architecture = raw.get("architecture") or []
    assets = raw.get("atomicAssets") or []
    if custom:
        architecture = _plan(architecture, "architecture", ("name", "purpose"))
        assets = _plan(assets, "atomicAssets", ("name", "partOf", "output"))
        known = {item["name"] for item in architecture}
        unknown = sorted({item["partOf"] for item in assets} - known)
        if unknown:
            raise ToolResearchError("atomicAssets.partOf names unknown architecture: "
                                    + ", ".join(unknown))
    elif architecture or assets:
        raise ToolResearchError("architecture and atomicAssets require customGeneration")
    return {
        "version": 1,
        "domain": _text(raw.get("domain"), "domain"),
        "stack": [_text(item, f"stack[{index}]") for index, item in enumerate(stack)],
        "common": common,
        "commonSufficient": sufficient,
        "whyCommonInsufficient": ("" if sufficient else
                                  _text(raw.get("whyCommonInsufficient"),
                                        "whyCommonInsufficient")),
        "selectedNiche": selected,
        "customGeneration": custom,
        "architecture": architecture,
        "atomicAssets": assets,
    }


def load(project_root: Path) -> dict[str, Any] | None:
    path = Path(project_root) / STORE / FILE
    if not path.exists():
        return None
    try:
        return validate(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise ToolResearchError(f"{FILE} is not JSON: {exc}") from exc


def context(value: Mapping[str, Any]) -> dict[str, Any]:
    """Only chosen evidence enters graphics inference. Rejected tools stay out."""
    return {key: value[key] for key in (
        "domain", "stack", "common", "commonSufficient",
        "whyCommonInsufficient", "selectedNiche", "architecture", "atomicAssets")}


def production_tool(value: Mapping[str, Any]) -> dict[str, str]:
    """The one production adapter allowed to receive the compiled prompt."""
    selected = value.get("selectedNiche")
    if not isinstance(selected, Mapping):
        selected = next(item for item in value["common"]
                        if item["name"] == "svgmaker-mcp")
    name = str(selected["name"])
    return {"name": name.removesuffix("-mcp"),
            "command": str(selected["command"])}
