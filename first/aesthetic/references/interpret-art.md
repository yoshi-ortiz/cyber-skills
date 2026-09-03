---
type: Playbook
title: Interpret visual and multimodal evidence
description: Turn a corpus and element-level preferences into one testable art direction.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
---

# Interpret visual and multimodal evidence

Load for **observe** on a visual or multimodal corpus, **continue** on art, or a greenfield run with no corpus at all. Treat indexes, prose, images, screenshots, and existing feedback as one evidence set. An `INDEX.md` does not stop visual inference.

Do not open `bootstrap_harness.py`. Do not invent colours or faces the corpus does not evidence. Read [sentiment-analysis.md](sentiment-analysis.md) before directing the round.

## Completion (checkable)

Stop when all are true:

1. A cohort of 3-6 elements is named in one sentence (what they share).
1. Direction is grounded: observations when a corpus exists, premises when it does not.
2. New drawings use new element ids, proposed at 0 stars until the user ranks.
3. Standing ranked elements outside the cohort are untouched.
4. User has the companion URL and a PNG pasted in chat for each new comp.

## Interpret the corpus

Read the named folder read-only and account for every supported item. Cluster by recurring relationships, not decoration. Fuse text and image observations only when the relationship is explicit; do not treat metadata as a visual observation. Declare foundations the user can rank.

Missing or empty directory: say so, then seed and direct from premises instead — `editorial_workflow.py seed`. Refusing to direct because the user brought no references is the failure mode this skill exists to avoid. A premise cites [golden-rules.md](golden-rules.md) or a [profile](domain-profiles.md), names counterevidence, and is recorded as inference, never as something the corpus showed.

Then follow [loop.md](loop.md): Frame, Direct, Declare, Build, Critique, Capture.

## Open the round by naming the cohort

Run `editorial_workflow.py preferences`. Pick **polish** first, then unresolved critical-epic elements, then **unscored**. Support each preference claim with element ids, visible features, counterevidence, coverage, and confidence.

`data-dh-cohort` goes on the same div as `data-dh-controls`. If you cannot say in one sentence what the cohort shares, it is not a cohort.

## Every new implementation gets its own element id

Redrawing under a user-ranked id leaves nothing to judge. Record new work with `decide --source agent --stars 0`. Supersede only after the user ranks the replacement higher — `supersede --element <loser> --by <winner>`.

## Ship the article

`adopt` before `article`. Validate project `--bg/--ink/--accent` before rendering. Take hex and faces from the corpus or a pinned licensed source; persist candidates in `theme.json`.

Signals: stars = execution; sentiment = direction. Full semantics: [companion-contract.md](companion-contract.md).

Never treat this skill's scripts as writable during a design run.

## Illustration: settle the construction language before the character

A figure carries two independent decisions, and a round that asks about both at
once gets an answer about neither. Split them, in this order:

1. **Construction language.** How any figure in this project is built — head to
   body ratio, contour weight, whether fills are flat or shaded, which
   primitives are allowed. Cohort: 3 languages that differ in *construction*,
   not in colour. Same subject in each, or the comparison is not controlled.
2. **Character design.** Who this particular figure is, inside the settled
   language. Cohort: 3 readings of the same written brief, differing by
   **silhouette first** — at delivery size the outline is the only mark left,
   so hair and stance separate characters and interior detail does not.

Quote the character's line from the inventory onto the sheet. A round judged
against the agent's memory of the brief is judged against the wrong thing.

Do not carry a character forward from a language round. A language round proves
a grammar; the figure in it is a placeholder and shipping it is how a cast ends
up as one recoloured mascot.

## Judge every proposal at delivery size

Render each proposal twice on the same sheet: once large enough to see the
craft, once at the size the artifact actually uses it, on the background it
actually sits on. `shown_at_delivery_size` in the assessment is that check, and
`review_delivery.py` refuses a cohort where any element fails it.

Detail that vanishes at delivery size is not neutral. It costs consistency
across the whole cast and buys nothing where the work is read.
