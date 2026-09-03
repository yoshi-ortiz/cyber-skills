#!/usr/bin/env python3
"""The one next action, computed from what is on disk.

`FLOW` is the whole prompt flow. Adding a branch means adding a row, and the row
carries the reason it fires so the caller is told why, not just what.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

# What a round has to prove before it is finished: that a browser drew the
# artifact at a real viewport and left an image a person can open.
PROOF_KIND = "hero-browser-render"

SHOTS_DIR = ".audit/shots"


def _stale(recorded: Any, current: str) -> bool:
    return str(recorded or "") != current


def correction_id(shot_id: str, observed_at: str) -> str:
    """A correction bundle has no natural identity, so give it one.

    Everything downstream needs to answer one question -- has this particular
    correction been applied -- and a bundle carries no id to answer it with.
    Applying one twice becomes impossible because its id is already in
    `appliedCorrections`; dropping one silently becomes impossible because an
    absent id keeps `apply-correction` firing.
    """
    return hashlib.sha256((shot_id + observed_at).encode()).hexdigest()


def correction_bundles(project_root: Path) -> list[dict[str, str]]:
    """Every Shot the user sent back, as the bounded bundle and nothing else."""
    bundles: list[dict[str, str]] = []
    for path in sorted((Path(project_root) / SHOTS_DIR).glob("*.json")):
        try:
            shot = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        said = shot.get("user_feedback") or {}
        text = str(said.get("correction") or "").strip()
        if not text:
            continue
        shot_id = str(shot.get("shot_id") or path.stem)
        observed_at = str(said.get("observed_at") or "")
        bundles.append({"correctionId": correction_id(shot_id, observed_at),
                        "shotId": shot_id, "observedAt": observed_at,
                        "correction": text})
    return bundles


def missing_proofs(support: Mapping[str, Any], artifact: Path) -> list[str]:
    """The proof kinds this artifact has no live evidence for."""
    if not artifact.exists():
        return [PROOF_KIND]
    from bootstrap_harness import sha256_file
    from review_delivery import REVIEW_WIDTH, proof_key, renderer_version

    expected = proof_key(sha256_file(artifact), str(REVIEW_WIDTH),
                         renderer_version(), PROOF_KIND)
    for proof in support.get("proofs") or []:
        if (isinstance(proof, Mapping) and proof.get("proofKey") == expected
                and Path(str(proof.get("image") or "")).is_file()):
            return []
    return [PROOF_KIND]


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
    ("research-tools", lambda st: not st["toolResearch"] or bool(st["toolResearchErrors"]),
     lambda st: ("research the project domain and stack before custom generation"
                 if not st["toolResearchErrors"] else
                 "fix graphics-tools.json: " + "; ".join(st["toolResearchErrors"]))),
    ("plan-assets", lambda st: bool(st["customPlanMissing"]),
     lambda st: "custom generation needs " + ", ".join(st["customPlanMissing"])
                + " before prompt compilation"),
    ("refine", lambda st: bool(st["refinePending"]),
     lambda st: "edit or reuse refine-tagged attempts before spending a fresh shot: "
                + ", ".join(st["refinePending"])),
    ("compile", lambda st: _stale(st["slicesHash"], st["sceneHash"]),
     lambda st: "scene changed since the slices were compiled"),
    ("compile", lambda st: _stale(st["slicesPromptHash"], st["promptHash"]),
     lambda st: "corpus context changed: roles, tags, or another prompt input "
                "changed since compilation"),
    ("export-avge", lambda st: st["selectedTool"] == "avge"
     and _stale(st["callsHash"], st["sceneHash"]),
     lambda st: "scene changed since avge-calls.json was exported"),
    ("preflight", lambda st: st["svgHash"] != st["sceneHash"]
     and st["adapters"].get(st["selectedTool"]) not in ("PASS", "BLOCKED"),
     lambda st: f"the selected {st['selectedTool']} adapter has no verdict on record"),
    ("run-avge", lambda st: st["svgHash"] != st["sceneHash"]
     and st["selectedTool"] == "avge"
     and st["adapters"].get("avge") == "PASS",
     lambda st: "AVGE is PASS, so run avge-calls.json through the AVGE Engine MCP"),
    ("run-selected-tool", lambda st: st["svgHash"] != st["sceneHash"]
     and st["selectedTool"] != "avge"
     and st["adapters"].get(st["selectedTool"]) == "PASS",
     lambda st: f"run the compiled graphics prompt through the selected "
                f"{st['selectedToolCommand']} command"),
    ("build", lambda st: st["svgHash"] != st["sceneHash"],
     lambda st: f"{st['selectedTool']} is "
                f"{st['adapters'].get(st['selectedTool'], 'unknown')}, "
                "so draw with the in-repo renderer instead"),
    ("repair-output", lambda st: bool(st["gateErrors"]),
     lambda st: "the gate rejected the drawn scene: " + "; ".join(st["gateErrors"])),
    # These two sit AFTER `repair-output`, and the position is load-bearing.
    # Ahead of it, `verify-delivery` would demand a render of an artifact the
    # gate has already rejected, and `apply-correction` would spend a user's
    # correction on a broken SVG. First match wins, so the ordering is the
    # whole guard; neither row needs one of its own.
    #
    # `apply-correction` comes first because an unapplied correction outranks
    # proving a proposal nobody asked for.
    ("apply-correction", lambda st: bool(st["correctionsPending"]),
     lambda st: "the user sent a round back and the correction is not applied: "
                + "; ".join(f"{bundle['shotId']}: {bundle['correction']}"
                            for bundle in st["correctionsPending"])),
    ("verify-delivery", lambda st: bool(st["proofsMissing"]),
     lambda st: "every structural gate passes, but nothing proves a human can "
                "see the work; no live " + ", ".join(st["proofsMissing"])),
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
    support_payload = (json.loads(support.read_text(encoding="utf-8"))
                       if support.exists() else {})
    applied = set(support_payload.get("appliedCorrections") or [])
    svg = project_root / str((manifest.get("outputs") or {}).get("vector")
                             or "shots/output.svg")
    corpus_root = project_root / str((manifest.get("corpus") or {}).get("root")
                                     or "moodboards")
    from graphics_tool_research import (ToolResearchError, load as load_tool_research,
                                        production_tool)
    tool_research, tool_errors = None, []
    try:
        tool_research = load_tool_research(project_root)
    except (OSError, ToolResearchError) as exc:
        tool_errors = [str(exc)]
    missing = []
    if tool_research and tool_research["customGeneration"]:
        if not tool_research["architecture"]:
            missing.append("architecture")
        if not tool_research["atomicAssets"]:
            missing.append("atomicAssets")
    selected = production_tool(tool_research) if tool_research else {"name": "", "command": ""}
    state = {
        "sceneErrors": errors,
        "corpusRoot": corpus_root.is_dir() and any(corpus_root.rglob("*.*")),
        "corpusRootPath": str((manifest.get("corpus") or {}).get("root")
                              or "moodboards"),
        "sceneHash": scene_hash(scene),
        "promptHash": prompt_inputs_hash(project_root, manifest, scene),
        "corpus": (store / "corpus.json").exists(),
        "tags": (store / "corpus-tags.json").exists(),
        "toolResearch": tool_research is not None,
        "toolResearchErrors": tool_errors,
        "customPlanMissing": missing,
        "selectedTool": selected["name"],
        "selectedToolCommand": selected["command"],
        "slicesHash": _recorded_hash(slices),
        "slicesPromptHash": _recorded_field(slices, "promptInputsHash"),
        "refinePending": [path for path, _ in refine_references(project_root)],
        "callsHash": _recorded_hash(calls),
        "adapters": support_payload.get("adapters", {}),
        "correctionsPending": [bundle for bundle in correction_bundles(project_root)
                               if bundle["correctionId"] not in applied],
        "proofsMissing": missing_proofs(support_payload, svg),
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
