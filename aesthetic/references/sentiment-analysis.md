---
type: Contract
title: Element-level sentiment analysis
description: Infer creative preferences without collapsing independent feedback signals.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

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

## Canonical art-direction spec

The `direction` command accepts this exact shape. Account for every corpus item in either `observations` or `omissions`; name only element ids emitted by `preferences`; keep comparison dimensions separate; use corpus, project, fetched, procedural, or omitted asset provenance.

```json
{
  "version": 1,
  "observations": [
    {
      "corpusItem": "reference.poster-01",
      "locator": "upper crop",
      "observation": "The headline crosses the subject boundary while the utility text stays on a fixed rail."
    }
  ],
  "omissions": [
    {
      "corpusItem": "reference.unreadable-scan",
      "reason": "The scan is too degraded to support a visual claim."
    }
  ],
  "preferencePatterns": [
    {
      "claim": "The user favors display type crossing image boundaries when utility text remains isolated.",
      "support": ["composition.hero.crop", "type.display.overprint"],
      "counterevidence": ["nav.utility.stack"],
      "n": 3,
      "coverage": 0.67,
      "confidence": "medium"
    }
  ],
  "hypotheses": [
    {
      "id": "hard-crop",
      "thesis": "Revision stays visibly unfinished.",
      "signatureMove": "Hard crops cross a fixed annotation rail.",
      "visualSystem": {
        "palette": "Warm paper field, near-black text, and one cobalt annotation color.",
        "typography": "Fetched pixel display face for labels; readable grotesk for body copy.",
        "grid": "Twelve columns with a persistent two-column evidence rail.",
        "hierarchy": "One dominant crop, one headline, then compact evidence labels.",
        "imagery": "Source images retain hard crop edges and visible provenance captions.",
        "voice": "Short observational statements; no promotional adjectives.",
        "motion": "Discrete index steps with reduced-motion parity."
      }
    },
    {
      "id": "open-index",
      "thesis": "Evidence accumulates in a navigable index.",
      "signatureMove": "Captions form the primary reading rail.",
      "visualSystem": {
        "palette": "Neutral paper field, charcoal text, and one vermilion locator color.",
        "typography": "Humanist sans for reading with monospaced source locators.",
        "grid": "Four unequal columns that expand around the active evidence group.",
        "hierarchy": "Source locator first, artifact second, interpretation third.",
        "imagery": "Uncropped source images alternate with magnified evidence details.",
        "voice": "Catalog language that distinguishes observation from inference.",
        "motion": "Rail expansion uses opacity and position only, with no-motion fallback."
      }
    }
  ],
  "comparison": [
    {
      "hypothesis": "hard-crop",
      "corpusFit": 5,
      "preferenceFit": 4,
      "subjectSpecificity": 5,
      "coherence": 4,
      "executionLeverage": 4,
      "tradeoff": "Stronger identity, but the evidence rail must protect reading order."
    },
    {
      "hypothesis": "open-index",
      "corpusFit": 4,
      "preferenceFit": 3,
      "subjectSpecificity": 4,
      "coherence": 5,
      "executionLeverage": 3,
      "tradeoff": "Clearer evidence browsing, but less visual tension in the hero."
    }
  ],
  "selected": "hard-crop",
  "selectionRationale": "It explains the strongest liked relationships while isolating the utility-stack counterexample.",
  "cohort": ["composition.hero.crop", "type.display.overprint", "nav.utility.stack"],
  "assets": [
    {
      "id": "poster-source",
      "provenance": "corpus",
      "corpusItem": "reference.poster-01"
    }
  ]
}
```
