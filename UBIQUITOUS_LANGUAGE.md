# Ubiquitous Language

The vocabulary of the **rail**: the package-level workflow described in
[GOAL.md](GOAL.md) and contracted in [SPEC.md](SPEC.md). Repo-Dev Context only.

Fog. Lives on `dev`, never published to `main`.

This is **not** the aesthetic skill's language. That one lives in
[aesthetic/UBIQUITOUS_LANGUAGE.md](aesthetic/UBIQUITOUS_LANGUAGE.md), ships to
users, and defines a different domain with words that look the same. See
Flagged ambiguities.

## The rail

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Rail** | The constrained set of workflow exits an agent may take, such that it always knows where it is and what the next step costs | Guardrail, framework, pipeline |
| **Family** | One of the six units the command surface is cut into, each owning one `SKILL.md` | Command group, category, namespace |
| **Phase** | The stretch of the rail a family occupies, carried as the prefix on its names | Stage, step, mode |
| **Prefix** | The leading segment of a command name, which is the phase and does the routing a router command would otherwise do | Namespace, group, scope |
| **On-ramp** | A family entered from outside the sequence rather than as a step in it, marked by carrying no prefix | Entry point, utility, standalone |
| **Router** | A skill that maps the flows and points at other skills, never doing the work itself | Index, dispatcher, menu |

## The command surface

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Command** | A name a user types | Skill, prompt, alias |
| **Skill** | A directory holding doctrine. It pays a description tax only when model-invoked. | Command, module, tool |
| **Stub** | An alias file carrying a name and a pointer, and no doctrine of its own | Wrapper, shim, proxy |
| **Whole alias** | A stub naming an entire skill | Synonym, rename |
| **Anchor alias** | A stub naming one section inside a skill, so the doctrine is written once and the name is a bookmark into it | Deep link, subcommand |
| **Ghost argument** | A stub whose name encodes the argument the skill runs with, so what you would have had to remember instead autocompletes | Flag, preset, shortcut |
| **Drives** | The relationship between a family and the external skill it invokes rather than reimplements | Depends on, wraps, uses |
| **Leader word** | A skill name a user reaches for by habit rather than by looking it up | Favourite, top skill, entry point |

## Cost

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Token weight** | What a piece of `md`/`txt` text costs a session, on two independent axes: token cost and signal density. Never a single number. | Cost, size, expense |
| **Token cost** | How many tokens a text spends under one tokenizer profile. Deterministic for the same text and profile; byte count is the explicitly estimated fallback when the target tokenizer is unavailable. | Weight, size, price |
| **Signal density** | Whether a text's content sharpens what the model attends to or dilutes it. Not countable, judged by whether a cold reader can act on first read without re-deriving, guessing, or re-reading. | Quality, clarity, focus |
| **Context load** | The token weight of descriptions kept in the model's context every turn so it can invoke skills autonomously. A placement cost paid by the model. | Cognitive load, description tax |
| **Cognitive load** | What a human must remember when user-invoked skills are invisible to the model. An invocation cost paid by the human, not an axis of token weight. | Context load, signal density |
| **Byte budget** | The `max_file_bytes` cap on an always-loaded file, which is that file's worst-case **token cost**. | Size limit, quota, guideline |
| **Description tax** | The **context load** a model-invoked skill's `description` costs every session, whether or not the skill runs. Zero for a user-invoked skill. | Overhead, registration cost |
| **Rung** | One level of the cost ladder, from statusline down to a new skill, naming how cheaply an item can be carried | Tier, option, layer |
| **Lazy detail** | Content held in `references/` and paid for only when a pointer is followed | Docs, appendix, deep dive |
| **Fog** | Development state that stays on `dev` and never reaches a published tree | Internal docs, dev files |

## Inference context

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Context compiler** | The deterministic program that resolves eligible context, counts it under a tokenizer profile, packs it by priority and pass budget, and explains every admission and omission | Retriever, neural router, prompt optimizer |
| **Invocation path** | One route through a skill for a particular task, naming the context and inference passes that route may use | Workflow, command, mode |
| **Semantic context** | A declared boundary around work that a body of evidence can legitimately inform, such as Repo-Dev or Design-Inference | Topic, namespace, layer |
| **Eat your own food** | The repo-context doctrine that Repo-Dev work on this package must run through the skills it ships; after a skill commit here, `kit sync` must re-arm this repo and its collection dependencies | Dogfooding, self-host |
| **Context bundle** | The exact, ordered content compiled for one invocation path and inference pass | Prompt, corpus, context window |
| **Loading tier** | The declared availability of content: always, invocation, conditional, or excluded | Priority, weight, publication channel |
| **Workflow role** | What an item does in an invocation path: instruction, reference, executable, fixture, test, generated output, or evidence | File type, semantic context, loading tier |
| **Tokenizer profile** | A named target-model tokenizer and its counting method, marked exact when the tokenizer is available and estimated otherwise | Model, encoding, token weight |
| **Inference pass** | One bounded act inside an inference attempt, such as retaining constraints, retrieving context, proposing, generating, implementing, or verifying | Phase, stage, layer |
| **Pass budget** | The maximum token cost one inference pass may admit under a tokenizer profile | Byte budget, context window, quota |
| **Proof gate** | The deterministic stop that withholds an expensive inference pass until its cheapest representative artifact has passed | Approval, confidence threshold, checkpoint |
| **Compiler trace** | The reproducible account of what each inference pass admitted, omitted, spent, and why | Log, explanation, chain of thought |
| **Agreed tokenization** | A reviewed human judgement that a chunk's token-level rendering is legible to the target model, pinned to the sha256 of the exact text reviewed | Signal density, token cost, legibility score |

## Inference outcomes

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Inference attempt** | One task execution from compiled context through artifacts and user outcome, recorded locally for comparison | Session, run, generation |
| **Accepted result** | An inference attempt whose output the user keeps or ships without a restart or major scope correction | Successful response, completion, positive score |
| **Context utility** | The observed usefulness of admitted context to an accepted result, kept separate from its token cost | Token weight, relevance, quality |
| **Contamination risk** | The likelihood that content from an incompatible semantic context will frame the current work | Context derail, noise, hallucination |
| **Learned recommendation** | A dev-only model suggestion to change a declaration, priority, pass budget, proof gate, or regression fixture; never live authority | Rule, decision, automatic optimization |

## Accumulation

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Accumulation** | How a collection grows without its per-session cost growing with it | Scaling, bloat, sprawl |
| **Demote** | Moving an item down the cost ladder so it is carried by something cheaper than a skill | Simplify, downgrade |
| **Gate** | Installing many skills and enabling few, so cost tracks what is loaded rather than what is present | Disable, filter, scope |
| **Collapse** | Folding several commands into modes of one skill | Merge, consolidate, unify |
| **Origin** | The `collection.yaml` entry that makes a skill arrive on a clean machine | Source, repo, upstream |

## Documents

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Goal** | The record of why the shape is the shape and what it costs, holding nothing contractual | Spec, plan, README |
| **Spec** | The settled contract, fixed for the duration of a build and holding nothing speculative | Goal, proposal, draft |
| **Prototype** | An unsettled item written as a question, to be answered with throwaway work before it earns a spec row | Wishlist item, TODO, backlog |
| **Burndown** | The roadmap read as remaining work, one state per item | Backlog, todo list, sprint |
| **Item** | One row of the burndown, in exactly one of `TODO`, `IN-PROGRESS`, `BLOCKED`, `DONE` | Task, ticket, story |
| **Root cause** | The engineering finding a bug closes on, never the symptom the fix suppressed | Fix, patch, resolution |

## Failure

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Max** | A session whose context window fills, forcing a compaction that loses the thread | Overflow, context limit |
| **Waste** | Tokens spent re-deriving what the repo already records | Inefficiency, churn |
| **Stuck** | An agent looping on a blocked item, spending budget without moving the burndown | Hang, spin, blocked |
| **Context derail** | A session reading one context's records while working in the other, producing confident wrong work | Confusion, drift, fog |

## Relationships

- A **family** owns exactly one **skill** and one **phase**, and is reached by one or more **commands**.
- A **command** is either a **skill** or a **stub**; only the skill pays a **description tax** worth naming.
- A **stub** is exactly one of whole, **anchor**, or **ghost argument**, and carries no doctrine in any of the three.
- An **anchor** names a section of a `SKILL.md`, so renaming that section breaks the command.
- A **family** **drives** zero or more external skills, each of which needs an **origin** or it does not arrive.
- A **prototype** becomes a **spec** row by being answered, never by being described in more detail.
- **Max**, **waste**, and **stuck** are distinct failures with distinct defences, and share only their symptom.
- A **context compiler** emits one **context bundle** and **compiler trace** per
  **inference pass**, under one **tokenizer profile** and **pass budget**.
- A **proof gate** separates a cheap representative pass from the expensive
  pass it authorizes.
- An **inference attempt** may produce an **accepted result**; only reviewed
  attempts may support a **learned recommendation**.
- A **learned recommendation** may propose deterministic policy, but it never
  overrides a semantic-context boundary, proof gate, or publication rule.

## Example dialogue

> **Dev:** "`/build-clean-code` and `/build-qa-tests` are two commands. Is that two **skills**?"
> **Rail owner:** "One. `build` is the **family**; both names are **anchor** stubs pointing at sections of its `SKILL.md`. The doctrine is written once and each name is a bookmark into it."
> **Dev:** "Then what makes `land-asap-burndown` different? That is not a section."
> **Rail owner:** "It is a **ghost argument**. The name carries the argument `land` runs with, so the thing you would have had to remember to type autocompletes instead. Same cost as an anchor, one description line."
> **Dev:** "And `/fix` has no **prefix** at all."
> **Rail owner:** "Because it is an **on-ramp**. Breakage arrives from outside the sequence, so the shape of the name says which kind of command you are looking at before you read it. `kit` is the other one."
> **Dev:** "So what is the **weight** of `fix`?"
> **Rail owner:** "That question does not have an answer, and that is a conflict we have to fix. See below."

## Flagged ambiguities

- **`check` names objects in two layers.** *Settled.* The `check` **family** is
  the proposed user-facing, read-only phase. `tools/check.py` is the Repo-Dev
  **gate runner** for this package. A command and a file may share the ordinary
  verb because neither routes to the other; prose calls the latter the gate
  runner so the two objects never share a domain name.

- **"Weight" was attached to the wrong object, and to only one of its two
  axes.** *Settled.* `GOAL.md` used to declare `weight` as frontmatter on a
  **skill**, checked against the byte budget. That was **token cost** only,
  and it failed even on that axis: `SPEC.md` cuts **families** by phase, and
  four of the six hold sections of different cost -- `fix` holds *Fix the
  code* (large) beside *Fix the rail* (small). One number per skill was false
  for most of them. Fixed by dropping the field: the byte cap already **is**
  the worst-case token cost, so a second field could only disagree with it.
  Separately, **signal density** -- the axis "weight" was also being asked to
  cover -- was never a field candidate at all, since it is not countable. Both
  are now named and kept apart in the Token weight group above, so "weight"
  alone should not be used as a synonym for either.

- **"Phase" is redundant with the family name in four cases out of six.**
  `kit` would declare `phase: kit`, `build` would declare `phase: build`. The
  field is load-bearing exactly twice, for `genesis` (phase `first`) and
  `aesthetic` (phase `first`), which are the two families whose skill name and
  phase name differ. **Recommendation: keep the field, and say in `SPEC.md`
  that it exists for the cases where name and phase diverge.** A field that is
  usually redundant is fine; a field nobody can predict the value of is not.

- **"The recommendation below" in `GOAL.md` no longer points at anything.**
  The Collapse rung still describes itself as "the recommendation below", but
  the recommendation moved to `SPEC.md` and the settled scheme is not a
  collapse. Dangling pointer, not a disagreement. Fix the sentence.

- **"Burndown"** means two things in this repository, and the collision is
  load-bearing rather than accidental. Here it is the roadmap's remaining
  **items**. In the aesthetic skill it is unresolved *creative* scope, and
  `CONTEXT.md` already names this split. Neither should be renamed: each is
  correct in its own context, and the defence is that the two documents never
  load together.

- **"Budget"** collides the same way. Here it is a **byte budget** on a file.
  An agent that has just read `contracts.py` will carry the byte meaning into a
  design session and start policing file sizes instead of directing art. Same
  defence: context separation, not renaming.

- **"Skill" and "command"** were used interchangeably in the source workflow,
  and the distinction is the entire argument for the stub scheme. A **command**
  is what the user types. A **skill** is what costs a **description tax**.
  Fifteen commands are fine; fifteen skills are the failure this package exists
  to prevent.

- **"Fix"** named two unrelated objects in the source workflow: repairing code
  and repairing the agent's context. Resolved by keeping both in the `fix`
  family as separate sections, because both are **writes** that restore a
  broken thing, while `check` only reads and reports. This is settled, recorded
  here so it is not reopened.
