# The loop, in full

`SKILL.md` carries the six steps in one line each. This is what each one means
when it is done properly. Read it when starting a project, when the thesis feels
thin, or when a screen came back scoring badly and you cannot say why.

## 1 · Frame

Pin the subject, the audience, the artefact's single job, the real content, the
constraints, and the user's ranked preferences. Infer what the evidence supports
rather than interviewing: ask only for a missing choice that would change the
result, and ask it once.

An artefact with two jobs has none. If the brief names two, say which one the
composition will serve and what the other gets instead.

## 2 · Direct

Cluster the corpus by recurring **relationships** — how a mark sits against its
ground, how a grid breaks, what repeats at what interval — never by isolated
decoration. Three references sharing a colour is a coincidence; three sharing a
figure-ground inversion is a direction.

Write a one-sentence visual thesis rooted in the subject's own materials,
language, tools, history or environment. Choose a movement, and one memorable
**signature** move that a viewer could describe from memory.

**The test:** if the thesis would fit an unrelated brief unchanged, it is not a
direction, it is a style. Reject it and go back to the corpus.

## 3 · Declare

Specify the system before drawing anything:

| Slot | Declared as |
| --- | --- |
| palette | roles — ground, ink, accent, and what each is *for* |
| type | roles and a scale, not a list of fonts |
| grid | the module, the gutter, and the rule for breaking it |
| hierarchy | primary → secondary → tertiary, named per surface |
| imagery | register (icon / index / symbol) |
| copy | voice, and the words that are never used |
| motion | what moves, why, and the reduced-motion answer |

Spend boldness on the signature; keep its supporting cast disciplined. A design
that is bold everywhere reads as noise, and the signature disappears into it.

```bash
python3 scripts/golden_rules.py --scaffold cover.ring.kicker > candidate.json
python3 scripts/golden_rules.py --design candidate.json --min-coverage 0.8
```

Coverage measures determinism, not beauty: a fully declared design can be wrong,
but it repeats, so it can be fixed. An undeclared decision varies per run and can
only be re-rolled. Checkable rules and directed doctrine — Albers, Itten,
Müller-Brockmann, Bringhurst, Gestalt, Peirce, movement — in
[golden-rules.md](golden-rules.md).

## 4 · Build

Load `modern-web-guidance` before writing the comp's CSS; take the pattern it
names instead of inventing one.

**Draw the comp in HTML/CSS, then render it.** Never hand-author SVG. Authoring
an SVG means authoring a coordinate system you never see, which is the one job
the model is worst at -- the ledger carried 59 such previews holding 6352
`<rect>` and 15 `<path>`, 34 of them with a near-zero opacity somewhere, and a
session once shipped a comp wrapped in a nested `opacity="0.13"` so the whole
of the next round went on repairing it instead of improving the design.

```bash
python3 scripts/bootstrap_harness.py shoot --html comp.html --out shots/<element>.png
python3 scripts/bootstrap_harness.py decide --element <id> --preview shots/<element>.png ...
```

`shoot` renders at 510px wide (Chrome, falling back to QuickLook) and **refuses
a comp that is blank or has no contrast against its own ground** -- measured on
the pixels, so "nearly invisible" cannot reach the ledger. `decide --preview`
re-checks every PNG for the same reason. If QuickLook is doing the rendering it
fits the page into a square, so the comp must read without depending on its own
aspect ratio.

Real content, never lorem and never emoji standing in for ranked artwork.
Preserve every standing element outside this round's cohort — an element the user
ranked is not yours to restyle because it happened to be nearby.

Match craft to the thesis. Expressive work needs enough of itself to land;
restrained work has nowhere to hide, so spacing, alignment and finish have to be
exact.

## 5 · Critique

Render and screenshot, then run `scripts/measure_screen.js` in the pane and fix
every `failingRules` entry **before** showing the screen. `unreadable: 0` is a
precondition, not a target: screens have twice shipped with body text at 1.1:1
that no reading of the markup could have caught, because a block painted a ground
and let its ink inherit the companion's frame.

Then compare against brief and corpus **at the same scale** — a thumbnail hides
exactly the failures a full-size view reveals, and vice versa. Ask of each:
hierarchy, composition, rhythm, specificity, coherence. Cut decoration with no
job. If it reads as a generic default, or the signature is not immediately
legible, revise before showing it.

## 6 · Capture

`open` already put the URL in chat. If `publish` reports a different session
directory it has already moved the screen there -- the companion restarts into
a new one and no caller can guess it.

Record what changed, embed each graphic beside its controls, `publish`, and ask
for ranks in the same turn. After the first proposal this session, run
`doctor --quiet` in the background -- it is a health check, not an opening act,
and its ok/FAIL lines do not belong in chat. Feedback that is not adopted in the
turn it arrives is lost at the next session boundary.

Next round, improve liked-but-low-scoring (`polish`) work first. A low star with
a thumb up is the clearest instruction the ledger can carry: the idea is right
and the drawing is not there yet. Never replace it.

`article` now **refuses** a round that ignores this, because for six sessions it
was a sentence here and nothing else: eighteen liked-and-low elements sat
untouched while eleven fresh siblings were proposed over them, and the mean
score fell to 1.56. It also refuses two redraws of the same incumbent in one
round — a second variant is wallpaper, not a second option. Redraw as
`<liked-low-id>.<slug>` so the pair is scored together, or name the id itself to
re-ask.
