---
type: Directory Contract
title: Knowledge reference directory
description: Admission and size rules for this skill's on-demand payload.
status: stable
purpose: on-demand payload, never auto-loaded
admits: the cached format specification, and the practice of distilling a source
refuses: anything SKILL.md must know before its first command; knowledge about any real subject
max_file_bytes: 9000
---

# Knowledge references

Two documents, loaded only when a step names one. They are themselves OKF
files, so `okf.py check --root knowledge/references --ignore CONTEXT.md` gates the skill with the
same rule it gates a project bundle with. That is the cheapest available proof
that the format described here is a format that works.

The cached spec exists so the skill never refetches it. Refresh it against the
upstream `resource` when OKF moves past 0.2, and say so in `sources`.
