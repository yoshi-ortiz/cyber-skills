---
type: Specification
title: Portable evidence-backed design harness
description: Product boundaries and acceptance seam for the aesthetic skill.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

# Portable evidence-backed design harness

## Problem

Design agents hallucinate when references, tools, preference evidence, and
approval state are implicit. The harness must preserve user-owned inspiration,
make feedback and scope replayable, and keep probabilistic art direction bounded
by inspectable evidence without becoming a generic workflow engine.

## Product contract

- Any user-named source folder remains read-only and is inventoried by hash.
- Images and text form one multimodal evidence set.
- User execution rank, direction sentiment, lifecycle, and missing feedback are
  independent fields at individual-element granularity.
- Deterministic descriptive statistics support sentiment inference; they do not
  create a synthetic taste or reward score.
- Art-direction hypotheses cite observations and preference evidence, include
  counterevidence and confidence, and select one small test cohort.
- Explicit project epics and elements produce two honest burndown series inside
  the established Aesthetic ranking article.
- Theme candidates persist in `spec/design-harness/theme.json`; unsafe elements
  fall back individually to their last safe values.
- Common graphics and fonts are fetched from pinned licensed sources before any
  deterministic procedural generation. Vector paths are never invented.
- API, MCP, desktop-automation, publishing, and output support is domain-neutral
  and earns PASS only through the evidence contract in
  [platform-support.md](platform-support.md).

## Boundaries

The harness does not automatically install external libraries, mutate the
reference corpus, infer user approval, replace a project design system, or claim
that automated checks prove aesthetic quality. Sentiment analysis is in scope
only for grounded creative direction and design feedback; broader behavioral
profiling is not.

## Acceptance seam

A disposable project fixture proves corpus integrity, independent feedback
replay, preference states, idempotent scope history, separate burndown series,
element-level contrast fallback, article structure, and companion controls.
Rendered desktop and narrow screenshots remain a required human-quality check.
The support manifest separately proves all seventeen workflow requirements;
missing credentials or compatible interfaces remain BLOCKED rather than being
simulated as PASS.
