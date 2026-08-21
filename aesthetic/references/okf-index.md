# OKF index spec

**OKF** (Open Knowledge Format) is how a text corpus exposes knowledge without reading every file. The catalog is always `{corpus}/INDEX.md`. Numbered source files are evidence, not the index.

## INDEX.md must carry

| Section | Holds |
| --- | --- |
| Claim-id table | Stable ids → file#anchor (or file path) for every citable fact |
| Suggested clusters | Optional cluster id → list of claim ids |
| Artefact statement | What this corpus produces (kit, talk, carousel, print piece) |

If INDEX.md is missing, treat the folder as a **visual** corpus — load [interpret-art.md](interpret-art.md), not this file.

## Reading order (mandatory)

1. Open INDEX.md only. Copy claim-id and cluster tables into working memory.
2. Name 3–5 clusters from suggested clusters or shared claim-id prefixes. **No numbered files yet.**
3. Open only the files INDEX points at for claim ids in chosen clusters.
4. Open `sources.md` only when a hook needs a named source. Do not quote it.
5. List every numbered file you did **not** open in `files_not_opened`.

Done when: every cited claim id exists in INDEX.md, and `files_not_opened` is complete.

## IA hierarchy (program → series → post)

Knowledge-index runs stop at IA. Record under `ia.*` and `social.*` only:

```
program → series → post → slide (myth3 only)
```

Every post needs: format, ≥1 claim id from INDEX.md, hook line, vault note (what must not be posted).

## Anti-patterns

- Opening every `01-*.md` … `n-*.md` before naming clusters.
- Hashing files and calling that an index.
- Inventing claim ids or statistics INDEX does not list.
- Drawing palette, type, or layout in this branch.

Full outline and completion checks: [interpret-knowledge.md](interpret-knowledge.md).
