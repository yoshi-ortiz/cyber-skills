---
name: aesthetic
description: Use when a multimodal corpus and human feedback must become grounded creative direction, ranked design decisions, and a responsive editorial burndown. It helps the agent understand user sentiment and what the user likes by keeping direction, execution quality, lifecycle, and missing feedback distinct. Use it to continue or critique a design sprint. Not for generic UI coding without references.
---

# Aesthetic ranking

This project-local system learns the user's design preferences. `continue`, `critique`, `prototype`, and `observe` are context clues.

Keep the established article and its hero, graph, TOC, four sections, and progress chart. Never replace it with a kanban or second site.

## Speak to the designer

Read [user-communication.md](references/user-communication.md) before any
user-visible update. It owns project language, plain words, functional emojis,
and what to say during long or invisible work.

## Start

Open the companion before any update.

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

`open` restores the last ranking page when available. Keep it live and give the
designer something useful to review while work continues.

If setup is missing, ask once for the reference folder, then initialize it read-only. User-visible language comes from `project.json`.

Inventory every supported file in the named reference folder. Interpret images and text together; `INDEX.md` is evidence, not a routing switch.

```bash
python3 <skill>/scripts/editorial_workflow.py observe \
  --project-root . --source-root <absolute-reference-folder>
```

Open supported items. Explain omissions. Metadata is not visual evidence.

## Read the user before directing the work

Adopt companion feedback, then produce the deterministic element-level brief.

```bash
python3 <skill>/scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl
python3 <skill>/scripts/editorial_workflow.py preferences --project-root . \
  --out /tmp/aesthetic-preferences.json
```

Read [sentiment-analysis.md](references/sentiment-analysis.md). Never collapse stars, thumbs, lifecycle, or missing feedback into one score.

Preferences apply to individual elements only. One liked element does not approve its epic, theme, page, or style.

## Infer and rank art direction

Read [loop.md](references/loop.md), [interpret-art.md](references/interpret-art.md), and [anti-slop.md](references/anti-slop.md). Follow their inference record before drawing. Compare ambiguous directions without averaging them, then select one hypothesis and a 3–6 element test cohort.

Do not average those dimensions into one reward or store agent rank as user feedback. With sparse feedback, lower confidence and test less.

Every selected visual rule cites both a corpus observation and relevant preference evidence when each exists. Labels such as “clean,” “bold,” “modern,” “editorial,” or “premium” are invalid unless replaced by observable relationships. If the thesis could fit an unrelated product unchanged, reject it.

```bash
python3 <skill>/scripts/editorial_workflow.py direction --project-root . \
  --spec /tmp/aesthetic-art-direction.json
```

This saves `art-direction.json`. Fix a rejected spec; never bypass the gate.

## Keep long runs useful

Before work that may take more than a minute, send one plain project-language
update and mirror it in the collapsed bottom status aid:

```bash
python3 <skill>/scripts/bootstrap_harness.py status --project-root . \
  --text "<emoji + visible work + why it matters>"
```

Name the visible result and link the live page. Give the designer a
review action while work continues.

The status is part of the run, not optional narration. Update it when the real
activity changes: reading references and ratings, choosing a direction,
drawing, checking readability, or publishing. Do not report setup commands.

## Scope the editorial burndown

Save explicit project epics and element membership in `spec/design-harness/editorial.json`; append state changes to `editorial-events.jsonl`. Read [editorial-workflow.md](references/editorial-workflow.md).

Every element has exactly one primary epic. Epics may describe any project concern; `critical` is a priority, not a foundation type. The article burns down unresolved epics and unresolved elements as separate series. Retrying an event id is a no-op.

## Build one testable cohort

Draw real HTML/CSS, render it, and inspect the PNG at desktop and narrow widths. Preserve ranked elements outside the cohort. New proposals use new ids and stay unscored until the user ranks them.

Never invent SVG paths. Follow [asset-sourcing.md](references/asset-sourcing.md): reuse a project/corpus asset, fetch a pinned licensed library asset, or use a deterministic procedural generator. If none is appropriate, omit the graphic and report it. This contract includes icons, ornaments, dividers, pixel fonts, kaomoji, and ASCII graphics.

Run the accessibility checks before publishing. Body text must reach 4.5:1 contrast and controls/meaningful graphics 3:1. A failing theme token is rejected or replaced by its last safe value; do not emit an illegible candidate and ask the user to discover it.

Keep theme controls collapsed in the bottom status aid. Store candidates, selection, accessibility issues, and follow-art-direction in `spec/design-harness/theme.json`; the browser is an unsaved preview. “Save current” updates the selection; “Save as new” preserves it and creates another.

## Publish the established article

```bash
python3 <skill>/scripts/bootstrap_harness.py article --project-root . \
  --out design/aesthetic-ranking.html --cohort "<element ids>" \
  --round-label "<object>" --asks "<one plain design question>" \
  --agent "<App | Model>" --agent-url "<task deep link>"
python3 <skill>/scripts/bootstrap_harness.py publish --project-root . \
  --screen design/aesthetic-ranking.html
python3 <skill>/scripts/bootstrap_harness.py status --project-root . --idle \
  --text "<project-language request to review the new designs>"
```

Keep the graph clickable, TOC sticky, slideshow functional, and Discarded last. Show the URL and screenshots. Ask the user to rank the new elements in the project language.

## Continue and critique

On continuation, use the latest state for the next action and append-only history for confidence and audit. Work in this order: like + low stars, dislike + high stars, unresolved critical work, unscored designs, then new exploration. Change one coherent 3–6 element cohort.

On critique, inspect the corpus, art-direction spec, preference brief, current screenshots, and accessibility report. Name the strongest mismatch first. Do not change ranks, sentiment, lifecycle, or scope while reporting.

## Done gate

A run is complete only when:

1. every inference claim cites visible corpus or feedback evidence and names counterevidence;
2. rank, sentiment, lifecycle, and missingness remain independent;
3. no text or interactive state fails deterministic contrast checks;
4. every nontrivial graphic has source/license/version provenance or a reproducible procedure;
5. the original article structure, scoring controls, burndown, slideshow, and responsive layout work;
6. the user receives the current URL, screenshots, and a clear feedback request.

Inspect the render. Checks prove safety, not design quality.
