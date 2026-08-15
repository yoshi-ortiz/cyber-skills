# Design tools

The harness names the adapters a design project may need and records which ones were **observed**. It never assumes one is present: the compute invariant forbids claiming an MCP server or local tool without preflight evidence.

## Preflight first

Before the first shot, check what is actually wired, then record it:

```bash
python3 scripts/bootstrap_harness.py preflight --project-root . \
  --available image,pdf,repository \
  --missing devtools,playwright
```

Only capabilities required by the selected profiles are accepted; anything else is a typo or the wrong profile. A capability never passed to `preflight` stays `available: false` — absence of evidence is not availability. Missing required capabilities keep the run in `draft`.

## Adapters by capability

| Capability | Typical adapter | Used for |
| --- | --- | --- |
| `image` | local render (`sips`, `qlmanage`), vision | Hashing and reading corpus stills |
| `pdf` | PDFKit/poppler + a pinned extractor | Page-level image and text evidence |
| `repository` | filesystem, git | Existing code, prior decisions, lineage |
| `browser` / `devtools` | Playwright, Chrome DevTools MCP | Rendering screens, measuring real layout |
| `playwright` | Playwright MCP | Responsive states, keyboard paths, screenshots |
| `lighthouse` | Lighthouse | Performance and accessibility conformance |
| `storybook` | Storybook MCP | The approved component registry |
| `layer-renderer` | deterministic compositor | `mockup-layering` output |
| `color-management` | ICC-aware pipeline | Print and cross-device colour |
| `motion-renderer` | pinned motion library | `motion` timelines, reduced-motion checks |
| `licensing` | rights records | Provenance for third-party art |
| `geometry` / `standards` | CAD, published standards | `physical-space` dimensions and clearances |
| `materials` | supplier data | `product-design` substrates and finishes |
| `copy-evidence` | research records | Claims that survive review |

## Design MCP servers

These cover most `art-direction`, `frontend-layout` and `mockup-layering` work. Install what the project needs; record the result with `preflight`.

| Server | Gives you | Maps to |
| --- | --- | --- |
| **Figma** | `get_design_context`, `get_variable_defs`, `get_screenshot`, Code Connect | `repository`, `image`, token and component registry |
| **Playwright** | Real browser, screenshots, viewport and input control | `browser`, `playwright`, `devtools` |
| **Shadcn UI** | Component and block registry, themes | Approved component registry |
| **Blender** | Viewport and thumbnail renders | `layer-renderer`, product and spatial mockups |
| **Context7** | Pinned library documentation | `knowledge` |

Figma and any hosted server need authorization before use. If a server is unauthorized in the current session, treat the capability as **missing**, say so, and fall back to a deterministic local path — never narrate a tool you did not run.

## Why this exists

A registry the agent can compose within is the difference between generating a design system implicitly on every prompt and building inside an explicit one. Component registries (Figma, Storybook, shadcn) and token sources are the highest-value adapters here: they are what keep generation inside reviewed primitives rather than freeform markup. See [anti-slop.md](anti-slop.md).
