# Deterministic inference context compiler

Status: promoted contract; implementation is tracked by
[R-50](../../ROADMAP.md#rail).

## Goal

Spend inference context on the evidence most likely to produce an accepted
result. The governing measure is **inference tokens per accepted result**, not
minimum tokens in isolation.

The product is a deterministic context compiler. A development-only neural
learner may recommend changes to its declarations and budgets, but no learned
value controls a live inference or a published tree.

## Unit of compilation

The compiler operates over this hierarchy:

```text
release package
  -> skill or family
    -> invocation path
      -> context bundle
        -> file
          -> semantic chunk
```

Each item keeps four independent dimensions. They must not be collapsed into
one `weight`:

| Dimension | Meaning |
| --- | --- |
| Semantic context | The work the content can inform, such as Repo-Dev or Design-Inference |
| Loading tier | Always, invocation, conditional, or excluded |
| Publication channel | `main`, `alpha`, or dev-only |
| Workflow role | Instruction, reference, executable, fixture, test, generated output, or evidence |

Files are the first admission boundary. Markdown headings and source-code
declarations may form smaller chunks after their file is admitted.

## Inputs

Every skill declares its invocation paths, eligible contexts, required
evidence, loading tiers, workflow roles, publication channels, pass budgets,
and cheapest representative proof. Existing `SKILL.md` links, commands,
directory contracts, publication rules, and tests may bootstrap suggested
declarations, but inferred declarations are not authoritative until reviewed.

A tokenizer profile names the target model family and records whether its
count is exact or estimated. An available target tokenizer supplies exact token
ids, offsets, and cost. A byte-based fallback must identify itself as an
estimate; one tokenizer must never stand in for every LLM.

## Deterministic program

For the same repository revision, task, declarations, tokenizer profile, and
budget, compilation must produce byte-for-byte equivalent output.

1. Parse the latest user request into explicit corrections, constraints, and
   acceptance criteria without weakening their wording.
2. Resolve the skill, invocation path, and eligible semantic contexts.
3. Exclude incompatible contexts and anything forbidden by loading or
   publication rules.
4. Tokenize eligible chunks with the selected tokenizer profile.
5. Order admission lexicographically:
   1. latest user corrections;
   2. task acceptance criteria;
   3. required primary evidence;
   4. workflow instructions;
   5. optional doctrine and examples.
6. Pack each inference pass without crossing its declared budget. Optional
   material is removed before any higher tier is truncated.
7. Emit a context bundle and an inspectable compiler trace naming why every
   candidate was selected, omitted, or truncated.
8. Stop before an expensive pass until its cheapest representative proof has
   passed, unless the user explicitly requested the expensive pass directly.

No learned score may override exclusion, priority, budget, proof, or
publication rules.

## Inference passes

Every invocation maps its work onto the smallest applicable subset of:

1. intent extraction;
2. constraint retention;
3. context retrieval;
4. proposal;
5. expensive generation;
6. implementation;
7. verification.

The compiler trace reports budget, exact or estimated use, admitted context,
omissions, proof state, and outcome for each pass. This pass trace is the
maintainer-facing meaning of a learning preview. Raw neural tensors are
optional diagnostics and are never presented as causal explanations.

## Outcome record

An inference attempt records the task, repository revision, tokenizer profile,
compiled bundle, pass trace, artifacts, user corrections, and final outcome.
Explicit rejection, restart, discarded output, and major scope correction are
strong negative outcomes. Partial retention is mixed; accepted or shipped work
is positive. Records remain local and dev-only.

The primary metric is median inference tokens per accepted result. Supporting
metrics are first-pass acceptance, discarded-output rate, correction retention,
required-context recall, contamination inclusion, and confidence calibration.

## Development-only learner

The optional learner uses reviewed attempts to compare context and prompt
plans for the same task. Pairwise learning-to-rank is the primary objective. A
shared encoder may additionally predict semantic group, contamination risk,
and context utility; these remain separate outputs rather than one token
weight.

The compatible reference stack is Python, PyTorch, Hugging Face Tokenizers,
and Sentence Transformers. Training data, dependencies, checkpoints, caches,
reports, and model execution stay in development tooling. Recommendations are
reviewed before they become deterministic declarations, budgets, or regression
fixtures.

## Publication boundary

Published skills may contain compact declarations, standard-library selectors,
and tests required by their runtime contract. Publication gates must reject
neural dependencies, datasets, checkpoints, caches, attempt histories, and
learning previews from both `main` and `alpha`.

## Acceptance

R-50 is complete only when:

- every indexed skill has reviewed invocation-path and context declarations;
- compilation is reproducible and every selection or omission is explained;
- supported tokenizer profiles distinguish exact counts from estimates;
- latest user corrections cannot be displaced by lower-priority context;
- expensive passes enforce their declared proof gate;
- held-out attempts improve tokens per accepted result without reducing
  required-context recall;
- the rejected landing-hero long shot is retained as a regression fixture;
- both publication channels prove that all learning artifacts remain fog.

## Non-goals

- Training or replacing an LLM tokenizer.
- Assigning one scalar weight to a skill, file, or token.
- Letting a neural model mutate prompts, declarations, or publication state.
- Reducing token count by dropping required evidence or user constraints.
