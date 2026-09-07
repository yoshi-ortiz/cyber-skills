---
type: Reference
title: Recursive self-improvement and governed evidence loops
description: Separate full recursive self-improvement from a bounded, reviewed improvement experiment.
status: stable
resource: https://www.anthropic.com/institute/recursive-self-improvement
tags:
  - sri
  - evaluation
  - recursive-self-improvement
  - quality-assurance
generated:
  by: codex/gpt-5
  at: 2026-09-06T00:00:00-06:00
sources:
  - resource: https://www.anthropic.com/institute/recursive-self-improvement
    title: Recursive self-improvement
    author: Anthropic Institute
  - resource: ../../project-management/QA/quality-improvement-methods.md
    title: Quality improvement methods for project QA
    author: Local cited knowledge bundle
---

# Recursive self-improvement and governed evidence loops

Anthropic describes full recursive self-improvement as a system autonomously
designing and developing its successor. Its article says that state is neither
present nor inevitable. Current ability to run code, delegate work, or execute
bounded research therefore does not establish recursive self-improvement.

## Purpose for SRI work

A useful near-term purpose is a governed experiment:

```text
human selects objective and metric
  -> candidate change
  -> execution and recorded observation
  -> predeclared evaluation
  -> human accepts, rejects, or requests correction
```

Anthropic reports experiments in which a goal and correctness metric were fixed
in advance, then an agent iterated by changing, running, timing, and comparing
code. That supports the shape above. It does not give the agent authority to
choose the objective, scoring rubric, successor, or release decision.

## QA relation

This mapping is an inference, grounded in the local
[project-QA concept](../../project-management/QA/quality-improvement-methods.md):

- Lean/TPS evidence makes waiting, rework, handoffs, and failed stops visible.
- Quality-management evidence assigns owners, acceptance requirements, review
  records, and evidence-based decisions.
- Statistical-control evidence tests whether a metric is stable enough to
  support a capability or improvement claim.

Together they make a candidate observable, measured, reviewable, and reversible.
They do not demonstrate autonomous self-improvement or that an observed change
caused a general capability gain.

## Controls inferred for a governed experiment

Keep a baseline and candidate, freeze the acceptance metric before comparison,
retain provenance and raw evidence, scope mutation to a reversible artifact, and
require a human decision before adoption. These controls are architectural
inferences from Anthropic's fixed-metric experiments and its discussion of human
judgment; they are not an Anthropic-prescribed implementation.
