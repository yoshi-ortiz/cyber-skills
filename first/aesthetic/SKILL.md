---
name: aesthetic
description: Design and art direction that reads as intentional, not templated. Use to start, continue, or critique visual work. Grounds direction in design fundamentals, and folds in a multimodal corpus and user sentiment when they exist, producing ranked decisions and an editorial burndown.
---

# Aesthetic ranking

`continue`, `critique`, `prototype`, and `observe` are context clues. A
requested diagram, scene, or illustration routes to
[text-to-graphics.md](references/text-to-graphics.md).

## Route before designing

Read [user-communication.md](references/user-communication.md). Run before every Loop step after opening the companion:

```bash
python3 <skill>/scripts/assistant_app.py --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl \
  --invocation <skill@timestamp> --turn "<latest turn>"
```

With `scene-spec.json` or `graphics-manifest.json`, run:

```bash
python3 <skill>/scripts/text_to_graphics.py --project-root . status
```

Do exactly the returned action. This route outranks generic art-direction
inference. Do not replace a passing graphic; reuse it from `shots/` first.

Choose chat language from the user's latest words and mirror their dialect in
project-authored publishing copy. `project.json.language` translates companion
controls; when it is set, every string you author into the screen -- round
question, element titles, descriptions, status -- is written in that same
language. One language per screen. An English `--asks` inside a Spanish
companion is the mixing this rule exists to stop.

Keep the established article: hero, graph, TOC, four sections, progress chart. Never replace it with a kanban or second site.

## Start

Open the companion first.

```bash
python3 <skill>/scripts/bootstrap_harness.py open --project-root . \
  --status "<emoji + user-language description of the first real design task>"
```

Follow `user-communication.md` for the URL-first reply with no preamble:

```text
🔗 <full URL>
🔑 <value after ?key=>
👀 <user-language review action in the publishing-copy register>
```

Update status when visible activity changes.

With a reference folder, read images and text together:

```bash
python3 <skill>/scripts/editorial_workflow.py observe \
  --project-root . --source-root <absolute-reference-folder>
```

Open items; metadata is not visual evidence. Without a folder, seed from a
named profile and ask for references without blocking:

```bash
python3 <skill>/scripts/editorial_workflow.py seed --project-root . \
  --profile <domain-profiles.md name> --subject "<what this is>"
```

## Read the user first

Record chat constraints in the brief before inference; user words outrank
references and doctrine.

```bash
python3 <skill>/scripts/brief_workflow.py answer --project-root . \
  --event-id <stable-id> --at <ISO-8601> --id <brief-field> --answer "<user words>"
python3 <skill>/scripts/direction_context.py --project-root . \
  --out /tmp/aesthetic-context.json
```

Read that context before doctrine. With ranked elements, read
[sentiment-analysis.md](references/sentiment-analysis.md). Never collapse stars,
thumbs, lifecycle, or missing feedback into one score.

Classify corpus before inference. `reference+pursue` may source a new direction;
`reference+avoid` is counterevidence; `attempt+refine` is a near-hit to edit or
reuse before spending another shot; constraints carry scene truth; derivatives
are audit evidence, never an original source. If `status` returns `refine`, do
that first. Read [text-to-graphics.md](references/text-to-graphics.md) for the
role/stance matrix and staleness rules.

## Infer and rank art direction

Read [golden-rules.md](references/golden-rules.md), [loop.md](references/loop.md)
for failed rounds, [interpret-art.md](references/interpret-art.md) for ambiguous
evidence, and [anti-slop.md](references/anti-slop.md) at critique.

Declare hierarchy, grid, type roles, color relationships, image register,
motion purpose, one subject-specific signature, and the question tested.

Select one evidence-backed hypothesis and a 3–6 element cohort. Reject a thesis
that fits an unrelated product unchanged.

In comparison rows, use `null` for `corpusFit` when there is no real corpus and
for `preferenceFit` when the user has not ranked anything. Missing evidence is
not a neutral score and never becomes a model-authored 3, 4, or 5.

Copy every `briefConstraints` item into the direction spec with its impact.

```bash
python3 <skill>/scripts/editorial_workflow.py direction --project-root . \
  --spec /tmp/aesthetic-art-direction.json
```

Fix a rejected spec; never bypass the gate.

## Scope the editorial burndown

Read [editorial-workflow.md](references/editorial-workflow.md). Then append scope
changes; every element has one primary epic and retrying an event id is a no-op.

## Build one testable cohort

Draw real HTML/CSS and inspect the PNG at desktop and narrow widths. Judge the
render using [fundamentals](references/graphic-design-fundamentals.md). Preserve
ranked elements outside the cohort; new proposals use new ids and start unscored.

```bash
python3 <skill>/scripts/golden_rules.py --design spec/design-harness/candidate.json --min-coverage 0.8
```

Never invent SVG paths. Follow [asset-sourcing.md](references/asset-sourcing.md).

Generated graphics are proposals, not silent assets: record the scene element
with its preview as an unscored decision and include it in the article cohort so
the user can rank the visual decision.

Require 4.5:1 text and 3:1 control contrast. Companion chrome follows
[companion-contract.md](references/companion-contract.md).

## Publish the established article

```bash
python3 <skill>/scripts/deliver.py --project-root . \
  --out design/aesthetic-ranking.html --cohort "<element ids>" \
  --round-label "<object>" --asks "<one plain design question>" \
  --assessments /tmp/proposal-assessments.json \
  --idle-text "<user-language request to review the new designs>" \
  --agent "<App | Model>" --agent-url "<task deep link>" \
  --invocation <skill@timestamp>
```

One call, because dropping either of its last two steps is how a user gets a
link to nothing. It prints `url`, `key`, `ask`, and every absolute review image
path; lead the reply with exactly those. Delivery accepts only subject-specific
rankable proposals.

## Continue and critique

On continuation order: like + low stars, dislike + high stars, unresolved work,
unscored designs, then exploration. Change one 3–6 element cohort.

On critique, name the strongest mismatch first. Do not mutate evidence.

## Done gate

A run is complete only when:

1. the render carries declared hierarchy, grid, type, color, and signature;
2. it remains subject-specific without the logo;
3. inference cites visible evidence and counterevidence;
4. rank, sentiment, lifecycle, and missingness remain independent;
5. contrast passes and graphics have provenance;
6. article, scoring, burndown, slideshow, and responsive layout work;
7. the user receives URL, key, review request, and review images.

Passing checks while looking templated is failure.
