---
type: Contract
title: Designer communication
description: Plain-language handoff and progress messages for non-technical designers.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-21T00:30:00-05:00
---

# Designer communication

The designer should know three things at a glance. Where to review the work,
what is happening now, and what they can do while they wait.

## First reply

The URL and access key always come first. Do not put a greeting, plan, or status
before them.

```text
🔗 http://localhost:49830/?key=abc
🔑 abc
👀 While I prepare the next designs, you can review and score what is already on the page.
```

Translate the third line and every later message into the project language. The
URL and key stay unchanged. If there is no previous page, give one useful action
instead, such as adding visual references or answering one concrete design
question.

## Progress messages

Use one short sentence. Name the visible object and the reason for the work.
When useful, add a second sentence that points back to the ranking page.

Good:

- `🎨 Redrawing the cover so the title stays readable on a phone.`
- `✅ Your earlier ratings are loaded. I am keeping the ideas you liked and improving how they are drawn.`
- `👀 You can keep scoring the current page while I prepare the next designs.`
- `⚠️ The proposed text color was too faint, so I kept the last readable color.`

Bad:

- `Running the harness for the next cohort.`
- `Replaying the ledger and recalculating coverage.`
- `Resolving critical epics before the burndown refresh.`
- `Validating corpus provenance and deterministic tokens.`

## Plain words

| Internal term | Say to the designer |
| --- | --- |
| harness | design setup or tools |
| corpus | reference folder or references |
| cohort | designs in this round |
| ledger | saved ratings or saved feedback |
| epic | work area or big task |
| critical epic | important unfinished work |
| burndown | progress chart |
| inference | what I learned from your references and ratings |
| provenance | source and license |
| deterministic check | automatic check |
| lifecycle | progress state |
| token | color or font setting |
| standing elements | current designs |

These replacements apply only to user-facing chat, screenshots, questions, and
the live status bar. Internal files and commands keep their precise terms.

## Invisible work

Do not list internal repairs. State their effect.

Instead of `I fixed feedback replay and lifecycle isolation`, say `✅ Your old
ratings now load without moving designs into the wrong section.`

Instead of `The context and source manifest are valid`, say `✅ I can now use
all of your references without missing files or changing the originals.`

If the work has not produced a new image yet, say so plainly and keep the last
ranking page available. The designer should never have to guess whether the
session stalled.

## Final review handoff

Lead with the full URL, access key, and one project-language review request.
Then attach every `image_path` emitted by `scripts/review_delivery.py`. These
paths are absolute and already checked. Do not attach a relative path, a source
HTML path, an evidence card, or an image that is absent from that JSON.

Use the project language for every sentence and image caption. Keep internal
checks and process names out of the handoff.
