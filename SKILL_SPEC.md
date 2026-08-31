# Skill-surface index

This is the navigation map for the six-family command surface. The contract
lives in [SPEC.md](SPEC.md); each shipped skill owns its doctrine in its own
`SKILL.md`. This file records one owner and one burndown state for every public
family or name promised by that contract.

`SHIPPED` means the named command resolves in this repository today.
`PARTIAL` means the family has a shipped owner, but its planned names or
sections do not exist yet. `PLANNED` means the family has no `SKILL.md` yet.
`alpha` is the development publication channel; a planned surface is not
installable until its owner exists and the publication gates pass.

| Family | Public command or alias surface | Channel | Canonical owner | Owning spec section | State | Roadmap |
| --- | --- | --- | --- | --- | --- | --- |
| `kit` | `kit`; `starter-pack`; `install`, `setup`, `init`, `start`; `sync`, `update`, `refresh`, `upgrade`; `fix`, `doctor`, `repair`, `troubleshoot`, `conflict` | `main` | [`kit/SKILL.md`](kit/SKILL.md) | Install, Sync, Fix | `SHIPPED` | `R-32` |
| `kit` modes | `kit design`; `kit español` | `main` | [`kit/SKILL.md`](kit/SKILL.md) | Install, Sync, Fix | `PLANNED` | `R-37` |
| `first` | `genesis`; `plan`; `first-plan-roadmap`; `first-take-note`; `first-idea-sketch`; `first-work-style`; `first-aesthetic`; `aesthetic` | `alpha` | [`first/genesis/SKILL.md`](first/genesis/SKILL.md), [`first/aesthetic/SKILL.md`](first/aesthetic/SKILL.md) | Interview before you architect, Promote to a spec, Fetch what you do not know, Source before you write, Update the state | `PARTIAL` | `R-32`, `R-35`, `E-02`, `E-03`, `E-04` |
| `first` graphics | `text-to-graphics` (loop reference, no separate command yet) | `alpha` | [`first/aesthetic/SKILL.md`](first/aesthetic/SKILL.md) | Source before you write | `PARTIAL` | `R-59` |
| `build` | `build-clean-code`; `build-qa-tests`; `build-pre-release`; `to`; `make` | `alpha` | Planned [`build/SKILL.md`](SPEC.md#the-families) | Clean code, QA tests, Pre-release | `PLANNED` | `R-36`, `E-05`, `E-06`, `E-07` |
| `land` | `land-asap-burndown`; `land-deployed-release`; `do`; `ship`; `burndown` | `alpha` | Planned [`land/SKILL.md`](SPEC.md#the-families) | Burndown, Release | `PLANNED` | `R-36`, `E-08`, `E-09` |
| `check` | `check-progress-goals`; `check-release-ontology`; `check` | `alpha` | Planned [`check/SKILL.md`](SPEC.md#the-families) | Progress, Ontology | `PLANNED` | `R-34` |
| `fix` | `fix`; `fix-context-derail`; `rail`; `unstick` | `alpha` | Planned [`fix/SKILL.md`](SPEC.md#the-families) | Fix the code, Fix the rail | `PLANNED` | `R-36` |

## Workflow order

Use the surfaces in this order when they are shipped:

```text
kit  →  first  →  build  →  land
          ↑                 │
          └── check ────────┘
          └── fix  ─────────┘
```

`kit` is Day 0. It provisions the skills loadout and does not own MCP
installation or MCP-server lifecycle. `first`, `build`, and `land` move work
forward. `check` reads evidence and returns it to planning. `fix` restores a
broken code path or workflow context, then returns to the affected family.

The name `repair` remains a `kit` alias for its Fix mode. The planned `fix`
family uses `rail` and `unstick` so each public name has one owner.

The [Main workflow goal](ROADMAP.md#main-workflow-goal) owns the topology. The
[Design workflow epics](ROADMAP.md#design-workflow-epics) own the design
capability burndown. A row marked `PLANNED` stays a roadmap promise until its
family contract, `SKILL.md`, publication channel, and verification evidence
exist.
