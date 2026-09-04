# 🗺️ Roadmap

Remaining implementation only. Contracts live in [SPEC.md](SPEC.md), open
questions in [GOAL.md](GOAL.md), defects in [BUGS.md](BUGS.md), and shipped
work in [CHANGELOG.md](CHANGELOG.md).

States: ⚪ `TODO` · 🟡 `IN-PROGRESS` · 🔴 `BLOCKED` · ✅ `DONE`

## 🧱 codebase / development enviroment

The architecture backlog is visible before delivery work so the rail is built
against deliberate seams. The first five rows harden the development
environment; the two Aesthetic rows remain post-MVP.

| ID | Core controller | State | Item | Bugs | Module | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| R-54 | [`skill_discovery.py`](tools/skill_discovery.py) · [`fog.py`](tools/fog.py) · [`index_gate.py`](tools/index_gate.py) | ✅ `DONE` | Deepen the Skill Catalog | [B-021](BUGS.md), [B-027](BUGS.md) | [`tools/`](tools/), [`kit/silly/`](kit/silly/) | — |
| R-58 | [`CLAUDE.md`](CLAUDE.md) · [`CONTEXT.md`](CONTEXT.md) | ✅ `DONE` | Make Repo-Dev context queryable | — | Repo-Dev context | R-54 |
| R-61 | [`genesis_flow.py`](first/genesis/scripts/genesis_flow.py) | ✅ `DONE` | Deepen deterministic Genesis | — | [`first/genesis/`](first/genesis/) | R-54 |
| R-17 | [`check.py`](tools/check.py) · [`release.py`](tools/release.py) · [`cook.py`](cook/cook.py) | ✅ `DONE` | Deepen Release Verification | [B-023](BUGS.md) | [`tools/`](tools/), [`cook/`](cook/) | R-54, R-61 |
| R-16 | [`loanwords.py`](tools/loanwords.py) | ✅ `DONE` | Enforce ubiquitous language | — | [`tools/`](tools/) | — |
| R-56 | [`server.cjs`](first/aesthetic/companion/server.cjs) · [`trace_preview.py`](tools/trace_preview.py) · [`vectors.py`](check/build-context-token-vectors/scripts/vectors.py) | ⚪ `TODO` | Deepen the Companion Host *(post-MVP)* | [B-024](BUGS.md) | [`first/aesthetic/companion/`](first/aesthetic/companion/) | MVP release |
| R-66 | [`assistant_app.py`](first/aesthetic/scripts/assistant_app.py) · [`graphics_flow.py`](first/aesthetic/scripts/graphics_flow.py) · [`deliver.py`](first/aesthetic/scripts/deliver.py) | ⚪ `TODO` | Deepen the Aesthetic Run *(post-MVP)* | [B-013](BUGS.md), [B-026](BUGS.md) | [`first/aesthetic/`](first/aesthetic/) | R-56, MVP release |

Build order:

1. R-54 makes skill identity, family, channel, aliases, origin, and path one
   catalog fact consumed by index, publish, install, and roadmap adapters.
2. R-58 gives cold Repo-Dev entry a goals → roadmap → module map instead of a
   whole-repository document walk.
3. R-61 makes named Genesis doctrine the source; the Python flow becomes an
   adapter instead of a second lifecycle.
4. R-17 makes one gate registry drive local checks, CI, Cook, and release;
   R-16 guards the vocabulary shared by those contracts.
5. Ship the routing-only MVP.
6. R-56 and R-66 deepen the deferred Aesthetic runtime after the rail is stable.

## 🚂 MVP — route proven public skills

The MVP adds no Aesthetic capability and does not reimplement the public skills
it routes. Each family owns sequence, aliases, and handoff only.

### 🧰 Sprint 1 — **kit + first**

| ID | Core controller | State | Item | Bugs | Module |
| --- | --- | --- | --- | --- | --- |
|  |  |  | **🧰 `kit`** |  |  |
| R-37 | [`kit/SKILL.md`](kit/SKILL.md) · [`harness.py`](../harness-core/harness.py) | 🟡 `IN-PROGRESS` | Add explicit domain activation and `español` mode to Kit *(scoped acquisition shipped; legacy exposure cleanup and español remain)* | — | [`kit/`](kit/) + `harness-core` |
| R-43 | [`manifest_gate.py`](tools/manifest_gate.py) | ⚪ `TODO` | Index every routed public skill and origin | — | [`tools/`](tools/) + `harness-core` |
| R-51 | [`harness.py`](../harness-core/harness.py) · [`collection.toml`](../harness-core/collection.toml) | ✅ `DONE` | Complete portable installation | [B-028](BUGS.md) | [`harness-core`](../harness-core/) |
| R-67 | [`mcp.toml`](../harness-core/mcp.toml) | 🟡 `IN-PROGRESS` | Sync a secret-free MCP catalog through managed adapters to agents and VS Code *(catalog shipped; adapters remain)* | — | [`kit/`](kit/) + `harness-core` |
|  |  |  | **🎭 `silly`** |  |  |
| R-45 | [`alias.py`](kit/silly/scripts/alias.py) | ✅ `DONE` | Generate whole, anchor, and ghost aliases | — | [`kit/silly/`](kit/silly/) |
|  |  |  | **🧭 `first`** |  |  |
| R-35 | [`genesis/SKILL.md`](first/genesis/SKILL.md) | ✅ `DONE` | Route `brainstorming`, `ask-matt`, `prototype`, and `grilling` | — | [`first/`](first/) |
| R-41 | [`genesis/SKILL.md`](first/genesis/SKILL.md) | 🟡 `IN-PROGRESS` | Make `first-work-style` write the project-owned domain rail *(contract shipped; field evidence remains)* | — | [`first/`](first/) + `harness-core` |
| R-38 | [`manifest_gate.py`](tools/manifest_gate.py) | ✅ `DONE` | Declare the First workflow phase | — | [`first/genesis/`](first/genesis/) |
| R-46 | [ADR contract](first/genesis/references/architecture-decisions.md) | ✅ `DONE` | Hand accepted decisions from First to Build | — | [`first/genesis/`](first/genesis/) |

Five of nine are done. R-37's legacy exposure cleanup and language mode,
R-41's field evidence, R-43's origin gate, and R-67's MCP adapters remain:

1. **R-43 needs verified selectors, then code.** pstack's source is now known
   as `cursor/plugins`, but its CLI advertises `Poteto Mode` and no `zoom-out`;
   the current Matt Pocock source also does not advertise `zoom-out`. gstack
   advertises only its bundle, not separate `review` or `land-and-deploy`
   leaves. Resolve those
   declared origins before making the manifest gate enforce them.

### 🏗️ Sprint 2 — build + land

| ID | Core controller | State | Item | Bugs | Module |
| --- | --- | --- | --- | --- | --- |
|  |  |  | **🏗️ `build`** |  |  |
| R-36 | [`build/SKILL.md`](build/SKILL.md) | ✅ `DONE` | Route `ponytail`, `tdd`, `code-review`, and `verification-before-completion` | — | [`build/`](build/) |
|  |  |  | **🚢 `land`** |  |  |
| R-64 | [`land/SKILL.md`](land/SKILL.md) | ✅ `DONE` | Route `finishing-a-development-branch` and `land-and-deploy` | — | [`land/`](land/) |

### 🛠️ Sprint 3 — fix + check

| ID | Core controller | State | Item | Bugs | Module |
| --- | --- | --- | --- | --- | --- |
|  |  |  | **🛠️ `fix`** |  |  |
| R-63 | [`fix/SKILL.md`](fix/SKILL.md) | ✅ `DONE` | Route `diagnosing-bugs` and `systematic-debugging` | — | [`fix/`](fix/) |
|  |  |  | **🔎 `check`** |  |  |
| R-34 | [`check/SKILL.md`](check/SKILL.md) | ✅ `DONE` | Route `zoom-out` and `review` read-only | — | [`check/`](check/) |

All four routers ship on `alpha`. Each declares its sections as anchor targets
and its flat names as aliases, so `alias.py link --fun` installs them; none
reimplements a skill it routes. Bare `fix` moved from a `kit` alias to the `fix`
family, leaving every public name with one owner.

`zoom-out` and `land-and-deploy` are routed by name while R-43 resolves their
declared origins. The routers name the skill, never a source the manifest gate
has not verified.

## 🎨 Deferred — Aesthetic and custom capabilities

| ID | Core controller | State | Item | Bugs | Skill / module |
| --- | --- | --- | --- | --- | --- |
| R-18 | [`assistant_app.py`](first/aesthetic/scripts/assistant_app.py) | ⚪ `TODO` | Enforce the companion live-check on every Loop entry | — | [`first/aesthetic/`](first/aesthetic/) |
| R-24 | [`golden_rules.py`](first/aesthetic/scripts/golden_rules.py) | ⚪ `TODO` | Cap golden-rule retry cost | [B-013](BUGS.md) | [`first/aesthetic/`](first/aesthetic/) |
| R-50 | [`direction_context.py`](first/aesthetic/scripts/direction_context.py) | 🟡 `IN-PROGRESS` | Complete the inference context compiler | — | [`first/aesthetic/`](first/aesthetic/) |
| R-60 | [`brief_workflow.py`](first/aesthetic/scripts/brief_workflow.py) | ⚪ `TODO` | Generalize durable form-state sync | — | [`first/aesthetic/`](first/aesthetic/) |
| R-62 | [`graphics_flow.py`](first/aesthetic/scripts/graphics_flow.py) · [`text_to_graphics.py`](first/aesthetic/scripts/text_to_graphics.py) | 🟡 `IN-PROGRESS` | Ship this repository as an Aesthetic Food Product | [B-026](BUGS.md), [B-027](BUGS.md) | [`first/aesthetic/`](first/aesthetic/) |
| R-52 | [`tokens_qa.py`](check/tokens-qa/scripts/tokens_qa.py) | ⚪ `TODO` | Gate agreed tokenization | — | [`check/tokens-qa/`](check/tokens-qa/) |
| R-57 | [`vectors.py`](check/build-context-token-vectors/scripts/vectors.py) | ⚪ `TODO` | Narrow the vectors interface | [B-023](BUGS.md) | [`check/build-context-token-vectors/`](check/build-context-token-vectors/) |
| R-55 | [`token_bench.py`](tools/token_bench.py) | ⚪ `TODO` | Make benchmark inputs reproducible repo data | — | [`tools/`](tools/) |
| R-40 | [`skill_discovery.py`](tools/skill_discovery.py) | ⚪ `TODO` | Measure the host's enabled collection | — | [`tools/`](tools/) |

## 🧪 Unscheduled

Legibility and product-monitoring choices remain prototypes in
[GOAL.md](GOAL.md). Design adapters remain in the
[platform-support contract](first/aesthetic/references/platform-support.md).
