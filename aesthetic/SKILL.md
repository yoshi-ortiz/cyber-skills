---
name: aesthetic
version: 0.8.0
description: Evidence-backed design harness for durable user decisions and ranked feedback. Use for design work with an inspiration corpus, a knowledge-index text corpus, or an existing spec/design-harness/. Covers art direction, UI, product, space, copy, motion, composition, and information architecture for social sharing.
argument-hint: "continue | critique | interpret @<art-folder> | interpret @<knowledge-index>"
---

# Aesthetic

Great design is specific to its subject, coherent as a system, visibly refined, and faithful to what the user chose. A round succeeds only if both happen: the work visibly improves, and a rank the user actually set reaches the ledger.

## When invoked

- **continue** (or nothing) — `doctor`, `stats`, name the cohort. If `ia.*` stands and there is no art folder, load [continue-after-ia.md](references/continue-after-ia.md). Interview before drawing. Infographic frames, not typeset quotes. Visual is inference. Else [loop.md](references/loop.md).
- **critique** — judge what stands. Rank nothing on the user's behalf.
- **interpret @\<art-folder\>** — load [interpret-art.md](references/interpret-art.md). Visual corpus.
- **interpret @\<knowledge-index\>** — load [interpret-knowledge.md](references/interpret-knowledge.md). Text corpus with INDEX.md. Propose IA. Do not draw.

Tie-break: INDEX.md present → knowledge. Images and no INDEX.md → art. Empty `inspiration/` is not a missing corpus when `knowledge-index/` exists.

**Read disk first.** `spec/design-harness/` exists → continue. It does not → ask once for the corpus directory (read-only, never guessed) and the artistic direction, then `init`. Named directory missing or empty: say so and stop.

## What a design run may write

| Writable | Read-only |
| --- | --- |
| the project's screens | this skill's `scripts/`, `references/`, `companion/` |
| `spec/design-harness/`, through harness verbs only | the corpus; companion `decisions.jsonl` |

Do not repair the harness while designing. Do not hand-write a ledger. Writes go through `adopt`, `decide`, `describe`, `supersede`.

## Start

Scripts at `<skill>/scripts/`, companion at `<skill>/companion/`. Existing: `bootstrap_harness.py doctor --project-root .`, then `DECISIONS.md`. New: [commands.md](references/commands.md), `init`, `doctor`. Companion dead: `companion/install.sh`, then `start-server.sh --project-dir "$PWD"`, then `doctor`. Two attempts; still red, stop.

Give the user the URL `doctor` prints, `?key=` and all. An IDE preview drops the query string.

## What a round must be

`article` refuses two rounds. Both are satisfiable by doing the right thing, not by a flag.

1. **Polish before novelty.** While anything carries a thumb up and ≤2 stars, the round must improve one of them — `<that-id>.<slug>`, or the id itself to re-ask. A thumb up on a low score is the ledger's clearest instruction: idea right, drawing not there yet.
2. **One redraw per element.** Two new drawings of the same incumbent is wallpaper — the user can only say which guess they prefer, not whether either beat what stands.

Comps are drawn in **HTML/CSS** and rendered with `shoot` -- never hand-authored SVG. `shoot` and `decide --preview` both refuse a PNG that is blank or has no contrast against its own ground, so an invisible drawing cannot reach the ledger.

Every thumbnail opens a slideshow: the graphic full height, its argument beside it, its own scoring strip, arrows across the set. Score from there or from the row — same control, one write path.

## Shared

1. Ledger via verbs. Do not open `bootstrap_harness.py` from a design run.
2. Do not edit this skill while designing.
3. Art path writes `core.*` `palette.*` `typography.*` `illustration.*` `composition.*` `voice.*` `motion.*`. Knowledge path writes `ia.*` `social.*`. No `palette.*` on a text corpus.
4. Knowledge interpret stops at IA. `continue` after standing `ia.*` may prototype social-size frames ([continue-after-ia.md](references/continue-after-ia.md)). Empty `inspiration/` is not a stop. Do not write `palette.*` as corpus evidence.

## interpret @knowledge-index

Load [interpret-knowledge.md](references/interpret-knowledge.md). INDEX.md is the catalog. Cluster from the catalog. Open numbered files only after a cluster is named. Output: program → series → post → slide, claim ids used, files not opened. Stop.

## interpret @art-folder

Load [interpret-art.md](references/interpret-art.md), then [loop.md](references/loop.md). Do not route images through interpret-knowledge.md.
