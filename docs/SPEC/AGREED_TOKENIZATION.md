# Agreed tokenization

Status: promoted contract; implementation is tracked by
[R-52](../../ROADMAP.md#next).

## Goal

Let a maintainer see how a target-class transformer chunks the compiled context
bundle, and record that they agreed with what they saw. The product is a
visualization plus a durable verdict, not a score.

This measures neither of the two axes in
[UBIQUITOUS_LANGUAGE.md](../../UBIQUITOUS_LANGUAGE.md). **Token cost** is
already counted by the compiler under a tokenizer profile. **Signal density**
stays uncountable and gets no checker. What gets a checker here is narrower and
fully deterministic: whether a human agreed, and whether the text has changed
since they did.

## Why a proxy tokenizer is legitimate

No frontier target publishes a loadable tokenizer except the open Chinese
architectures. Anthropic, Google, and Apple each expose only a counting API or
an on-device call, and reproducing a vendor tokenizer is already a non-goal of
[the compiler contract](INFERENCE_CONTEXT_COMPILER.md).

That does not block this contract, because the observable is structural rather
than fiscal. Measured on this repository's `proposal` pass: `Xenova/gpt-4`
charges 8,013 tokens and `Xenova/gpt-4o` charges 8,006, a 0.09% spread, and both
fragment the same declared domain terms the same way -- `bur|nd|own`,
`multim|odal`, `templ|ated`, `crit|ique`. The fragmentation is a property of the
words the repository chose, not of the tokenizer reading them. Any modern BPE is
therefore an adequate lens, and the count it reports remains an **estimate** of
what the target charges. The existing binary holds: an exact count names the
target's own tokenizer or it is not exact.

`Xenova/gpt-4o` is the declared lens. It is current-generation, it is the same
tiktoken-family BPE as the open Chinese architectures, and it tokenizes CJK
20-40% more compactly than the `cl100k` default it replaces.

## Program

Three artifacts, and only the middle one is a decision:

| Artifact | Where | Published | What it is |
| --- | --- | --- | --- |
| Click log | `spec/design-harness/context-tags-inbox.jsonl` | fog, untracked | Append-only working state. Every click, never deduplicated. |
| Verdict | tracked, fog | fog, tracked | The agreed judgement, pinned to a content hash. One row per chunk per signal. |
| Gate | `tools/check.py` | fog | Refuses a verdict whose text has moved. |

The click log is history and stays local. `--review` promotes it into a verdict,
which is the act that turns a **learned recommendation** into a declaration.
Nothing infers a verdict; a maintainer writes one.

A verdict row carries the chunk key, the signal, the agreed value, the sha256 of
the exact text reviewed, the tokenizer that rendered it, and the time.

## The gate

For every pass that has a verdict file, each recorded key's current text must
hash to the recorded hash. A pass with no verdict file is not a failure: the
gate is green on a fresh repository and goes red only when an agreement is
contradicted by an edit. Coverage grows as review happens, so the gate never
ships red and never needs a threshold nobody can defend.

## Acceptance

R-52 is complete only when:

- the declared lens is `Xenova/gpt-4o` in every surface that names a tokenizer,
  and no surface names one independently;
- a verdict file is produced only by an explicit review, never by a click;
- every verdict row pins the sha256 of the text it agreed with;
- editing a verified chunk turns the gate red, and re-agreeing turns it green;
- a repository with no verdict files passes;
- the click log, the verdict files, and the preview page are fog on both
  channels.

## Non-goals

- Reproducing any vendor's tokenizer or its billed cost.
- A threshold, a score, or a ratio derived from token counts.
- Checking signal density, which remains uncountable by doctrine.
- Verifying fog that no consuming model ever loads.
