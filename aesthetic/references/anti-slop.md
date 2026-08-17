# Anti-slop constraints

Source: `Knowledge/design/ai-design-slop.md`. Slop is **unconstrained generation followed by insufficient curation** — plausible-looking work produced faster than it is understood, directed, or reviewed. This file turns that into checks the harness enforces rather than advice it hopes you remember.

The harness already implements the constraint stack from that note: intent → brand → tokens → component registry → behavior → review. The ledger *is* the registry; the corpus *is* the brand evidence. Use them.

## 1. Aesthetic homogenization

The failure mode is statistical defaults: familiar sans-serif, purple-to-cyan gradients, interchangeable cards, vague hero copy.

- Every visual move traces to a corpus cluster or a verbatim excerpt. Anything else is **inference**, is labelled as such, and is recorded at one star.
- Do not introduce a colour, typeface, or texture the corpus does not evidence. If a project has an existing identity, extend it — replacing it is a decision the user makes, not a side effect of a redraw.
- Reach for the corpus before reaching for a default. "Looks fine" is the symptom, not the goal.
- `controls` never hardcodes colour: it emits `var(--dh-*)` with fallbacks so the project palette wins.

- Comps are drawn in HTML/CSS and rendered by `shoot`, never hand-written as
  SVG. A drawing the model cannot see is a drawing nobody reviewed, which is
  the definition at the top of this file.

**Check:** would this read as this product with the logo removed?

## 2. Maintenance debt behind a convincing surface

The failure mode is unstructured DOM, utility sprawl, hardcoded values, duplicated patterns.

- Generate compositions of elements already in standing, not arbitrary markup.
- A new design-element id means a genuinely new element. Renaming one in standing is a **supersede**, recorded before the change.
- Reuse the tokens the screen already declares. A literal colour in generated markup is a defect.

**Check:** is every generated layer something the team can name, find in the ledger, and delete?

## 3. Lost CSS craft, interaction, and constraint

The failure mode is a layout that predicts well and behaves badly.

- Specify behaviour, not just appearance: narrow and wide containers, long content, empty states, missing assets.
- Interactive controls are reachable and operable by keyboard, with visible `:focus-visible`.
- Honour `prefers-reduced-motion`.
- Prefer container queries and logical properties over fixed breakpoints and physical directions.
- Every state a screen can enter needs a defined appearance — including "no data yet".

**Check:** change the content, the viewport, and the input method. Does it still hold?

## 4. Integrity: review-sized change

The failure mode is output produced faster than anyone can review it.

- One iteration changes only the elements it names. Prefer many small iterations to one large proposal.
- Do not restate settled work. Rebuilding a surface silently drops every element it carried.
- Say plainly what is evidence and what is inference. Never present a guess in the voice of a finding.
- If asked to do something the evidence contradicts, say so once, then do the work under a stated assumption.

**Check:** is the diff small enough that the user can disagree with a specific part of it?

## Slop tells

Stop and re-source when you notice yourself:

- reaching for a gradient, a card grid, or a pill badge with no corpus support;
- describing work as "modern", "clean", or "polished" instead of naming the move and its source;
- producing a second variant that differs only in colour — that is wallpaper, not an option;
- inventing an id, a palette split, or a rule the user never stated;
- adding an element because a layout looked empty rather than because a decision called for it.

## What the harness enforces mechanically

| Constraint | Enforced by |
| --- | --- |
| Decisions survive the session | `decisions.json`, `validate` |
| Rank reflects the user, not the agent | `stars` set by user; inference at 1★ |
| The graphic is rendered, not assumed | `decide --preview`, hash-pinned by `validate` |
| Corpus is evidence, not decoration | `source-manifest.json`, `validate` |
| Palette is declared, not defaulted | `controls` emits `var(--dh-*)` only |
| Adapters are observed, not claimed | `preflight` writes `capability-matrix.json` |

Everything else is judgement — which is exactly why the small, reviewable iteration matters.
