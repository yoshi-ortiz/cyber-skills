---
name: aesthetic
description: Design and art direction that reads as intentional, not templated. Use to start, continue, or critique visual work. Grounds direction in design fundamentals, and folds in a multimodal corpus and user sentiment when they exist, producing ranked decisions and an editorial burndown.
---

# Aesthetic ranking

`continue`, `critique`, `prototype`, and `observe` are context clues.

Keep the established article: hero, graph, TOC, four sections, progress chart. Never replace it with a kanban or second site.

## Start

Read [user-communication.md](references/user-communication.md) before any user-visible update. Open the companion first.

```bash
python3 <skill>/scripts/bootstrap_harness.py open --project-root . \
  --status "<emoji + project-language description of the first real design task>"
```

First reply, no preamble:

```text
🔗 <full URL>
🔑 <value after ?key=>
👀 <project-language review action>
```

`open` restores the last ranking page.

User-visible language comes from `project.json`.

With a reference folder, read images and text together:

```bash
python3 <skill>/scripts/editorial_workflow.py observe \
  --project-root . --source-root <absolute-reference-folder>
```

Open supported items. Explain omissions. Metadata is not visual evidence.

No folder is not a stop. Seed and direct from premises:

```bash
python3 <skill>/scripts/editorial_workflow.py seed --project-root . \
  --profile <domain-profiles.md name> --subject "<what this is>"
```

A premise cites [golden-rules.md](references/golden-rules.md) or a [profile](references/domain-profiles.md), names counterevidence, and stays labeled inference — never evidence. Ask for references in passing; never block.

## Read the user first

Adopt feedback, then build the element brief.

```bash
python3 <skill>/scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl
python3 <skill>/scripts/editorial_workflow.py preferences --project-root . \
  --out /tmp/aesthetic-preferences.json
```

Read [sentiment-analysis.md](references/sentiment-analysis.md). Never collapse stars, thumbs, lifecycle, or missing feedback into one score.

Preferences apply per element. One liked element does not approve its epic, theme, page, or style.

## Infer and rank art direction

Read [golden-rules.md](references/golden-rules.md) first — it carries the formal, philosophical, and historical bodies a direction cites. Then [loop.md](references/loop.md), [interpret-art.md](references/interpret-art.md), and [anti-slop.md](references/anti-slop.md).

Declare hierarchy, composition, grid, type roles, color relationships, image register, motion purpose, and one subject-specific signature. State the aesthetic question tested. Replace "clean," "premium," or "editorial" with observable relationships and counterevidence.

Select one evidence-backed hypothesis and a 3–6 element cohort. Never average direction, execution, lifecycle, or missing feedback. Reject a thesis that fits an unrelated product unchanged.

```bash
python3 <skill>/scripts/editorial_workflow.py direction --project-root . \
  --spec /tmp/aesthetic-art-direction.json
```

Fix a rejected spec. Never bypass the gate.

## Long runs

Before work over a minute, send one project-language update, mirrored in the status aid:

```bash
python3 <skill>/scripts/bootstrap_harness.py status --project-root . \
  --text "<emoji + visible work + why it matters>"
```

Name the visible result and link the page. Update the status when the real activity changes. Never report setup commands.

## Scope the editorial burndown

Read [editorial-workflow.md](references/editorial-workflow.md). Save epics in `editorial.json`, append changes to `editorial-events.jsonl`. Every element has one primary epic. Retrying an event id is a no-op.

## Build one testable cohort

Draw real HTML/CSS, render it, inspect the PNG at desktop and narrow widths. Judge hierarchy, grouping, measure, and color in the render, never from isolated values — [fundamentals](references/graphic-design-fundamentals.md). Preserve ranked elements outside the cohort. New proposals use new ids, unscored until the user ranks them.

```bash
python3 <skill>/scripts/golden_rules.py --design spec/design-harness/candidate.json --min-coverage 0.8
```

Never invent SVG paths. Follow [asset-sourcing.md](references/asset-sourcing.md). Reuse a project asset, fetch a pinned licensed one, generate deterministically, or omit.

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
  --text "<project-language request to review the new designs>"
```

Keep the graph clickable, TOC sticky, slideshow functional, and Discarded last. `review_delivery.py` takes only rankable, subject-specific proposals with a legible signature; evidence cards, explanations, generic defaults, missing files, and hash drift fail. Lead the final chat with the URL, key, and project-language review request. Attach only emitted absolute `image_path` values.

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
8. the user receives the current URL, key, project-language request, and emitted review images.

Criteria 3–8 prove the run is safe and honest. Criteria 1–2 are the design bar: inspect the render and judge it. Passing every check and still looking templated is a failure.
