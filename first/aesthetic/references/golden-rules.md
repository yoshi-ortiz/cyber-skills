---
type: Playbook
title: Applying Golden Rules
description: Separate deterministic design constraints from evidence-guided creative principles.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
sources:
  - id: graphic-design-fundamentals
    resource: graphic-design-fundamentals.md
    academic_role: bundle concept
  - id: aesthetics-philosophy
    resource: aesthetics-philosophy.md
    academic_role: bundle concept
  - id: art-history
    resource: art-history.md
    academic_role: bundle concept
---

# Applying Golden Rules

A Golden Rule is stable domain doctrine used to frame or test a design. It is
not learned user preference. Preference Evidence says what this person likes;
Rule Evidence says why a formal or historical claim is credible. Keep both in
the direction brief and never collapse them.

Read the three indexed bodies before declaring a direction:

- [Graphic design fundamentals](graphic-design-fundamentals.md) supplies formal
  relationships and accessibility constraints.
- [Aesthetics philosophy](aesthetics-philosophy.md) supplies questions and
  stances for judging experience.
- [Art history](art-history.md) supplies contextual precedent and lineage.

## Checkable constraints

These are decided by `scripts/golden_rules.py`. Determinism coverage says how
much of the declared design a rule can decide; it is not a quality score.

| Rule | Constraint | Evidence class |
| --- | --- | --- |
| `measure` | declare body measure; 45–75 characters is the skill's readable default heuristic | university accessibility guidance |
| `contrast` | normal text at least 4.5:1; large text and meaningful UI graphics at least 3:1 | WCAG 2.2 |
| `grid` | declare `manuscript`, `column`, or `modular` | formal design vocabulary |
| `gestalt` | name the grouping relation: `proximity`, `similarity`, `closure`, `continuity`, or `figure-ground` | perceptual design vocabulary |
| `register` | declare each meaningful mark as `icon`, `index`, or `symbol` | semiotic vocabulary |

```bash
python3 scripts/golden_rules.py --design spec/design-harness/candidate.json --min-coverage 0.8
```

A declared decision lands identically on every run even when it fails. Raise
coverage to make runs agree; fix failures to make the design work.

## Directed principles

These require judgement and must cite corpus observations, Rule Evidence, and
Preference Evidence before drawing.

- Declare the hierarchy, composition, grid, type roles, color relationships,
  image register, motion purpose, and one subject-specific signature.
- Judge color in context rather than from isolated swatches.
- Treat a historical movement as contextual lineage, not a visual preset.
- State the aesthetic question being tested. Beauty, sublimity, ugliness,
  friction, harmony, and estrangement can coexist; do not force them into a
  false binary.
- Replace labels such as “clean,” “premium,” or “editorial” with observable
  relationships and named counterevidence.

Any unsupported move is explicitly agent inference and remains unscored at 0★
until the user ranks it. See [anti-slop.md](anti-slop.md).
