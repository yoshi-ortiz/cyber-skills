---
name: aesthetic
description: Evidence-backed design harness for durable user decisions and ranked feedback. Use for design work with an inspiration corpus or an existing spec/design-harness/. Covers art direction, UI, product, space, copy, motion, and composition.
---

# Aesthetic

Great design is specific to its subject, coherent as a system, visibly refined, and faithful to what the user chose. This harness makes those choices survive between sessions without inventing feedback.

Success needs **both**: a visible design improvement, and a rank the user actually set reaching the ledger. Screens without captured feedback are guesses; captured feedback without better work is bureaucracy. Fix harness defects here once — never spend a design turn making the user QA the scoring UI.

## Start correctly

- **Existing harness:** `bootstrap_harness.py doctor --project-root .`, then read `spec/design-harness/DECISIONS.md` before proposing anything.
- **New project:** read [commands.md](references/commands.md), `init` with the user-named read-only corpus (never assume its path), then `doctor` and read the new ledger.

`doctor` sends a real click through a real socket. It is **the only evidence** the companion works — an earlier green proves nothing. Red means stop: no new screen, no restated URL. See [companion-contract.md](references/companion-contract.md).

## The loop: frame · direct · declare · build · critique · capture

1. **Frame.** Pin the subject, audience, the artefact's single job, real content, constraints, ranked preferences. Infer what the evidence supports; ask only for a missing choice that would change the result.
2. **Direct.** Cluster the corpus by recurring *relationships*, not isolated decoration. Write a one-sentence visual thesis rooted in the subject's own materials, language, tools, history or environment. Choose a movement and one memorable **signature** move. Reject any idea that would fit an unrelated brief unchanged.
3. **Declare.** Specify the system before drawing: palette with roles, typographic roles and scale, grid and spacing logic, primary → secondary → tertiary hierarchy, imagery register, copy voice, motion. Spend boldness on the signature; keep everything supporting it disciplined.
4. **Build.** Real content. Preserve every standing element outside this iteration's scope. Match craft to the thesis — expressive work needs enough to land, restrained work needs exact spacing, alignment and finish. Never substitute placeholders or emoji for ranked artwork.
5. **Critique.** Render and screenshot it, then **run `scripts/measure_screen.js` in the pane and fix every rule it reports under `failingRules` before showing the screen.** Legibility is measured, never eyeballed: screens have twice shipped with body text at 1.1:1 that no reading of the markup could catch, because a block painted a ground and let its ink inherit the companion's frame. `unreadable: 0` is a precondition. Then compare against brief and corpus **at the same scale**: hierarchy, composition, rhythm, specificity, coherence. Cut decoration with no job. If it reads as a generic default, or the signature is not immediately legible, revise before showing it.
6. **Capture.** Record what changed, embed the graphic beside its controls, `publish`, re-run `doctor`, ask for ranks. Next turn, improve liked-but-low-scoring (`polish`) work first — never replace it.

Plan and critique internally. Show the strongest coherent result, not a pile of alternatives, unless comparison *is* the question.

## Scope one cohort per round

When brainstorming is invoked, or the user asks to continue prototyping, **first name the cohort this round will work: a small set of related features or graphics, three to six elements that share a surface or a problem.** Say the cohort out loud, declare it on the screen, and leave every other element untouched.

```html
<div data-dh-cohort="cover-furniture"
     data-dh-controls="cover.ring.kicker,cover.spine.right,cover.solapa.right"></div>
```

A round that touches everything scores nothing. Twenty-five rows of near-identical thumbnails is not thoroughness — it is an unreadable screen the user abandons halfway, and abandoned screens are why coverage stalls while the ledger fills with agent inference. A cohort small enough to redraw properly is small enough to judge properly.

`doctor` enforces the honest half of this: a live element with no scoring row anywhere **fails** unless the screen declares a cohort. Declaring one converts a silent omission into a decision on record — it does not license leaving work unscoreable forever. Name in the same breath what the next round picks up.

Pick the cohort from `stats`: `polish` first (liked, badly drawn), then `unscored`. Never from what is easiest to redraw.

## Read the signals literally

| Signal | Means | Does **not** mean |
| --- | --- | --- |
| **★ 1–5** | Graphic execution quality, ugly → beautiful | Confidence, priority, or whether to keep it |
| **0** | Worst execution; a real score | Unrated — never-touched is `scored: false` |
| **👍 / 👎** | Direction is / is not worth pursuing | Drawing quality |
| **☑ completed** | Done for now; toggleable status | Approval or a freeze |

**👍 with 2 stars is the most useful state:** *good idea, badly drawn yet* — improve it. Never drop, supersede or reject for a low execution score; `stats` reports these as `polish`. A score never changes state; only an explicit verdict does.

## Declare, then draw

```bash
python3 scripts/golden_rules.py --scaffold cover.ring.kicker > candidate.json
# fill body / grid / gestalt / register, then:
python3 scripts/golden_rules.py --design candidate.json --min-coverage 0.8
```

Coverage measures determinism, not beauty: a fully declared design can be wrong, but it repeats, so it can be fixed. Checkable rules and directed doctrine — Albers, Itten, Müller-Brockmann, Bringhurst, Gestalt, Peirce, movement — in [golden-rules.md](references/golden-rules.md).

## Commands

Every verb takes `--project-root` and answers `--help`. Full list and examples: [commands.md](references/commands.md). Two facts that are semantics, not usage: **`adopt` is the only source of ranks above 1 star**, and **`decide` is capped at 1** — a higher rank must come from a click.

Rows derive from state: pinned, `proposed`, `completed`/`approved`, then dimmed `rejected`/`superseded`. Nothing disappears; undo a wrong rejection by clicking, never by editing JSON.

## Rules no tool enforces

- **Every visual move traces to a corpus cluster, verbatim excerpt, or golden rule.** Anything else is inference: label it, 1 star. See [anti-slop.md](references/anti-slop.md).
- **Counting markup is not verification.** Assert on what a parser builds, not a string the generator built. When a screen looks wrong, screenshot it. See [verification.md](references/verification.md).
- **The skill owns the scoring UI.** Never write scoring CSS in a project; fix `FEEDBACK_STYLE` so every project benefits.
- **Look before extracting.** Screenshots answer most sourcing questions; byte extraction is an escalation the user opts into. See [sourcing-policy.md](references/sourcing-policy.md).
- **"Continue prototype" means `/prototype`.** This skill supplies the ledger and scoring rows; `/prototype` drives the build.

Changing this skill: [AGENTS.md](AGENTS.md).
