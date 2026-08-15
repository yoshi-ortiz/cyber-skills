---
name: aesthetic
description: Bootstrap a deterministic, evidence-backed design harness for a design project, then serve as its resumable context. Use when a project needs read-only inspiration intake, hashed image/PDF evidence, bounded design loops, a star-ranked decision ledger that survives session boundaries, companion feedback adoption, or art-direction, frontend, product, physical-space, copywriting, motion, composition and mockup-layering workflows. Also use when resuming design work on a project that already has `spec/design-harness/`, so prior decisions are honoured rather than rebuilt.
---

# Aesthetic

Create the least-agentic workflow that can move a project from evidence to an approved design output without inventing context.

This skill has two modes. Establish which applies before doing anything else:

- **Not yet bootstrapped** (no `spec/design-harness/`) — generate the harness. Follow *Start*.
- **Already bootstrapped** — the harness *is* your context. Do not re-derive it and do not re-bootstrap over it. Follow *Resuming an existing harness*.

## Resuming an existing harness

```bash
python3 scripts/bootstrap_harness.py validate --project-root /absolute/project
```

Then read `spec/design-harness/DECISIONS.md` **before proposing anything**.

Every element under Standing is binding. Each carries a 1–5 star rank set by the user: higher rank wins when two elements conflict, and a tie is a question for the user, not a judgement call for you. Agent inference is recorded at one star and never outranks a user decision.

Work in small iterations. Name the design elements the iteration touches, change only those, carry the rest through untouched. Rebuilding a surface from scratch silently drops every element that surface carried — if a change would drop one, stop and record the supersede first:

```bash
scripts/bootstrap_harness.py decide --project-root . \
  --element cover.layout.single-column --verdict approved --stars 4 \
  --evidence "user: 'drop the second column'" \
  --supersedes cover.layout.two-column
```

Capture feedback as it arrives, not at the end. Feedback set in a companion is adopted, never retyped:

```bash
scripts/bootstrap_harness.py adopt --project-root . \
  --companion-ledger .superpowers/brainstorm/decisions.jsonl
```

Interactions with no design-element id are skipped and reported — ask the user for the id rather than inventing one. Conversation history is not a record: an unrecorded decision is lost at the next session boundary, and losing one is a defect, not an inconvenience.

## Avoiding slop

Read [anti-slop.md](references/anti-slop.md) before generating. In short: every visual move traces to a corpus cluster or a verbatim excerpt; anything else is inference, labelled and ranked one star. Compose from elements already in standing rather than inventing markup. Specify behaviour — narrow and wide containers, long content, empty states, keyboard focus, reduced motion — not just appearance. Keep the diff small enough that the user can disagree with a specific part of it.

## Companion feedback

The harness ships no companion and requires no particular one. Any browser surface works if it meets [companion-contract.md](references/companion-contract.md): a durable ledger outside the session directory, design-element ids on every control, and two signals per element — a 1–5 star rank and a like/dislike.

**Stars carry strength, sentiment carries direction.** `stars: n` approves at rank *n*; `like` approves, `dislike` rejects, each with a fixed default rank when no star is given. Replay is ordered by timestamp, so `adopt` is idempotent.

Never hand-author element ids into a screen — that is how ids drift from the ledger. Generate them, and pass the project palette so the controls are not styled by defaults:

```bash
scripts/bootstrap_harness.py controls --project-root . --out controls.html \
  --bg "#f9e7b5" --ink "#111" --accent "#d9482a"
```

**Rank the graphic, not the id.** A star beside `cover.ring.kicker` is a guess unless the thing itself is on screen, so attach the graphic when you record the decision:

```bash
scripts/bootstrap_harness.py decide --project-root . \
  --element cover.ring.kicker --verdict proposed --stars 3 \
  --evidence "user: 'kinda fine'" --preview shots/cover-ring.svg
```

Previews are hash-pinned: if the graphic changes, `validate` fails until it is re-recorded, because a preview that changed is a preview nobody reviewed. Elements with no preview render as "sin gráfico" — the harness says so rather than faking one.

The markup covers only elements in standing and is byte-stable for a given ledger. If the companion cannot meet the contract, say so and use `decide` in the terminal instead of remembering what was clicked.

## Start

1. Read the project's agent entrypoint and existing context/contracts/workflows before editing.
2. Require the user or project to identify the inspiration source path. Never assume its directory name.
3. Resolve the exact source path and treat it as read-only. Do not rename, move, delete, normalize, optimize, or write metadata into it.
4. Select only the domain profiles needed now. Read [domain-profiles.md](references/domain-profiles.md) for non-frontend work.
5. Preflight the design tools before the first shot, then record what you actually observed. See [design-tools.md](references/design-tools.md):

```bash
python3 scripts/bootstrap_harness.py preflight --project-root /absolute/project \
  --available image,pdf,repository --missing playwright
```

A capability never preflighted stays unavailable. Never narrate a tool you did not run.

6. Run the bootstrap script from this skill directory:

```bash
python3 scripts/bootstrap_harness.py init \
  --project-root /absolute/project \
  --source-root /absolute/inspiration-source \
  --profiles frontend-layout,art-direction
```

Generated files live under `spec/design-harness/`. If the project already has authoritative context files, merge the generated invariants into them instead of creating competing authority.

## Source Safety

- Require an explicit `--source-root`; accept any directory name.
- Resolve and record the absolute path, but never copy it into a fixed project directory.
- Snapshot path, byte size, media type, and SHA-256 for every regular file.
- Reject symlinks and unreadable files instead of following or changing them.
- Run `validate` before and after any design session. A changed or missing source hash blocks inference and promotion.
- Store generated derivatives only in the project cache or evidence directory.
- Ask for explicit approval naming the exact path before any action that could mutate a source root.

## Workflow

Use `draft -> evidence-ready -> proposed -> revision-requested -> proposed -> approved -> promoted`.

### Bootstrap and preflight

- Generate project context, contracts, workflow, capability matrix, source manifest, and questionnaire.
- Inspect repository evidence before external research.
- Record actual adapters; never claim an MCP server or local tool is available without preflight evidence.
- Missing required capabilities keep the run in `draft`.

### Confirm deterministic sourcing

Generate the questionnaire before fetching supplemental material. Recommend likely art-detail inputs proactively—ASCII/Unicode libraries, icon sets, motion references, composition systems, type sources, materials, spatial standards, copy evidence, or mockup renderers—when the selected profile or source manifest indicates the need.

Ask the user to confirm or reject each recommendation. Do not make them name the library first. After approval, pin the authoritative URL or package version, license, retrieval time, and content hash. Follow [sourcing-policy.md](references/sourcing-policy.md).

### Ingest evidence

- Images: hash original bytes; derive bounded deterministic metadata before vision; group no more than four new images per vision call.
- PDFs: pin renderer and extractor versions; create one image hash and one normalized text hash per page; keep page order; never send the full PDF when page evidence suffices.
- HTML/API: fetch without executing; cap bytes and excerpts; store provenance and raw content outside committed context.
- Physical product/space: record units, scale, dimensions, materials, lighting, viewpoints, tolerances, and manufacturing or accessibility constraints.
- Copy: separate user-provided claims from researched claims; retain audience, hierarchy, voice, proof, legal, and localization constraints.
- Mockups: use an ordered layer manifest with source hashes, transforms, masks, blend modes, color profile, output size, and pinned renderer version.

### Bound model work

Build requests from hashes, compact excerpts, selected constraints, semantic axes, and schema references only. Keep visible observation separate from interpretation. Require structured output, a request fingerprint, one observation per source, and confidence. Reuse validated inference by fingerprint at zero new-source cost.

Use short shots. Start with four external tool calls, two URLs, four new visual sources, 24,000 extracted characters, and 1,200 output tokens unless the generated contract lowers them. Never silently raise a limit; create another shot.

### Iterate and promote

- Treat every user response as critique evidence, even when vague or poorly framed.
- Preserve exact positive and negative excerpts, then translate them into testable constraints.
- Write every accepted excerpt to the ledger with `decide` in the same turn you receive it. An excerpt that stays in the conversation is not retained.
- Ask for a star rank per design element alongside approval; rank is the ordering signal when elements conflict.
- Mixed or negative critique requests revision. Positive-only critique may approve.
- Always ask for approval after a proposal.
- Automated checks cannot manufacture user approval.
- Promotion requires current lineage, unchanged source hashes, a ledger that validates, required capability evidence, and passing domain-specific conformance.

## Validation

Run the highest-level seam:

```bash
python3 scripts/bootstrap_harness.py validate --project-root /absolute/project
```

For skill changes, also run:

```bash
python3 scripts/bootstrap_harness.py self-test
python3 /path/to/skill-creator/scripts/quick_validate.py /path/to/aesthetic
```

The self-test uses a nonstandard source directory name, bootstraps a disposable fixture, verifies generated contracts and recommendations, and proves every source hash remains unchanged.

## Resources

- [domain-profiles.md](references/domain-profiles.md): required context and conformance by design domain.
- [sourcing-policy.md](references/sourcing-policy.md): proactive but approval-gated deterministic sourcing.
- [implementation-spec.md](references/implementation-spec.md): architecture specification and acceptance seam.
- `assets/spec/`: boilerplate copied into each project.
