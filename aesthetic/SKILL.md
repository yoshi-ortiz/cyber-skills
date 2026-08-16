---
name: aesthetic
description: Evidence-backed design harness for durable user decisions and ranked feedback. Use for design work with an inspiration corpus or an existing spec/design-harness/. Covers art direction, UI, product, space, copy, motion, and composition.
---

# Aesthetic

Great design is specific to its subject, coherent as a system, visibly refined, and faithful to what the user chose. This harness makes those choices survive between sessions without inventing feedback. A round succeeds only if **both** happen: the work visibly improves, and a rank the user actually set reaches the ledger.

## When invoked

Arguments are usually empty or a stub — "continue prototype development", or nothing. **They are not the brief.** Read the state from disk first:

- **`spec/design-harness/` exists** → continue: `doctor`, `stats`, `DECISIONS.md`, then name the cohort. Do not re-ask what the ledger already answers.
- **It does not** → ask, in one question, for the two things only the user has: **the inspiration corpus directory** — read-only, never guessed — and **the artistic direction**: subject, audience, what the artefact is for. Then `init`.

A run with no corpus produces inference, not evidence: if the named directory is missing or empty, say so and stop rather than designing from memory.

## What a design run may write

| Writable | Read-only for the whole run |
| --- | --- |
| the project's screens | **this skill's own files** — `scripts/`, `references/`, `companion/` |
| `spec/design-harness/`, through harness verbs only | the corpus, and the companion's `decisions.jsonl` |

**Do not repair the harness while designing.** A defect in these scripts is a finding, not this turn's work: name it in one line, route around it, hand it off, keep designing. Whole sessions have gone into patching the scoring UI and shipped no design — that is the failure this rule exists to stop. Changing the skill is its own session: [AGENTS.md](AGENTS.md).

**Do not hand-write a ledger.** Appending to `decisions.jsonl` forges a user click; editing `decisions.json` desyncs `DECISIONS.md`. Every write goes through `adopt`, `decide` or `describe`. Feedback no verb recovers is lost — say so rather than reconstructing it.

## Start correctly

Scripts are at `<skill>/scripts/`, the companion at `<skill>/companion/` — never search the filesystem for them.

- **Existing harness:** `bootstrap_harness.py doctor --project-root .`, then read `DECISIONS.md` before proposing anything.
- **New project:** read [commands.md](references/commands.md), `init` with the user-named corpus, then `doctor`.
- **Companion dead:** `companion/install.sh`, then `companion/start-server.sh --project-dir "$PWD"`, then `doctor`. Two attempts; still red, say so and stop — no new screen, no restated URL.

`doctor` sends a real click through a real socket. It is **the only evidence** the companion works — an earlier green proves nothing. [companion-contract.md](references/companion-contract.md)

## Open the round by naming the cohort

**Before any other work, say which three to six elements this round works** — a set sharing a surface or a problem — and leave the rest untouched. Pick from `stats`: `polish` first (liked, badly drawn), then `unscored`; never what is easiest to redraw.

```html
<div data-dh-cohort="cover-furniture"
     data-dh-controls="cover.ring.kicker,cover.spine.right,cover.solapa.right"></div>
```

A round that touches everything scores nothing: twenty-five near-identical thumbnails is a screen the user abandons halfway. `doctor` enforces the honest half — a live element with no scoring row **fails** unless the screen declares a cohort.

Startup is not the round. If the cohort is unnamed and no screen is on its way after a dozen tool calls, you are doing infrastructure — say what is blocking.

## The loop

Each step in full, with its failure modes: [loop.md](references/loop.md).

1. **Frame.** Subject, audience, the artefact's single job, real content, constraints, ranked preferences.
2. **Direct.** Cluster the corpus by recurring *relationships*, not decoration. One-sentence visual thesis from the subject's own materials; one memorable **signature** move. Reject any idea that would fit an unrelated brief unchanged.
3. **Declare.** Palette roles, type roles and scale, grid, hierarchy, imagery register, copy voice, motion — before drawing. `golden_rules.py --scaffold` writes the spec; `--design --min-coverage 0.8` checks it.
4. **Build.** Real content. Preserve every standing element outside the cohort. Never substitute placeholders or emoji for ranked artwork.
5. **Critique.** Render, screenshot, then **run `scripts/measure_screen.js` in the pane and fix every `failingRules` entry before showing the screen** — `unreadable: 0` is a precondition; legibility is measured, never eyeballed. Then compare against brief and corpus at the same scale, and revise anything that reads as a generic default.
6. **Capture.** Record what changed, embed each graphic beside its controls, `publish`, re-run `doctor`, ask for ranks in the same turn.

Plan internally and show the strongest coherent result, not a pile of alternatives — unless comparison *is* the question.

## Read the signals literally

**★ 1–5** is graphic execution, ugly → beautiful — never confidence, priority, or whether to keep a thing. **0** is a real score, the worst one; never-touched is `scored: false`. **👍/👎** judges the direction, not the drawing. **☑ completed** is a status, not approval and not a freeze. Full semantics: [companion-contract.md](references/companion-contract.md).

**👍 with 2 stars is the most useful state:** *good idea, badly drawn yet* — improve it. Never drop, supersede or reject for a low score; `stats` reports these as `polish`. A score never changes state; only a verdict does.

## Commands

Every verb takes `--project-root` and answers `--help`. Full list: [commands.md](references/commands.md). Two facts that are semantics, not usage: **`adopt` is the only source of ranks above 1 star**, and **`decide` is capped at 1** — a higher rank comes from a click. Nothing ever disappears; undo a wrong rejection by clicking, never by editing JSON.

## Rules no tool enforces

- **Every visual move traces to a corpus cluster, verbatim excerpt, or golden rule.** Anything else is inference: label it, 1 star. [anti-slop.md](references/anti-slop.md)
- **Counting markup is not verification.** Assert on what a parser builds, not a string the generator built; screenshot a screen that looks wrong. [verification.md](references/verification.md)
- **The scoring UI belongs to the generator.** Never write scoring CSS in a project; if the strip is wrong, report it and keep designing.
- **Look before extracting.** Screenshots answer most sourcing questions; byte extraction is an escalation the user opts into. [sourcing-policy.md](references/sourcing-policy.md)
- **"Continue prototype" means `/prototype`**, after the cohort is named. This skill supplies the ledger and rows; `/prototype` drives the build.
