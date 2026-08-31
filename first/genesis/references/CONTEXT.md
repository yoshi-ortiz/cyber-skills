---
type: Directory Contract
title: Genesis reference directory
description: Admission and size rules for the skill's on-demand contracts.
status: stable
purpose: on-demand payload, never auto-loaded
admits: the contracts behind a step in SKILL.md, one file per concern
refuses: anything a step needs before it runs; distilled external sources, which belong in the target project
max_file_bytes: 9000
---

# Genesis references

Three contracts, each named by exactly one step. A reference nothing points at
is a reference nothing loads, so a fourth file needs a fourth step first.

These are doctrine, not distilled sources. They carry OKF frontmatter because
the package writes reference bundles that way, and their trust boundary in
`index.md` says plainly that they are this skill's own opinion.
