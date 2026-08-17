# interpret-knowledge.md

Branch file. Load only when `observe`'s target is a **text corpus** (`*.md`, `*.txt`) or the user said `knowledge-index`. If the target is an art folder (images), do not load this file; use the visual interpret path.

Do not open `bootstrap_harness.py`. Do not hash the folder. Do not invent a palette. Do not draw.

## Completion (checkable)

Stop when all are true:

1. `ia.program` has one thesis sentence.
2. 3-5 named series exist under `ia.series.*`.
3. Each series has 4-8 posts under `ia.post.*`.
4. Every post has: format (`carousel slide` | `single square` | `3-slide myth-bust`), ≥1 claim id from INDEX.md, a hook line, a vault note.
5. Output lists **claim ids used** and **files not opened**.
6. No `palette.*` / `type.*` / `illustration.*` elements were created in this branch.

If any post lacks a claim id, delete that post. Do not keep it.

## Steps

### 1. Confirm branch

- Text corpus or user said knowledge-index → continue.
- Images / art folder → stop this file; visual interpret instead.
- Empty `inspiration/` is not a reason to stop.

Done when: one sentence names the corpus path.

### 2. Read INDEX.md only

Open `{corpus}/INDEX.md`. Do not open `01-*.md` ... `n-*.md` yet. Do not open `sources.md` yet.

Copy the claim-id table and the suggested cluster table into working memory.

Done when: you can list cluster ids without having opened a numbered source file.

### 3. Cluster from the catalog

Use INDEX suggested clusters if present. Otherwise group claim ids by shared prefix or heading. Do not invent a cluster with zero claim ids.

Name 3-5 clusters. These become series candidates.

Done when: a list `cluster-id → [claim ids]` exists. Still no numbered source files opened.

### 4. Open files for named clusters only

For each chosen cluster, open only the files INDEX points at for those claim ids. Never open the whole folder "to be safe."

If a hook needs a named source, open `sources.md`. Do not quote it. There are no quotes.

Done when: every chosen claim id has been read at its file#anchor, and every numbered file not cited remains closed.

### 5. Propose IA (fill this outline)

```
program:
  id:
  thesis:   # one sentence
  artefact: # social infographic program, not a site, not a printed kit
  audience:
series:
  - id:
    name:
    cluster_id:
    posts:
      - id:
        format: carousel slide | single square | 3-slide myth-bust
        claim_ids: []    # from INDEX.md
        hook:
        vault:           # what must NOT be posted
        slides:          # 1, or 3 if myth3
labeling:
  filename_pattern:
  hashtags: []         # topic labels only; no engagement advice
not_to_post: []
claim_ids_used: []
files_not_opened: []
```

Hierarchy is program → series → post → slide. Record:

- `ia.program`, `ia.series.<id>`, `ia.post.<id>` (and slide children if myth3)
- `social.format`, `social.hashtags`, `social.not_to_post`

Use ledger verbs only. Do not edit this skill.

Done when: the outline is filled, every `claim_ids` entry exists in INDEX.md, `files_not_opened` lists numbered corpus files you did not read.

### 6. Rank and stop

Rank series by teaching leverage (definitions before failure modes before meta-job, unless INDEX clusters say otherwise). Show the outline. Stop.

Do not continue into visual design. Do not call doctor unless the user asked.

## Anti-patterns (delete the draft if you did these)

- Invented a palette, type ramp, illustration cohort, or motion system.
- Drew or specified layout grids "so the carousel looks finished."
- Hashed any file and called that an index.
- Opened `bootstrap_harness.py`.
- Opened every markdown file before naming a cluster.
- Cited a claim id not in INDEX.md, or a statistic not in the corpus (there are none).
- Restated SKILL.md foundations instead of filling the outline.
- Wrote engagement advice (reach, best time, hashtag counts).

## What this branch does not load

loop.md, interpret-art.md, CONTEXT.md article/type JSON, cohort CSS, `bootstrap_harness.py`.
