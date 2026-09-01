# Epic 3, concluded by one Shot

> Supersedes the ordering of Epic 3 in
> [2026-08-31-release-ready-tokens-qa-aesthetic.md](2026-08-31-release-ready-tokens-qa-aesthetic.md).
> Task content is unchanged. What changes is the sequence and what blocks what.

**Goal:** Fire one Shot, get an explicit L3 verdict on it, and release only if
that verdict is `accepted`.

**Why a single Shot.** Epic 3 has one irreducible step and three enabling ones.
The irreducible step is a human looking at a hero image and a thumbnail and
saying whether they are good. Everything else is machinery that exists to make
that judgement trustworthy. The plan is therefore ordered so the judgement
happens as early as it honestly can.

## The ordering change, and the argument for it

The source plan runs Epic 3 as R-15 split, then proof, then the Shot, then
release. This plan runs proof, then the Shot, then R-15, then release.

R-15 is modularity debt. `bootstrap_harness.py` is 216,757 bytes against a
30,000 byte cap, and three other files are over. None of that changes a single
pixel the user judges. Splitting it first spends a large mechanical effort
before the only question that can invalidate the work has been asked.

The source plan's own reason for putting R-15 first is a conflict flag, that
R-15 and the proof work both touch `first/aesthetic/scripts/`. That is an
argument against running them **concurrently**, which this plan also refuses.
It is not an argument about order.

The one real cost of deferring R-15 is that the board cannot reach 27/27 until
it lands, because `contracts-budget` is red precisely because of those four
files. That matters for the release and not for the Shot.

## Preconditions, all currently true

- Tokens QA control plane is complete. Six verbs, v2 contract, bounded
  correction bundles.
- The board is 26/27, with `contracts-budget` the one deliberate red.
- The rejected baseline `.audit/shots/20260901T025137Z-a7052318.json` is
  intact at sha256 `a481fa5a…` and refuses writes.
- `correction` emits the bounded bundle against that baseline and nothing
  consumes it yet.

## Phase 0. Establish a known starting state

The working tree carries uncommitted changes to `design/`, `spec/design-harness/`,
and four files under `first/aesthetic/` from before this work began. A Shot
recorded on top of unknown edits proves nothing about what produced it.

Decide per file whether it is part of the round or leftover, commit or revert
accordingly, and record the resulting HEAD as the Shot's provenance. This is
not optional bookkeeping. `provenance` is a required field of the contract.

## Phase 1. Make the flow demand proof it does not currently demand

Source plan Task 5. The single fact that justifies it, verified today:
`graphics_flow.FLOW` falls through to `done` when every structural gate passes,
with no browser render and no thumbnail anywhere in the table.

- Add `apply-correction` and `verify-delivery` to `FLOW` ahead of `done`.
- `proof_key(artifact_hash, viewport, renderer_version, assets_hash, kind)`
  makes a cached render reusable only when every declared input is identical.
- `review_delivery.py` emits proof descriptors for `hero-browser-render` and
  `ranking-thumbnail` from real renders.
- `direction_context.py` admits the bounded correction bundle ahead of optional
  doctrine, so a correction outranks taste guidance.
- `deliver.py` records the Shot through the CLI at the delivery boundary.

**Exit gate.** A structurally green state with no visual proof returns
`verify-delivery`, never `done`. Changing viewport, CSS, or renderer version
invalidates the proof key.

## Phase 2. The Shot

Source plan Task 6. This is the deliverable the whole epic exists for.

- Feed the bounded correction from the rejected baseline through refine.
  The exact words are on record and say the round did not improve the graphics
  or the thumbnail.
- Change the hero composition and the thumbnail crop or scale. Card chrome and
  harness plumbing do not count, and the eval must be able to tell the
  difference.
- Render at the declared desktop viewport and the exact thumbnail dimensions.
  Inspect the rendered artifacts, never the source HTML.
- Record the candidate, compare against the baseline, and assert it stays
  `pending` while passing L1 and L2.
- Present it. Attach the verdict verbatim.

**Exit gate.** A candidate carrying fresh hero and real thumbnail proof, held
at `pending`. Machine proof must not be able to accept it. That property is
already enforced by the control plane and this is its first real exercise.

**If the verdict is rejection or correction**, repeat Phase 2 only. The control
plane does not change. That containment is the point of the bounded bundle.

## Phase 3. Repay R-15

Source plan Task 8, unchanged, and now unblocked by a verdict rather than
blocking one. Behaviour-preserving, characterization-tested, four files under
30,000 bytes.

The source plan's success criterion of "51/51" matches nothing measurable.
Today the suite is 502 tests, contracts covers 53 directories, and
`first/aesthetic/scripts/` holds 37 files. Replace it with the two real
conditions. Every existing test still passes, and
`contracts.py --only budget` is green.

## Phase 4. Release

Source plan Task 9, with three corrections.

- Step 4 requires 23/23. The board is 27 gates now. Require **27/27**, which is
  reachable only once Phase 3 lands.
- Fold in the publication leak found during the readiness review.
  `TODOS.md` and `startups_hackathon_schedule_methodology.md` are untracked
  working-tree files and both ship in the `main` and `alpha` trees, because
  `publish.py` copies untracked files and `fog.py` does not name them. A user
  installing the skill currently receives a hackathon schedule.
- Promotion to `main` happens only on explicit L3 `accepted` with no hard veto.

## What this plan refuses

- Running R-15 and the proof work concurrently. Same directory, guaranteed
  conflict.
- Any automated taste scoring. Machine checks prove identity and
  renderability, never acceptance.
- Redesigning the ranking page. Only the thumbnail proof the Shot needs.
- Promoting to `main` on green gates alone. Green is not a verdict.
