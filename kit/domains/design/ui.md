# UI

Build and refine interfaces on a fixed process, so two runs of the same brief
take the same path and differ only where the design genuinely differs.

Determinism here is process, not output. Three levers hold it: work against a
captured **baseline**, vary along a named **axis**, and spend a stated
**budget**. A run that skips one of the three is improvising.

## Pick the mode

| The ask | Mode |
| --- | --- |
| polish, tighten, fix, refine, "make this better" | **Refine** — converge on the composition that exists |
| explore, options, directions, "what if", "show me a few" | **Explore** — diverge across compositions that don't exist yet |

Refining inside an Explore ask returns one timid variant. Exploring inside a
Refine ask returns a rewrite nobody asked for. Read the ask, name the mode in
your first line, then run that mode's steps.

## Refine

1. **Capture the baseline.** Render the current UI and save the image. Every
   later claim is a diff against this file; without it "better" is unfalsifiable.
2. **Name the defects.** List them as observable statements — *measure runs to
   110ch*, *the card's 4 weights read as 4 voices*, *primary and secondary CTA
   have equal visual weight*. A defect that can't be stated observably is a
   preference; log it as one and move on.
3. **Fix one defect per pass.** One change, one re-render. Bundled fixes make
   the regression untraceable when the composition gets worse.
4. **Re-capture and diff.** Put before and after side by side and say which
   defect this pass closed.
5. **Run the gates** (below).

**Done when** every named defect is closed or explicitly declined with a
reason, the after-capture exists, and the gates are green.

## Explore

The design space is fixed, so it is the same space on every run. Vary along
these axes, one axis per variant:

| Axis | The two poles |
| --- | --- |
| **Density** | generous whitespace ↔ tight information density |
| **Type scale** | near-uniform ↔ extreme display-to-body contrast |
| **Structure** | strict symmetric grid ↔ deliberate asymmetry |
| **Emphasis** | typographic ↔ chromatic ↔ spatial |
| **Surface** | flat ↔ layered depth |

**Budget: four variants**, each moving one axis and holding the rest. Four is
enough to bracket a direction and few enough that each gets real work; a run
that returns two has under-explored, and one that returns nine has produced
noise to pick from.

Name the axis in each variant's title. Render all four. Then say which axis
produced the most useful variance for *this* brief and why — that sentence is
the actual deliverable, since it tells the next run where to spend its budget.

**Done when** four rendered variants exist, each names its axis, no two are
near-duplicates, and the axis verdict is written.

## Editorial

The house direction, resolved to properties you can check rather than a mood:

- **One type family**, used across a real weight range. Two families only when
  the second is a monospace doing a different job.
- **Measure capped at 65–75ch.** Long lines are the single most common tell.
- **A stated scale ratio** — pick one (1.25, 1.333, 1.5) and derive every size
  from it, so the sizes present are a sequence rather than a pile.
- **Leading loosens as size drops.** Display type sits tight; body type breathes.
- **Restrained palette**: one ink, one ground, one accent. The accent appears
  where a decision happens.
- **Whitespace carries structure.** Space groups and separates before a rule or
  a border does.
- **Asymmetry over centering** for anything longer than a hero.

Check these first when a composition reads as templated — the tell is almost
always measure, an unstructured type scale, or a third colour.

## Gates

Green on all three before calling UI work finished.

| Gate | Run | Green when |
| --- | --- | --- |
| **Rules** | `impeccable` skill | Its detector rules pass, or each failure is declined with a reason |
| **States** | `storybook-story-writing` skill | Every component state has a story: empty, loading, error, overflow, longest-plausible-content |
| **Measured** | `npx lighthouse <url> --output=json --quiet` | LCP, CLS and INP recorded; a regression against the baseline run is named |

The states gate catches what a screenshot cannot: a composition that holds at
one content length and collapses at another. Write the overflow story before
you believe the layout.

## Tools

Installed and verified. Reach for the narrowest one that covers the job.

| Skill | Job |
| --- | --- |
| `impeccable` | 61 deterministic detector rules, no LLM. The rules gate, and the only installed critique that runs the same way twice |
| `frontend-design` | Direction for new UI — first-party, use when starting from nothing |
| `web-design-guidelines` | Vercel's interface checklist. Live-fetches upstream, so it stays current |
| `modern-web-guidance` | Chrome team. Read before writing HTML/CSS/client JS — it carries the platform features that training weights miss |
| `emil-design-eng` | Detail and polish decisions at component level |
| `apple-design` | Motion physics, materials, optical typography |
| `animate`, `review-animations`, `improve-animations`, `animation-vocabulary` | Build, critique, audit and name motion |
| `theme-factory` | Token systems and theming |
| `shadcn` | Scaffolds shadcn/ui components. Scaffolding, not composition |
| `storybook-story-writing` | The states gate |
| `canvas-design`, `algorithmic-art` | Static compositions and generative work |

### The MCP gap

`mcp.toml`'s `design` profile carries `context7`, `playwright` and
`figma-desktop`. Three servers this domain wants are absent from every config
on this machine, and two of them are named in `tools.md` as "already in
`.mcp.json`" — there is no `.mcp.json`, and the global client config holds only
`context7`. Treat those two rows as false until a config proves otherwise.

| Server | Package | Standing |
| --- | --- | --- |
| Chrome DevTools | `chrome-devtools-mcp` | First-party, `ChromeDevTools` org, 3.3M weekly. Missing |
| Storybook | `@storybook/addon-mcp` | Storybook official, 2.1M weekly. Missing — the *skill* is installed, the server is not |
| Lighthouse | — | No credible server. `lighthouse-mcp` is 1.4k weekly, solo maintainer, **no repository URL** — below this collection's provenance bar |

Until they land: drive the browser with the already-configured `playwright`
server, and run Lighthouse through its CLI as the gates table shows. Google's
own `lighthouse` package is the audit engine either way, so the CLI path loses
the conversational interface and none of the measurement.
