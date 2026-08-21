# Sentiment analysis contract

Use the deterministic preference brief before proposing or critiquing art direction. This is element-level descriptive analysis, not a latent taste score and not model training.

## Independent fields

| Field | Question answered |
| --- | --- |
| `rank` | How well was this element executed? |
| `sentiment` | Does the user want this direction pursued? |
| `lifecycle` | Where is the element in project work? |
| missing field | What has the user not judged? |

Never impute missing feedback. Never pool agent placeholders with user-set ranks. Never infer whole-theme approval from one element.

## Required brief

For the current standing and proposed cohort, report:

- coverage: user-ranked / standing elements;
- each element's rank, sentiment, lifecycle, provenance, preview, and evidence;
- anchors, polish, conflicts, discards, and unknowns as separate sets;
- every claimed preference pattern with supporting ids, visible features, counterexample ids, `n`, coverage, and confidence;
- the next smallest hypothesis and 3–6 element cohort that can distinguish it.

Confidence is qualitative (`low`, `medium`, `high`) and justified by sample size, coverage, repetition, and counterevidence. It is not computed from an invented weighted formula.

## Action table

| Direction | Execution | Instruction |
| --- | --- | --- |
| like | high | anchor; preserve the identifying relationship |
| like | low | polish the same idea; do not replace it |
| dislike | high | reject the direction while retaining the craft lesson |
| dislike | low | discard and avoid recurrence |
| missing | any/missing | exploration candidate, not evidence of approval |

Rank and sentiment thresholds select actions; they do not become a combined score. Latest state governs the next action. Append-only events establish repetition and reversals for confidence and audit.

## Claim shape

Write a claim as an observable relationship:

> The user favors dense type-image overlap in `composition.hero.crop` and `type.display.overprint` (n=2, 67% cohort coverage), but rejects the same overlap in `nav.utility.stack`; medium confidence because the counterexample is a utility surface.

Do not write “the user likes bold editorial design.” That hides the element, the observed feature, the counterevidence, and the uncertainty.
