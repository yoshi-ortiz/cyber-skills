# Skill-surface index

This is the navigation map for the six-family command surface. The contract
lives in [SPEC.md](SPEC.md); each shipped skill owns its doctrine in its own
`SKILL.md`. This file records one owner and one burndown state for every public
family or name promised by that contract.

✅ `SHIPPED` means the named command resolves in this repository today.
🔵 `PARTIAL` means the family has a shipped owner, but its planned names or
sections do not exist yet. 🟡 `PLANNED` means the family has no `SKILL.md` yet.
`alpha` is the development publication channel; a planned surface is not
installable until its owner exists and the publication gates pass.

| Family | Public command or alias surface | Channel | Canonical owner | Owning spec section | State | Roadmap |
| --- | --- | --- | --- | --- | --- | --- |
| `kit` | `kit`; `starter-pack`; `install`, `setup`, `init`, `start`; `sync`, `update`, `refresh`, `upgrade`; `doctor`, `repair`, `troubleshoot`, `conflict` | `main` | [`kit/SKILL.md`](kit/SKILL.md) | Install, Sync, Fix | ✅ `SHIPPED` | `R-32` |
| `kit` modes | `kit <domain...>` including `kit design`; `kit español` | `main` | [`kit/SKILL.md`](kit/SKILL.md) | Domain, Install, Sync, Fix | 🔵 `PARTIAL` | `R-37` |
| `first` | `genesis`; `plan`; `first-plan-roadmap`; `first-take-note`; `first-idea-sketch`; `first-work-style`; post-MVP `first-aesthetic`, `aesthetic` | `alpha` | [`first/genesis/SKILL.md`](first/genesis/SKILL.md), [`first/aesthetic/SKILL.md`](first/aesthetic/SKILL.md) | Work style, Interview, Spec, Architecture decisions, Sources, State | 🔵 `PARTIAL` | `R-35`, `R-41`, `R-66` |
| `first` graphics | `text-to-graphics` (loop reference, no separate command yet) | `alpha` | [`first/aesthetic/SKILL.md`](first/aesthetic/SKILL.md) | Source before you write | 🔵 `PARTIAL` | `R-66` |
| `build` | `build-clean-code`; `build-qa-tests`; `build-pre-release`; `to`; `make` | `alpha` | [`build/SKILL.md`](build/SKILL.md) | Clean code, QA tests, Pre-release | ✅ `SHIPPED` | `R-36` |
| `land` | `land-asap-burndown`; `land-deployed-release`; `do`; `ship`; `burndown` | `alpha` | [`land/SKILL.md`](land/SKILL.md) | Burndown, Release | ✅ `SHIPPED` | `R-64` |
| `check` | `check-progress-goals`; `check-release-ontology`; `check` | `alpha` | [`check/SKILL.md`](check/SKILL.md) | Progress, Ontology | ✅ `SHIPPED` | `R-34` |
| `fix` | `fix`; `fix-context-derail`; `rail`; `unstick` | `alpha` | [`fix/SKILL.md`](fix/SKILL.md) | Fix the code, Fix the rail | ✅ `SHIPPED` | `R-63` |

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

The names `doctor`, `repair`, `troubleshoot`, and `conflict` remain `kit`
aliases for its Fix mode. Bare `fix` belongs to the `fix` family, and `kit`
stopped answering to it when that family shipped, so each public name has one
owner.

The MVP section in [ROADMAP.md](ROADMAP.md) owns delivery order. Its deferred
section owns Aesthetic and custom capabilities. A row marked `PLANNED` stays
a roadmap promise until its family contract, `SKILL.md`, publication channel,
and verification evidence exist.
