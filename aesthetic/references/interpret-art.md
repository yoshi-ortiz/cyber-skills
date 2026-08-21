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

Load for **observe** on a visual or multimodal corpus, or **continue** on art. Treat indexes, prose, images, screenshots, and existing feedback as one evidence set. An `INDEX.md` does not stop visual inference.

Do not open `bootstrap_harness.py`. Do not invent colours or faces the corpus does not evidence. Read [sentiment-analysis.md](sentiment-analysis.md) before directing the round.

## Completion (checkable)

Stop when all are true:

1. A cohort of 3-6 elements is named in one sentence (what they share).
2. New drawings use new element ids, proposed at 0 stars until the user ranks.
3. Standing ranked elements outside the cohort are untouched.
4. User has the companion URL and a PNG pasted in chat for each new comp.

## Interpret the corpus

Read the named folder read-only and account for every supported item. Cluster by recurring relationships, not decoration. Fuse text and image observations only when the relationship is explicit; do not treat metadata as a visual observation. Declare foundations the user can rank. Missing or empty directory: say so and stop.

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
