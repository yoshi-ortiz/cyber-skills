# interpret-knowledge.md

Branch file. Load only when **observe** targets a text corpus or the user said knowledge-index. Visual corpus → stop; use [interpret-art.md](interpret-art.md).

Read [okf-index.md](okf-index.md) first — OKF catalog rules and reading order.

Do not open `bootstrap_harness.py`. Do not hash the folder. Do not invent a palette. Do not draw.

## Completion (checkable)

Stop when all are true:

1. `ia.program` has one thesis sentence.
2. 3-5 named series exist under `ia.series.*`.
3. Each series has 4-8 posts under `ia.post.*`.
4. Every post has: format, ≥1 **claim id** from INDEX.md, hook line, vault note.
5. Output lists **claim_ids_used** and **files_not_opened**.
6. No `palette.*` / `type.*` / `illustration.*` elements were created.

If any post lacks a claim id, delete that post.

## Steps

### 1. Confirm branch

Done when: one sentence names the corpus path.

### 2. Read INDEX.md only

Open `{corpus}/INDEX.md`. Do not open numbered source files yet. Copy claim-id and cluster tables.

Done when: you can list cluster ids without opening a numbered file.

### 3. Cluster from the catalog

Use INDEX suggested clusters or group claim ids by shared prefix. Name 3-5 clusters as series candidates.

Done when: `cluster-id → [claim ids]` exists. Still no numbered files opened.

### 4. Open files for named clusters only

Open only files INDEX points at for chosen claim ids. Open `sources.md` only when a hook requires a named source — do not quote it.

Done when: every chosen claim id was read at its anchor; uncited numbered files stay closed.

### 5. Propose IA

Fill the outline in [okf-index.md](okf-index.md). Record `ia.program`, `ia.series.*`, `ia.post.*`, `social.format`, `social.hashtags`, `social.not_to_post`.

Use ledger verbs only.

Done when: outline filled, every claim id verified against INDEX.md, `files_not_opened` complete.

### 6. Rank and stop

Rank series by teaching leverage. Show the outline. Stop — no visual design in this branch.

## Anti-patterns

- Opened every markdown file before naming clusters.
- Hashed files and called that an index.
- Cited a claim id not in INDEX.md or a statistic not in the corpus.
- Drew layout, palette, or type "so the carousel looks finished."

## Do not load

loop.md, interpret-art.md, article CSS JSON, `bootstrap_harness.py`.
