---
name: aesthetic
description: Create or extend a portable, evidence-backed design harness for a new project. Use when a project needs configurable read-only inspiration intake, deterministic image/PDF or web evidence, bounded AI design loops, proactive art-detail sourcing, iterative critique, or frontend, product, physical-space, copywriting, motion, composition, and mockup-layering workflows.
---

# Aesthetic

Create the least-agentic workflow that can move a project from evidence to an approved design output without inventing context.

## Start

1. Read the project's agent entrypoint and existing context/contracts/workflows before editing.
2. Require the user or project to identify the inspiration source path. Never assume its directory name.
3. Resolve the exact source path and treat it as read-only. Do not rename, move, delete, normalize, optimize, or write metadata into it.
4. Select only the domain profiles needed now. Read [domain-profiles.md](references/domain-profiles.md) for non-frontend work.
5. Run the bootstrap script from this skill directory:

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
- Mixed or negative critique requests revision. Positive-only critique may approve.
- Always ask for approval after a proposal.
- Automated checks cannot manufacture user approval.
- Promotion requires current lineage, unchanged source hashes, required capability evidence, and passing domain-specific conformance.

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
