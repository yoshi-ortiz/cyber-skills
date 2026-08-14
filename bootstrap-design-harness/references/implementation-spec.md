# Portable Evidence-Backed Design Harness

## Problem Statement

Design agents perform well when a project already contains curated visual context, but hallucinate when inspiration, tooling, domain constraints, and approval state are implicit. Existing harnesses are commonly tied to one repository, one fixed inspiration directory, and frontend-only conformance. They fail to proactively source deterministic art detail and do not carry product, physical-space, copywriting, or mockup-layering context into bounded model work.

The reusable harness must preserve user-owned inspiration exactly, make probabilistic boundaries typed and verifiable, recommend missing authoritative sources before inference, and support iterative critique without becoming a generic workflow engine.

## Solution

Create a portable skill with one standard-library bootstrap/validation script, declarative domain profiles, and context/contract/workflow templates. A caller supplies any source-root path. The skill snapshots it by SHA-256, writes all generated files elsewhere, derives a profile-specific capability matrix and sourcing questionnaire, and validates the source before and after each session.

Agents work in bounded shots and import compact evidence from native tools, MCP adapters, APIs, HTML, images, and per-page PDF derivatives. The same lifecycle handles frontend and physical product design: evidence, structured inference, semantic proposal, exact-excerpt critique, approval, and guarded promotion.

## User Stories

1. As a user, I can select an inspiration directory with any name.
2. As a user, I can keep that directory outside the project.
3. As a user, I can see its exact resolved path in project configuration.
4. As a user, I can trust the harness not to write metadata or derivatives into it.
5. As a user, I can detect any changed, missing, or added source file by SHA-256.
6. As a user, I can use the workflow on a repository that already has context contracts without creating conflicting authority.
7. As an agent, I read repository context before external sources.
8. As an agent, I can select only the domain profiles required for the current project.
9. As an agent, I receive a derived list of required capabilities instead of claiming tools are present.
10. As an agent, I remain in draft when a required adapter has not been evidenced.
11. As a designer, I receive proactive recommendations for likely art-detail sources.
12. As a designer, I am asked to confirm an ASCII/Unicode library when text-based imagery is relevant.
13. As a designer, I can approve, reject, or replace each proposed source.
14. As a designer, I do not need to know a library name before the agent raises the category.
15. As a maintainer, every fetched source has a primary locator, license, version or retrieval date, and hash.
16. As a maintainer, search snippets and model memory cannot masquerade as authoritative sources.
17. As an agent, I can ingest images without embedding raw bytes in model context.
18. As an agent, I can derive one deterministic page image and normalized text record per PDF page.
19. As an agent, I can fetch HTML for evidence without executing it.
20. As an agent, I can ingest APIs using bounded bodies and compact excerpts.
21. As an agent, I separate visible observations from interpretation.
22. As an agent, I reuse validated inference by request fingerprint.
23. As a user, I can see hard budgets for tools, URLs, visuals, extracted text, and model output.
24. As a user, budget exhaustion creates a new shot rather than silently increasing cost.
25. As a frontend designer, I can require DevTools, Playwright, Lighthouse, responsive screenshots, and Storybook MCP evidence.
26. As an art director, I can pin icon, illustration, texture, type, and composition sources.
27. As a motion designer, I can capture choreography and reduced-motion behavior as data.
28. As a product designer, I can capture use, ergonomics, materials, manufacturing, assembly, and regulatory context.
29. As a spatial designer, I can distinguish measured dimensions from inferred dimensions.
30. As a spatial designer, I can record scale, units, clearances, materials, lighting, viewpoints, and accessibility constraints.
31. As a copywriter, I can separate sourced claims from stylistic inspiration.
32. As a copywriter, I can record audience, promise, hierarchy, voice, legal, and localization constraints.
33. As a mockup designer, I can reproduce an output from an ordered, hashed layer manifest.
34. As a mockup designer, I can pin canvas, transforms, masks, blending, color profile, and renderer version.
35. As a user, every response I give becomes critique evidence.
36. As a user, vague feedback is preserved verbatim before being translated into a testable constraint.
37. As a user, mixed or negative feedback cannot be mislabeled as approval.
38. As a user, every proposal asks explicitly for approval.
39. As a release owner, automated checks cannot create user approval.
40. As a release owner, promotion requires unchanged sources, current lineage, required tools, domain conformance, and positive-only critique.

## Implementation Decisions

1. Use one Python standard-library script with `init`, `validate`, and `self-test` commands.
2. Require `--source-root`; provide no fixed-name default and no automatic discovery.
3. Resolve paths before comparing boundaries and reject generated output inside the source root.
4. Reject symlinks rather than following them.
5. Record deterministic manifests without volatile timestamps.
6. Generate under `spec/design-harness/` and merge into existing authority when necessary.
7. Keep profiles declarative and share one state machine.
8. Generate capability requirements from profiles; adapters are filled only by preflight evidence.
9. Generate confirmation questionnaires from deterministic profile recommendations.
10. Fetch recommended sources only after explicit confirmation.
11. Store raw external material and derivatives outside the immutable source root and committed compact context.
12. Default to four external tool calls, two URLs, four visual sources, 24,000 extracted characters, and 1,200 output tokens per shot.
13. Represent mockups with ordered layer manifests rather than ad hoc image editing instructions.
14. Keep promotion a separate record/state guarded by source, lineage, critique, and conformance checks.

## Testing Decisions

The highest-value seam is a disposable end-to-end fixture with a deliberately nonstandard source directory name. The test writes text and image fixtures, snapshots their hashes, bootstraps physical-space, art-direction, and mockup-layering profiles, validates all generated contracts and capability coverage, confirms proactive ASCII/spatial/layering questions, and proves the source manifest is byte-identical afterward.

Skill metadata receives the standard skill validator. Individual Markdown template sentences do not receive isolated unit tests; the acceptance seam checks their required invariants. Project-specific browser, visual, accessibility, spatial, and renderer checks remain downstream conformance tests selected by profiles.

## Out of Scope

- A generic MCP client or workflow engine.
- Automatic installation of tools or external libraries.
- Fetching unapproved supplemental sources.
- Mutating or reorganizing user inspiration.
- Automatic CSS, HTML, animation, copy, CAD, or final mockup generation.
- Universal sentiment analysis for critique.
- Replacing project-specific design systems or release pipelines.
- Guaranteeing pixel-identical rendering across unpinned renderers or color-management stacks.

## Further Notes

The governing principle is minimum necessary autonomy inside maximum legible control. Determinism applies to intake, derivation, manifests, routing, budgets, and validation; visual interpretation remains probabilistic but bounded by evidence and schemas. New profiles should extend the shared lifecycle only when an actual project demonstrates a missing context or conformance category.

