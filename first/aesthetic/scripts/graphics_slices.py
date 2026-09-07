#!/usr/bin/env python3
"""Turn a scene and its corpus into the prompt slices an adapter is sent.

Extracted from `text_to_graphics.py`, which is a parser and a re-export block
and went over its byte budget by being the easy place to put things. One
concern lives here: what a model is told, and which part of that is measured
evidence rather than someone's prose.

The facade delegates to this module and this module imports the facade's
loaders. That is a one-way dependency, not a cycle: nothing in
`text_to_graphics` imports this module at import time.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from graphics_corpus import (prompt_inputs_hash, refine_references,
                             tagged_references)
from text_to_graphics import (DERIVED_FILE, STORE, GraphicsError, _atomic_json,
                              _read_json, _sha256_bytes, _slices_dir, _truncate,
                              inventory_sections, load_manifest, load_scene,
                              spaces_of, validate_scene)

STYLE_SLICE_MAX = 4000
INVENTORY_PER_SPACE_MAX = 3000
GEOMETRY_SLICE_MAX = 8000
MOODBOARD_SLICE_MAX = 12000
TOOLS_SLICE_MAX = 6000
CLEAR_SHOT_PROMPT_MAX = 12000


def known_failures(project_root: Path) -> list[dict[str, str]]:
    """Defects a generator already produced and the user already rejected.

    Kept as data rather than prose so a rejection reaches the next prompt by
    itself. Without this the lesson lives in a tag note and a shot record that
    nothing assembling the prompt ever reads, which is how the same broken road
    came back round after round.
    """
    path = project_root / STORE / "known-failures.json"
    if not path.exists():
        return []
    payload = _read_json(path) or {}
    return [entry for entry in payload.get("failures") or []
            if isinstance(entry, Mapping) and entry.get("constraint")]


def _corpus_path(manifest: Mapping[str, Any], path: str) -> str:
    root = str((manifest.get("corpus") or {}).get("root") or "moodboards").rstrip("/")
    return f"{root}/{path.lstrip('/')}"


def _clear_shot_reference(project_root: Path,
                          manifest: Mapping[str, Any]) -> str:
    configured = str(((manifest.get("adapters") or {}).get("agy") or {}).get(
        "clearShotReference") or "").strip()
    if configured:
        return configured
    matches = [path for path, _ in tagged_references(project_root, "composition")
               if "clear layout" in path.lower()]
    if not matches:
        raise GraphicsError("no clear-shot composition reference is configured or tagged")
    return _corpus_path(manifest, matches[0])


def _clear_shot_cast(project_root: Path,
                     scene: Mapping[str, Any]) -> list[str]:
    path = project_root / STORE / "cast.json"
    cast = _read_json(path) if path.exists() else {}
    figures = cast.get("figures") or {}
    lines = []
    for space in spaces_of(scene):
        identifier = str(space["id"])
        figure = figures.get(identifier) or {}
        name = str(figure.get("name") or space.get("boss") or "one room boss")
        prop = str(figure.get("prop") or "one readable signature object")
        direction = str(figure.get("direction") or "").strip()
        palette = space.get("palette")
        hue = ", ".join(str(item) for item in palette) \
            if isinstance(palette, list) else str(palette)
        kind = "open room" if space in (scene.get("mainRooms") or []) else "small kiosk"
        line = (
            f"- {identifier}, {space.get('position')}, {hue} {kind}. "
            f"{name} with one clearly held {prop}.")
        lines.append(line + (f" {direction}" if direction else ""))
    return lines


def clear_shot_prompt(project_root: Path) -> dict[str, Any]:
    """Write the focused image-edit prompt used for the clear-shot attempt.

    This is shorter than the audit-oriented deterministic prompt. It tells the
    image model what to preserve, gives each fact once, and carries only the
    rejection constraints that the model can act on.
    """
    manifest = load_manifest(project_root)
    scene = load_scene(project_root, manifest)
    errors = validate_scene(scene)
    if errors:
        raise GraphicsError("; ".join(errors))

    target = _clear_shot_reference(project_root, manifest)
    illustration = [path for path, _ in tagged_references(project_root, "illustration")
                    if path.startswith("cartoon/")]
    if not illustration:
        illustration = [path for path, _ in
                        tagged_references(project_root, "illustration")]
    references = [_corpus_path(manifest, path) for path in illustration]
    road = scene.get("road") or {}
    sequence = " -> ".join(str(step) for step in road.get("sequence") or [])
    billboards = scene.get("billboards") or {}
    failures = known_failures(project_root)
    rules = {str(entry.get("id")): str(entry.get("rule") or entry["constraint"])
             for entry in failures}

    used_rules: set[str] = set()

    def section_rules(*identifiers: str) -> list[str]:
        selected = []
        for identifier in identifiers:
            if identifier in rules:
                selected.append(f"- {rules[identifier]}")
                used_rules.add(identifier)
        return selected

    lines = [
        "Edit the target image. Keep what works. Fix the drawing errors without "
        "replacing its personality.",
        "",
        f"Target: {target}",
        "Keep its composition and cartoon register. Keep the compact isometric "
        "world, saturated flat color, heavy dark outlines, cute characters, and "
        "busy room interiors.",
    ]
    if references:
        lines += ["", "Character reference:"]
        lines += [f"- {path}" for path in references]
        lines += ["Use these images for faces, body shapes, poses, outline weight, "
                  "and comic detail. Do not replace them with corporate flat people "
                  "or homemade geometric figures."]

    lines += [
        "",
        "Output",
        "- One 16:9 PNG at 1536 by 864 pixels.",
        "- Warm off-white background.",
        *section_rules("watermark"),
        "",
        "Road",
        *section_rules("open-road"),
        f"- Travel {road.get('direction')} through {sequence}.",
        *section_rules("opposing-arrows"),
        "",
        "Spaces",
        "- Draw four large rooms and two smaller kiosks. Draw no seventh space.",
        *section_rules("empty-rooms", "ghosted-kiosks", "tall-cubic-rooms",
                       "rooms-undersized"),
        *_clear_shot_cast(project_root, scene),
        "",
        "Labels",
        *section_rules("missing-billboards", "duplicated-billboards",
                       "text-painted-on-walls", "invented-numerals",
                       "invented-billboard-strings"),
        "- Reproduce these strings exactly. These are the only words in the image:",
        *[f'- {key}: "{billboards[key]}"' for key in sorted(billboards)],
    ]

    observations = _character_observations(project_root)
    positive = [line for line in observations
                if line.startswith("- ") and not line.startswith("- Never")]
    if positive:
        lines += ["", "Characters", *section_rules("realistic-people"), *positive]

    remaining = [f"- {rules[identifier]}" for identifier in rules
                 if identifier not in used_rules]
    if remaining:
        lines += ["", "Other constraints", *remaining]

    text = "\n".join(lines).strip() + "\n"
    if len(text.encode("utf-8")) > CLEAR_SHOT_PROMPT_MAX:
        raise GraphicsError(
            f"clear-shot prompt exceeds {CLEAR_SHOT_PROMPT_MAX} bytes")
    outputs = (manifest.get("outputs") or {}).get("prompts") or {}
    out = project_root / str(outputs.get("clearShot") or
                             "moodboards/llm-shots/prompts/clear-shot-prompt.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return {"clearShotPrompt": str(out), "bytes": len(text.encode("utf-8")),
            "target": target, "references": references,
            "billboards": len(billboards), "failures": len(failures)}


def deterministic_prompt(project_root: Path) -> dict[str, Any]:
    """Assemble the whole image prompt from the sources that already hold it.

    The hand-written prompt this replaces stated the billboard strings twice
    and the two lists disagreed on three of six, so the generator was handed a
    contradiction and invented a third answer. Every fact here appears exactly
    once, taken from the file that owns it: strings from the scene spec,
    colour from measured pixels, figure construction from observations, and
    the negative constraints from the failure ledger.
    """
    from graphics_corpus import derived_measurements, evidenced_palette
    from iso_svg import PALETTE_FILL, snap_palette

    manifest = load_manifest(project_root)
    scene = load_scene(project_root, manifest)
    errors = validate_scene(scene)
    if errors:
        raise GraphicsError("; ".join(errors))

    spaces = spaces_of(scene)
    rooms = [str(room["id"]) for room in scene.get("mainRooms") or []]
    road = scene.get("road") or {}
    billboards = scene.get("billboards") or {}

    out: list[str] = [
        f"# {scene['element']} -- deterministic prompt",
        "",
        "Generated by `text_to_graphics.py deterministic`. Do not hand-edit: the",
        "previous hand-written version stated the billboard text twice and the two",
        "lists disagreed, which is what produced invented signage. Every fact below",
        "appears exactly once.",
        "",
        "## STYLE",
        _style_directive(manifest),
    ]

    # `rule`, not `read`. The long form carries its provenance essay and crop
    # box, which is the audit trail; an image model needs the one imperative.
    # An entry with no rule is audit-only and never reaches the generator.
    payload = _read_json(project_root / STORE / "character-observations.json") \
        if (project_root / STORE / "character-observations.json").exists() else {}
    build, avoid = [], []
    for entry in (payload or {}).get("observations") or []:
        if not isinstance(entry, Mapping) or not entry.get("rule"):
            continue
        (avoid if entry.get("stance") == "avoid" else build).append(
            f"- {entry['rule']}")
    if build:
        out += ["", "How a figure is built in this style:"] + build
    if avoid:
        out += ["", "Never draw figures in this register:"] + avoid

    pursued = [path for path, _ in tagged_references(project_root, "illustration")]
    palette = evidenced_palette(project_root, pursued or None)
    measured = derived_measurements(project_root)
    papers = [rec["paper"] for path, rec in sorted(measured.items())
              if path in pursued and rec.get("paper")]
    inks = [rec["ink"] for path, rec in sorted(measured.items())
            if path in pursued and rec.get("ink")]
    # Per-space colour is the scene's declared intent, not a snap onto the
    # measured list. The in-repo renderer snaps because it must not invent a
    # colour; a generative model can draw any hue, and forcing /build onto the
    # nearest corpus swatch would silently repaint a room the scene calls
    # magenta. The measured values set the register, the scene sets the hue.
    out += ["", "## COLOUR"]
    if palette:
        out += [f"Background {papers[0] if papers else 'warm off-white'}. "
                f"Outline {inks[0] if inks else 'near-black'}, one weight everywhere.",
                "Saturation and temperature to match these measured reference "
                "values: " + " ".join(palette)]
    out.append("Each space in its own declared hue, flat fills, no gradients:")
    for space in spaces:
        hue = space.get("palette")
        hue = ", ".join(hue) if isinstance(hue, list) else str(hue)
        out.append(f"- {space['id']}: {hue}")

    sequence = " -> ".join(str(step) for step in road.get("sequence") or [])
    out += ["", "## GEOMETRY",
            f"Layout: {scene.get('layout')}. Six spaces, no seventh.",
            f"Road: {road.get('shape')}, {road.get('direction')}, one way, "
            f"following {sequence} and closing on itself.",
            "Spaces and where they sit:"]
    for space in spaces:
        kind = "room" if str(space["id"]) in rooms else "kiosk"
        out.append(f"- {space['id']} ({kind}) at {space.get('position')}")

    out += ["", "## BILLBOARDS -- one per space, six in total",
            "Reproduce each string character for character, leading slash included.",
            "These are the only words that may appear anywhere in the image."]
    out += [f'- {key}: "{billboards[key]}"' for key in sorted(billboards)]

    out += ["", "## WHAT EACH SPACE CONTAINS",
            _inventory_directive(project_root, scene)]

    failures = known_failures(project_root)
    if failures:
        out += ["", "## ALREADY REJECTED -- do not reproduce any of these",
                "Each line is a defect a generator produced and the user sent back."]
        for entry in failures:
            out.append(f"- {entry['id']}: {entry['constraint']}")
            out.append(f"  (seen in {entry.get('seenIn')}: {entry.get('defect')})")

    # Raw shot corrections deliberately do NOT go in. They are addressed to
    # other adapters -- HTML comps, the companion app -- and shipping them to an
    # image model is context contamination. `known-failures.json` is their
    # curated form, and that is what an image generator can act on.

    text = "\n".join(out) + "\n"
    outputs = (manifest.get("outputs") or {}).get("prompts") or {}
    target = project_root / str(outputs.get("deterministic")
                                or "moodboards/llm-shots/prompts/deterministic-prompt.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return {"deterministic": str(target), "bytes": len(text.encode("utf-8")),
            "billboards": len(billboards), "failures": len(failures),
            "palette": palette}


def _requested_hue(palette_fill: Mapping[str, str], space: Mapping[str, Any]) -> str:
    name = space.get("palette")
    if isinstance(name, list) and name:
        name = name[0]
    return palette_fill.get(str(name), "#cccccc")


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


def _measured_line(record: Mapping[str, Any]) -> str:
    """One reference's measured colour, in the order a drawer needs it."""
    fills = [str(entry.get("hex")) for entry in record.get("palette") or []
             if isinstance(entry, Mapping) and entry.get("hex")]
    parts = [f"paper {record['paper']}"] if record.get("paper") else ["no light ground"]
    if record.get("dominant"):
        parts.append(f"widest {record['dominant']}")
    if record.get("ink"):
        parts.append(f"ink {record['ink']}")
    if fills:
        parts.append("fills " + " ".join(fills))
    if record.get("inkShare") is not None:
        parts.append(f"contour covers {float(record['inkShare']) * 100:.0f}% of the frame")
    return ", ".join(parts)


def _character_observations(project_root: Path) -> list[str]:
    """How a figure is built, as imperatives a model can act on.

    Emits `rule`, never `read`, and never the source path. The long form and
    its crop box are the audit trail and belong in the observations file; a
    filename in a prompt is worse than useless here, because naming an
    avoid-tagged reference is how a model goes and fetches that very register.
    The `no-avoid-corpus-as-style-source` gate exists for exactly that, and it
    caught this the first time round.
    """
    path = project_root / STORE / "character-observations.json"
    if not path.exists():
        return []
    payload = _read_json(path) or {}
    build, avoid = [], []
    for entry in payload.get("observations") or []:
        if not isinstance(entry, Mapping) or not entry.get("rule"):
            continue
        (avoid if entry.get("stance") == "avoid" else build).append(
            f"- {entry['rule']}")
    if avoid:
        build.append("\nNever draw figures in this register:")
        build += avoid
    return build


def _style_slice(project_root: Path, manifest: Mapping[str, Any]) -> str:
    from graphics_corpus import derived_measurements, evidenced_palette

    lines = [_style_directive(manifest)]
    observed = _character_observations(project_root)
    if observed:
        lines.append("\nHow this corpus builds a figure, read off the references:")
        lines += observed
    pursued = tagged_references(project_root, "illustration")
    measured = derived_measurements(project_root)
    if pursued:
        lines.append("\nPursue these references:")
        for path, note in pursued:
            described = f"- {path}" + (f" ({note})" if note else "")
            record = measured.get(path)
            if record:
                described += "\n  measured: " + _measured_line(record)
            else:
                described += "\n  measured: not measured; do not infer its colour"
            lines.append(described)
    evidenced = evidenced_palette(project_root,
                                  [path for path, _ in pursued] or None)
    if evidenced:
        # The whole point of measuring. A fill outside this list is a colour
        # the corpus does not evidence, which is the move anti-slop.md forbids.
        lines.append("\nDraw fills from these measured colours only, widest coverage first:")
        lines.append(" ".join(evidenced))
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


def measure_corpus_images(project_root: Path) -> dict[str, Any]:
    """Read the pixels of every image the corpus lists.

    Runs against the whole corpus rather than the pursued subset, because a
    stance can change without the files changing, and re-measuring on every
    retag would be work the bytes do not justify.
    """
    from corpus_measure import measure_corpus

    corpus = _read_json(project_root / STORE / "corpus.json")
    images = [item for item in corpus.get("items") or []
              if isinstance(item, Mapping) and item.get("kind") == "image"]
    result = measure_corpus(project_root, images)
    _atomic_json(project_root / STORE / DERIVED_FILE, result)
    return result


def compile_slices(project_root: Path) -> dict[str, Any]:
    from graphics_tool_research import context, load as load_tool_research

    research = load_tool_research(project_root)
    if research is None:
        raise GraphicsError("missing graphics-tools.json; run status and research-tools")
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
    refine = "\n".join(
        ["REFINE EXISTING ATTEMPTS - edit or reuse these; do not spend a fresh shot."]
        + [f"- {path}: {note}" for path, note in refine_references(project_root)])
    tools = _truncate(json.dumps(context(research), ensure_ascii=False, sort_keys=True),
                      TOOLS_SLICE_MAX)

    slices = {
        "version": 1,
        "element": scene["element"],
        "style": style,
        "geometry": geometry,
        "moodboard": moodboard,
        "inventory": inventory,
        "refine": refine,
        "tools": tools,
        "sceneSpecHash": _sha256_bytes(
            json.dumps(scene, sort_keys=True).encode("utf-8")),
        "promptInputsHash": prompt_inputs_hash(project_root, manifest, scene),
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
            "refine": refine,
            "tools": tools,
        },
    }
    _atomic_json(compiled, graphics_prompt)
    for name, text in slices.items():
        if name in {"version", "element", "sceneSpecHash", "promptInputsHash"}:
            continue
        (slices_dir / f"{name}.txt").write_text(text + "\n", encoding="utf-8")
    _atomic_json(slices_dir / "manifest.json", slices)
    return {"compiled": str(compiled), "slicesDir": str(slices_dir), "slices": slices}
