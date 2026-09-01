# QA: shot evaluation contract

Universal contract for any **LLM tool-using shot**: one bounded task, one
compute pass (or declared graph of passes), one deliverable, one user verdict.
Repo-agnostic. Copy this file into any skills repository; nothing here names a
specific harness, folder layout, or product.

This document is a **rubric and pipeline index**, not a second spec. Settled
command-surface contracts live elsewhere in each repo. Skill playbooks implement
adapters; they do not restate this file.

Schema for observation logs: [docs/SPEC/SHOT_OBSERVATION.md](docs/SPEC/SHOT_OBSERVATION.md).

## Pipeline

Every shot is understood as three engineering steps plus a feedback arc:

```text
INPUT (corpus + scope)
  -> COMPUTE (tokenized prompt + tools + observation log)
  -> OUTPUT (deliverable shot, pending user feedback)
  -> FEEDBACK (rank, correction, sentiment) -> corpus / index / next shot
```

| Step | Role |
| --- | --- |
| **Input** | Optional multimodal corpus, declared references, bounded scope |
| **Compute** | Executable, scoped prompt; tools; structured observation log |
| **Output** | The deliverable the user judges (image, document, code, bundle, alias, chart, etc.) |
| **Feedback** | User chat is the primary quality signal; outputs may re-enter the corpus |

Determinism here means **observable process control**: same declared inputs and
compiled prompt should yield a replayable trace and inspectable artifact. LLM
probability is not pixel-identical output. Cheap representative checks may
precede expensive passes; shipping paths favor parsers, gates, and procedural
renderers over unverified model prose.

## Shot record

Every shot writes one **shot record**. JSON (or equivalent structured data) is
the source of truth. Markdown may wrap or summarize it; it must not replace it.

Minimum fields (normative):

| Field | Required | Meaning |
| --- | --- | --- |
| `shot_id` | yes | Stable id for this attempt |
| `scope` | yes | One bounded task this shot solves |
| `inputs` | yes | Declared sources: corpus refs, prompt hash, tool stack |
| `compute` | yes | Observation log: model, harness, duration, token counts |
| `output` | yes | Deliverable reference or inline payload pointer |
| `provenance` | yes | `corpus`, `procedural`, `fetched`, or `inference` |
| `user_feedback` | yes | Rank, correction, sentiment, or `pending` |
| `gates` | no | L1/L2 machine results when an adapter ran them |

Adapters extend `output` typing only (`graphic`, `document`, `bundle`, `code`,
`alias`, etc.). They may not omit required fields.

Full schema: [docs/SPEC/SHOT_OBSERVATION.md](docs/SPEC/SHOT_OBSERVATION.md).

## Compliance layers

Quality and compliance are not the same.

| Layer | Authority | Question |
| --- | --- | --- |
| **L3 User** | **Primary** | Did the user accept it? Any negative sentiment or correction? |
| **L2 Verification** | Extra | Parsers, browser checks, schema validation (adapter-specific) |
| **L1 Gates** | Extra | Cheap machine vetoes (stale hash, scope tags, avoid-in-prompt) |
| **Hard veto** | Blocks compliance | Scope breach, missing observation log, context derail, ungrounded corpus claim |

**Good** is decided mainly in user chat: short success, clear improvement, no
corrections or negative sentiment.

**Compliant** requires L3 acceptance and no hard veto. L1/L2 reduce risk; they
do not override a delighted user, and they do not rescue a shot the user rejects.

## Input: multimodal corpus

The user may point at a folder of inspirational material: curated editorial
work, rough sketches, procedural targets (HTML, SVG, JSON scene data), and
**avoid** examples (failed agent shots, hallucinated slop, directions never to
repeat).

When a corpus exists, the agent **data-engineers** it:

1. Tag files by role (`reference`, `pursue`, `avoid`, `near-hit`, etc.).
2. Find expression patterns across files.
3. Compose a new product that may match references (image→text→image) or
   convert procedurally to other formats.

The corpus may also hold **other agents' shots**, good and bad. Classify; do
not treat every file as style evidence.

When the user approves a direction in chat, that feedback becomes evidence for
refinement. Good shots and ranked directions re-enter the corpus or index.

**Corpus is optional.** When absent, the agent must still be resourceful:
indexed knowledge bundles, declared fetches, and named tools before compute.
Record `provenance: fetched` or `provenance: inference` and list sources in
`inputs`. Do not invent corpus-fit scores without evidence.

Goal of input work: a **cheap, indexed context** suitable for embedding at
inference time, not a dump of every file into the prompt.

## Post-input: scoped prompt

After input (or without corpus), the agent reasons an **executable scoped
prompt**: what the compute step must do, what format the output must take, and
what must not change. Treat the LLM+tools box as black box only at the boundary;
inside, prefer tokenized logic (conditionals, graphs, declared passes) and
classical code for anything that must survive replay.

One scope per shot. Sub-scoping beats one prompt that mutates unrelated surfaces.

## Compute: observation log

Any tool-using LLM pass emits a **per-prompt-scope observation log**:

- Model and harness application names
- Wall duration and inference token consumption
- Compiled prompt identity (hash or version)
- Tool calls invoked
- Text or artifact sizes produced

This log is evidence for token budgeting and regression comparison. Do not
corrupt or discard it to make a shot look cheaper than it was.

Prefer structured logs. If a human-readable report exists, embed or link the
canonical JSON alongside it.

## Output: the shot

The shot is the deliverable the user judges: a graphic, a spec section, an OKF
bundle, a ranked table, a symlink forest, a landing page, a correction-ready
draft.

Success criteria:

- Solves the declared `scope` in one pass when possible
- Carries honest `provenance`
- Awaits L3 feedback without hiding known defects

Accepted outputs may return to the corpus with model and user tags attached.

## Derailing mitigation

LLMs derail by default: hallucinate tools, skip search, build on the wrong
stack, contaminate context, or overstep scope.

| Failure | Mitigation |
| --- | --- |
| **Limits unaware** | Declare what the model cannot do reliably (raw SVG, pixel truth). Prefer intermediate structured artifacts (JSON scene, DOM spec) and procedural renderers. |
| **Stackless build** | Name tools, runtimes, and adapters before the first implementation prompt. |
| **Zero-shot corpus** | Index and scope context. Compile slices per invocation; never load an entire repo doctrine into a design round. |
| **Context contamination** | Repo-Dev records (burndown, incident log, rail spec) stay out of Design-Inference runs. Use a context map (below). |
| **Scope creep** | One shot, one burndown row, one creative surface. Supersede explicitly instead of silent rebuild. |
| **Slop tolerance** | Treat waste as defect: lean manufacturing mindset, zero unpriced tokens, zero unlogged passes. |

## Minimum project surface

Any skills repository can run this contract with only:

| Surface | Purpose |
| --- | --- |
| **Corpus root** (optional) | Reference material |
| **Shot log directory** | Structured attempt records (convention: `.audit/shots/`) |
| **Scope declaration** | Per-shot bounded task in the shot record |
| **User feedback channel** | Chat rank, correction, or explicit negative sentiment |

No particular skill layout, scene spec, or graphics harness is required. Adapters
are optional packs.

## Context map

Do not load this entire file into every inference. Compile **sections only**:

| Invocation | Admit from `QA.md` | Exclude |
| --- | --- | --- |
| Design / creative shot | Pipeline, Shot record, Compliance, Input, Output, Derailing | Repo burndown, rail spec |
| Document / burndown shot | Pipeline, Scope, Shot record, Compliance, Derailing | Corpus graphics detail |
| Repo-Dev / contributor | Full `QA.md` | Design corpus paths as doctrine |
| Read-only audit | Compliance, Observation schema link | Post-input prompt craft |

Implement compilation in each repo's context compiler. Agents must not hand-pick
sections ad hoc.

## Reference implementations (cyber-skills)

This checkout implements the contract; it is not special-cased in the rules
above.

| Concern | Location |
| --- | --- |
| Graphics adapter | [first/aesthetic/references/text-to-graphics.md](first/aesthetic/references/text-to-graphics.md) |
| Visual verification | [first/aesthetic/references/verification.md](first/aesthetic/references/verification.md) |
| Sentiment / rank shape | [first/aesthetic/references/sentiment-analysis.md](first/aesthetic/references/sentiment-analysis.md) |
| Context compiler | [docs/SPEC/INFERENCE_CONTEXT_COMPILER.md](docs/SPEC/INFERENCE_CONTEXT_COMPILER.md) |
| Dogfood project state | `spec/`, `design/`, `shots/`, `moodboards/` (dev fog, not skill payload) |
| Shot log convention | `.audit/shots/` under project root |

Vocabulary stubs: [UBIQUITOUS_LANGUAGE.md](UBIQUITOUS_LANGUAGE.md) (Repo-Dev;
points here, does not duplicate).
