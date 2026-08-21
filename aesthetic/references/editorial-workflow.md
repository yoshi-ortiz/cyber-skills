# Editorial workflow contract

Use this reference while writing the direction-set JSON consumed by `editorial_workflow.py publish`. The file is an inference record. It is not a mood board or a user-feedback ledger.

## Required shape

```json
{
  "version": 1,
  "coverage": {
    "observed": ["image-id", "text-id"],
    "omitted": [
      {"corpusItem": "item-id", "reason": "unsupported diagram encoding"}
    ]
  },
  "directions": [
    {
      "id": "hard-crop",
      "name": "Hard crop",
      "thesis": "A subject-specific claim about the experience and its hierarchy.",
      "signatureMove": "One visible compositional behavior that makes this direction identifiable.",
      "evidence": [
        {
          "corpusItem": "image-id",
          "locator": "upper-right crop",
          "observation": "The crop withholds context and makes scale feel unstable."
        },
        {
          "corpusItem": "text-id",
          "locator": "Field notes, paragraph 2",
          "observation": "The brief asks readers to see revision as part of the finished work."
        }
      ],
      "visualSystem": {
        "palette": "Named colors and their jobs",
        "typography": "Families, contrast, and hierarchy",
        "grid": "Columns, rhythm, and intentional breaks",
        "hierarchy": "What dominates, supports, and recedes",
        "imagery": "Crop, treatment, density, and subject rules",
        "voice": "Sentence character and editorial stance",
        "motion": "What moves, why it moves, and when it stays still"
      },
      "scorecard": {
        "corpusFit": 5,
        "subjectSpecificity": 5,
        "systemCoherence": 4,
        "distinctiveness": 5,
        "executionLeverage": 4
      },
      "agentRank": {
        "place": 1,
        "rationale": "The deciding comparison with the other two directions."
      }
    }
  ],
  "selected": "hard-crop",
  "sprint": {
    "name": "Issue 01",
    "goal": "A concrete outcome for the selected direction.",
    "items": [
      {
        "id": "hero-compose",
        "direction": "hard-crop",
        "title": "Compose the opening spread",
        "deliverable": "A responsive opening spread with the hard crop in place.",
        "points": 5,
        "acceptance": [
          {
            "check": "Desktop and narrow screenshots keep the headline readable.",
            "evidenceKind": "screenshot"
          }
        ],
        "executionElement": "composition.hero"
      }
    ]
  }
}
```

Repeat the direction object exactly three times. Use unique `id` values and unique `agentRank.place` values from 1 through 3.

## Evidence rules

Copy corpus item ids from `corpus.json`. Never invent an id. A locator tells the next agent where to look. An observation says what the material does and why that behavior matters.

Account for every supported item once in `coverage`. Put an item in `observed` after you open it. Use `omitted` only when you cannot inspect it, and state the reason. Do not cite an omitted item as evidence.

When the corpus contains both image and text items, the selected direction must cite both. The other directions still need grounded evidence. A filename, hash, MIME type, or generic phrase such as "strong visual language" is not an observation.

## Direction rules

Three palette swaps are one direction. Vary the governing structure. Useful differences change reading order, density, image behavior, spatial tension, editorial voice, or interaction logic.

The thesis states the direction's argument. The signature move states the repeated visible act that carries that argument. The visual system states how the rest of the page supports it.

The scorecard measures agent judgment about art direction. Existing `decisions.json` stars measure user judgment about executed elements. Do not add `stars`, `rating`, or `userStars` anywhere in the direction set.

## Sprint rules

Put only selected-direction work in `sprint.items`. The board parks the other two directions automatically.

Use points as relative remaining effort. Each item needs a deliverable the agent can build and an acceptance check the agent can prove. Keep the sprint at 20 items or fewer.

Use these evidence kinds when they fit.

- `screenshot` for composition, responsive layout, hierarchy, and visual state.
- `measurement` for size, contrast, line length, load, or timing.
- `copy` for exact language, sequence, or editorial claims.
- `interaction` for focus, keyboard, pointer, state, and recovery behavior.

## State and burndown

`editorial-events.jsonl` is append-only. Each event moves one work item to Backlog, Doing, Review, or Done. The renderer derives both the board columns and remaining points from the same events.

Use a stable event id for every move. Retrying an existing event id is a no-op. Moving an item out of Done restores its points to the burndown.
