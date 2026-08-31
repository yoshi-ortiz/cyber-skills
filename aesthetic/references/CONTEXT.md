---
type: Directory Contract
title: Aesthetic reference directory
description: Admission and size rules for the skill's on-demand knowledge bundle.
status: stable
generated:
  by: codex/gpt-5
  at: 2026-08-20T23:57:30-05:00
purpose: on-demand payload, never auto-loaded
admits: doctrine, worked examples, failure catalogues, command reference
refuses: anything SKILL.md must know before its first command
max_file_bytes: 9000
---

# References

Read on demand, linked from `SKILL.md`. Cost is paid only when opened, so depth is
cheap here and expensive there.

One subject per file. When two files start describing the same mechanism, one of
them is about to go stale -- merge them.

Every concept is listed in [index.md](index.md). Operational contracts describe
this skill; Golden Rule references additionally carry independent academic or
standards evidence. Machine verification checks provenance and reachability, not
the truth or aesthetic value of a claim.

## If this repo ever grows a CLAUDE.md

None exists here today -- this directory and `SKILL.md` already carry the
skill's own doctrine and conventions. If one is ever added, it must stay a
minimal index of pointers to context docs, the same role [index.md](index.md)
already plays for this bundle, and never carry doctrine, workflow detail, or
skill-specific guidance of its own. That content belongs in `SKILL.md` or a
file here, not duplicated into a CLAUDE.md where it can drift out of sync and
contaminate the skill's own conventions with unrelated repo-wide context.
