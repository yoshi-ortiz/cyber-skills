---
type: Policy
title: Asset sourcing contract
description: Resolve licensed reusable assets before deterministic generation.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

# Asset sourcing contract

Do not spend inference effort rebuilding common visual assets, and never hallucinate vector geometry.

## Resolution order

1. Reuse an asset already present in the project or corpus.
2. Fetch the smallest suitable asset from a pinned open-source library or primary archive.
3. Generate it procedurally only when the desired form is genuinely custom and the procedure is deterministic.
4. Otherwise omit it and report the missing asset.

This order applies to icons, ornaments, dividers, marks, textures, bitmap and pixel fonts, kaomoji, Unicode arrangements, and ASCII graphics. A publicly available pixel font should be fetched and licensed, not redrawn glyph by glyph.

## Cheap evidence first

Inspect representative pages and images before expensive extraction. Corpus
files are hashed at intake; parsing every embedded object or installing a new
tool requires a design question that the cheaper view cannot answer.

Each recommendation names its category, observed cue, design question, primary
source, license or attribution, pinned version or retrieval date, expected cost,
and disposition. Raise obvious categories such as iconography, pixel type,
ASCII/Unicode, motion curves, spatial standards, or compositing sources without
asking the user to invent a library name.

Resolve the official documentation or primary repository, confirm the license,
pin the source, fetch only the current cohort's artifact, hash it outside the
immutable corpus, and record every transformation. A search snippet, unofficial
mirror, remembered vector path, or generated imitation is not a resolved source.

## Provenance record

Every fetched asset records:

- canonical source URL and collection;
- asset name and stable upstream id;
- version, commit, or retrieval date;
- license and required attribution;
- local path and content hash;
- transformations applied.

For icons, prefer a broad structured collection such as pinned Iconify JSON when it fits. Fetch the exact icon data. Never fabricate an `svg path`, trace a remembered logo, or claim an icon exists without resolving it.

## Procedural graphics

A procedure must declare its seed, dimensions, character/glyph set, algorithm, parameters, and output path. The same inputs must reproduce the same bytes. HTML/CSS geometric primitives are acceptable when they are the visible system itself; opaque hand-written SVG coordinates are not.

Kaomoji and ASCII art are sourced text graphics. Preserve whitespace and line endings, declare the font fallback, expose accessible text or an equivalent label, and test narrow containers. Emoji are not a substitute for a requested graphic.

## Failure behavior

If licensing, identity, or geometry cannot be verified, omit the asset. Keep an explicit placeholder in the work record, not a plausible imitation in the design.
