---
name: first
description: Capture project owner intent and sketch creative directions. Use first or f, with f take note for goals and instincts or f design for mockup exploration.
disable-model-invocation: true
exits: build, check, fix
aliases:
  - f
---

# First

Take note, then sketch. Start from the project owner's words and existing work.
Aesthetic is excluded from this route until it passes an unslop review and the
owner explicitly re-enables it. Complete these steps using available tools.

| Request | Sequence |
| --- | --- |
| `first` | Take note, then Design when creative direction is relevant |
| `first take note` | Capture intent and align the bounded outcome to Big Bang |
| `first design` | Read existing intent, fill material gaps, then explore mockups |

## Bootstrap and index

For repository bootstrap, call [Kit](../kit/SKILL.md) before implementation.
Derive the repo domain from the owner's requirements and `docs/WORK_STYLE.md`;
pass explicitly named catalog domains to Kit, or sync the existing selection.
If no selection exists, resolve the domain with the owner. Record the selected
domain and Kit's actual result; tool absence is an explicit setup gap.
A note-only request records this setup requirement for the bootstrap handoff.

Index domain concepts and software stack knowledge separately in the target's
`docs/knowledge/index.md`, reusing canonical indexes when present. Each pointer
names its leading word, loading condition, source and trust boundary. Use
[Knowledge](knowledge/SKILL.md) for cited source notes; derive stack versions
from the manifest rather than repeating them in the index.

For an agent project, make the collection's
[agent knowledge index](../knowledge/index.md) available through a conditional
pointer in the target index. In this checkout it resolves to
`/Users/bebote-pro/Development/cyber-skills/knowledge/index.md`. Resolve the
installed collection location elsewhere; record a missing source as a setup gap
instead of writing a broken absolute path. Load only the relevant subject.
Done when both knowledge branches resolve and agent projects can reach that index.

## Take note

1. Read existing requirements and the current request. Preserve the owner's
   intent, instinct, goals, audience, constraints and examples in their words.
   Append new statements to the canonical requirements record, using
   `docs/REQUIREMENTS.md` when none exists. Keep agent assumptions separate.
   Done when stated intent is traceable to its source and unknowns are explicit.
2. Translate that record into one proposed outcome, testable acceptance criteria,
   exclusions and next decision. Use the conventions in
   [Big Bang](big-bang/SKILL.md) to align the spec and roadmap; a note-only request
   ends with this alignment and does not start implementation. Ask only for
   missing decisions that materially affect scope. Done when the owner can see
   how the proposed Item follows from the original intent.

## Design

1. Identify which creative choices are unresolved: composition, information
   hierarchy, components, typography, color, imagery, interaction or voice.
   Reuse the prompter's references and constraints. Done when each proposed
   direction answers a named uncertainty.
2. Sketch two or three meaningfully different directions with available drawing,
   image or mockup tools. A text wireframe is valid when rendering is unavailable;
   label its fidelity. For each direction show the main elements, intended
   impression, one representative flow and the tradeoff it explores. Keep the
   work exploratory until a direction is selected. Done when the prompter can
   compare concrete options rather than adjectives alone.
3. Record actual feedback and the chosen direction, or mark selection pending.
   Promote agreed constraints into the spec without rewriting the raw notes.
   Conclude with the selected Item, evidence and next decision or build action.
   Done when the design handoff names both the direction and its acceptance path.

Use Tokens QA's session compass to summarize progress when available. Keep
research, notes and sketches focused on the active goal; implementation starts
through `build` when authorized.
