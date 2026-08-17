# continue-after-ia.md

Load only on `continue` when `ia.*` / `social.*` already stand in the ledger and there is no visual art corpus (empty `inspiration/` is expected). If the user named an art folder, stop this file and load interpret-art.md instead.

This branch does not reopen INDEX.md. It does not invent a brand and call it evidence.

**Interview before drawing.** Frame is not optional here. The knowledge index paid for *what to say*. It did not pay for *what an infographic is*, or for art direction. Wikipedia-level research is enough to start. A deeper field-map is not a gate.

Do not open `bootstrap_harness.py`. Do not read `spec/information-architecture.md` or `benchmark/`. Do not hash an empty folder.

## Completion (checkable)

Stop when all are true:

1. Frame is written (see Interview). Art direction is either answered or explicitly left as 1-star inference.
2. A cohort of 3-6 standing `ia.post.*` ids is named (one series, or one format).
3. Each cohort post has a throwaway prototype at a social size that **passes the infographic test**.
4. Real content is the post's hook and claim ids. No placeholder copy. No emoji stand-ins for diagrams.
5. Visual execution is recorded as **inference**, `decide` at **1 star max**, new ids (`composition.*` or `proto.*`). No `palette.*` claimed from corpus.
6. Empty `inspiration/` was not treated as a missing brief.

If art direction is still open and the user has not been asked, **do not draw**. Ask once, then wait or take their answer.

## Interview (Frame)

Ask only the missing choices that change the result. One round. Record answers with `decide` under `ia.frame.*` at 1 star.

Pin:

- artefact's **single job** (teach a relation / bust a myth / install a word). Two jobs means none.
- **infographic structure** per format: layers, pointer, sequence, split. Not "nice type on a square."
- art direction: if still open, ask once (register, ink/paper vs a named corpus). Do not mint a studio palette while you wait.
- Wikipedia-level claims from INDEX.md are acceptable as the start. Do not delay Frame for more research.

Infer what the ledger already answers. Do not re-ask series order or claim ids.

## Infographic test

A frame **fails** (delete it) if all of these are true:

- Removing the geometry, rules, and spatial structure leaves the same post.
- The hook could run as a pull-quote or a typeset paragraph unchanged.
- There is no diagram of a relation (tier stack, pointer, mode swap, myth | correction | consequence).

A frame **passes** if the claim is carried by a visual structure the viewer could describe with their hands: stacked layers, a named arrow, a three-beat split, a before/after.

Elegant type layouts are not infographics. Do not ship them as `proto.*`.

## Sizes

| format from `social.format` | size |
|---|---|
| single square | 1080 x 1080 |
| carousel slide | 1080 x 1080 |
| 3-slide myth-bust | 1080 x 1080 per slide (three frames) |

Portrait 1080 x 1350 only if the post's format needs a tall single. Do not invent a size.

## How to build (after Frame)

`/prototype` drives the throwaway build. Put prototypes under `prototypes/` with throwaway names.

Ink/paper is the default inference **after** Frame, not a way to skip it. Do not mint a studio palette. Do not draw a logo.

## Cohort pick

From `stats`: standing `ia.post.*` in series order (contract → tiers → alias → theming → jobs) unless the user named a series. First round: 3-6 posts from **series contract**.

Redraw under new `proto.*` ids. Leave `ia.*` standing. Supersede only after the user ranks a frame above the IA-only row.

## Doctor / article

Run `doctor` if the companion is up and the screen has `data-dh-controls` for the new `proto.*` ids. If the companion is down, two install attempts then keep prototyping and say the companion is red. Do not stop the round on a dead companion when the ask is frames.

If `start-server.sh` or `node server.cjs` fails with Auto-review bind ("executable content could not be bound") and no approval card appears, stop retrying. Do not wrap the launcher. Frames under `prototypes/` are the review surface. The user can start the companion in their own terminal.

`article` is optional until an IA article exists. Do not generate a 48-row strip as the prototype.

## Anti-patterns (delete the draft)

- Drew before Frame / interview.
- Shipped a typeset quote as an infographic (failed the infographic test).
- Waited on a deeper research brief before interviewing.
- Stopped because `inspiration/` is empty.
- Wrote `palette.*` as if a visual corpus existed.
- Opened gold IA or benchmark to copy layouts.
- Prototyped the creator chrome and skipped the infographic frame.
- Changed copy so it no longer cites the claim id.
