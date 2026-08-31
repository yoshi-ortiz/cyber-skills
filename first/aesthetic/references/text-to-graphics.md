---
type: Playbook
title: Text-to-graphics loop
description: Corpus-tagged inference from references to a checked, procedurally drawn scene.
status: draft
generated:
  by: cursor/claude-opus-5
  at: 2026-08-30T17:45:00-06:00
---

# Text-to-graphics

Loop inference skill for **Design-Inference Context**. A scene is data, not a
prompt. Geometry, labels, and topology come from `scene-spec.json` and are
checked after drawing. Image models probe composition and never ship.

Read [asset-sourcing.md](asset-sourcing.md) first. Never mix inventory prose and
style directives in one model call.

## Run it

Ask the loop what to do. Do that one thing. Ask again.

```bash
python3 <skill>/scripts/text_to_graphics.py --project-root . status
```

`status` reads the artifacts and prints one `action` with the `reason` it fired.
Exit 0 means done, exit 2 means the named action is outstanding. Nothing else in
this file tells you what order to work in, because the order is computed.

| Action | Do |
| --- | --- |
| `edit-scene-spec` | Fix what the reason names. The scene is the truth everything else derives from. |
| `add-corpus` | Put reference material under the manifest's corpus root. There is nothing to observe yet |
| `observe` | `text_to_graphics.py observe` |
| `seed-tags` | `text_to_graphics.py seed-tags`, then tag by hand for anything the manifest hints miss |
| `compile` | `text_to_graphics.py compile` |
| `export-avge` | `text_to_graphics.py export-avge` |
| `preflight` | Probe the adapter yourself, then record what you saw (below) |
| `run-avge` | Execute every call in `slices/avge-calls.json` through the AVGE Engine MCP |
| `build` | `text_to_graphics.py build`, the in-repo renderer, when no adapter is available |
| `repair-output` | The gate rejected the drawing. Fix the cause the reason names, then redraw |
| `done` | Every gate passes and no artifact is stale |

An output is stale when no recorded attempt drew it from the current scene hash.
An artifact with no attempt behind it has unknown provenance and is redrawn.

## Resolution order

1. Reuse an asset already in corpus or `shots/`.
2. **AVGE Engine MCP** procedural scene from `avge-calls.json`.
   2b. `iso_svg.py` in-repo renderer, when no adapter is authorized. It draws
   `isometric-x` layouts only and refuses anything else by name.
3. **SVGMaker MCP** for vector styling or raster conversion.
4. **agy CLI** moodboard raster. Never a deliverable.
5. Omit and record the gap.

## Adapter verdicts

Python cannot call an MCP, so `preflight` records what you saw rather than
probing. A verdict without evidence is refused.

```bash
python3 <skill>/scripts/text_to_graphics.py --project-root . preflight \
  --adapter avge --verdict PASS --evidence "tool list returned isometric_box"
```

Verdicts land in `spec/design-harness/support.json` and route the draw step.
That file records adapter availability for this loop. It is **not** the
seventeen-requirement design manifest that `support_contract.py` validates; do
not point one at the other.

## Slices, and why they never merge

`compile` writes four slices. Each has one consumer and one forbidden content.

| Slice | Built from | Max bytes | Must not carry |
| --- | --- | --- | --- |
| `style` | manifest `styleDirective` plus `illustration·pursue` corpus paths | 4 000 | inventory, space names, billboard text |
| `geometry` | `scene-spec.json` only | 8 000 | character prose, style adjectives |
| `moodboard` | `style` plus `composition·pursue` corpus paths | 12 000 | full inventory |
| `inventory` | `inventoryRef`, split per space | 3 000 each | anything sent to an image model |

Only `pursue` tags reach a slice. That is what makes the `avoid` stance mean
something, and it is why retagging a reference changes the next prompt.

A long human-authored inventory is an **authoring surface**. `compile` splits it
on its `## /space` headings and keys it to the scene's declared spaces. Sending
it whole to an image model is how this loop failed before it existed.

## Project agnostic

The module names no room. Everything fixture-specific is data.

| Lives in | Carries |
| --- | --- |
| `scene-spec.json` | element, layout, road, `positions`, spaces, billboards, `inventoryRef` |
| `graphics-manifest.json` | `palettes`, `styleDirective`, corpus root, adapters, outputs, tag hints |

`validate_scene` checks structure, never a specific scene. A road is valid when
its sequence closes and names only declared spaces. A new element is a new JSON
file, not a code change.

## Gates

Every check parses the artifact. None greps a string the loop just wrote, per
[verification.md](verification.md).

- `scene-spec-valid` structure, closed road, every space positioned and labelled.
- `svg-exists` the output parses as XML.
- `billboard-text-present` each command appears as `<text>` node content.
- `road-topology` the element with `id="road"` is closed, crosses itself the
  declared number of times, and reaches the sequenced spaces in order. The
  geometry slice tells every adapter to emit that id, because this is the check
  the loop exists for.
- `no-avoid-corpus-as-style-source` no `avoid`-tagged path reached the prompt.

Deferred: monochrome histogram, sprite sheets, browser preview and PNG export.
