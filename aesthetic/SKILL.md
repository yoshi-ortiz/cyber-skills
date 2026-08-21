---
name: aesthetic
description: Use when a multimodal corpus must become grounded, ranked art direction and a responsive editorial board. Also use to continue or critique that design sprint. Not for generic UI coding without references.
---

# Aesthetic

Turn the corpus into a decision before drawing. The default path is one closed sequence.

```text
inspectable corpus -> three grounded directions -> agent rank -> selected direction -> editorial sprint -> board
```

User execution stars never choose the art direction. Agent rank never enters `decisions.json`.

## Pick the mode

- `observe @/corpus` starts a new editorial sprint from the named folder.
- `continue` opens a valid sprint, completes one work item, and advances its state.
- `critique` judges the selected direction and current execution without changing rank, stars, or work state.

If the user supplies a corpus without a verb, use `observe`. If the user supplies neither, use `continue` only when `spec/design-harness/art-direction.json` exists. Otherwise ask for the corpus path.

## Intake

Run this first for `observe`.

```bash
python3 <skill>/scripts/editorial_workflow.py observe \
  --project-root . --source-root <absolute-corpus-path>
```

Read `spec/design-harness/corpus.json`. Open every item listed in `items`. Use the image viewer for images. Read text from `inspectPath`. A hash proves which file you opened. It is not visual or editorial evidence.

Do not fork on `INDEX.md`. A corpus with text and images needs one fused interpretation. Mark every supported item as observed or omit it with a concrete reason.

## Ground and rank

Read [editorial-workflow.md](references/editorial-workflow.md). Write one temporary direction-set JSON file in its exact shape.

Produce exactly three structurally different directions. Each direction needs a thesis, one signature move, a complete visual system, cited observations, a five-part scorecard, and an agent-rank rationale. The selected direction must cite image and text evidence when both exist.

Score corpus fit, subject specificity, system coherence, distinctiveness, and execution leverage from 1 through 5. Rank the directions 1 through 3. Do not average blindly. Explain the deciding tradeoff in the rank rationale.

Reject a direction when its thesis could describe an unrelated product, its signature move is decoration, or its evidence repeats filenames without an observation.

Turn only the selected direction into sprint work. Each item needs a concrete deliverable, positive points, and an observable acceptance check. Park alternate directions outside the board.

## Publish

Run the compiler only after you inspected the corpus and wrote the direction set.

```bash
python3 <skill>/scripts/editorial_workflow.py publish \
  --project-root . \
  --directions /tmp/aesthetic-directions.json \
  --out design/editorial-board.html
```

`publish` fails before it writes when inference is incomplete. Fix the direction set. Never bypass validation and never fall back to `bootstrap_harness.py article`.

## Editorial board

The output has one selected direction, a compact ranked comparison, a points burndown, and four columns named Backlog, Doing, Review, and Done. It reads user-set execution feedback from the existing ledger without changing it.

Open the served project after a successful publish.

```bash
python3 <skill>/scripts/bootstrap_harness.py open --project-root .
```

Show the URL and a screenshot. Check both desktop and narrow layouts. If the direction is generic, the hierarchy collapses, content clips, or interaction fails, the run is not done.

## Continue one item

Validate before work.

```bash
python3 <skill>/scripts/editorial_workflow.py validate --project-root .
```

Read the selected direction, the event history, the current board, and the latest execution preview. Pick one item from Doing, then Review, then Backlog. Work only on that deliverable.

Move the item when its acceptance evidence exists. Use a stable event id so a retry changes nothing.

```bash
python3 <skill>/scripts/editorial_workflow.py advance \
  --project-root . --item <work-id> --to <backlog|doing|review|done> \
  --event-id <stable-event-id>

python3 <skill>/scripts/editorial_workflow.py output \
  --project-root . --out design/editorial-board.html
```

Moving an item out of Done raises remaining points. That is a revision, not a broken chart.

## Critique

Read the corpus evidence, selected direction, board, and current screenshots. Judge the work against the direction's thesis, signature move, visual system, and item acceptance checks. Name the strongest mismatch first. Do not change files, events, agent rank, or user execution stars.

## Quality gate

A run succeeds only when all checks pass.

1. The selected direction uses observations from every available supported medium.
2. The three candidates differ in structure, not only color, typeface, or wording.
3. The selected signature move is visible in the current execution.
4. Every sprint item can be accepted with a screenshot, measurement, copy check, or interaction check.
5. The board is under 40 KB, needs no JavaScript, and works at desktop and narrow widths.
6. The user has a current screenshot and one clear execution decision to make.

Automated checks prove the workflow is consistent. They do not prove the design is good. Look at the result.

## Write boundary

During a design run, write project screens and `spec/design-harness/` only through the workflow commands. Treat the corpus and this skill's `scripts/`, `references/`, and `companion/` as read-only.

To change this skill, read `AGENTS.md`.
