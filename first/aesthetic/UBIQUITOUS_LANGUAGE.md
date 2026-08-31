# Aesthetic ranking language

The skill learns from human feedback without pretending that different signals mean the same thing.

## Creative work

**Element**:
A stable, individually rankable design decision with a dotted id such as `cover.layout.two-column`.
_Avoid_: Task, widget, layer

**Epic**:
A project-defined body of creative or delivery work that owns a set of elements. Each element has one primary epic.
_Avoid_: Foundation, prefix, bucket

**Critical epic**:
An epic whose unresolved elements currently determine the direction or block delivery.
_Avoid_: Foundation element, critical component

**Foundation**:
A design facet such as palette, typography, composition, imagery, voice, or motion.
_Avoid_: Epic, lifecycle state

**Direction**:
A subject-specific creative thesis supported by corpus observations and user feedback.
_Avoid_: Style, vibe, theme

## Human feedback

**Rank**:
A user-set score from 0 to 5 for the execution quality of one element.
_Avoid_: Sentiment, agent score, preference strength

**Sentiment**:
A user-set like or dislike for the creative direction of one element.
_Avoid_: Rank, verdict, approval

**Lifecycle**:
The explicit state of an element, independent of rank and sentiment.
_Avoid_: Score, completion inferred from stars

**Unscored**:
An element with no explicit user rank. Zero is a score and is never unscored.
_Avoid_: Neutral, zero-star

**Preference state**:
The rank, sentiment, lifecycle, provenance, and visible preview of one element considered without collapsing them into one number.
_Avoid_: Aggregate taste score, reward

**Polish**:
A liked element with low execution rank. Preserve the idea and redraw its execution.
_Avoid_: Reject, discard

**Conflict**:
A disliked element with high execution rank. Preserve the evidence of craft and reject its direction.
_Avoid_: Mixed score, average

## Progress

**Loop**:
The evidence-backed creative cycle: frame, direct, declare, build, critique, capture.
_Avoid_: Workflow, pipeline, process

**Scope event**:
An append-only record that adds, moves, resolves, reopens, or discards an epic or element.
_Avoid_: Mutable counter, inferred timestamp

**Burndown**:
Two histories derived from scope events. One counts unresolved epics and one counts unresolved elements.
_Avoid_: Coverage, rank histogram, invented points

**Coverage**:
The share of standing elements with an explicit user rank.
_Avoid_: Burndown, completion, sentiment count

## Theme and assets

**Theme candidate**:
A saved set of art-direction colors and fonts that the companion may follow.
_Avoid_: Automatic palette, highest-ranked colors

**Theme element**:
One independently validated role in a theme candidate, such as background, ink, accent, or font.
_Avoid_: Whole theme, raw CSS

**Safe value**:
The last saved value for a theme element that passed deterministic legibility checks.
_Avoid_: Guessed fallback, silent correction

**Sourced asset**:
An exact project, corpus, or library asset with a locator, license, version, and hash.
_Avoid_: Generated approximation, remembered icon

**Procedural asset**:
A graphic produced by a named deterministic generator from recorded parameters and a seed when applicable.
_Avoid_: Hand-authored SVG path, improvised replacement

## Rules

**Golden Rule**:
Stable design doctrine used to frame or test work. It is independent of an individual's feedback and must be indexed with credible Rule Evidence.
_Avoid_: Taste rule, preference, aesthetic score

**Design Fundamental**:
A teachable formal relationship or constraint involving composition, hierarchy, typography, color, image, space, or perception.
_Avoid_: Style preset, visual trend

**Aesthetic Principle**:
A philosophical question or account used to articulate the kind of experience or judgement a direction seeks.
_Avoid_: Mood word, universal law of beauty

**Art-Historical Precedent**:
A contextualized work, movement, method, or production relationship used to explain lineage and its limits.
_Avoid_: Style costume, movement preset

**Checkable Constraint**:
A declared property with a deterministic pass/fail result, such as contrast or allowed grid vocabulary.
_Avoid_: Quality score, aesthetic judgement

**Directed Principle**:
A stable design principle whose application requires contextual judgement and explicit evidence.
_Avoid_: Deterministic rule, model intuition

**Rule Evidence**:
A curriculum, standard, scholarly reference, institutional chronology, or primary source supporting a formal, philosophical, or historical claim.
_Avoid_: User preference, reachable URL alone

**Preference Evidence**:
Element-level user rank, sentiment, words, and visible preview used to infer what this user wants pursued.
_Avoid_: Golden Rule, population-level taste

**Academic Reception Evidence**:
Evidence that a subject is taught or recognized in a university or art-institute curriculum. It establishes academic relevance, not the truth of every claim.
_Avoid_: Source accuracy, popularity

**Source Receipt**:
A cached machine record that a named resource was reachable at a time, with its locator and response metadata.
_Avoid_: Truth certificate, peer review

## Contexts and scope

**Subject**:
The one product or page a round is working on.
_Avoid_: Product, project, client

**Parent item**:
The element id prefix a Subject's work sits under, such as `cover` for `cover.layout.two-column`.
_Avoid_: Category, folder, group

**Round Scope**:
The boundary confining a round's proposals to one parent item.
_Avoid_: Global scope, cross-project inference

**Design-Inference Context**:
An agent running `SKILL.md` to produce creative decisions.
_Avoid_: Using the skill, runtime

**Repo-Dev Context**:
An agent changing this skill's own code, contracts, or tests.
_Avoid_: Developing the skill, dev mode

**Context bleed**:
One context's vocabulary framing the other's decisions.
_Avoid_: Contamination

## Flagged ambiguities

- "Workflow" names the Burndown scripts (`editorial_workflow.py`,
  `brief_workflow.py`), never the creative cycle. Say **Loop** for the cycle.

## Invariants

- Rank, sentiment, and lifecycle never write one another.
- A round's proposals stay under one parent item.
- Neither context's doctrine frames the other's decisions.
- User feedback outranks agent inference.
- Like plus high rank is a positive anchor.
- Like plus low rank requests polish of the same idea.
- Dislike plus high rank rejects the direction without denying the craft.
- Dislike plus low rank is a discard candidate.
- Missing feedback is an exploration candidate, not neutral evidence.
- Each element burns down under exactly one primary epic.
- An unsafe theme element returns to inference while unrelated safe elements remain valid.
- Reuse or fetch a commodity asset before generating one.
- Golden Rules and learned user preferences remain separate evidence classes.
- Machine reachability, academic reception, and substantive accuracy are three different claims.
