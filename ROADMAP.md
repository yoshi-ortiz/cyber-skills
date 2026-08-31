# Roadmap

The burndown. One row per item, each in exactly one state, so "what is left"
is answerable without reading prose.

States: `TODO` · `IN-PROGRESS` · `BLOCKED` · `DONE`

Bugs live in [BUGS.md](BUGS.md) with their root causes. Shipped changes live in
[CHANGELOG.md](CHANGELOG.md). This file is what remains.

Fog. Lives on `dev`, never published to `main`.

Contract and vocabulary: [SPEC.md](SPEC.md), [GOAL.md](GOAL.md),
[UBIQUITOUS_LANGUAGE.md](UBIQUITOUS_LANGUAGE.md). Promoted specs live under
`docs/SPEC/`.

## The rail

Six **families**, one command surface. Prefix routes; no router command.

| Family | Phase | Shipped in this repo | Planned owner |
| --- | --- | --- | --- |
| `kit` | Day 0 on-ramp | `kit/` (`starter-pack`, `silly` nested) | `kit/SKILL.md` |
| `first` | Plan | `first/genesis/`, `first/knowledge/`, `first/aesthetic/` | genesis + aesthetic |
| `build` | Code · Build · Test | — | `build/SKILL.md` |
| `land` | Release · Deploy | — | `land/SKILL.md` |
| `check` | Monitor (return arc) | `check/build-context-token-vectors/` | `check/SKILL.md` |
| `fix` | Operate (bare on-ramp) | — | `fix/SKILL.md` |

```text
kit → first → build → land
        ↑         │
        └── check ┘
        └── fix ──┘
```

Eat-your-own-food: Repo-Dev work runs through these skills. After a commit here,
`kit sync` re-arms the collection; graphics and the landing hero ship through
`aesthetic` / `text-to-graphics` on **this** checkout (`design/`,
`shots/landing.hero.flow.svg`), not hand-copy.

Out of repo scope: work that only applies to an external design fixture (e.g.
`keynote-performance` preview redraws). Harness lessons from that fixture stay;
the fixture's ledger does not.

## Epics

Open rows grouped by what unblocks what. Priority order:

1. **E1 Platform plumbing** — R-54, R-56, R-51, R-43
2. **E4 Aesthetic core** — R-15, R-62, R-24
3. **E2 Token intelligence** — R-50, R-52, R-53, R-55, R-57, R-40
4. **E3 Companion surface** — R-18, R-60 (after R-56)
5. **E5 Rail command surface** — R-35, R-36, R-34, R-45, R-49, R-37, R-46, R-47, R-44, R-38
6. **E6 Repo-Dev ergonomics** — R-58, R-41, R-42, R-61, R-16, R-17
7. **Design E-A → E-B → E-C** — after E4 is healthy

| Epic | North star |
| --- | --- |
| **E1** | `kit sync` after a commit re-arms everything; one corpus module; one server seam |
| **E2** | Every published benchmark number is reproducible from repo data |
| **E3** | No Loop step runs unless the browser ledger is live and replayable |
| **E4** | `bootstrap_harness.py` under budget; this repo's landing hero ships via `text_to_graphics.py` |
| **E5** | Every name in SPEC resolves to a stub or skill without a router |
| **E6** | Entering burndown mode costs less than one skill walk |

### E1 — Platform plumbing

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-54 | `TODO` | One module owns the skill corpus | B-021. Six frontmatter parsers, no interface. R-55 and R-57 depend on this. |
| R-56 | `TODO` | Decide the companion seam: shared, or gated identical | `trace_preview.py` and `vectors.py` duplicate the loopback server wholesale. |
| R-51 | `IN-PROGRESS` | Port harness-core to one tested Python file | `harness.py` landed; remaining Windows parity for sync/onboard, then drop bash. Lives in harness-core. |
| R-43 | `TODO` | Index `collection.yaml`, add missing sources | `poteto`, `poteto-mode`, `zoom-out` not in any manifest today. |

### E2 — Token intelligence

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-50 | `IN-PROGRESS` | Build the inference context compiler | [Contract](docs/SPEC/INFERENCE_CONTEXT_COMPILER.md). Slice in `direction_context.py`; remaining: per-skill declarations, exact tokenizer, advisory ranker. |
| R-52 | `TODO` | Agreed tokenization, visualized and gated | [Contract](docs/SPEC/AGREED_TOKENIZATION.md). Durable sha256-pinned verdicts; gate refuses stale agreements. |
| R-53 | `TODO` | Advisory clustering over the corpus | [Contract](docs/SPEC/ADVISORY_CLUSTERING.md). EVoC proposals for semantic group and contamination risk; advisory only. |
| R-55 | `TODO` | Flows become repo data; benchmark gains release mode | `token_bench.py` flows are CLI strings today, not reproducible repo data. |
| R-57 | `TODO` | Narrow the vectors interface | B-023. Split corpus load → R-54, serve → R-56; expose `embed()` and `cluster()` as callables. |
| R-40 | `TODO` | Measure the host's actual enabled collection | Model-invoked descriptions only; installed count is not context load. |

### E3 — Companion surface

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-18 | `TODO` | Companion live-check, every run | Hard precondition before any other Loop step; not an unchecked `open`. |
| R-60 | `TODO` | Generalize companion form-state sync | Loopback app under `.superpowers/`: inputs sync to durable file data (pattern from `trace_preview.py`). Blocked on R-56. |

### E4 — Aesthetic core health

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-15 | `TODO` | Split `bootstrap_harness.py` | 210 KB vs 30 KB budget. Split before adding; do not widen the cap. |
| R-62 | `TODO` | Dogfood this repo's graphics and website | `landing.hero.flow` through `text_to_graphics.py` → `design/landing-flow-hero.html`. Proof = `kit sync` then a green graphics run on this checkout. |
| R-24 | `TODO` | Cap golden-rule retry cost | B-013. Retries must narrow scope, not re-attempt the same rejected spec. |
| R-25 | `TODO` | Explicit `subject` in `editorial.json` | Durable model behind R-21; not urgent while dotted-id convention holds. |

### E5 — Rail command surface

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-35 | `TODO` | Ship five `first-*` stubs | Over `genesis` and `aesthetic`; do not write a second planning skill. |
| R-36 | `TODO` | Write `build`, `land`, and `fix` | `build` routes ponytail/tdd; `land` owns burndown state machine; `fix` owns the rail. |
| R-34 | `TODO` | Write `check` | Read-only; `check-` prefix routes. |
| R-45 | `TODO` | Teach `alias.py` anchor and ghost-argument stubs | Whole aliases exist; § and ⇢ kinds do not. |
| R-49 | `TODO` | Record routerless rail in SPEC | Prefix scheme is intentional; document so it is not "fixed" later. |
| R-37 | `TODO` | Add `design` and `español` modes to `kit` | Two rows in the mode table; no new skill. |
| R-46 | `TODO` | Approve-features gate | Between sketch and build; decision moment is unrecorded today. |
| R-47 | `TODO` | Legibility gate on build output | Green tests are not evidence a non-coder can read the deliverable. |
| R-44 | `TODO` | Two pasteable monitor prompts | `check-user-metrics`, `check-production-health`; zero description tax. |
| R-38 | `TODO` | Declare `phase` in frontmatter | G-2. Declare without gate; load-bearing for `genesis` and `aesthetic` only. |

### E6 — Repo-Dev ergonomics

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-58 | `TODO` | Give the burndown a query interface | Mode A entry is ~73 KB across five files; query `IN-PROGRESS`, `R-43`, last bug. |
| R-41 | `TODO` | Write the rail as a `CLAUDE.md` import | Fixed bytes at session start, not a command to remember. |
| R-42 | `TODO` | Move measurements to hooks / statusLine | Token rail and burndown off the command surface. |
| R-61 | `TODO` | Deterministic markdown | Fenced blocks in skill doctrine are production code, like notebook cells: named, gated, replayable. `graphics_flow.FLOW` is the reference; extend to kit/genesis paths. |
| R-16 | `TODO` | Enforce ubiquitous language | Checker over `UBIQUITOUS_LANGUAGE.md` banned synonyms. |
| R-17 | `TODO` | Automate verification in CI | `check.py` today is manual. |

### Design — three phases

Domain-neutral workflow in
[`platform-support.md`](aesthetic/references/platform-support.md). E-01 is
`DONE`. Defer external adapter epics until E4 dogfood is green on this repo.

| id | State | Family | Phase | Epic | Exit |
| --- | --- | --- | --- | --- | --- |
| E-02 | `TODO` | `first` | **E-A** Discover & frame | Brief + design contract | `DES-09` |
| E-03 | `TODO` | `first` | **E-A** | Inspiration adapters | `DES-01`–`DES-04` |
| E-04 | `TODO` | `first` | **E-A** | Editable workspaces | `DES-05`–`DES-07` |
| E-05 | `TODO` | `build` | **E-B** Build & prove | Blind operator control | `DES-08` |
| E-06 | `TODO` | `build` | **E-B** | Sketch-to-production | `DES-10`–`DES-12` |
| E-07 | `TODO` | `build` | **E-B** | Screenshot TDD | `DES-13` |
| E-08 | `TODO` | `land` | **E-C** Ship & publish | Observable deployment | `DES-14` |
| E-09 | `TODO` | `land` | **E-C** | Deliverables + publication | `DES-15`–`DES-17` |

`check` reads this table; `fix` returns the first failing epic to `TODO` or
`BLOCKED`.

## Done

R-01–R-10 repo bootstrap. R-11–R-12 corpus tagging. R-14 design quality
judged (external fixture used as measurement only). R-19–R-23, R-27–R-30
companion and brief. R-31–R-33, R-39, R-48 rail topology and invocation audit. R-59 graphics loop
(`graphics_flow.py` + `text_to_graphics.py status`).
E-01 support contract.

Closed out of repo scope: **R-13** (external fixture SVG previews, B-007),
**R-26** (external fixture ring type, B-017).

Detail for each shipped row: [CHANGELOG.md](CHANGELOG.md).

## Working notes

**Published article is static.** After a render change, run `article` + `publish`
or `article` with no `--cohort` before screenshotting:

```bash
python3 first/aesthetic/scripts/bootstrap_harness.py article \
  --project-root . --out /tmp/check.html
```

**Installed copy does not sync itself.** Run `kit sync` after editing skills here.
