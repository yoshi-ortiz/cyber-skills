#!/usr/bin/env python3
"""Laying a harness down, and checking that the one on disk is still whole.

`init` writes the scaffolding a project needs and hashes the read-only source
it was built from; `validate` reads that back and refuses a harness whose
source has drifted. Kept together because they are two halves of one promise.
"""

from __future__ import annotations

import json
from pathlib import Path

from harness_core import (DECISION_STATES, HarnessError, PROFILES, STAR_RANGE,
                          TEMPLATE_NAMES, VERSION, ZERO_STARS, is_within,
                          questionnaire, sha256_file, source_entries,
                          write_json)
from harness_strings import DEFAULT_LANGUAGE
from harness_ledger import empty_decisions, load_decisions, render_decisions_md


def init_harness(project_root: Path, source_root: Path, profiles: list[str],
                 language: str = DEFAULT_LANGUAGE) -> Path:
    project_root = project_root.resolve(strict=True)
    source_root = source_root.resolve(strict=True)
    if not project_root.is_dir() or not source_root.is_dir():
        raise HarnessError("project root and source root must be directories")
    output = project_root / "spec" / "design-harness"
    if is_within(output.resolve(), source_root):
        raise HarnessError("generated harness cannot live inside the read-only source root")
    if output.is_dir() and any(output.iterdir()):
        route = ("run text_to_graphics.py status" if
                 any((output / name).is_file() for name in
                     ("scene-spec.json", "graphics-manifest.json")) else
                 "continue the existing harness")
        raise HarnessError(f"design harness already exists; {route} instead of init")

    before = source_entries(source_root)
    output.mkdir(parents=True, exist_ok=True)
    template_root = Path(__file__).resolve().parent.parent / "assets" / "spec"
    for name in TEMPLATE_NAMES:
        template = template_root / f"{name}.tmpl"
        if not template.is_file():
            raise HarnessError(f"missing skill template: {template}")
        (output / name).write_bytes(template.read_bytes())

    project = {
        "version": VERSION,
        "sourceRoot": str(source_root),
        "sourcePolicy": "read-only",
        "profiles": profiles,
        # UI locale only. Chat language comes from the user's words and the
        # project's published copy, never from this field.
        "language": language,
        "state": "draft",
        "budgets": {"toolCalls": 4, "urls": 2, "newVisuals": 4, "extractedChars": 24000, "outputTokens": 1200},
    }
    capabilities = sorted({capability for profile in profiles for capability in PROFILES[profile]})
    matrix = {
        "version": VERSION,
        "profiles": profiles,
        "requiredCapabilities": [{"category": category, "adapter": None, "available": False} for category in capabilities],
        "promotionChecks": ["source-integrity", "lineage", "user-approval", "domain-conformance"],
    }
    manifest = {"version": VERSION, "algorithm": "sha256", "sourceRoot": str(source_root), "entries": before}
    write_json(output / "project.json", project)
    write_json(output / "capability-matrix.json", matrix)
    write_json(output / "source-manifest.json", manifest)
    (output / "QUESTIONNAIRE.md").write_text(questionnaire(profiles), encoding="utf-8")
    if not (output / "decisions.json").is_file():
        decisions = empty_decisions()
        write_json(output / "decisions.json", decisions)
        (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")

    after = source_entries(source_root)
    if before != after:
        raise HarnessError("source root changed during bootstrap")
    return output


def validate_harness(project_root: Path) -> None:
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    required = [*TEMPLATE_NAMES, "project.json", "capability-matrix.json", "source-manifest.json",
                "QUESTIONNAIRE.md", "decisions.json", "DECISIONS.md"]
    missing = [name for name in required if not (output / name).is_file()]
    if missing:
        raise HarnessError(f"missing generated file(s): {', '.join(missing)}")
    project = json.loads((output / "project.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "source-manifest.json").read_text(encoding="utf-8"))
    matrix = json.loads((output / "capability-matrix.json").read_text(encoding="utf-8"))
    if project.get("sourcePolicy") != "read-only" or project.get("sourceRoot") != manifest.get("sourceRoot"):
        raise HarnessError("source-root contract is missing or contradictory")
    profiles = project.get("profiles")
    if not isinstance(profiles, list) or any(profile not in PROFILES for profile in profiles):
        raise HarnessError("project contains unknown profiles")
    expected_capabilities = sorted({capability for profile in profiles for capability in PROFILES[profile]})
    actual_capabilities = sorted(item.get("category") for item in matrix.get("requiredCapabilities", []))
    if actual_capabilities != expected_capabilities:
        raise HarnessError("capability matrix does not match selected profiles")
    source_root = Path(project["sourceRoot"]).resolve(strict=True)
    actual_entries = source_entries(source_root)
    corpus_drift: list[str] = []
    if manifest.get("algorithm") != "sha256":
        raise HarnessError("source manifest algorithm is not sha256")
    if manifest.get("entries") != actual_entries:
        was = {e["path"]: e["sha256"] for e in manifest.get("entries", [])}
        now = {e["path"]: e["sha256"] for e in actual_entries}
        corpus_drift = ([f"removed: {p}" for p in sorted(set(was) - set(now))]
                        + [f"added: {p}" for p in sorted(set(now) - set(was))]
                        + [f"changed: {p}" for p in sorted(set(was) & set(now)) if was[p] != now[p]])
    if "read-only" not in (output / "CONTRACTS.md").read_text(encoding="utf-8"):
        raise HarnessError("generated contracts omit the read-only source invariant")

    decisions = load_decisions(output)
    warnings: list[str] = []
    seen: set[str] = set()
    for entry in decisions.get("elements", []):
        element = entry.get("element")
        if not element or element in seen:
            raise HarnessError("decisions.json contains a missing or duplicate element id")
        seen.add(element)
        if entry.get("state") not in DECISION_STATES:
            raise HarnessError(f"decision '{element}' has an unknown state")
        stars_value = entry.get("stars")
        if not isinstance(stars_value, int) or not (
                stars_value == ZERO_STARS or STAR_RANGE[0] <= stars_value <= STAR_RANGE[1]):
            raise HarnessError(f"decision '{element}' has an invalid star rank")
        if not str(entry.get("evidence", "")).strip():
            raise HarnessError(f"decision '{element}' has no user evidence excerpt")
        preview = entry.get("preview")
        if preview is not None:
            if not isinstance(preview, dict) or not preview.get("path") or not preview.get("sha256"):
                raise HarnessError(f"decision '{element}' has a malformed preview reference")
            shot = project_root.resolve(strict=True) / preview["path"]
            if not shot.is_file():
                raise HarnessError(f"decision '{element}' references a missing preview: {preview['path']}")
            if sha256_file(shot) != preview["sha256"]:
                warnings.append(f"preview for '{element}' changed since it was ranked "
                                f"(re-record with `decide --preview` when convenient)")
        target = entry.get("supersededBy")
        if target and target not in {e.get("element") for e in decisions["elements"]}:
            raise HarnessError(f"decision '{element}' is superseded by an unknown element")
    if decisions.get("state") != project.get("state"):
        raise HarnessError("project.json state disagrees with decisions.json state")
    if (output / "DECISIONS.md").read_text(encoding="utf-8") != render_decisions_md(decisions):
        raise HarnessError("DECISIONS.md is stale; regenerate it with `decide`")
    return {"warnings": warnings, "corpusDrift": corpus_drift}
