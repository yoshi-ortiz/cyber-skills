#!/usr/bin/env python3
"""Compile, gate, and record text-to-graphics inference attempts.

Reads graphics-manifest.json and scene-spec.json. Emits adapter-specific prompt
slices so inventory and style never share one model call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

STORE = Path("spec/design-harness")
MANIFEST_FILE = "graphics-manifest.json"
SCENE_FILE = "scene-spec.json"
ATTEMPTS_FILE = "inference-attempts.jsonl"
SUPPORT_FILE = "support.json"
VERDICTS = ("PASS", "BLOCKED")
SVG_NS = "{http://www.w3.org/2000/svg}"

STYLE_SLICE_MAX = 4000
INVENTORY_PER_SPACE_MAX = 3000
GEOMETRY_SLICE_MAX = 8000
MOODBOARD_SLICE_MAX = 12000

REQUIRED_SCENE_KEYS = ("version", "element", "layout", "road", "positions",
                       "mainRooms", "kiosks", "billboards")
REQUIRED_ROAD_KEYS = ("shape", "direction", "sequence")


class GraphicsError(ValueError):
    pass


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise GraphicsError(f"missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with open(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
        Path(temporary).replace(path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _truncate(text: str, limit: int) -> str:
    if len(text.encode("utf-8")) <= limit:
        return text
    encoded = text.encode("utf-8")[:limit]
    return encoded.decode("utf-8", errors="ignore").rstrip() + "…"


def _slug(identifier: Any) -> str:
    return str(identifier).strip("/").replace("/", "_")


def scene_hash(scene: Mapping[str, Any]) -> str:
    return _sha256_bytes(json.dumps(scene, sort_keys=True).encode("utf-8"))


def _slices_dir(project_root: Path, manifest: Mapping[str, Any]) -> Path:
    prompts = (manifest.get("outputs") or {}).get("prompts") or {}
    path = project_root / str(prompts.get("slicesDir")
                              or "moodboards/llm-shots/prompts/slices")
    path.mkdir(parents=True, exist_ok=True)
    return path



def load_manifest(project_root: Path) -> dict[str, Any]:
    raw = _read_json(project_root / STORE / MANIFEST_FILE)
    if not isinstance(raw, Mapping) or raw.get("version") != 1:
        raise GraphicsError(f"{MANIFEST_FILE} must be version 1 object")
    return dict(raw)


def load_scene(project_root: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    rel = str(manifest.get("sceneSpec") or SCENE_FILE)
    raw = _read_json(project_root / rel)
    if not isinstance(raw, Mapping):
        raise GraphicsError("scene-spec must be an object")
    return dict(raw)


def spaces_of(scene: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Main rooms then kiosks, in one list. Both are spaces; only size differs."""
    return [entry for group in ("mainRooms", "kiosks")
            for entry in (scene.get(group) or [])
            if isinstance(entry, Mapping)]


def validate_scene(scene: Mapping[str, Any]) -> list[str]:
    """Structural rules only. The scene names its own spaces, road, and layout."""
    errors: list[str] = []
    for key in REQUIRED_SCENE_KEYS:
        if key not in scene:
            errors.append(f"scene missing {key}")

    positions = scene.get("positions")
    if not isinstance(positions, Mapping) or not positions:
        errors.append("positions must declare at least one named footprint")
        positions = {}

    spaces = spaces_of(scene)
    if not spaces:
        errors.append("scene declares no spaces")
    identifiers = []
    for space in spaces:
        identifier = str(space.get("id") or "")
        if not identifier:
            errors.append("a space has no id")
            continue
        identifiers.append(identifier)
        position = str(space.get("position") or "")
        if position not in positions:
            errors.append(f"{identifier} sits at undeclared position {position!r}")
    duplicates = sorted({name for name in identifiers if identifiers.count(name) > 1})
    if duplicates:
        errors.append(f"duplicate space ids: {', '.join(duplicates)}")

    road = scene.get("road")
    if isinstance(road, Mapping):
        for key in REQUIRED_ROAD_KEYS:
            if key not in road:
                errors.append(f"road missing {key}")
        sequence = road.get("sequence")
        if not isinstance(sequence, list) or len(sequence) < 3:
            errors.append("road.sequence must name at least two spaces and return")
        else:
            if sequence[0] != sequence[-1]:
                errors.append("road.sequence must return to its first space")
            unknown = sorted({str(step) for step in sequence} - set(identifiers))
            if unknown:
                errors.append(
                    f"road.sequence names undeclared spaces: {', '.join(unknown)}")
    else:
        errors.append("road must be an object")

    billboards = scene.get("billboards")
    if isinstance(billboards, Mapping):
        unlabelled = sorted(set(identifiers) - set(billboards))
        if unlabelled:
            errors.append(f"spaces with no billboard: {', '.join(unlabelled)}")
        stray = sorted(set(billboards) - set(identifiers))
        if stray:
            errors.append(f"billboards for undeclared spaces: {', '.join(stray)}")
    else:
        errors.append("billboards must be an object")
    return errors


def tagged_references(project_root: Path, aspect: str,
                      stance: str = "pursue") -> list[tuple[str, str]]:
    """Corpus paths carrying one aspect and stance, with the note the user left.

    This is the only route from a tag to a prompt. Anything not tagged `pursue`
    never reaches a slice, which is what makes the avoid stance mean something.
    """
    corpus_path = project_root / STORE / "corpus.json"
    tags_path = project_root / STORE / "corpus-tags.json"
    if not corpus_path.exists() or not tags_path.exists():
        return []
    corpus = _read_json(corpus_path)
    tags = (_read_json(tags_path) or {}).get("tags") or {}
    by_digest = {str(item.get("sha256")): str(item.get("path"))
                 for item in corpus.get("items", []) if isinstance(item, Mapping)}
    found = []
    for digest, tag in tags.items():
        if not isinstance(tag, Mapping) or tag.get("stance") != stance:
            continue
        aspects = tag.get("aspects") or [tag.get("aspect")]
        if aspect not in [str(item) for item in aspects]:
            continue
        path = by_digest.get(str(digest))
        if path:
            found.append((path, str(tag.get("note") or "").strip()))
    return sorted(found)


def inventory_sections(text: str) -> dict[str, str]:
    """Split an inventory document on its `## /space` headings."""
    sections: dict[str, str] = {}
    current = None
    body: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^##\s+`?(/[\w-]+)`?", line)
        if match:
            if current:
                sections[current] = "\n".join(body).strip()
            current = match.group(1)
            body = []
        elif current:
            body.append(line)
    if current:
        sections[current] = "\n".join(body).strip()
    return sections


def _inventory_directive(project_root: Path, scene: Mapping[str, Any]) -> str:
    reference = scene.get("inventoryRef")
    identifiers = [str(space["id"]) for space in spaces_of(scene)]
    if not reference:
        return "INVENTORY: none declared for this scene."
    path = project_root / str(reference)
    if not path.exists():
        return f"INVENTORY: {reference} declared but not found; gap recorded."
    sections = inventory_sections(path.read_text(encoding="utf-8"))
    lines = ["INVENTORY PER SPACE - never send this to a style or image model."]
    for identifier in identifiers:
        section = sections.get(identifier)
        lines.append(f"\n## {identifier}\n" + (
            _truncate(section, INVENTORY_PER_SPACE_MAX) if section
            else "(no inventory section; gap)"))
    return "\n".join(lines)


def _style_slice(project_root: Path, manifest: Mapping[str, Any]) -> str:
    lines = [_style_directive(manifest)]
    pursued = tagged_references(project_root, "illustration")
    if pursued:
        lines.append("\nPursue these references:")
        lines += [f"- {path}" + (f" ({note})" if note else "")
                  for path, note in pursued]
    return "\n".join(lines)



def _style_directive(manifest: Mapping[str, Any]) -> str:
    directive = str(manifest.get("styleDirective") or "").strip()
    if not directive:
        raise GraphicsError("graphics-manifest.json missing styleDirective")
    return directive


def _geometry_directive(scene: Mapping[str, Any]) -> str:
    sequence = " -> ".join((scene.get("road") or {}).get("sequence") or [])
    billboards = scene.get("billboards") or {}
    space_lines = []
    for space in spaces_of(scene):
        palette = space.get("palette")
        if isinstance(palette, list):
            palette = ", ".join(str(name) for name in palette)
        space_lines.append(f"- {space['id']} at {space['position']} ({palette})")
    return "\n".join([
        "GEOMETRY ONLY - no character inventory prose.",
        f"Layout: {scene.get('layout')}.",
        f"Road: {(scene.get('road') or {}).get('shape')}, one-way {sequence}.",
        "Spaces:",
        *space_lines,
        'The road element must carry id="road" so the gate can read its topology.',
        "Billboards (exact text):",
        *[f"- {key}: {billboards[key]}" for key in sorted(billboards)],
    ])


def compile_slices(project_root: Path) -> dict[str, Any]:
    manifest = load_manifest(project_root)
    scene = load_scene(project_root, manifest)
    errors = validate_scene(scene)
    if errors:
        raise GraphicsError("; ".join(errors))

    style = _truncate(_style_slice(project_root, manifest), STYLE_SLICE_MAX)
    geometry = _truncate(_geometry_directive(scene), GEOMETRY_SLICE_MAX)
    composition = tagged_references(project_root, "composition")
    moodboard = _truncate("\n".join(
        [style, "", "Composition references:"]
        + [f"- {path}" + (f" ({note})" if note else "") for path, note in composition]
        + ["", "Match composition only. This is a moodboard probe, never a deliverable."]),
        MOODBOARD_SLICE_MAX)
    inventory = _inventory_directive(project_root, scene)

    slices = {
        "version": 1,
        "element": scene["element"],
        "style": style,
        "geometry": geometry,
        "moodboard": moodboard,
        "inventory": inventory,
        "sceneSpecHash": _sha256_bytes(
            json.dumps(scene, sort_keys=True).encode("utf-8")),
    }

    outputs = manifest.get("outputs") or {}
    prompts = outputs.get("prompts") or {}
    compiled = project_root / str(prompts.get("compiled")
                                 or "moodboards/llm-shots/prompts/graphics-prompt.json")
    slices_dir = project_root / str(prompts.get("slicesDir")
                                   or "moodboards/llm-shots/prompts/slices")
    slices_dir.mkdir(parents=True, exist_ok=True)

    graphics_prompt = {
        "prompt": moodboard,
        "negative_prompt": ("photorealistic, glossy 3D, pixel art, monochrome, "
                            "broken road, dead-end road, small rooms, cramped cubes"),
        "aspect_ratio": manifest.get("adapters", {}).get("agy", {}).get(
            "aspectRatio", "16:9"),
        "style": "isometric editorial infographic",
        "background": "warm off-white",
        "slices": {
            "style": style,
            "geometry": geometry,
            "moodboard": moodboard,
            "inventory": inventory,
        },
    }
    _atomic_json(compiled, graphics_prompt)
    for name, text in slices.items():
        if name in {"version", "element", "sceneSpecHash"}:
            continue
        (slices_dir / f"{name}.txt").write_text(text + "\n", encoding="utf-8")
    _atomic_json(slices_dir / "manifest.json", slices)
    return {"compiled": str(compiled), "slicesDir": str(slices_dir), "slices": slices}


def _svg_texts(root: ET.Element) -> set[str]:
    return {"".join(node.itertext()).strip() for node in root.iter(f"{SVG_NS}text")}


def _svg_road(root: ET.Element) -> list[tuple[float, float]]:
    for tag in ("polyline", "polygon"):
        for node in root.iter(f"{SVG_NS}{tag}"):
            if node.get("id") == "road":
                pairs = [chunk.split(",") for chunk in node.get("points", "").split()]
                return [(float(x), float(y)) for x, y in pairs]
    return []


def _avoid_paths(project_root: Path) -> list[str]:
    return [path for path, _ in
            tagged_references(project_root, "illustration", stance="avoid")
            + tagged_references(project_root, "composition", stance="avoid")]


def gate_outputs(project_root: Path) -> dict[str, Any]:
    """Every check parses an artifact. None greps a string the loop just wrote."""
    from iso_svg import self_intersections, visit_order

    manifest = load_manifest(project_root)
    scene = load_scene(project_root, manifest)
    errors = validate_scene(scene)
    checks: list[dict[str, Any]] = [{"id": "scene-spec-valid", "passed": not errors}]

    svg_path = project_root / str((manifest.get("outputs") or {}).get("vector")
                                  or "shots/output.svg")
    root = None
    if not svg_path.exists():
        errors.append(f"missing svg: {svg_path}")
    else:
        try:
            root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
        except ET.ParseError as exc:
            errors.append(f"svg does not parse: {exc}")
    checks.append({"id": "svg-exists", "passed": root is not None})

    billboards = set((scene.get("billboards") or {}).values())
    missing = sorted(billboards - _svg_texts(root)) if root is not None else sorted(billboards)
    if missing:
        errors.append(f"svg missing billboards: {', '.join(missing)}")
    checks.append({"id": "billboard-text-present", "passed": not missing})

    faults: list[str] = []
    if root is not None:
        road = _svg_road(root)
        sequence = [str(step) for step in
                    ((scene.get("road") or {}).get("sequence") or [])][:-1]
        if len(road) < 8:
            faults.append('no element with id="road" carrying a point list')
        elif road[0] != road[-1]:
            faults.append("road is not closed")
        else:
            crossings = self_intersections(road)
            expected = int((scene.get("road") or {}).get("crossings", 1))
            if crossings != expected:
                faults.append(f"road crosses itself {crossings} times, expected {expected}")
            elif sequence:
                anchors = _scene_anchors(scene, road, sequence)
                order = visit_order(road, anchors)
                if order != sequence:
                    faults.append(f"road visits {order}, expected {sequence}")
    else:
        faults.append("no svg to read a road from")
    errors.extend(faults)
    checks.append({"id": "road-topology", "passed": not faults})

    compiled = project_root / str(((manifest.get("outputs") or {}).get("prompts")
                                   or {}).get("compiled") or "")
    leaked = []
    if compiled.exists():
        text = compiled.read_text(encoding="utf-8")
        leaked = [path for path in _avoid_paths(project_root) if path in text]
    if leaked:
        errors.append(f"avoid-tagged corpus used as style source: {', '.join(leaked)}")
    checks.append({"id": "no-avoid-corpus-as-style-source", "passed": not leaked})

    return {"passed": all(check["passed"] for check in checks),
            "checks": checks, "errors": errors}


def _scene_anchors(scene: Mapping[str, Any], road: list[tuple[float, float]],
                   sequence: list[str]) -> list[tuple[str, float, float]]:
    """Anchor each sequenced space to the road point nearest its declared centre."""
    xs = [x for x, _ in road]
    ys = [y for _, y in road]
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    positions = scene.get("positions") or {}
    anchors = []
    for space in spaces_of(scene):
        if str(space["id"]) not in sequence:
            continue
        box = positions.get(str(space["position"])) or {}
        cx = left + (right - left) * (box.get("x", 0.5) + box.get("width", 0) / 2)
        cy = top + (bottom - top) * (box.get("y", 0.5) + box.get("depth", 0) / 2)
        anchors.append((str(space["id"]), cx, cy))
    return anchors




def record_adapter(project_root: Path, adapter: str, verdict: str,
                   evidence: str) -> dict[str, Any]:
    """Record what a preflight probe actually saw. Python cannot call an MCP."""
    if verdict not in VERDICTS:
        raise GraphicsError(f"verdict must be one of {', '.join(VERDICTS)}")
    if not evidence.strip():
        raise GraphicsError("a verdict without evidence is a guess")
    path = project_root / STORE / SUPPORT_FILE
    record = _read_json(path) if path.exists() else {"version": 1, "adapters": {}}
    record.setdefault("adapters", {})[adapter] = verdict
    record.setdefault("evidence", {})[adapter] = {
        "verdict": verdict, "saw": evidence.strip(),
        "at": datetime.now(timezone.utc).isoformat()}
    _atomic_json(path, record)
    return record


def build_svg(project_root: Path) -> dict[str, Any]:
    """Draw with the in-repo renderer. Rung 2b, for when no adapter is available."""
    from iso_svg import build

    manifest = load_manifest(project_root)
    scene = load_scene(project_root, manifest)
    errors = validate_scene(scene)
    if errors:
        raise GraphicsError("; ".join(errors))
    out = project_root / str((manifest.get("outputs") or {}).get("vector")
                             or "shots/output.svg")
    out.parent.mkdir(parents=True, exist_ok=True)
    svg = build(scene)
    out.write_text(svg, encoding="utf-8")
    append_attempt(project_root, {"adapter": "iso-svg", "outcome": "accepted",
                                  "output": str(out), "sceneSpecHash": scene_hash(scene)})
    return {"vector": str(out), "bytes": len(svg.encode("utf-8"))}



def append_attempt(project_root: Path, record: Mapping[str, Any]) -> None:
    path = project_root / STORE / ATTEMPTS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(record)
    payload.setdefault("at", datetime.now(timezone.utc).isoformat())
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True) + "\n")


def _iso_fill(palette: Any, palettes: Mapping[str, Any]) -> str:
    if isinstance(palette, list) and palette:
        palette = palette[0]
    return str(palettes.get(str(palette), "#cccccc"))


def export_avge_calls(project_root: Path) -> dict[str, Any]:
    """Flatten the scene into the pattern list the AVGE Engine MCP consumes."""
    manifest = load_manifest(project_root)
    scene = load_scene(project_root, manifest)
    errors = validate_scene(scene)
    if errors:
        raise GraphicsError("; ".join(errors))

    positions = scene["positions"]
    palettes = manifest.get("palettes") or {}
    sequence = (scene.get("road") or {}).get("sequence") or []
    billboards = scene.get("billboards") or {}

    calls: list[dict[str, Any]] = [{
        "pattern": "create_line_pattern",
        "params": {
            "note": "Draw the road first, one-way arrows, sequence "
                    + " -> ".join(sequence),
            "stroke": str(manifest.get("roadStroke") or "#f4c430"),
            "z_index": 1,
        },
    }]
    z = 10
    for space in spaces_of(scene):
        calls.append({
            "pattern": "isometric_box",
            "params": {
                "new_prefix": _slug(space["id"]),
                **positions[str(space["position"])],
                "fill": _iso_fill(space.get("palette"), palettes),
                "z_index": z,
                "shadow": space in (scene.get("mainRooms") or []),
            },
        })
        z += 1
    for space in spaces_of(scene):
        calls.append({
            "pattern": "attach",
            "params": {
                "parent": f"{_slug(space['id'])}_top",
                "parent_anchor": "front_center",
                "note": f"Two-pole billboard text exactly: {billboards[space['id']]}",
                "z_index": z,
            },
        })
        z += 1

    payload = {
        "version": 1,
        "element": scene["element"],
        "adapter": "avge-engine",
        "sceneSpecHash": scene_hash(scene),
        "calls": calls,
    }
    out = _slices_dir(project_root, manifest) / "avge-calls.json"
    _atomic_json(out, payload)
    return {"avgeCalls": str(out), "callCount": len(calls)}


def seed_tags_from_manifest(project_root: Path) -> dict[str, Any]:
    from corpus_tags import group_of, load_corpus, load_tags, save_tags, tag_group

    manifest = load_manifest(project_root)
    hints = manifest.get("corpusTagHints")
    if not isinstance(hints, Mapping):
        raise GraphicsError("graphics-manifest.json missing corpusTagHints")

    corpus = load_corpus(project_root)
    paths = {str(item.get("path")): str(item.get("sha256"))
             for item in corpus.get("items", [])
             if isinstance(item, Mapping) and item.get("path") and item.get("sha256")}
    stamp = datetime.now(timezone.utc).isoformat()
    tagged_files = 0
    tagged_groups = 0

    for key, hint in hints.items():
        if not isinstance(hint, Mapping):
            continue
        event = {
            "aspects": [str(hint.get("aspect"))],
            "stance": hint.get("stance"),
            "quality": hint.get("quality"),
            "note": hint.get("note") or "",
            "at": stamp,
        }
        if key in paths:
            current = load_tags(project_root)
            digest = paths[key]
            current["tags"][digest] = {
                **event,
                "group": group_of(key),
                "note": str(hint.get("note") or "").strip(),
            }
            save_tags(project_root, current)
            tagged_files += 1
            continue
        group = key.rstrip("/")
        event["group"] = group
        tagged_groups += tag_group(project_root, event)

    return {"taggedFiles": tagged_files, "taggedGroupItems": tagged_groups}


def refresh_corpus(project_root: Path) -> dict[str, Any]:
    from editorial_workflow import observe_corpus

    manifest = load_manifest(project_root)
    root = project_root / str((manifest.get("corpus") or {}).get("root") or "moodboards")
    corpus = observe_corpus(project_root, root)
    return {"items": len(corpus.get("items", [])), "root": corpus.get("root")}


def run_moodboard(project_root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    manifest = load_manifest(project_root)
    compile_slices(project_root)
    agy = ((manifest.get("adapters") or {}).get("agy") or {})
    model = agy.get("imageModel", "gemini-3.1-flash-image-preview")
    compiled = project_root / "moodboards/llm-shots/prompts/graphics-prompt.json"
    prompt = _read_json(compiled)["prompt"]
    attempts_dir = project_root / str(
        (manifest.get("outputs") or {}).get("moodboardAttempts")
        or "moodboards/llm-shots/attempts")
    attempts_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    record = {
        "adapter": "agy",
        "model": model,
        "promptHash": _sha256_bytes(prompt.encode("utf-8")),
        "promptBytes": len(prompt.encode("utf-8")),
        "outcome": "rejected" if dry_run else "mixed",
        "note": "moodboard only; not deliverable",
    }
    if dry_run:
        record["command"] = (
            f"agy --dangerously-skip-permissions --print-timeout 15m -p "
            f"'Call generate_image once: AspectRatio 16:9, model {model}, "
            f"Prompt from {compiled}'"
        )
        append_attempt(project_root, record)
        return record

    instruction = (
        "Call generate_image exactly ONCE with AspectRatio 16:9, "
        f"ImageName moodboard_{stamp}, and the Prompt below. "
        f"Save PNG under {attempts_dir}/. Print path or error.\n\n"
        f"{prompt}"
    )
    cmd = ["agy", "--dangerously-skip-permissions", "--print-timeout", "15m", "-p", instruction]
    completed = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    record["exitCode"] = completed.returncode
    record["stdoutTail"] = completed.stdout[-2000:]
    record["stderrTail"] = completed.stderr[-2000:]
    record["outcome"] = "accepted" if completed.returncode == 0 else "rejected"
    append_attempt(project_root, record)
    if completed.returncode != 0:
        raise GraphicsError(f"agy moodboard failed: {completed.stderr[-500:]}")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("compile", help="emit adapter prompt slices and graphics-prompt.json")
    sub.add_parser("observe", help="refresh spec/design-harness/corpus.json from moodboards")
    sub.add_parser("seed-tags", help="apply graphics-manifest corpusTagHints to corpus-tags.json")
    sub.add_parser("export-avge", help="write moodboards/llm-shots/prompts/slices/avge-calls.json")
    sub.add_parser("gate", help="parse the drawn scene and check it")
    sub.add_parser("status", help="print the one next action and why")
    sub.add_parser("build", help="draw with the in-repo renderer (rung 2b)")
    pre = sub.add_parser("preflight", help="record what an adapter probe saw")
    pre.add_argument("--adapter", required=True)
    pre.add_argument("--verdict", required=True, choices=VERDICTS)
    pre.add_argument("--evidence", required=True)
    init = sub.add_parser("init", help="observe, seed-tags, compile, export-avge")
    mood = sub.add_parser("moodboard", help="run agy moodboard inference (not deliverable)")
    mood.add_argument("--dry-run", action="store_true", help="record command without calling agy")

    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    try:
        if args.command == "compile":
            result = compile_slices(root)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        elif args.command == "observe":
            result = refresh_corpus(root)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        elif args.command == "seed-tags":
            result = seed_tags_from_manifest(root)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        elif args.command == "export-avge":
            result = export_avge_calls(root)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        elif args.command == "init":
            steps = {
                "observe": refresh_corpus(root),
                "seedTags": seed_tags_from_manifest(root),
                "compile": compile_slices(root),
                "exportAvge": export_avge_calls(root),
            }
            json.dump(steps, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        elif args.command == "status":
            from graphics_flow import next_action, read_state

            state = read_state(root)
            step = next_action(state)
            json.dump({**step, "state": state}, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0 if step["action"] == "done" else 2
        elif args.command == "build":
            result = build_svg(root)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        elif args.command == "preflight":
            result = record_adapter(root, args.adapter, args.verdict, args.evidence)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        elif args.command == "gate":
            result = gate_outputs(root)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0 if result["passed"] else 1
        elif args.command == "moodboard":
            result = run_moodboard(root, dry_run=args.dry_run)
            json.dump(result, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        return 0
    except (GraphicsError, OSError, ValueError) as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("run `status` for the next action this project can actually take.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
