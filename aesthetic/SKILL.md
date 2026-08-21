---
name: aesthetic
description: Use when a multimodal corpus and human feedback must become grounded creative direction, ranked design decisions, and a responsive editorial burndown. It helps the agent understand user sentiment and what the user likes by keeping direction, execution quality, lifecycle, and missing feedback distinct. Use it to continue or critique a design sprint. Not for generic UI coding without references.
---

# Aesthetic ranking

This is a project-local sentiment-analysis and creative-direction system. Its feedback loop helps the agent understand this user over time. `continue`, `critique`, `prototype`, and `observe` are context clues, not separate product workflows.

Keep the established article: hero, ranking graph, TOC, This round, Critical components, On development, and Discarded. The burndown sits after the hero. Never replace it with a kanban or second site.

## Start

Open the companion first and return its keyed URL.

```bash
python3 <skill>/scripts/bootstrap_harness.py open --project-root .
```

If no harness exists, ask once for the reference folder, then initialize it. The corpus is read-only. User-visible language comes from `project.json`.

For a named reference folder, capture its complete inspectable inventory. Images and text are interpreted together; an `INDEX.md` is evidence, not a routing switch.

```bash
python3 <skill>/scripts/editorial_workflow.py observe \
  --project-root . --source-root <absolute-reference-folder>
```

Open each supported item and explain omissions. Paths, hashes, MIME types, and search snippets are provenance, not aesthetic evidence.

## Read the user before directing the work

Adopt companion feedback, then produce the deterministic element-level brief.

```bash
python3 <skill>/scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl
python3 <skill>/scripts/editorial_workflow.py preferences --project-root . \
  --out /tmp/aesthetic-preferences.json
```

Read [sentiment-analysis.md](references/sentiment-analysis.md). Never collapse stars, thumbs, lifecycle, or missing feedback into one score.

- like + high stars: preserve as an anchor;
- like + low stars: keep the idea and polish its execution;
- dislike + high stars: acknowledge the craft and reject the direction;
- dislike + low stars: discard;
- missing rank or sentiment: unknown, never neutral.

Preferences apply to individual elements only. One liked element does not approve its epic, theme, page, or style.

## Infer and rank art direction

Read [loop.md](references/loop.md), [interpret-art.md](references/interpret-art.md), and [anti-slop.md](references/anti-slop.md). Before drawing, write a temporary inference record:

1. observations with corpus item and visual/text locator;
2. user-preference patterns with supporting element ids, counterevidence, sample size, coverage, and confidence;
3. two to four structurally distinct hypotheses when the evidence is ambiguous;
4. a dimension-by-dimension comparison of corpus fit, preference fit, subject specificity, coherence, and execution leverage;
5. one selected hypothesis, its losing tradeoff, signature move, complete visual system, and 3–6 element test cohort.

Do not average those dimensions into one reward or store agent rank as user feedback. With sparse feedback, lower confidence and test less.

Every selected visual rule cites both a corpus observation and relevant preference evidence when each exists. Labels such as “clean,” “bold,” “modern,” “editorial,” or “premium” are invalid unless replaced by observable relationships. If the thesis could fit an unrelated product unchanged, reject it.

```bash
python3 <skill>/scripts/editorial_workflow.py direction --project-root . \
  --spec /tmp/aesthetic-art-direction.json
```

This saves `art-direction.json`. Fix a rejected spec; never bypass the gate.

## Scope the editorial burndown

Save explicit project epics and element membership in `spec/design-harness/editorial.json`; append state changes to `editorial-events.jsonl`. Read [editorial-workflow.md](references/editorial-workflow.md).

Every element has exactly one primary epic. Epics may describe any project concern; `critical` is a priority, not a foundation type. The article burns down unresolved epics and unresolved elements as separate series. Retrying an event id is a no-op.

## Build one testable cohort

Draw real HTML/CSS, render it, and inspect the PNG at desktop and narrow widths. Preserve ranked elements outside the cohort. New proposals use new ids and stay unscored until the user ranks them.

Never invent SVG paths. Follow [asset-sourcing.md](references/asset-sourcing.md): reuse a project/corpus asset, fetch a pinned licensed library asset, or use a deterministic procedural generator. If none is appropriate, omit the graphic and report it. This contract includes icons, ornaments, dividers, pixel fonts, kaomoji, and ASCII graphics.

Run the accessibility checks before publishing. Body text must reach 4.5:1 contrast and controls/meaningful graphics 3:1. A failing theme token is rejected or replaced by its last safe value; do not emit an illegible candidate and ask the user to discover it.

Store theme candidates, the selected candidate, accessibility issues, and the follow-art-direction setting in `spec/design-harness/theme.json`. The browser is an unsaved preview. “Save current” updates the selected candidate; “Save as new” preserves it and creates another.

## Publish the established article

```bash
python3 <skill>/scripts/bootstrap_harness.py article --project-root . \
  --out design/aesthetic-ranking.html --cohort "<element ids>" \
  --round-label "<object>" --asks "<one plain design question>" \
  --agent "<App | Model>" --agent-url "<task deep link>"
python3 <skill>/scripts/bootstrap_harness.py publish --project-root . \
  --screen design/aesthetic-ranking.html
```

Keep the graph clickable, TOC sticky, slideshow functional, and Discarded last. Show the URL and screenshots. Ask the user to rank the new elements.

## Continue and critique

On continuation, use the latest state for the next action and append-only history for confidence and audit. Work in this order: liked/low-star polish, unresolved critical-epic elements, unscored cohort, then new exploration. Change one coherent 3–6 element cohort.

On critique, inspect the corpus, art-direction spec, preference brief, current screenshots, and accessibility report. Name the strongest mismatch first. Do not change ranks, sentiment, lifecycle, or scope while reporting.

## Done gate

A run is complete only when:

1. every inference claim cites visible corpus or feedback evidence and names counterevidence;
2. rank, sentiment, lifecycle, and missingness remain independent;
3. no text or interactive state fails deterministic contrast checks;
4. every nontrivial graphic has source/license/version provenance or a reproducible procedure;
5. the original article structure, scoring controls, burndown, slideshow, and responsive layout work;
6. the user receives the current URL, screenshots, and a clear feedback request.

Checks establish safety, not design quality. Inspect the render.
