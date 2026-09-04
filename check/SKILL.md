---
name: check
description: Read progress and release evidence back into planning, and change nothing while doing it. Routes zoom-out for the map above the code, review for a read of the diff, and graphify when the question is about a whole codebase. Use when the user says check, check-progress-goals, or check-release-ontology, or asks where a project stands, whether the shipped names still match the contract, or what a subsystem actually does.
disable-model-invocation: true
anchors:
  check-progress-goals: Progress
  check-release-ontology: Ontology
---

# Check

The return arc. Check reads evidence and hands it back to planning. It is safe
mid-session because it writes nothing: no file, no branch, no deploy.

| Say | Do |
| --- | --- |
| `check` | Progress, then Ontology |
| `check-progress-goals` | Progress only |
| `check-release-ontology` | Ontology only |

A finding is not a fix. Check produces a written answer with the evidence
attached, and the family that owns the problem does the writing. A broken code
path goes to `fix`, unfinished work goes to `first`, a failing verification goes
back to `build`.

## Progress

Where the work actually stands, against what was promised.

| Reach for | For |
| --- | --- |
| **zoom-out** | A subsystem you do not know well. The map of modules and callers, one layer above the code |
| **graphify** | A whole codebase, its architecture, and how its files relate |
| **review** | A diff or a branch, read rather than changed. Reached through the `gstack` bundle |

Read the project's own record first, because a roadmap is cheaper than a
repository walk. In this repository:

```bash
python3 tools/repo_context.py summary
python3 tools/repo_context.py state IN-PROGRESS
```

Report the gap between the record and the code, not the record alone. An item
marked done whose evidence nobody can produce is the finding.

Measurement skills in this family carry their own doctrine.
[`build-context-token-vectors/`](build-context-token-vectors/) clusters the
installed corpus, and [`tokens-qa/`](tokens-qa/) reads one shot and says what it
cost.

## Ontology

Whether the names a release promises still have one owner apiece.

Every public name resolves to exactly one skill, and every shipped skill
answers to the names its own description says. A name declared in one file and
absent from a description is a word nothing answers to.

```bash
python3 tools/index_gate.py
python3 tools/check.py
```

The gates are the answer. This section says which one to run and how to read
what comes back, and adds no second implementation of what they already decide.

A name with two owners, or an owner with no name, is a contract defect. It goes
to `first` to be settled in the spec, never patched here.
