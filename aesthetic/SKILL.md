---
name: aesthetic
description: Use when a multimodal corpus and user sentiment must become grounded creative direction, ranked decisions, and a responsive editorial burndown. Use it to continue or critique a design sprint. Not for generic UI coding without references.
---

# Aesthetic ranking

`continue`, `critique`, `prototype`, and `observe` are context clues.

Keep the established article and its hero, graph, TOC, four sections, and progress chart. Never replace it with a kanban or second site.

## Speak to the designer

Read [user-communication.md](references/user-communication.md) before any user-visible update.

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

`open` restores the last ranking page. Keep it live during the work.

If setup is missing, ask once for the reference folder, then initialize it read-only. User-visible language comes from `project.json`.

Inventory the named reference folder. Interpret images and text together.

```bash
python3 <skill>/scripts/editorial_workflow.py observe \
  --project-root . --source-root <absolute-reference-folder>
```

Open supported items. Explain omissions. Metadata is not visual evidence.

## Read the user before directing the work

Adopt feedback, then produce the element-level brief.

```bash
python3 <skill>/scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl
python3 <skill>/scripts/editorial_workflow.py preferences --project-root . \
  --out /tmp/aesthetic-preferences.json
```

Read [sentiment-analysis.md](references/sentiment-analysis.md). Never collapse stars, thumbs, lifecycle, or missing feedback into one score.

Preferences apply to individual elements only. One liked element does not approve its epic, theme, page, or style.

## Infer and rank art direction

Read [loop.md](references/loop.md), [interpret-art.md](references/interpret-art.md), and [anti-slop.md](references/anti-slop.md). Select one evidence-backed hypothesis and a 3–6 element cohort. Never average direction, execution, lifecycle, or missing feedback. Reject a thesis that fits an unrelated product unchanged.

```bash
python3 <skill>/scripts/editorial_workflow.py direction --project-root . \
  --spec /tmp/aesthetic-art-direction.json
```

Fix a rejected spec. Never bypass the gate.

## Keep long runs useful

Before work that may take more than a minute, send one project-language update and mirror it in the bottom status aid:

```bash
python3 <skill>/scripts/bootstrap_harness.py status --project-root . \
  --text "<emoji + visible work + why it matters>"
```

Name the visible result and link the page. Update the status when the real activity changes. Do not report setup commands.

## Scope the editorial burndown

Read [editorial-workflow.md](references/editorial-workflow.md). Save epics in `editorial.json` and append changes to `editorial-events.jsonl`. Every element has one primary epic. Retrying an event id is a no-op.

## Build one testable cohort

Draw real HTML/CSS, render it, and inspect the PNG at desktop and narrow widths. Preserve ranked elements outside the cohort. New proposals use new ids and stay unscored until the user ranks them.

Never invent SVG paths. Follow [asset-sourcing.md](references/asset-sourcing.md). Reuse a project asset, fetch a pinned licensed asset, use a deterministic generator, or omit the graphic.

Before publishing, require 4.5:1 text contrast and 3:1 control contrast. Roll back only the unsafe theme setting.

Keep **Agent settings** collapsed in the bottom status aid. **Update app theme** is off by default. **Saved themes**, **Reset theme**, and **Save** use `spec/design-harness/theme.json`; unsafe color or font changes roll back one setting at a time.

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

Keep the graph clickable, TOC sticky, slideshow functional, and Discarded last. `review_delivery.py` accepts only rankable, subject-specific proposals with a legible signature; evidence cards, explanations, generic defaults, missing files, and hash drift fail. In final chat, lead with the URL, key, and project-language review request. Attach only the emitted absolute `image_path` values.

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
6. the user receives the current URL, key, project-language request, and emitted review images.

Inspect the render. Checks prove safety, not design quality.
