---
name: aesthetic
description: Evidence-backed design harness for durable user decisions and ranked feedback. Use for design work with an inspiration corpus or an existing spec/design-harness/. Covers art direction, UI, product, space, copy, motion, and composition.
---

# Aesthetic

Great design is specific to its subject, coherent as a system, visibly refined, and faithful to what the user actually chose. This harness makes those choices survive between sessions without inventing feedback.

Success requires both: **a visible design improvement and a rank the user actually set reaching the ledger.** Screens without captured feedback are guesses; captured feedback without better work is bureaucracy. Fix harness defects in this skill once—never spend a design turn making the user QA the scoring UI.

## Start correctly

- **Existing harness:** run `python3 scripts/bootstrap_harness.py doctor --project-root .`, then read `spec/design-harness/DECISIONS.md` before proposing anything.
- **New project:** read [commands.md](references/commands.md), run `init` with the user-named read-only corpus, then run `doctor` and read the new ledger. Never assume the corpus path.

`doctor` sends a real click through a real socket. It is **the only evidence** that the companion works; an earlier green check proves nothing. Red means stop: no new screen and no restated URL. See [companion-contract.md](references/companion-contract.md).

## Quality loop: frame, direct, declare, build, critique, capture

1. **Frame.** Pin the concrete subject, audience, artefact's single job, real content, constraints, and already-ranked preferences. Infer what the evidence supports; ask only for a missing choice that would materially change the result.
2. **Direct.** Cluster the corpus by recurring relationships, not isolated decoration. Write a one-sentence visual thesis rooted in the subject's own materials, language, tools, history, or environment. Choose a fitting movement or lineage and one memorable **signature** move. Reject any idea that would fit an unrelated brief unchanged.
3. **Declare.** Specify a compact system before drawing: named palette with roles, typographic roles and scale, grid and spacing logic, primary → secondary → tertiary hierarchy, imagery or material register, copy voice, and motion or physical behavior where relevant. Spend boldness on the signature; keep supporting decisions disciplined.
4. **Build.** Use real content. Preserve every standing element outside this iteration's scope. Match execution complexity to the thesis: expressive work needs enough craft to land; restrained work needs exact spacing, type, alignment, and finish. Never substitute placeholders or emoji for ranked artwork.
5. **Critique.** Render and inspect a screenshot. Compare it with the brief and corpus at the **same scale**. Check hierarchy, legibility, composition, rhythm, contrast, specificity, coherence, accessibility, and domain constraints. Remove decoration with no job. If it resembles a generic default or the signature is not immediately legible, revise before showing it.
6. **Capture.** Record what changed, embed the actual graphic beside its controls, `publish`, verify again with `doctor`, and ask for ranked feedback. On the next turn, improve liked low-scoring (`polish`) work first; do not replace it.

Do planning and self-critique internally. Show the strongest coherent result, not a pile of underdeveloped alternatives, unless comparison is the design question.

## Read the signals literally

| Signal | Means | Does **not** mean |
| --- | --- | --- |
| **★ 1–5** | Graphic execution quality, ugly → beautiful | Confidence, priority, or whether to keep it |
| **0** | Worst execution; a real score | Unrated—never-touched is `scored: false` |
| **👍 / 👎** | Direction is / is not worth pursuing | Drawing quality |
| **☑ completed** | Done for now; toggleable status | Approval or a freeze |

**👍 with 2 stars is the most useful state:** *good idea, badly drawn yet*. Improve it. Never drop, supersede, or reject for a low execution score; `stats` reports these as `polish`. A score never changes state; only an explicit verdict does.

## Declare, then draw

Name checkable decisions before rendering:

```bash
python3 scripts/golden_rules.py --scaffold cover.ring.kicker > candidate.json
# fill body / grid / gestalt / register, then:
python3 scripts/golden_rules.py --design candidate.json --min-coverage 0.8
```

Coverage measures determinism, not beauty: a fully declared design can be wrong, but it can be repeated and fixed. [golden-rules.md](references/golden-rules.md) contains the checkable rules and directed doctrine—Albers, Itten, Müller-Brockmann, Bringhurst, Gestalt, Peirce, composition, typography, and movement.

## Commands

Every verb takes `--project-root` and answers `--help`; examples are in [commands.md](references/commands.md). `doctor` proves the path · `adopt` imports clicks, the only source of ranks above 1 · `decide` records inference, capped at 1 · `describe` relabels without touching a rank · `embed`/`publish` add and serve scoring rows idempotently · `stats` reports coverage · `init`/`validate`/`self-test` maintain the harness.

Rows derive from state: pinned, `proposed`, `completed`/`approved`, then dimmed `rejected`/`superseded`. Nothing disappears; undo a wrong rejection by clicking, never by editing JSON.

## Rules no tool enforces

- **Every visual move traces to a corpus cluster, verbatim excerpt, or golden rule.** Anything else is inference: label it, 1 star. See [anti-slop.md](references/anti-slop.md).
- **Counting markup is not verification.** Assert on what a parser builds, not on a string the generator built. When a screen looks wrong, screenshot it. See [verification.md](references/verification.md).
- **The skill owns the scoring UI.** Never write scoring CSS in a project; fix `FEEDBACK_STYLE` so every project benefits.
- **Look before extracting.** Screenshots answer most sourcing questions; byte extraction is an escalation the user opts into. See [sourcing-policy.md](references/sourcing-policy.md).
- **"Continue prototype" means `/prototype`.** This skill supplies the ledger and scoring rows; `/prototype` drives the build.

Changing this skill: [AGENTS.md](AGENTS.md). Other references: [design-tools.md](references/design-tools.md), [domain-profiles.md](references/domain-profiles.md).
