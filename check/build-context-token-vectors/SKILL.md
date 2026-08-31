---
name: build-context-token-vectors
description: Derive which installed skills are actually a skill's peers, then tune EVoC live in a browser companion without rebuilding the embeddings. Use before benchmarking a skill flow, so the comparison set is read off the corpus rather than assumed, and to see which skills have no peer at all.
disable-model-invocation: true
---

# Build context token vectors

A benchmark is only as good as what it compares against, and
`tools/token_bench.py` takes its comparison set by hand. This derives one.

## Run it

```bash
python3 -m venv /tmp/vectors
/tmp/vectors/bin/pip install evoc model2vec matplotlib
/tmp/vectors/bin/python check/build-context-token-vectors/scripts/vectors.py --serve
```

`--serve` starts a loopback companion, opens it, and stays alive until Ctrl-C.
Change any EVoC parameter in the page and press **Retune**: the companion fits
EVoC again while reusing the loaded corpus, embeddings, projection, and nearest
peers. `--port` changes its default port, `8932`. `--out <file>` writes a
read-only snapshot instead. With neither flag, the tables print to the terminal.

`matplotlib` is required and **not declared** by `evoc`: `evoc.label_propagation`
imports it at module scope, so `import evoc` fails on a clean install without
it. Report that upstream rather than patching around it here.

`--root` points at another skills directory, default `~/.agents/skills`.
`--model` names another [model2vec](https://github.com/MinishLab/model2vec)
static model, default `minishlab/potion-base-8M`. `-k` sets how many neighbours
each skill reports.

## Tune it

Every EVoC parameter is both a flag and a live control. Only values you set are
passed, so a run that changed nothing says `EVoC defaults` rather than looking
tuned. Empty live controls restore the corresponding default.

| Flag | Turns |
| --- | --- |
| `--base-min-cluster-size` | How many points make a cluster. Lower splits, higher merges. |
| `--n-neighbors` | The kNN graph's width. Lower sees local structure, higher sees global. |
| `--min-samples` | The density estimate. |
| `--noise-level` | How readily a point is called noise. |
| `--n-epochs`, `--neighbor-scale`, `--min-similarity-threshold` | The node embedding, and where layers separate. |

The useful act is comparing two settings, never trusting one:

```
EVoC defaults                            8 clusters, 49 noise
--base-min-cluster-size 3 --n-neighbors 10   9 clusters, 53 noise
--noise-level 0.2                        7 clusters, 39 noise
```

The page prints the settings behind its current result, so a screenshot still
says what produced it.

## Explore it

The dashboard is not a report. Switch **layer** to move between the resolutions
EVoC found, coarsest first. **Rail** organizes known skills as `first`, `build`,
`land`, `check`, then the `kit` and `fix` aids; this is display metadata and
never changes the vectors. Filter to **Local**, **All**, or **Noise**. Search by
skill name, by a peer's name, or by a cluster id such as `c4`. Click any point or
row to inspect one skill: its membership strength, its full neighbour list, and
every other member of its cluster at the current layer.

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

The live companion writes nothing. A deliberate `--out` writes only its page.
Neither mode authors a `--flow`, edits `token_bench.py`, ranks a skill, or
records a judgement. Reading it may change which comparison you run next;
nothing here runs one.

Its three dependencies live in a virtual environment you create. Nothing under
`first/aesthetic/scripts/` or `tools/` imports them, and this skill ships none of
them.
