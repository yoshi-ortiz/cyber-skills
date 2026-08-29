---
name: build-context-token-vectors
description: Derive which installed skills are actually a skill's peers, by embedding every SKILL.md and clustering the vectors with EVoC. Use before benchmarking a skill flow, so the comparison set is read off the corpus rather than assumed, and to see which skills have no peer at all.
disable-model-invocation: true
---

# Build context token vectors

A benchmark is only as good as what it compares against, and
`tools/token_bench.py` takes its comparison set by hand. This derives one.

## Run it

```bash
python3 -m venv /tmp/vectors
/tmp/vectors/bin/pip install evoc model2vec matplotlib
/tmp/vectors/bin/python build-context-token-vectors/scripts/vectors.py --serve
```

`--serve` writes the dashboard and opens it. `--out <file>` writes it without
opening. Neither flag prints the tables to the terminal instead.

`matplotlib` is required and **not declared** by `evoc`: `evoc.label_propagation`
imports it at module scope, so `import evoc` fails on a clean install without
it. Report that upstream rather than patching around it here.

`--root` points at another skills directory, default `~/.agents/skills`.
`--model` names another [model2vec](https://github.com/MinishLab/model2vec)
static model, default `minishlab/potion-base-8M`. `-k` sets how many neighbours
each skill reports.

## Read it

| Output | Means |
| --- | --- |
| Cosine similarity | How close two skills' doctrine sits. Roughly: above 0.80 a real peer, 0.65 to 0.80 a loose one, below 0.65 no peer at all. |
| A cluster tag | The skill was placed, and the other members of that cluster are its neighbourhood. |
| `noise` | It was placed nowhere. |
| The scatter plot | Two principal components, for orientation only. Clustering ran in full dimensionality, so two points that look adjacent may not be. The neighbour table carries the real numbers. |

**`noise` is not a verdict.** It says the corpus holds no peer. Whether that is
novelty or a diluted `SKILL.md` is a judgement this cannot make, for the same
reason it cannot rank: clustering observes position, never quality.

## The seed is not tuning

EVoC is stochastic. Without `random_state` two runs over identical input return
different labels, and a comparison set that changes per run is not one. `SEED`
is declared in the script and is part of any result worth quoting.

## What it will not do

It writes a page and nothing else. It does not author a `--flow`, edit
`token_bench.py`, rank a skill, or record a judgement. Reading it may change
which comparison you run next; nothing here runs one.

Its three dependencies live in a virtual environment you create. Nothing under
`aesthetic/scripts/` or `tools/` imports them, and this skill ships none of
them, which is why it stays on the `alpha` channel.
