---
name: aesthetic
description: Evidence-backed design harness for durable user decisions and ranked feedback. Use for design work with an inspiration corpus or an existing spec/design-harness/. Covers art direction, UI, product, space, copy, motion, and composition.
argument-hint: "[continue|<corpus-dir>]"
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

**Give the user the URL `doctor` prints on its last line, `?key=…` and all.** The key *is* the address. An IDE preview widget shows the origin only — it drops the query string — so the widget can never open the companion in the user's own browser; pasting the origin alone lands on "Session key required". Restate the full URL whenever the companion restarts, since the key changes with it.

## Open the round by naming the cohort

**Before any other work, say which three to six elements this round works** — a set sharing a surface or a problem — and leave the rest untouched. Pick from `stats`: `polish` first (liked, badly drawn), then `unscored`; never what is easiest to redraw.

```html
<div data-dh-cohort="cover-furniture"
     data-dh-controls="cover.ring.kicker,cover.spine.right,cover.solapa.right"></div>
```

`data-dh-cohort` goes on the **same div** as `data-dh-controls` — `embed` rewrites that placeholder, and an outer wrapper's attributes never reach it. From there `embed` renders the cohort name above the rows, so the user opens the round reading which elements it asks about and which are deliberately untouched.

A round that touches everything scores nothing: twenty-five near-identical thumbnails is a screen the user abandons halfway. `doctor` enforces the honest half — a live element with no scoring row **fails** unless the screen declares a cohort.

Startup is not the round. If the cohort is unnamed and no screen is on its way after a dozen tool calls, you are doing infrastructure — say what is blocking.

## Every new implementation gets its own element id

**Redrawing an element under the id the user already ranked leaves them nothing to judge.** A new drawing of the anillo is a new proposal — `cover.ring.kicker.antetitulo-arco`, not another pass at `cover.ring.kicker`. Record it with `decide` as `proposed` at **1 star max**, put it in the cohort, and leave the id it competes with standing until the user picks. Supersede only after they rank the replacement above it.

`doctor` **fails** a screen on which every element is already user-ranked: that round improved the drawing and proposed nothing. Watch for `agent-set 0` in `stats` — with `coverage 100%` it looks finished, but it means the round asked no question.

## Ship the article, not a list of rows

`article --out <screen>.html --cohort <ids> --cohort-name <name>` writes the whole page: a sticky contents bar whose **this round** link is the one call to action, a hero whose thesis is **the question this round asks**, then four zones — **this round** (inverted, the only section asking for anything), **design fundamentals**, **backlog** (with its own second-level sticky nav, since it is the long one), **antipatterns** (last, trash-marked, on muted ground).

**Design fundamentals gathers the direction itself** — core ideas, palette and typography — *whatever their lifecycle state*. A type system is judged as a system: the family pairings, the scale, the faces against the palette. Scattering half of it into a backlog because it is still `proposed` makes exactly the comparison the user needs impossible. Rows run best-score-first inside each foundation. Pass the project's own `--bg/--ink/--accent`: the article is structure only and takes the palette being judged, never one of its own.

**A 👍 is never an antipattern**, whatever became of that particular drawing — the thumb judges the direction, so superseded work the user still likes is held in the backlog, not condemned. Only a 👎, or work turned down without one, goes to the bottom. That section mutes its **ground**, never its rows: the stars and thumbs inside are the only way a rejection gets undone, so they stay at full contrast and stay clickable.

`adopt` **before** `article`, always. The article places each element by its ledger state, so an unadopted click puts a thing the user just endorsed under Antipatterns.

**A section must show its material, not name it.** A "Typography" heading over one scoring row is a list. Record the specimens and the section becomes a design system:

```bash
describe --element palette.family-from-cards --tokens '{"colors":[{"name":"menta","value":"#b2ffc2","role":"grupo"}]}'
describe --element type.dotmatrix --tokens '{"fonts":[{"name":"Matriz 5x7","stack":"ui-monospace","use":"display","variants":[{"weight":700,"size":"40px","use":"titular","sample":"EN VIVO"},{"weight":400,"size":"12px","use":"etiqueta","sample":"rol de lenguaje"}]}]}'
```

**Itemise the faces.** A name and one sample line is a caption — it cannot say which weight sets a heading and which sets a caption, and that is most of what a type system decides. Every `variant` names the **job it does** (`use` is required) and renders at its own weight and size, so the section shows the scale rather than describing it.

Swatches render the real hex, specimens the real face. **Take both from the corpus, never invent them** — a plausible hex is exactly the fabricated evidence the star cap exists to stop, and `describe` has no cap to catch you.

## The strip is a design system, not a list

Rows group themselves by **design-system foundation** — core ideas, colour palette, typography, illustration & texture, composition & layout, copy & voice, motion — read off the element id's own prefix. `palette.family-from-cards` files under colour, `type.bracket-numerals` under typography, `family.mark.dotmatrix` under illustration, anything unrecognised under core ideas. Nothing to configure: **name ids for the foundation they belong to and the system assembles itself.** Each foundation heads its section once per screen.

This is what makes a round rankable as a system rather than a to-do list — the user sees the whole typography together and can say the lettering is working while the palette is not.

**The strip speaks the project's language.** `init --language es` stores it; every later verb reads it from `project.json`, and `--lang` overrides per run. Never hardcode a word into the generator — a screen that mixes an English banner with Spanish rows is the bug this replaced. Only `en` and `es` ship; add a language by adding one dict to `STRINGS`.

## The loop

Each step in full, with its failure modes: [loop.md](references/loop.md).

1. **Frame.** Subject, audience, the artefact's single job, real content, constraints, ranked preferences.
2. **Direct.** Cluster the corpus by recurring *relationships*, not decoration. One-sentence visual thesis from the subject's own materials; one memorable **signature** move. Reject any idea that would fit an unrelated brief unchanged.
3. **Declare.** Palette roles, type roles and scale, grid, hierarchy, imagery register, copy voice, motion — before drawing. `golden_rules.py --scaffold` writes the spec; `--design --min-coverage 0.8` checks it.
4. **Build.** Real content. Preserve every standing element outside the cohort. Never substitute placeholders or emoji for ranked artwork.
5. **Critique.** Render, screenshot, then **run `scripts/measure_screen.js` in the pane and fix every `failingRules` entry before showing the screen** — `unreadable: 0` is a precondition; legibility is measured, never eyeballed. Then compare against brief and corpus at the same scale, and revise anything that reads as a generic default.
6. **Capture.** Record what changed, embed each graphic beside its controls, `publish`, re-run `doctor`, ask for ranks in the same turn.

Plan internally and show the strongest coherent result, not a pile of alternatives — unless comparison *is* the question.

**A score is the input to the next iteration, not the end of the round.** When ranks arrive, redraw in the same session: every 👍 at 0–2 stars is the user saying *the idea is right and your drawing is not* — that is a brief, already written. Report what landed in two lines, then keep going. Ending on a summary and "say the word and I'll open on…" spends the user's scoring on a status update and ships no improvement; they clicked to get better work, not to be asked a question back.

Stop and ask only when the ranks genuinely contradict each other, or when the next move needs something only the user has.

### Redraw the whole cohort, never one element

**A round ships 3–6 redraws in one turn.** Drawing a single element, publishing, and ending the turn to wait for its rank makes the project move one element per session — a thirty-element system then needs thirty sessions, which is the pace the user experiences as *stuck*. Draw the whole cohort, embed every new id, publish once, and ask for the set.

Never end a turn waiting for a rank while work you could already do is sitting in the ledger. **`stats` → `polish` is a standing brief**: those elements are 👍 at 0–2 stars, so the user has already said the idea is right and the drawing is not. Take the top 3–6 and redraw them without asking which.

If the user has scored everything and nothing is proposed, that is not a blocked state — it is the fullest brief you will ever get. `doctor` failing with *"every element on this screen is already user-ranked"* means **go build now**; it is the one red that is never a reason to stop, unlike a dead companion.

Per turn: one `doctor`, one `adopt`, one `article`, one `publish` — and the rest of the turn drawing. If half a turn has gone to harness commands, you are doing infrastructure on the user's time.

## Read the signals literally

**★ 1–5** is graphic execution, ugly → beautiful — never confidence, priority, or whether to keep a thing. **0** is a real score, the worst one; never-touched is `scored: false`. **👍/👎** judges the direction, not the drawing. **☑ completed** is a status, not approval and not a freeze. Full semantics: [companion-contract.md](references/companion-contract.md).

**Taking a thumb back is itself a signal** — "I no longer stand behind this direction", which is not the same as never having judged it. The companion sends it as an explicit `sentiment: null` and `adopt` clears the stored thumb; a plain star click, carrying no sentiment key at all, leaves it alone.

**👍 with 2 stars is the most useful state:** *good idea, badly drawn yet* — improve it. Never drop, supersede or reject for a low score; `stats` reports these as `polish`. A score never changes state; only a verdict does.

## Commands

Every verb takes `--project-root` and answers `--help`. Full list: [commands.md](references/commands.md). Two facts that are semantics, not usage: **`adopt` is the only source of ranks above 1 star**, and **`decide` is capped at 1** — a higher rank comes from a click. Nothing ever disappears; undo a wrong rejection by clicking, never by editing JSON.

**Record a win with `supersede --element <loser> --by <winner>`, never `decide --supersedes`.** The winner is by definition the element the user just ranked, and `decide` writes the element it names through the agent path — 1 star, `source=agent`. Recording the win that way overwrites the click that decided it, and `adopt` will not give it back: it has already consumed that click. `supersede` writes only the loser.

## Rules no tool enforces

- **Every visual move traces to a corpus cluster, verbatim excerpt, or golden rule.** Anything else is inference: label it, 1 star. [anti-slop.md](references/anti-slop.md)
- **Counting markup is not verification.** Assert on what a parser builds, not a string the generator built; screenshot a screen that looks wrong. [verification.md](references/verification.md)
- **The scoring UI belongs to the generator.** Never write scoring CSS in a project; if the strip is wrong, report it and keep designing.
- **Look before extracting.** Screenshots answer most sourcing questions; byte extraction is an escalation the user opts into. [sourcing-policy.md](references/sourcing-policy.md)
- **"Continue prototype" means `/prototype`**, after the cohort is named. This skill supplies the ledger and rows; `/prototype` drives the build.
