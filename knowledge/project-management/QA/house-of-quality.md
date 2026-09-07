---
type: Reference
title: House of Quality for project QA
description: Use the Quality Function Deployment planning matrix to trace customer needs to measurable, prioritized quality characteristics.
status: stable
resource: https://asq.org/quality-resources/house-of-quality
tags:
  - project-management
  - quality-assurance
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
  - resource: https://search.worldcat.org/title/Quality-Function-Deployment-QFD-Integrating-Customer-Requirements-into-Product-design/oclc/1050966150
    title: Quality Function Deployment: Integrating Customer Requirements into Product Design
    author: Yoji Akao and Glenn H. Mazur
---

# House of Quality for project QA

House of Quality is QFD's product-planning matrix. It connects customer
requirements to the ways a team intends to meet them. The Cambridge QFD guide
describes linked areas for voice-of-customer attributes, engineering
characteristics, their relationship strengths, technical priorities and targets,
technical correlations, and planning information. ASQ says the targets should
be measurable and supported by historical records, designed experiments, or
competitor analysis.

## QA purpose

Use the matrix as a cross-functional, reviewable translation from cited customer
needs to measurable quality characteristics. It can expose omitted needs,
competing technical targets, and where a planned verification measure does not
actually address a stated need. Keep the source, context, date, relationship
scale, responsible reviewers, and uncertainty with each row and relationship.

For QA, the output is a proposed measurement and verification plan, not a
verdict. Validate targets independently against observations, tests, or other
fit-for-purpose evidence before accepting a result.

## Relation to SRI

This is a QA-only inference, not a claim made by the QFD sources: a governed
self-recursive-improvement experiment could use a House of Quality artefact to
link its declared objective to measurable evaluation characteristics and to
surface conflicts. The matrix cannot define the objective, validate evidence,
choose an action, or authorize a mutation.

## Boundary

House of Quality is a planning and translation aid. Its scores and relationship
strengths are team judgments, not proof of causal effect, customer truth,
deployment approval, or a released outcome. The Cambridge guide notes that QFD
can become complex and time-consuming and needs facilitation; do not create a
matrix where the evidence, decision, or accountable owner is absent.
