---
type: Reference
title: Design domain profiles
description: Evidence and verification extensions for different creative domains.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

# Domain profiles

Select the smallest set that covers the current project. Profiles extend one evidence, critique, and promotion lifecycle; they do not create separate workflows.

## frontend-layout

Capture framework and Storybook availability, semantic component inventory, responsive viewports, browser state, accessibility, performance, and visual baselines. Prefer DOM/text inspection before screenshots. Use DevTools MCP, Playwright, Lighthouse, and Storybook MCP only when available and recorded by preflight.

## art-direction

Capture visual grammar, mark-making, shape, texture, illustration, iconography, type, color behavior, and licensing. Generate confirmation questions for likely deterministic libraries or archives. For terminal-like, monospaced, diagrammatic, retro-computing, or text-ornament cues, explicitly recommend evaluating an ASCII/Unicode art library.

## motion

Capture trigger, duration, easing, choreography, interruption, reduced-motion behavior, and performance budget. Prefer named timelines and keyframe data over prose. Pin any motion library version and verify reduced-motion conformance.

## composition

Capture hierarchy, grid, focal path, density, rhythm, cropping, negative space, and responsive transformations. Express decisions as semantic relationships and testable frames rather than generated CSS.

## physical-space

Capture units, scale, dimensions, clearances, human reach/viewing distance, orientation, materials, finishes, lighting, environmental conditions, accessibility, safety, fabrication constraints, and camera/viewpoints. Reject unscaled imagery as dimensional evidence. Keep observed dimensions separate from inferred dimensions.

## product-design

Capture user/job, object lifecycle, interaction sequence, ergonomics, assembly, materials, manufacturing process, tolerances, serviceability, packaging, regulatory constraints, and environmental impact. Pair with `physical-space` when the object depends on its environment.

## copywriting

Capture audience, job, promise, voice, information hierarchy, required claims, evidence for claims, prohibited language, legal review, localization, and channel constraints. Do not turn unsupported inspiration copy into a factual claim. Keep source quotations short and traceable.

## mockup-layering

Represent every output with an ordered layer manifest: canvas size, units, color profile, renderer/version, source hashes, layer order, position, scale, rotation, crop, mask, opacity, blend mode, effects, and export format. A render is reproducible only when the same manifest and source hashes produce the same output hash, or a documented renderer-specific tolerance.
