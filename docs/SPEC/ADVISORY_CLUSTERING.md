# Advisory clustering

Status: promoted contract; implementation is tracked by
[R-53](../../ROADMAP.md#next). Supplies the advisory ranker that
[R-50](INFERENCE_CONTEXT_COMPILER.md) names as remaining.

## Goal

Propose groupings over embedded material, so the user is answering a candidate
rather than authoring from nothing. Every output is a **learned
recommendation**: it may propose a declaration and never becomes one.

The engine is [EVōC](https://evoc.readthedocs.io/en/latest/), which clusters
high-dimensional embedding vectors with a node-embedding step related to UMAP
and density clustering related to HDBSCAN. It returns `labels_` with `-1` for
noise, `membership_strengths_` as confidence, and `cluster_layers_` as a
hierarchy sorted finest to coarsest.

## Two callers, corpus first

| Caller | Embeds | Proposes | Context |
| --- | --- | --- | --- |
| Design corpus | Each item in `corpus.json`, as a CLIP-class image vector | Candidate groups, against the folders the user already authored | Design-Inference |
| Context bundle | Each compiled chunk, as a sentence-vector | **Semantic group**, and **contamination risk** where a chunk lands in the wrong context's cluster or returns `-1` | Repo-Dev |

The corpus caller lands first. It has real material, and the payoff is legible:
`corpus_tags.py` reads grouping off folder names because *"intent is not readable
off a filename"* and the user curated the folders by hand. A cluster that splits
one of those folders or merges two is exactly the signal worth showing them.

**What neither caller can propose is context utility.** That needs accepted-result
outcomes, which only the attempt record holds. The three signals stay
independent, and clustering fills two of the three.

## Determinism is not optional here

EVōC is stochastic by default: without `random_state` a rerun on identical input
returns different labels. This repository's compiler contract requires
reproducible compilation and a trace that replays byte for byte, so a declared
`random_state` is part of this contract rather than a tuning parameter. A
proposal produced without one is not a proposal, because nothing can be compared
against it later.

## Authority boundary

The user's folder is the declaration. A cluster that disagrees with it is a
recommendation to accept or ignore, and ignoring it must leave no residue.

Proposals key by **sha256**, following the rule `corpus_tags.py` already
established: hashes follow the bytes, so reshuffling or renaming folders never
orphans the work.

Nothing here may write a tag, a declaration, a pass budget, a proof gate, or a
publication decision. `direction_context.py` never imports it, and no gate
depends on it.

## Dependency boundary

EVōC requires `numpy`, `scipy`, `scikit-learn`, and `numba`, and it does not
produce embeddings -- a separate model does that, and is the larger dependency.

The standard-library-only rule in `CLAUDE.md` governs shipped skill code under
`aesthetic/scripts/` and `tools/`. This is dev-only and lives outside both, the
same carve-out R-50 already makes for a development-only learner.

The precedent set by `tools/trace_preview.py` -- push the heavy dependency into
a browser, load it from a CDN, vendor nothing, keep it out of the compiler --
**does not transfer**. Numba compiles Python, so there is no browser to push
this into, and the boundary has to be drawn somewhere else.

## Acceptance

R-53 is complete only when:

- a declared `random_state` makes two runs on identical input return identical
  labels, proven by a test;
- proposals key by sha256 and survive a folder rename;
- the corpus caller shows where clusters disagree with the authored folders,
  and shows nothing else;
- no proposal can write a tag or a declaration, and declining one leaves no
  residue;
- no module under `aesthetic/scripts/` or `tools/` imports the engine, and no
  gate depends on it;
- both publication channels prove the engine, its embeddings, its caches, and
  its proposals are fog.

## Non-goals

- Authoring corpus tags, or replacing the folders the user curated.
- Proposing context utility, which clustering cannot observe.
- Any clustering result reaching a published tree, a gate, or a live inference.
- Shipping an embedding model, a checkpoint, or a cache inside a skill.
