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

- Rank, sentiment, and lifecycle never write one another.
- User feedback outranks agent inference.
- Like plus high rank is a positive anchor.
- Like plus low rank requests polish of the same idea.
- Dislike plus high rank rejects the direction without denying the craft.
- Dislike plus low rank is a discard candidate.
- Missing feedback is an exploration candidate, not neutral evidence.
- Each element burns down under exactly one primary epic.
- An unsafe theme element returns to inference while unrelated safe elements remain valid.
- Reuse or fetch a commodity asset before generating one.
