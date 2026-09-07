---
type: Reference
title: House of Quality as a conceptual relation model
description: Represent explicit need-to-characteristic relationships, priorities, targets, and trade-offs without mistaking the matrix for a formal ontology.
status: stable
resource: https://www.ifm.eng.cam.ac.uk/research/dmg/tools-and-techniques/quality-function-deployment-qfd/
tags:
  - ontology
  - conceptual-model
  - quality-function-deployment
  - house-of-quality
generated:
  by: codex/gpt-5
  at: 2026-09-06T00:00:00-06:00
sources:
  - resource: https://asq.org/quality-resources/house-of-quality
    title: House of Quality
    author: American Society for Quality
  - resource: https://www.ifm.eng.cam.ac.uk/research/dmg/tools-and-techniques/quality-function-deployment-qfd/
    title: Quality Function Deployment (QFD)
    author: University of Cambridge Institute for Manufacturing
---

# House of Quality as a conceptual relation model

House of Quality can be represented as an explicit relation model: customer
needs, engineering characteristics, evidence or benchmarks, relationship
strengths, technical targets, and technical correlations. Typical edges are
`addresses`, `supports`, `conflicts_with`, and `prioritized_by`.

## Purpose

Use this model when a team needs to preserve why a characteristic was proposed,
which need it addresses, what evidence supported the relationship, and what
trade-off was recorded. Preserve provenance, context, relationship scale, team
or decision date, and uncertainty rather than storing only a final priority.

## Boundary

This is a conceptual relation model, not an OWL/RDF ontology or an executable
schema. Matrix rows, columns, and weights do not establish semantic identity,
causal truth, or permission for a system to take action. The corresponding QA
note owns the procedural use of House of Quality; this note only exposes its
conceptual structure.
