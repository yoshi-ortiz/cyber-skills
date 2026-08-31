---
type: Specification
title: Domain-neutral design workflow support
description: PASS contract for APIs, MCP tools, desktop automation, outputs, and publication.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-28T00:00:00-05:00
---

# Domain-neutral design workflow support

The workflow accepts any project domain and stack. `DESIGN.md` is the canonical
human-readable intent and contains deterministic JSON code blocks for tokens,
component trees, content, assets, responsive rules, interactions, accessibility,
provenance, and tests. Generated files are projections of that contract, not
independent sources of truth.

Only project-relevant outputs are generated. The product, however, may claim a
requirement is supported only when its support manifest passes
`scripts/support_contract.py`.

## Requirements

| ID | Required support | PASS evidence |
| --- | --- | --- |
| `DES-01` | Pinterest inspiration | Official OAuth/API intake and Pin creation where authorized; source URL, author, rights status, retrieval time, and hash retained. |
| `DES-02` | Dribbble inspiration | Official OAuth/API read and shot publication where authorized; provenance retained. |
| `DES-03` | Instagram inspiration and publishing | Official Instagram API for professional accounts; container validation, caption, disclosure, quota, and publish receipt tested. |
| `DES-04` | UI libraries | Discover the repo's installed registry, package manifests, Storybook, and design tokens before adding components. |
| `DES-05` | Figma | Prefer official MCP/API/plugin capabilities. Editable native document or plugin output satisfies the mockup contract; proprietary `.fig` manufacture is not required. |
| `DES-06` | Adobe | Product-specific official API, SDK, plugin, or script for Express, Photoshop, Illustrator, InDesign, or Acrobat; compatible desktop automation is the recorded fallback. |
| `DES-07` | Canva | Prefer official Canva MCP, Connect API, or Apps SDK. Account plan and per-user authorization are part of the evidence. |
| `DES-08` | Friendly time travel | Versioned Git history with plain-language preview, restore, compare, and undo; Git vocabulary is optional in the operator UI. |
| `DES-09` | Technical specification and context | Clean indexed repo context, `DESIGN.md`, schema version, artifact hashes, decisions, and exact revision. |
| `DES-10` | Domain and stack architecture | Project-scoped boundaries, native framework conventions, typed trust boundaries, and no invented universal architecture. |
| `DES-11` | Responsive and accessible output | Semantic structure, keyboard paths, focus, contrast, reduced motion, overflow, and project viewport tests pass. |
| `DES-12` | Sketch to production UI | Raster, hand sketch, or design frame becomes production-ready components; exact pixel imitation is not the goal. |
| `DES-13` | Screenshot TDD | Fixture, interaction, accessibility, responsive, overflow, and human visual-baseline evidence is retained. |
| `DES-14` | Observable deployment | Project-selected static or full-stack IaC, health checks, logs, metrics, deployment receipt, and dashboard link pass. |
| `DES-15` | Documents | Relevant `DESIGN.md`, PDF, and PPT/PPTX outputs preserve structure, fonts, links, and page/slide render checks. |
| `DES-16` | Social and data outputs | Relevant PNG sizes and captions, publication receipts, XLS/XLSX data, and runnable `.py` pass format-specific checks. |
| `DES-17` | Editable mockups and app | Relevant SVG, editable Figma document/plugin output, EPS, and deployable app pass parse/build/render checks. |

## Integration rule

Resolve each operation through the first compatible interface:

1. official API;
2. official MCP;
3. official SDK, plugin, or script;
4. approved browser or desktop automation;
5. approved community MCP.

A fallback is not a silent substitute. Record its name, pinned version,
permissions, sandbox boundary, and the reason every earlier rung was unavailable.
Community and UI automation support is labeled `compatible-automation`, never
official support.

Figma and Canva currently publish official MCP surfaces. Canva's server is
remote even when operated from a desktop MCP client. Adobe support remains
product-specific; one adapter must not claim support for the whole Adobe family.

## PASS contract

A PASS belongs to a capability-environment tuple: operation, interface and
version, account tier, permissions, test layer, evidence artifact, and time.
External platform and publishing requirements need all three layers:

- `fixture`: deterministic contract test on every change;
- `credentialed`: authorized sandbox or test-account run before release;
- `canary`: bounded live run with a receipt.

Missing credentials, tier, permissions, or access is `BLOCKED`, not PASS.
Publication additionally requires preview, explicit human approval,
idempotency, a receipt, and delete or compensating rollback where available.

AI tools are capability adapters, not the source of truth. Record provider,
model, version, prompt hash, parameters, seed when supported, input hashes, and
raw result. Normalize their result into the versioned `DESIGN.md` contract;
deterministic code and artifact builders consume that contract. A model's
similar-looking second answer is not determinism evidence.

## Manifest

Commit `spec/design-harness/support.json`. This abbreviated example shows the
shape; the real file contains one unique entry for every `DES-01` through
`DES-17` requirement.

```json
{
  "version": 1,
  "project": {
    "domain": "project-defined",
    "stack": "repo-native",
    "selectedOutputs": ["DESIGN.md", "app"]
  },
  "requirements": [
    {
      "id": "DES-01",
      "status": "PASS",
      "interfaces": [
        {"kind": "official-api", "name": "Pinterest API", "version": "v5"}
      ],
      "evidence": [
        {"layer": "fixture", "passed": true, "artifact": "evidence/DES-01-fixture.json"},
        {"layer": "credentialed", "passed": true, "artifact": "evidence/DES-01-sandbox.json"},
        {"layer": "canary", "passed": true, "artifact": "evidence/DES-01-canary.json"}
      ]
    }
  ],
  "controls": {
    "preview": true,
    "approval": true,
    "idempotency": true,
    "receipt": true,
    "rollback": "delete-or-compensate",
    "provenance": true
  }
}
```

Validate it with:

```bash
python3 scripts/support_contract.py spec/design-harness/support.json
```

Official capability references: [Pinterest](https://developers.pinterest.com/docs/work-with-organic-content-and-users/create-boards-and-pins/),
[Dribbble](https://developer.dribbble.com/v2/),
[Instagram](https://developers.facebook.com/docs/instagram-platform/content-publishing/),
[Figma MCP](https://developers.figma.com/docs/figma-mcp-server/),
[Canva MCP](https://www.canva.dev/docs/mcp/), and
[Adobe developer platform](https://developer.adobe.com/).
