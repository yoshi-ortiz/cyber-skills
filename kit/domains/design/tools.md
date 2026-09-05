Everything mentioned across both research passes, ordered by provenance and maturity.

**Disposition.** Tiers 1-3 are now resolved in `harness-core/collection.toml`
under `[skills.design]`. A row here is research; the manifest is the install.
When the two disagree, the manifest is right and this file is stale.

## Tier 1 — Senior, stable, already installed and wired

| Thing | Source | Signal |
|---|---|---|
| `modern-web-guidance` | GoogleChrome/modern-web-guidance | First-party Chrome team. Mandatory per your `CLAUDE.md` |
| `web-design-guidelines` | vercel-labs/agent-skills (30,876★) | Vercel official. Live-fetches `vercel-labs/web-interface-guidelines` (843★, MIT, maintained by John Pham @vercel, pushed 2026-08-18) |
| `emil-design-eng`, `apple-design`, `animate`, `review-animations`, `improve-animations`, `animation-vocabulary`, `ask-sonner`, `find-animation-opportunities`, `pick-ui-library` | emilkowalski/skills (35,692★) | Emil Kowalski himself — author of `sonner` (12,937★) and `vaul` (8,595★) |
| Chrome DevTools MCP | Google (51k★) | First-party, already in `.mcp.json` |
| `@storybook/addon-mcp` | Storybook (`^0.3.4`) | Installed, already in `.mcp.json` |

The repo ships 12 skills; the manifest names 9. `write-swift` and
`animate-expo` are native and out of scope for this domain, and `prototype`
collides with `mattpocock/skills`, which already owns that name. The other
three — `ask-sonner`, `find-animation-opportunities`, `pick-ui-library` — were
dropped with no reason recorded, so they are now named.

`modern-web-guidance` and `web-design-guidelines` were reachable only through
the `web` domain, so a host that onboarded `design` alone got neither Tier-1
authority. Both are now declared under `[skills.design]` too, with source
strings byte-identical to their `[skills.web]` entries: `merge_sources` unions
the subsets into one clone rather than cloning the same repo twice.

The two MCP servers are not skills and do not belong in `collection.toml`.
MCP has its own lifecycle and client schema; its catalog is `mcp.toml`, and
both of these are already in `.mcp.json`.

## Tier 2 — Canonical documents, not skills

| Thing | Signal | Status |
|---|---|---|
| `raunofreiberg/interfaces` | 1,940★, Rauno Freiberg (Vercel) | Last push **2023-09-07** — frozen. The ancestor of Vercel's guidelines, worth reading once |
| `anthropics/skills` | 174,515★, first-party | 19 skills, none of them a design reviewer |

Neither row is an install. `raunofreiberg/interfaces` ships prose, not a
`SKILL.md`, so there is nothing for the harness to acquire; read it once.
`anthropics/skills` is already declared under `[skills.design]` as a named
subset. Tier 2 is closed with no manifest change.

## Tier 3 — Credible, actively maintained, resolved this pass

| Thing | Signal | Verdict |
|---|---|---|
| **`pbakaus/impeccable`** | 65,820★ · 1,819 commits · **40+ human contributors** · Apache-2.0 · 4 releases in the last two days · Paul Bakaus, creator of jQuery UI | **Installed.** Bare entry under `[skills.design]`; the repo resolves to exactly one skill, `impeccable`, so a one-name list would be a bare entry that rots the day a second lands. Ships 61 deterministic detector rules that run with no LLM. Hazard: `/impeccable init` writes `DESIGN.md` — global scope only, never `init` in a project checkout |
| `garrytan/gstack` | 131,526★ · MIT · 12 contributors, 345 of 386 commits by Garry Tan | Already installed, under `[skills.coding]` — it is a stack workflow, not a design authority, so it is not copied into this domain. At 1.77 vs upstream 1.79. Its `browse` is buildable TS in-repo, not missing |

## Tier 4 — Credible author, solo or stalled

| Thing | Signal |
|---|---|
| `MengTo/Skills` | 5,813★ · solo (127/127 commits) but sustained across 24 days. Its `editorial-tech` is a mood, not a method |
| `bergside/awesome-design-skills` | 2,688★ · Zoltán Szőgyényi (Flowbite, 9.3k★) · **10 weeks cold** · Tailwind lineage. Read the Editorial/Riso direction files; don't wire them in |

## Tier 5 — Adoption without provenance

| Thing | Signal |
|---|---|
| `Owl-Listener/designer-skills` | 2,522★, active today — but the author is not independently verifiable and the **second-largest contributor is the login `claude`** |
| `ui-ux-pro-max` *(installed)* | `nextlevelbuilder/ui-ux-pro-max-skill`, claimed 125,262★, **provenance entirely unexamined** |
| `mattpocock/skills` *(installed)* | 252,368★ — the single largest source in your lockfile, also unexamined |

## Tier 6 — Sus

| Thing | Why |
|---|---|
| `plugin87/ux-ui-agent-skills` | 880★ against **2 watchers**. **No licence file** — legally undefined to vendor |
| `OneWave-AI/claude-skills` → `claude-design-critic` | **Retracted.** 287★, 5 watchers, 205 skills in 36 commits, one 2-follower author, org created the day of the repo. My former #1 |
| `richhemsley3/claude-design-skills` | **Retracted.** 0 stars, 0 forks, one commit ever, on an account whose 21 repos are all at 0. My former #2 |

## Tools assessed and set aside

`amzn/style-dictionary` (4,800★) is real but inverts your token pipeline — your source of truth is hand-authored CSS in `src/tokens/`. `webpro-nl/knip` (12,178★) duplicates the `fallow` you already run. Playwright MCP adds nothing over `scripts/capture-storybook.mjs`. Screenshot diffing answers "did this change", not "is this good" — it belongs after the editorial pass as a baseline in the conformance matrix. `aesthetic` stays deferred; `shadcn` stays out.

**The through-line, revised.** The original read was that everything in Tier 1
was already on disk and none of it critiques composition, so nothing in
Tiers 3–6 was worth installing and the critique skill had to be written
locally. Two of those three clauses held; the third did not.

`pbakaus/impeccable` critiques composition, deterministically and without an
LLM, and it is Apache-2.0 with 40+ human contributors — the one candidate in
the whole set that is a reviewer rather than a producer. It is installed. That
does not retire the local critique skill: 61 detector rules answer *does this
violate a rule*, which is a different question from *is this good*, and the
criteria in `spec/expressive-vainilla/DECISIONS.md` are this project's, not
Bakaus's. Build the local skill on top of it, not instead of it, and keep the
rubric architecture borrowed from `review-animations`.

Tiers 4–6 are unchanged and stay out. Nothing below Tier 3 was installed.

**Two provenance debts survive this pass**, both flagged in Tier 5 and both
still unpaid: `ui-ux-pro-max` and `mattpocock/skills` are installed today with
their provenance entirely unexamined, and `mattpocock/skills` is the single
largest source in the lockfile. Adding a vetted Tier-3 entry does not settle
them.
