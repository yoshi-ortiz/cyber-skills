---
purpose: derive which installed skills are a skill's real peers, by embedding and clustering every SKILL.md
admits: SKILL.md, the clustering script, its dashboard template, and any reference this skill alone needs
refuses: aesthetic doctrine, rail documents, anything from another skill in this package
max_file_bytes: 8000
---

# Build context token vectors

A benchmark needs a comparison set, and `tools/token_bench.py` takes one by
hand: someone decided `ask-matt` is the reference. This derives it. Embed every
installed `SKILL.md`, cluster the vectors, and the neighbours are the skills a
benchmark should actually run against.

It observes **position and overlap**, never quality. A skill that clusters with
nothing is a skill the corpus holds no peer for, which is novelty or dilution
and this cannot tell you which.

It needs `evoc`, `model2vec`, and `matplotlib` in a virtual environment the user
creates. The skill documents those, ships none of them, and nothing under
`first/aesthetic/scripts/` or `tools/` imports any of them.

`--serve` is a loopback-only live companion. It prepares the corpus once, then
reruns only advisory EVoC analysis when a maintainer changes a parameter. It
does not persist tuning state or feed a cluster back into declarations, gates,
or live inference.
