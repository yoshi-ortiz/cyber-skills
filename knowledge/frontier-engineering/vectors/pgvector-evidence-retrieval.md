---
type: Reference
title: pgvector evidence retrieval
description: Use pgvector to retrieve candidate prior evidence while relational records retain scope, provenance, and authority.
status: stable
resource: https://github.com/pgvector/pgvector
tags:
  - vectors
  - pgvector
  - retrieval
generated:
  by: codex/gpt-5
  at: 2026-09-06T00:00:00-06:00
sources:
  - resource: https://github.com/pgvector/pgvector
    title: pgvector
    author: pgvector contributors
---

# pgvector evidence retrieval

pgvector adds vector types and nearest-neighbor search to PostgreSQL. It supports
exact search by default and approximate HNSW or IVFFlat indexes when speed is
worth a recall tradeoff. PostgreSQL columns and filters can keep evidence scoped
by source, revision, tenant, model, or review state before distance ranking.

## Purpose

Store derived embeddings beside immutable evidence identifiers, content and
revision hashes, source URI, timestamp, embedding model and dimension, review
verdict, and observed outcome. Retrieve semantically related prior failures or
experiments, then inspect the original records and their proof through a
deterministic gate.

## Boundary and measurement

Similarity only ranks candidates. It does not prove relevance, correctness,
causality, or authorize a change. Exact retrieval is the default reference when
a result supports acceptance or release. Measure any HNSW or IVFFlat recall
against exact search on a frozen evaluation set, record index and query settings,
and keep the relational record as the source of truth. Approximate indexes trade
recall for speed; filtered approximate search can return too few candidates.
