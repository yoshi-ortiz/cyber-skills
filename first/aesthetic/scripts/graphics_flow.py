#!/usr/bin/env python3
"""The one next action, computed from what is on disk.

`FLOW` is the whole prompt flow. Adding a branch means adding a row, and the row
carries the reason it fires so the caller is told why, not just what.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _stale(recorded: Any, current: str) -> bool:
    return str(recorded or "") != current


FLOW = (
    ("edit-scene-spec", lambda st: bool(st["sceneErrors"]),
     lambda st: "scene-spec.json does not validate: " + "; ".join(st["sceneErrors"])),
    ("add-corpus", lambda st: not st["corpusRoot"],
     lambda st: f"the manifest's corpus root {st['corpusRootPath']!r} holds no "
                "reference material, and observe cannot run against nothing"),
    ("observe", lambda st: not st["corpus"],
     lambda st: "no corpus.json, so nothing has been observed yet"),
    ("seed-tags", lambda st: not st["tags"],
     lambda st: "corpus is observed but untagged, and only pursue tags reach a slice"),
    ("refine", lambda st: bool(st["refinePending"]),
     lambda st: "edit or reuse refine-tagged attempts before spending a fresh shot: "
                + ", ".join(st["refinePending"])),
    ("compile", lambda st: _stale(st["slicesHash"], st["sceneHash"]),
     lambda st: "scene changed since the slices were compiled"),
    ("compile", lambda st: _stale(st["slicesPromptHash"], st["promptHash"]),
     lambda st: "corpus context changed: roles, tags, or another prompt input "
                "changed since compilation"),
    ("export-avge", lambda st: _stale(st["callsHash"], st["sceneHash"]),
     lambda st: "scene changed since avge-calls.json was exported"),
    ("preflight", lambda st: st["svgHash"] != st["sceneHash"] and not st["adapters"],
     lambda st: "no adapter verdict on record, so the draw step has no route"),
    ("run-avge", lambda st: st["svgHash"] != st["sceneHash"]
     and st["adapters"].get("avge") == "PASS",
     lambda st: "AVGE is PASS, so run avge-calls.json through the AVGE Engine MCP"),
    ("build", lambda st: st["svgHash"] != st["sceneHash"],
     lambda st: f"AVGE is {st['adapters'].get('avge', 'unknown')}, "
                "so draw with the in-repo renderer instead"),
    ("repair-output", lambda st: bool(st["gateErrors"]),
     lambda st: "the gate rejected the drawn scene: " + "; ".join(st["gateErrors"])),
)


def next_action(state: Mapping[str, Any]) -> dict[str, str]:
    """The one thing to do next, and why. The whole prompt flow is this table."""
    for action, fires, explain in FLOW:
        if fires(state):
            return {"action": action, "reason": explain(state)}
    return {"action": "done", "reason": "every gate passes and no artifact is stale"}


def read_state(project_root: Path) -> dict[str, Any]:
    from text_to_graphics import (SUPPORT_FILE, STORE, gate_outputs, load_manifest,
                                  load_scene, prompt_inputs_hash, refine_references,
                                  scene_hash, validate_scene, _slices_dir)

    manifest = load_manifest(project_root)
    scene = load_scene(project_root, manifest)
    errors = validate_scene(scene)
    store = project_root / STORE
    slices = _slices_dir(project_root, manifest) / "manifest.json"
    calls = _slices_dir(project_root, manifest) / "avge-calls.json"
    support = store / SUPPORT_FILE
    svg = project_root / str((manifest.get("outputs") or {}).get("vector")
                             or "shots/output.svg")
    corpus_root = project_root / str((manifest.get("corpus") or {}).get("root")
                                     or "moodboards")
    state = {
        "sceneErrors": errors,
        "corpusRoot": corpus_root.is_dir() and any(corpus_root.rglob("*.*")),
        "corpusRootPath": str((manifest.get("corpus") or {}).get("root")
                              or "moodboards"),
        "sceneHash": scene_hash(scene),
        "promptHash": prompt_inputs_hash(project_root, manifest, scene),
        "corpus": (store / "corpus.json").exists(),
        "tags": (store / "corpus-tags.json").exists(),
        "slicesHash": _recorded_hash(slices),
        "slicesPromptHash": _recorded_field(slices, "promptInputsHash"),
        "refinePending": [path for path, _ in refine_references(project_root)],
        "callsHash": _recorded_hash(calls),
        "adapters": (json.loads(support.read_text(encoding="utf-8")).get("adapters", {})
                     if support.exists() else {}),
        "svgHash": drawn_from(project_root, svg) if svg.exists() else "",
        "gateErrors": [],
    }
    if not errors and svg.exists():
        state["gateErrors"] = gate_outputs(project_root)["errors"]
    return state


def drawn_from(project_root: Path, output: Path) -> str:
    """The scene hash the newest recorded attempt drew this output from.

    An artifact with no attempt behind it has unknown provenance and is treated
    as stale, which is what keeps goal 6 honest.
    """
    from text_to_graphics import ATTEMPTS_FILE, STORE

    ledger = project_root / STORE / ATTEMPTS_FILE
    if not ledger.exists():
        return ""
    found = ""
    for line in ledger.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(record.get("output")) == str(output):
            found = str(record.get("sceneSpecHash") or "")
    return found


def _recorded_hash(path: Path) -> str:
    return _recorded_field(path, "sceneSpecHash")


def _recorded_field(path: Path, field: str) -> str:
    if not path.exists():
        return ""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get(field) or "")
