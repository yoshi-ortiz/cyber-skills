---
type: Reference
title: Embedding Vector Oriented Clustering
description: Use EVoC clusters as reviewable candidate families, never as truth or a mutation trigger.
status: stable
resource: https://evoc.readthedocs.io/en/latest/user_guide.html
tags:
  - ontology
  - clustering
  - evoc
generated:
  by: codex/gpt-5
  at: 2026-09-06T00:00:00-06:00
sources:
  - resource: https://evoc.readthedocs.io/en/latest/user_guide.html
    title: EVoC user guide
    author: Tutte Institute
  - resource: https://github.com/TutteInstitute/evoc
    title: EVoC source repository
    author: Tutte Institute
---

# Embedding Vector Oriented Clustering

EVoC builds a k-nearest-neighbor graph from embeddings, learns a lower-dimensional
node embedding, and applies hierarchical density clustering. Its output can
include labels at multiple resolutions, a cluster tree, noise assignments, and
near-duplicate candidates. The upstream project describes it as early beta and
notes that its implemented algorithm has no published paper.

## Purpose

Cluster immutable, provenance-carrying attempt records to surface recurring
failure families, duplicate work, or outliers for human review. Preserve the
record ID, source and revision, embedding model and version, input snapshot,
parameters, verdict, and proof with every candidate group.

## Boundary

A cluster reflects the embedding representation, graph construction, density
parameters, and stochastic optimization. It is not an ontology fact, semantic
truth, quality judgment, causal explanation, or proof of improvement. Fix the
input snapshot, `random_state`, and parameters for reproducibility; evaluate any
downstream use on held-out evidence. Cluster labels must not automatically alter
prompts, policies, acceptance, or closure.
