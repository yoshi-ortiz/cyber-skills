# Goal

What this package is for, and the shape it has to take to be it.

Fog. Lives on `dev`, never published to `main`. This is a plan, not a contract:
the parts of it that get built become contracts inside the skills that hold
them, and this file shrinks as that happens.

## The goal, in one line

**A rail an LLM cannot fall off.** Not a collection of capable skills: a
workflow with so few exits that an agent always knows where it is, what it is
allowed to touch, and what it costs to find out.

## The failure it exists to prevent

Three distinct ways a session dies. They look alike from the outside and have
nothing in common underneath, so they are named separately and defended
separately.

| Failure | What it looks like | What defends against it |
| --- | --- | --- |
| **Max** | Context window fills, the session compacts mid-thought and loses the thread | Token cost: a command's worst case is knowable before it runs |
| **Waste** | Tokens spent re-deriving what the repo already records, or exploring instead of executing | Signal density, plus workflow place: text that sharpens attention instead of diluting it, loaded from a place the agent did not have to search for |
| **Stuck** | An agent loops on a blocked task, burning the budget without moving the burndown | Async, nonblocking steps and a burndown with one state per item |

The repo already says this, in the one place it was enforced. From
`aesthetic/scripts/contracts.py`:

> The bloat this catches is the bloat that already happened once: `SKILL.md`
> grew to 3,200 tokens because nothing declared a budget for it.

That is the thesis. Everything below generalises it from one directory to the
package.

## Token weight has two axes, and they are not the same defence

Every skill puts literal text in front of the model: `md`/`txt`, read as tokens,
turned into output. **Token weight** is what that text costs the session on two
independent axes. Conflating them is the mistake an earlier draft of this file
made, treating "weight" as a single deterministic number.

| Axis | Question | Measured in | Defends against |
| --- | --- | --- | --- |
| **Token cost** | How many tokens does this text spend? | Bytes, counted before the session runs | Max |
| **Signal density** | Does this text sharpen what the model attends to, or does it dilute it? | Not countable. Judged by whether a cold reader can act without re-deriving, guessing, or re-reading | Waste |

These axes describe text after it reaches the model. Invocation adds a separate
placement trade: **context load** is the token weight of descriptions kept in
the model's window every turn; **cognitive load** is what a human must remember
when a user-invoked skill has no visible description. Cognitive load is not
signal density, because it is paid by the human rather than by the model.

Two files can carry the same byte count and opposite signal density. A table
of `file:line`, one term with one meaning, an explicit *why* line -- these are
**light**: they let the model act on the first read. Ambiguous prose, a term
used two ways in the same paragraph, doctrine restated in three places, an
acceptance criterion nobody checks -- these are **heavy** at any size: the model
either re-derives the missing decision (waste) or picks the wrong one silently
(the same failure `context derail` names one document down).

This is why `UBIQUITOUS_LANGUAGE.md` and the GOAL/SPEC split are not tidiness.
A glossary is a signal-density tool: it forces one term, one meaning, so the
model is never spending attention resolving which "budget" or "burndown" a
sentence means. `SPEC.md` carrying zero speculation is the same move at the
document level -- a reader of it never has to hold "is this settled or a wish"
open while reading a row.

### Token cost, mechanically

A command has deterministic **cost** when the byte count is a property of the
command rather than of the session it runs in. Three mechanisms already carry
that cost across the package:

| Mechanism | Where it lives now | Contract |
| --- | --- | --- |
| Byte budget on the always-loaded file | `max_file_bytes` in every skill directory's `CONTEXT.md`, checked by `contracts.py` | 22 of 22 contracted directories declare one |
| Lazy detail | `references/` behind context pointers | Branch-specific reference stays off the primary path |
| Fog | `tools/fog.py` drops dev state from `main` | Unchanged, already correct |

A skill's `SKILL.md` byte cap **is** its worst-case session load. That is the
whole of the mechanism, and it is why the cap is load-bearing rather than
tidiness. `R-15` remains at 210KB against 30KB; the current extraction brought
`server.cjs` under its 40KB budget without creating another module.

A model-invoked description costs on **every** session whether the skill runs
or not. A user-invoked skill declares `disable-model-invocation: true`, so its
description costs the model zero context; the human pays cognitive load by
remembering the command instead.

### Signal density, mechanically

Cost has a checker (`contracts.py`). Density does not, and probably should not
get a mechanical one -- it is closer to editing than to counting. What this
package already does that raises it, so the pattern is at least namable:

| Move | Where |
| --- | --- |
| One term, one meaning, aliases banned | `UBIQUITOUS_LANGUAGE.md`, and `aesthetic/UBIQUITOUS_LANGUAGE.md` for its own domain |
| Settled fact separated from open question | `SPEC.md` (contract) vs `GOAL.md` (reasoning) vs the Prototype backlog (unanswered) |
| A table instead of the same fact restated in prose | Every accumulation table in `SPEC.md`, this failure table above it |
| A `why` line, not a `what` line | This repo's own comment convention: describe the non-obvious reason, never the mechanism the code already shows |
| A stub that points instead of re-explains | The three alias kinds -- doctrine written once, everything else a bookmark |

A row that fails this -- restates what another file already says, uses a word
this file uses two ways, states a conclusion without the fact that produced it
-- is heavy regardless of its byte count, and is the thing a review of this
package should be hunting for once the cost mechanism is in place everywhere.

## Asynchronous, nonblocking, SRE compliant

Concretely, not as an adjective:

| Property | Rule |
| --- | --- |
| **Nonblocking** | A step that fans out over minutes is backgrounded, announced in chat, and reported by progress line. It never goes quiet and never blocks the next step that does not depend on it. |
| **Observable** | Keep the whole log, `tee` it, never pipe it through `head` or `tail`. A truncated log replaces the real exit code with the pager's, so a run that died a third of the way through reads as success. |
| **Idempotent** | Every mode ends in the same re-fetch, so running the wrong one is a no-op rather than damage. Never ask the user which mode: pick, run, and let the idempotence absorb the guess. |
| **Error budget** | The byte budget is the budget. Blowing it is an incident with a `BUGS.md` row, not a number to widen. |
| **One state per item** | `TODO` / `IN-PROGRESS` / `BLOCKED` / `DONE`. "What is left" is answerable without reading prose. |

`kit/SKILL.md` already implements the first three, in its "Report it while it
runs" section and its three-mode table. It is the pattern to generalise, not a
new thing to invent.

## Every skill declares its workflow place

A skill that does not say where it sits makes the agent decide, and deciding
costs the tokens the rail exists to save. The declaration goes in frontmatter,
next to the name, so it is read at the same moment the skill is:

```yaml
phase: first         # kit | first | build | land | check | fix
```

`phase` is where in the workflow, and it earns its place only where a skill's
name and its phase diverge: `genesis` and `aesthetic` both sit in `first`. For
the other four the field restates the name, which is acceptable; a field that
is sometimes redundant is fine, a field whose value nobody can predict is not.

**There is no `weight` field.** An earlier draft declared one and had the gate
check it against the byte budget -- a **cost** field only, never a stand-in for
density. It cannot work even at that: families are cut by phase, and four of
the six hold sections of different cost -- `fix` holds *Fix the code* beside
*Fix the rail*, `first` holds *Interview* beside *Promote to a spec*. One
number per skill would be false for most of them. The byte cap already **is**
the worst-case session load, so a second field could only ever disagree with
it. Signal density was never a candidate for this field either: it is not a
number, so nothing was lost by not declaring one. Token weight stays a word we
reason with on both axes, not a field we declare on either.
## The six families are an SDLC, not a taxonomy

The phase enum is not invented. Laid against the DevOps loop, the six families
land on it one to one, and the two that look irregular -- `kit` outside the
sequence, `check` and `fix` without an ordering position -- are irregular in
the loop too.

```
                      first          build
                    ( Plan ) ---> ( Code ) ---> ( Build ) ---> ( Test )
                       ^                                          |
                       |                                          v
      check       ( Monitor )                                 ( Release )   land
   (return arc)        ^                                          |
                       |                                          v
                    ( Operate ) <------------------------------ ( Deploy )
                        fix
                  incident response

    kit  -- Day 0. Provisions the environment the loop runs in.
            Not a phase: nothing flows through it twice.
```

| Family | SDLC phase | Why it is one family and not three |
| --- | --- | --- |
| `kit` | **Day 0**, outside the loop | Provisioning the machine is not a stage work passes through. Nothing re-enters it per feature, which is exactly why it is an on-ramp rather than a prefix. |
| `first` | **Plan** | Interview, spec promotion, and glossary are one phase in every SDLC worth the name. `genesis` already implements it. |
| `build` | **Code, Build, Test** | Three loop stages, one family, because they share a blast radius: all three write code and tests and nothing else. Cutting them apart would buy three commands and no new guarantee. |
| `land` | **Release, Deploy** | The irreversible half. Separate from `build` for the reason the loop separates them: a failed test costs a re-run, a failed deploy costs users. |
| `check` | **Monitor**, and the Monitor-to-Plan edge | Read-only, and it is the loop's return arc rather than a stage. This is why it has no position in the prefix ordering. |
| `fix` | **Operate**, incident response | The other return arc. Breakage enters from outside the sequence and merges back into it, which is the definition of an on-ramp and the reason `/fix` carries no prefix. |

### This resolves G-4

The ontology block -- `DEPLOY`, `LIVE OPS / RUN`, `MONITOR`, `PLAN (view
tickets)` -- kept refusing to fit any family, and the reason is now legible:
**it is the loop's right half, and the rail as specified is the left half.**
`first`, `build`, and `land` carry work up to the moment of deployment.
`check` and `fix` are return arcs, not an operate-and-monitor practice.

So the ontology is not a missing command. It is the half of the SDLC this
package does not currently do, described from the far side. Two honest options,
and the mapping makes the choice a real one instead of a shrug:

| Option | What it means |
| --- | --- |
| **Close the loop** | `check` and `fix` grow real Operate and Monitor sections, and the rail becomes a full SDLC. Large, and it makes this package responsible for running products. |
| **Declare the boundary** | The rail ends at `land`. The ontology is named as out of scope in `SPEC.md`, and a deployed product is somebody else's loop. |

Nothing forces the first. A package that says plainly where it stops is more
useful than one that gestures at a half it never built.

## What accumulation actually costs, measured

Installed file count is not context load. User-invoked skills cost the model no
description tokens, and a disabled plugin costs nothing even when its files are
present. `R-40` therefore tracks the missing host-level inventory rather than
repeating the earlier, invalid 15,300-token estimate.

### Benchmarked against `ask-matt`

The source workflow asked for a collection that "functions like `ask-matt`", so
`ask-matt` is the reference implementation and the comparison is measurable
rather than admiring. `tools/token_bench.py` is the measurement, and it is
re-runnable, which is the whole of what "deterministic" buys here: a number in
a document goes stale silently, a command does not.

```bash
python3 tools/token_bench.py --root ~/.agents/skills \
  --flow "ask-matt=ask-matt,grill-with-docs,grilling,domain-modeling,to-spec,to-tickets,implement,tdd,code-review" \
  --flow "rail-today=genesis,aesthetic,ponytail,tdd,code-review,diagnosing-bugs"
```

Two axes again, and a design can win one while losing the other. **Context** is
the description text model-invoked skills put in front of the model every
session. **On path** is the `SKILL.md` bytes one end-to-end walk loads.

| Flow | Skills | Context | On path |
| --- | --- | --- | --- |
| `ask-matt`, full flow | 9 | 937 B | 36,509 B |
| The rail as it stands today | 6 | 1,856 B | 37,573 B |
| | | **1.98x** | 1.03x |

Same work, near-identical path cost, and the rail pays **98% more** context
while shipping three fewer skills. Invocation choice and model-invoked
description length, not raw skill count, explain the difference.

**Finding 1: invocation choice comes before description length.** `ask-matt`,
`implement`, and the other user-invoked steps contribute zero context despite
having descriptions on disk. The rail's context cost comes from the skills the
model must discover autonomously, led by `ponytail` at 851 description bytes.
Prune those descriptions for signal density, but do not count user-invoked
files as model input.

**Finding 2: the router costs a third of the walk.**

```bash
python3 tools/token_bench.py --root ~/.agents/skills \
  --flow "with-router=ask-matt,grill-with-docs,grilling,to-spec,to-tickets,implement,tdd,code-review" \
  --flow "no-router=grill-with-docs,grilling,to-spec,to-tickets,implement,tdd,code-review"
```

| Flow | On path |
| --- | --- |
| Starting at the router | 33,082 B |
| Same work, entered directly | 21,591 B |
| | **0.65x** |

`ask-matt/SKILL.md` is 11,491 bytes: **35% of its own flow**, spent answering
"what should I run" before any work starts. That is the price of a map, and it
is only worth paying when the reader is actually lost.

This is the strongest argument for the prefix scheme. Typing `/first-` narrows
to planning without loading a map, so the six families buy back the router's
11.5 KB on every walk that would otherwise have started there. **The rail
should function like `ask-matt` without paying for `ask-matt`'s router.**

**Finding 3: the stub scheme is already the reference implementation's.**
`grill-with-docs` is 245 bytes and says, in full, "Run a `/grilling` session,
using the `/domain-modeling` skill." `implement` is 433 bytes and only
sequences `/tdd` and `/code-review`. Both carry a name, a pointer, and no
doctrine. The three alias kinds in `SPEC.md` are not a new idea being proposed
here; they are a measured description of what the reference already does, which
is why `STUB_MAX_BYTES` in the benchmark is read off `ask-matt`'s own files
rather than chosen.

## Three ways a collection accumulates

They are not competing designs. They compose, and they are ordered here by cost
to adopt, cheapest first.

### Demote: most workflow steps are not skills

The cost ladder. For each item, the question is not *which command* but *how
far down this ladder it can go.* Only the bottom rung charges rent.

| Rung | Cost | Fits |
| --- | --- | --- |
| **Statusline / hook** | Zero, and automatic | A measurement or a reflex. Nothing the user should have to remember to run. |
| **`CLAUDE.md` import** | Fixed, known bytes, every session | Always-true context. A state file the agent must never re-derive. |
| **Prompt file the user pastes** | Zero until used | Rare and terminal. Nothing routes to it because nothing needs to. |
| **`references/` behind a router** | Zero until read | Depth. Detail a mode needs once already running. |
| **Mode row in an existing skill** | A line | A variant of something that already exists. |
| **A new skill** | **Permanent, every session, forever** | Only when the assistant must find it cold, without being told. |

`/CHECK-tokens-rail` is the clearest case. As a command it is a paradox: it
spends tokens to report the token budget, and only when someone remembers to ask.
As a **statusline** it is free, continuous, and impossible to forget. Same for
`/DO-burndown`: a **hook** that updates the burndown on stop is the asynchronous,
nonblocking version of a command that blocks and must be invoked.

None of `hooks`, `statusLine`, or `CLAUDE.md` imports are configured on this
machine today. Three free rungs, entirely unused.

### Gate: install many, load few

Plugins already work here. `enabledPlugins` in `settings.json` carries ten, of
which eight are `false`: installed, costing nothing, one flag from returning.
Cost becomes proportional to what is **enabled**, not what is installed, so the
collection can grow without bound as long as a phase only turns on its own.

The catch is that gating is manual and stateful. A disabled skill is invisible
rather than discoverable, so anything cross-phase has to stay on. This is the
right home for the four dead clusters: terraform, xcode, firecrawl, and mem0 are
whole categories that are either wholly relevant or wholly absent.

### Collapse: fewer skills, mode tables inside them

Bounded by the `SKILL.md` byte budget: a mode table that keeps growing
eventually costs what the separate skills did, because `SKILL.md` is loaded
whole. Collapse is what to do with commands that must all stay reachable at
once; it is not a substitute for demoting or gating.

**This is not the scheme that was chosen.** [SPEC.md](SPEC.md) keeps fifteen
flat names and collapses only the *doctrine* behind them, using anchor and
ghost-argument stubs. The cost difference is measured below and it is small.

## The settled scheme

The contract moved out. [SPEC.md](SPEC.md) holds it: the six families, their
`SKILL.md` sections, every alias and argument that answers to them, and what
each one drives. Nothing in that file is speculative, which is the point of
having it separately -- a spec that carries wishes is a conversation, not a
contract.

What stays here is why the shape is that shape, what it costs, and what is not
built yet.

### What the flat scheme costs, and why it is affordable

The flat names are user-invoked stubs. They cost no model context and only their
small bodies when the human invokes one. A name becomes model-invoked only when
the agent must discover it cold or another skill must reach it. The command
surface therefore spends human cognitive load for autocomplete without paying
fifteen permanent descriptions.

The rule that still binds: doctrine lives in the six skills, never in the
stubs. A stub that starts explaining what its skill does is a second copy that
will drift, which is why `starter-pack` says only "read the other file".

## Prototype backlog

Everything in the source workflow that [SPEC.md](SPEC.md) does **not** carry.
Each is a prototype: a question to answer with throwaway work before it earns a
row in the spec. They are written as questions on purpose. An item here that
starts describing its own implementation has stopped being a prototype and
should be promoted or dropped.

### Not commands, and should not become skills

Four rungs down the ladder. The prototype in each case is one settings edit or
one file, and the question is whether it holds.

| Item | Prototype | Answers | Row |
| --- | --- | --- | --- |
| `CHECK-tokens-rail` | A `statusLine` script printing the session's token position | Does a number you always see change behaviour more than a command you must remember? A command here is a paradox: it spends tokens to report the token budget. | R-42 |
| `DO-burndown` | A `Stop` hook that updates `ROADMAP.md` when a session ends | Can the burndown maintain itself? *Working* the burndown stays `land-asap-burndown`; only *updating* it moves. | R-42 |
| `kit [roadmap/domain rail]` | A rail file written by `first-work-style`, imported from `CLAUDE.md` | Does fixed, known, every-session context actually stop the derail? Clearing fog by running a command is backwards: the fog is the absence of a file that should have loaded at session start. | R-41 |
| `CHECK-user-metrics`<br>`CHECK-production-health` | Two pasteable prompt files | These ask about a deployed product, not about building one, and nothing routes to them. Does zero-tax text serve as well as a command? | R-44 |

### Missing machinery, not missing names

Three steps in the summary workflow that no family owns. These are the real
gaps: no amount of naming fixes them.

| Step | Prototype | The question | Row |
| --- | --- | --- | --- |
| **2. Approve features** | A decision record between `first-idea-sketch` and `build` | Sketching produces options and building consumes a decision. The moment of deciding is unrecorded, so nothing can later say *why* this was built. Is it a `first` section, a `land` gate, or an ADR? | R-46 |
| **3. Clean code for blind no coders** | A legibility check on what `build` hands back | Stated as an acceptance criterion and nothing verifies it. A green test run is not evidence the deliverable is legible to the person who cannot read the code. What would be? | R-47 |
| **5. Portable ontology** | A read-only view of `DEPLOY`, `LIVE OPS / RUN`, `MONITOR`, `PLAN (view tickets)` | The only part of the workflow that describes a **running product** rather than the work of building one. Does it belong under `check-release-ontology`, or outside this package entirely? | G-4, R-39 |

### The manifest gaps

| Item | Prototype | The question | Row |
| --- | --- | --- | --- |
| Leader words in `collection.yaml` | Inline comments naming the top skills and `ponytail`, `ask-matt`, `poteto` | Only `ponytail` is a manifest entry. `ask-matt` arrives incidentally through the bare `mattpocock/skills` line, and `poteto` belongs to **pstack**, which is in no manifest at all -- nor is `zoom-out`, which `check` drives. A leader word that is not a source cannot be indexed, and a clean install produces a rail with holes in it. | R-43 |
| `alias.py` stub kinds | Two more shapes in `stub()` | Anchor and ghost-argument stubs are one line each. Does the gate still hold when a name points at a section rather than a skill? | R-45 |

### Agreed tokenization, unanswered parts

The contract in [docs/SPEC/AGREED_TOKENIZATION.md](docs/SPEC/AGREED_TOKENIZATION.md)
carries what R-52 settled. These are the parts it deliberately does not carry.

| Item | Prototype | The question | Row |
| --- | --- | --- | --- |
| The command's name | Rename `check-transformers-neural-network` to a `tokenize` name | The user reaches for `tokenize`, and the current name describes the library rather than the act. But `check` in `SPEC.md` is the **shipped** read-only phase, and this skill is fog that never publishes. Does a Repo-Dev-only command take a rail prefix it can never appear in, or does the rail simply not name it? | R-52 |
| Where a verdict lives | One tracked-but-fog file, or one per pass | The click log is fog and untracked; a verdict must be fog and **tracked**, which `BUGS.md` and `ROADMAP.md` already prove is a real place. Whether seven passes share one file or take one each is a merge-conflict question, and nobody has reviewed two passes yet to produce one. | R-52 |
| CJK in the bundle | Tokenize a Chinese fixture through the declared lens | The `bytes/4` estimate and the fragmentation argument both assume English prose. CJK runs 1.06-1.55x English under `o200k`, so a bundle carrying Chinese would move the ratio and the lens would be reporting on text the budget never modelled. Nothing in the corpus is Chinese today, which is why this is a question and not a defect. | R-52 |

## Open questions

| # | Question | Why it is not settled |
| --- | --- | --- |
| G-2 | Does `phase` frontmatter earn its gate | One field across six families, load-bearing for only two of them. Cheap to declare, not obviously worth enforcing. `weight` was dropped: see "Every skill declares its workflow place". |
| G-4 | Close the SDLC loop, or declare the boundary | Answered as far as reasoning can take it: the ontology is the loop's right half, so this is not a naming question but a scope decision. Grow real Operate and Monitor sections in `check` and `fix`, or say in `SPEC.md` that the rail ends at `land`. See "The six families are an SDLC". |
