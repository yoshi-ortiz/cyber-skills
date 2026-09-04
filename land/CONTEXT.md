---
purpose: the land family router for Release and Deploy
admits: SKILL.md, and any reference this family alone needs
refuses: reimplementations of the public skills it routes, and this package's own publication doctrine, which lives in tools/
max_file_bytes: 8000
---

# land

Routes the Release and Deploy stop on the rail. [SKILL.md](SKILL.md) owns the
burndown state machine and the release handoff; `finishing-a-development-branch`
and `land-and-deploy` arrive through the harness collection.

The irreversible stop. It does not verify: a branch that arrives without
`build`'s Pre-release evidence goes back rather than forward.
