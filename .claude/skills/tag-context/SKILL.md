---
name: tag-context
description: Review what one inference pass actually spends. Serves the compiler trace, counts it with a real tokenizer through Transformers.js, and records reviewed judgements about each chunk. Use when tuning pass budgets, doctrine order, or which context a skill should load.
disable-model-invocation: true
---

# Tag context

Repo-Dev only. Nothing here ships on either channel.

## Run it

```bash
python3 tools/trace_preview.py --project-root . --pass proposal --serve
```

Open the URL it prints. Press **Count** to tokenize with a real target
tokenizer, fetched by your browser and never by a gate. Passes are `intent`,
`constraint`, `retrieval`, `proposal`, `generation`, `implementation`, and
`verification`. `generation` is gated, so it needs `--proof golden-rules` or an
explicit `--force`.

Ctrl-C when done, then:

```bash
python3 tools/trace_preview.py --project-root . --pass proposal --review
```

## What you are judging

Three controls per chunk, and none of them implies another:

| Signal | Asks |
| --- | --- |
| utility | Did this content earn its tokens in an accepted result? |
| group | Which semantic context does it actually belong to? |
| contamination | Would it frame this work as the wrong kind of work? |

A chunk can be expensive and essential, or cheap and a derail. One score for
all three would make those indistinguishable, which is why the companion
contract splits stars, thumbs, and the tick the same way.

Each change appends one line to `context-tags-inbox.jsonl` with the exact token
cost the browser measured. Two clicks on one signal are two rows. Refresh
restores what you clicked.

## What it will not do

`--review` reports what your tags imply and edits nothing. A reviewed judgement
becomes a declaration when you write it into `PASS_BUDGETS`, `DOCTRINE_ORDER`,
or `BRIEF_PRIORITY` in `aesthetic/scripts/direction_context.py`, never when a
tool infers it.

Without `--serve`, `--out <file>` writes a read-only copy. The trace and exact
counting still work; the controls disable and say so.
