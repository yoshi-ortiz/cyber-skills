---
name: aesthetic
version: 0.8.3
description: Ranked design work on a live page. Use to continue a round, critique what stands, prototype one idea, or observe a folder of references — art, UI, product, space, copy, motion, or social posts.
argument-hint: "continue | critique | prototype | observe @/art-folder"
---

# Aesthetic

Great design is specific to its subject, coherent as a system, visibly refined, and faithful to what the user chose. A round succeeds only if both happen: the work visibly improves, and a rank the user actually set reaches the ledger.

## When invoked

- **continue** (or nothing) — `open`. Reply with the URL.
- **critique** — judge what stands. Rank nothing on the user's behalf.
- **prototype** — draw one comp to answer one question, `shoot` it, show it. No ledger round, no cohort.
- **observe @/art-folder** — read the corpus. Routes on what is actually there: INDEX.md present → text, load [interpret-knowledge.md](references/interpret-knowledge.md), propose IA, do not draw. Images and no INDEX.md → visual, load [interpret-art.md](references/interpret-art.md).

Empty `inspiration/` is not a missing corpus when `knowledge-index/` exists.

## First tool call

```bash
python3 <skill>/scripts/bootstrap_harness.py open --project-root .
```

Done when the reply is the URL (`?key=` included). Read `spec/design-harness/project.json` → `language`. One sentence in **that language**, then the URL. The bottom bar carries longer status.

If the harness is missing: ask once for the references folder and direction, then `init`, then `open`.

## While you work

Load [loop.md](references/loop.md) only after the URL is in chat. Do not read DECISIONS.md or reference files first — draw.

**Language.** Reason in English if it helps; every word the user sees is in `project.json` → `language`. Chat, `--status`, `--description`, `--title`, `--asks`, `--round-label`. Ids and flags stay English.

**Heartbeat.** Before a step longer than a minute: one chat sentence + `status --text`. After every `shoot`: paste the PNG in chat before `publish`. Silence reads as a hang.

**Agent on the page.** Pass `article --agent` your model name and `--agent-url` the deep link to this session. Pass `--round-label` the object name (e.g. Micrófono), not a slug like `objeto`.

**New proposals stay unscored.** `decide --source agent --stars 0 --preview content/<element>.html`. The row and slideshow show blank stars until the user ranks. Never pass a PNG when the HTML comp exists.

Look at the last graphic and references at the same scale. Name the one move. Draw HTML/CSS, `shoot`, look at the PNG. Redraw once if you would not pin it.

If `ia.*` stands and there is no art folder, load [continue-after-ia.md](references/continue-after-ia.md).

## What a design run may write

| Writable | Read-only |
| --- | --- |
| the project's screens | this skill's `scripts/`, `references/`, `companion/` |
| `spec/design-harness/`, through harness verbs only | the corpus; companion `decisions.jsonl` |

Do not repair the harness while designing. Writes go through `adopt`, `decide`, `describe`, `supersede`.

## What a round must be

`article` refuses two rounds. Both are satisfiable by doing the right thing, not by a flag.

1. **Polish before novelty.** While anything carries a thumb up and ≤2 stars, improve one of them — `<that-id>.<slug>`, or re-ask the id. A thumb up on a low score means idea right, drawing not there yet.
2. **One redraw per element.** Two new drawings of the same incumbent is wallpaper.

Comps are **HTML/CSS** + `shoot` — never hand-authored SVG. Every thumbnail opens a slideshow with its scoring strip.

## How to talk to the user

They are a designer. Name the move, not the machinery. One sentence before a long step; the bottom bar carries the rest. A round ends with: what changed, the URL if new, and the one thing to rank. Never explain the harness unless asked.

## Shared

1. Ledger via verbs. Run them; do not edit this skill's scripts.
2. Do not edit this skill while designing.
3. Art path writes `core.*` `palette.*` `typography.*` `illustration.*` `composition.*` `voice.*` `motion.*`. Knowledge path writes `ia.*` `social.*`.
4. Observing a text corpus stops at IA. Empty `inspiration/` is not a stop.

## observe — text corpus

Load [interpret-knowledge.md](references/interpret-knowledge.md). INDEX.md is the catalog. Stop at IA.

## observe — art folder

Load [interpret-art.md](references/interpret-art.md), then [loop.md](references/loop.md).
