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

## Language

Use the language in the user's latest words. When that language is Spanish,
read project-authored publishing copy and mirror its dialect, vocabulary, and
register rather than defaulting to generic Spanish. Exclude reference captions,
prompts, generated artifacts, machine locale, and prior agent replies from that
decision. `project.json.language` translates companion controls only; it never
chooses the language of chat.
Treat the user's current language plus the publishing-copy register as the
project language for chat.

Every visible sentence then stays in that language -- not only the three moments
named below. That includes running commentary on what you are doing right now
("exploring the references", "rendering the comp"), not just the labelled
handoffs. Do not code-switch mid-reply.

## First reply

The URL and access key always come first. Do not put a greeting, plan, or status
before them. Render them as a small table so the long key does not force the
reader to hunt through a line of prose for it; the review action stays its own
sentence below, since it is prose, not a fact. Mask the raw URL behind a short
link label -- a pasted `?key=` string is not something a reader should have to
read past, only click.

```text
| Access |
| --- |
| 🔗 [Open your designs](http://localhost:49830/?key=abc) |
| 🔑 abc |

👀 While I prepare the next designs, you can review and score what is already on the page.
```

Translate the review-action line and every later message into the project language.
The URL and key stay unchanged, and the link text is never the raw URL. If there is no previous page, give one useful action
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

Every word in the left column has leaked into a real reply. Before sending any
message, reread it and swap each one out; a table you looked at once and did
not apply is the same as not having it.

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

## Long runs

Before tool work, mirror one project-language progress line in the status aid.
Name the result, not setup commands.

```bash
python3 <skill>/scripts/bootstrap_harness.py status --project-root . \
  --text "<emoji + visible work + why it matters>"
```

## Name the weakest proposal before asking

Hand over a cohort with your own read of it: which element is strongest, which
is weakest, and the visible reason. Cite what is in the render — a shape that
reads as the wrong object, a mark that disappears at delivery size — never a
preference.

Presenting three proposals as equals when one is visibly worse hides the
judgement the user is paying for, and it is the same failure as reporting a run
green because the exit code was zero. A round the agent cannot criticise is a
round the agent did not look at.

Never record a verdict the user did not give. `pending` is the honest state
until they speak; an agent-written `accepted` is the one value in the ledger
that cannot be earned.
