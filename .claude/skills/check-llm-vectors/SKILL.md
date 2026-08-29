---
name: check-llm-vectors
description: Derive which installed skills are actually a local skill's peers, by embedding every SKILL.md and clustering the vectors with EVoC. Use before benchmarking, to choose a comparison set rather than assert one.
disable-model-invocation: true
---

# Check LLM vectors

Repo-Dev only. Nothing here ships on either channel; `.claude/` is fog on both.

`tools/token_bench.py` measures a flow against a reference flow, and the
reference is hand-authored -- someone decided `ask-matt` is the peer. This
derives the comparison set instead. Embed every installed `SKILL.md`, cluster
the vectors, and read off which skills a benchmark should actually run against.

## Run it

```bash
python3 -m venv /tmp/vecs
/tmp/vecs/bin/pip install evoc model2vec matplotlib
/tmp/vecs/bin/python .claude/skills/check-llm-vectors/vectors.py
```

`matplotlib` is not optional and not declared: `evoc.label_propagation` imports
it at module scope, so `import evoc` fails without it. Report that upstream
rather than working around it here.

The dependencies stay in a throwaway venv outside the repository. Nothing under
`aesthetic/scripts/` or `tools/` may import any of them; those directories are
standard library only, and this is the carve-out R-50 already makes for
development-only tooling.

`--root` points at another skills directory, `--model` at another
[model2vec](https://github.com/MinishLab/model2vec) static model, `-k` sets how
many neighbours to print.

## What the numbers mean

| Output | Reads as |
| --- | --- |
| Cosine similarity | How close two skills' doctrine sits. Above ~0.80 is a real peer; below ~0.65 means the corpus holds no peer. |
| `[c<n>]` | The skill clustered, and the members of `c<n>` are its neighbourhood. |
| `[noise]` | EVoC placed it nowhere. Either genuinely novel, or incoherent enough that no density survives. |
| `*` | Another local skill, from this repository. |

**Noise is not a verdict.** A skill sitting alone means the 206 installed skills
contain nothing like it. Whether that is novelty or a diluted `SKILL.md` is a
judgement this tool cannot make, for the same reason it cannot propose context
utility: clustering observes position, never quality.

## Why the seed is not tuning

EVoC is stochastic. Without `random_state` two runs on identical input return
different labels, and a comparison set that changes per run cannot be compared
against anything. `SEED` is declared in the script and is part of the result.

## What it will not do

It writes nothing. It does not choose a flow, edit `token_bench.py`, or rank a
skill. Reading it may change which `--flow` you author next; nothing here
authors one.
