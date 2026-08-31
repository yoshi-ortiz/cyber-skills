---
name: aesthetic
description: Design and art direction that reads as intentional, not templated. Use to start, continue, or critique visual work. Grounds direction in design fundamentals, and folds in a multimodal corpus and user sentiment when they exist, producing ranked decisions and an editorial burndown.
---

# Aesthetic ranking

`continue`, `critique`, `prototype`, and `observe` are context clues. A
requested diagram, scene, or illustration routes to
[text-to-graphics.md](references/text-to-graphics.md).

## Route before designing

Read [user-communication.md](references/user-communication.md) before any
user-visible update. Inspect `spec/design-harness/` before opening or
initializing the generic ranking workflow. If `scene-spec.json` or
`graphics-manifest.json` exists, run:

```bash
python3 <skill>/scripts/text_to_graphics.py --project-root . status
```

Do exactly the returned action. This filesystem route outranks a supplied
reference folder and generic art-direction inference. Do not run `init`,
`seed`, or `direction`; do not replace a passing graphic with alternate page
concepts. Reuse the passing artifact from `shots/` first.

Choose chat language from the user's latest words. When they use Spanish,
mirror the dialect and register in project-authored publishing copy. Never use
reference captions, machine locale, a previous agent reply, or
`project.json.language` to choose chat language; that field translates only
the companion controls.

Keep the established article: hero, graph, TOC, four sections, progress chart. Never replace it with a kanban or second site.

## Start

Open the companion first.

```bash
python3 <skill>/scripts/bootstrap_harness.py open --project-root . \
  --status "<emoji + user-language description of the first real design task>"
```

`open` restores the last ranking page. Follow `user-communication.md` for the
URL-first reply with no preamble:

```text
🔗 <full URL>
🔑 <value after ?key=>
👀 <user-language review action in the publishing-copy register>
```

Update status when visible activity changes. `project.json.language` translates
the controls; it does not translate your reply.

With a reference folder, read images and text together:

```bash
python3 <skill>/scripts/editorial_workflow.py observe \
  --project-root . --source-root <absolute-reference-folder>
```

Open items; metadata is not visual evidence.

No folder is not a stop. Seed and direct from premises:

```bash
python3 <skill>/scripts/editorial_workflow.py seed --project-root . \
  --profile <domain-profiles.md name> --subject "<what this is>"
```

A premise cites [golden-rules.md](references/golden-rules.md) or a
[profile](references/domain-profiles.md), names counterevidence, and remains
inference. Ask for references without blocking.

`init` is only for a project with no existing `spec/design-harness` contents;
`seed` is only for a project with no saved corpus. Both commands refuse to
overwrite existing evidence.

## Read the user first

Adopt feedback. Record chat constraints in the brief before inference; user
words outrank references and doctrine.

```bash
python3 <skill>/scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl
python3 <skill>/scripts/brief_workflow.py answer --project-root . \
  --event-id <stable-id> --at <ISO-8601> --id <brief-field> --answer "<user words>"
python3 <skill>/scripts/direction_context.py --project-root . \
  --out /tmp/aesthetic-context.json
```

Read that context before doctrine. It is the project evidence bundle: current
constraints, reference tags, and element feedback. With ranked elements, read
[sentiment-analysis.md](references/sentiment-analysis.md). Never collapse stars,
thumbs, lifecycle, or missing feedback into one score.

## Infer and rank art direction

Read [golden-rules.md](references/golden-rules.md), then only the indexed body
needed by the claim. Read [loop.md](references/loop.md) for a thin/failed round,
[interpret-art.md](references/interpret-art.md) for ambiguous evidence, and
[anti-slop.md](references/anti-slop.md) at critique. Root `GOAL.md`, `SPEC.md`,
`ROADMAP.md`, and `BUGS.md` are never design evidence.

Declare hierarchy, composition, grid, type roles, color relationships, image register, motion purpose, and one subject-specific signature. State the aesthetic question tested. Replace "clean," "premium," or "editorial" with observable relationships and counterevidence.

Select one evidence-backed hypothesis and a 3–6 element cohort. Never average direction, execution, lifecycle, or missing feedback. Reject a thesis that fits an unrelated product unchanged.

In comparison rows, use `null` for `corpusFit` when there is no real corpus and
for `preferenceFit` when the user has not ranked anything. Missing evidence is
not a neutral score and never becomes a model-authored 3, 4, or 5.

Copy every `briefConstraints` item from `/tmp/aesthetic-context.json` into the
direction spec and add its concrete `impact`. The gate rejects missing or stale
answers.

```bash
python3 <skill>/scripts/editorial_workflow.py direction --project-root . \
  --spec /tmp/aesthetic-art-direction.json
```

Fix a rejected spec; never bypass the gate.

## Scope the editorial burndown

Read [editorial-workflow.md](references/editorial-workflow.md). Save epics in `editorial.json`, append changes to `editorial-events.jsonl`. Every element has one primary epic. Retrying an event id is a no-op.

## Build one testable cohort

Draw real HTML/CSS, render it, inspect the PNG at desktop and narrow widths. Judge hierarchy, grouping, measure, and color in the render, never from isolated values — [fundamentals](references/graphic-design-fundamentals.md). Preserve ranked elements outside the cohort. New proposals use new ids, unscored until the user ranks them.

```bash
python3 <skill>/scripts/golden_rules.py --design spec/design-harness/candidate.json --min-coverage 0.8
```

Never invent SVG paths. Follow [asset-sourcing.md](references/asset-sourcing.md). Reuse a project asset, fetch a pinned licensed one, [generate deterministically](references/text-to-graphics.md), or omit.

Before publishing, require 4.5:1 text contrast and 3:1 control contrast.

Companion chrome and theme controls follow [companion-contract.md](references/companion-contract.md).

## Publish the established article

```bash
python3 <skill>/scripts/bootstrap_harness.py article --project-root . \
  --out design/aesthetic-ranking.html --cohort "<element ids>" \
  --round-label "<object>" --asks "<one plain design question>" \
  --agent "<App | Model>" --agent-url "<task deep link>"
python3 <skill>/scripts/bootstrap_harness.py publish --project-root . \
  --screen design/aesthetic-ranking.html
python3 <skill>/scripts/review_delivery.py --project-root . \
  --cohort "<element ids>" --assessments /tmp/proposal-assessments.json
python3 <skill>/scripts/bootstrap_harness.py status --project-root . --idle \
  --text "<user-language request to review the new designs>"
```

Keep the graph, sticky TOC, slideshow, and Discarded-last order. Delivery accepts
only subject-specific rankable proposals with a legible signature. Lead with
the URL, key, review request, and every absolute `image_path` emitted by the
delivery check.

## Continue and critique

On continuation, use latest state for the next action, append-only history for audit. Order: like + low stars, dislike + high stars, unresolved critical work, unscored designs, then new exploration. Change one coherent 3–6 element cohort.

On critique, inspect corpus, direction spec, preference brief, screenshots, and a11y report. Name the strongest mismatch first. Do not change ranks, sentiment, lifecycle, or scope while reporting.

## Done gate

A run is complete only when:

1. the cohort declares its hierarchy, grid, type roles, color relationships, and one subject-specific signature, and the render carries them;
2. the design would still read as this subject with the logo removed, and does not fit an unrelated product unchanged;
3. every inference claim cites visible corpus or feedback evidence and names counterevidence;
4. rank, sentiment, lifecycle, and missingness remain independent;
5. no text or interactive state fails deterministic contrast checks;
6. every nontrivial graphic has source/license/version provenance or a reproducible procedure;
7. the original article structure, scoring controls, burndown, slideshow, and responsive layout work;
8. the user receives the current URL, key, user-language request, and emitted review images.

Passing checks while looking templated is failure.
