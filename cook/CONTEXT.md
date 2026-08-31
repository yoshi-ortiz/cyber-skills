---
purpose: run this repository's own skills against a throwaway project and assert what a user would actually see
admits: the dogfood loop, its tests, and doctrine about running it
refuses: skill payload, design project state, anything a published tree carries
max_file_bytes: 12000
---

# Cook

Eat your own food. `cook` runs a skill the way a user runs it and checks the
**visible** outcome, because every gate in this repository so far checks an
exit code, and an exit code is what the companion bug hid behind: `open`
returned a URL, returned zero, and served an empty page.

Fog, on purpose and permanently. This directory is registered in
`tools/fog.py` FOG_DIRS and in `tools/skill_discovery.py` SKIP, so it publishes
to no channel and the index gate never asks the README to carry a row for it.
A test harness that shipped with the skills would be payload the user installs
and never runs.

## The contamination this exists to prevent

Running a design skill with `--project-root .` writes project state into the
repository root, where `spec/design-harness/`, `design/`, `shots/` and
`moodboards/` already hold one project's work beside the skill source that
produced it. An agent then reads a tree where **skill package** and **shot
test** are the same directory, which is the context derail the root
`CONTEXT.md` names, arriving through the filesystem instead of through a
document.

So `cook` refuses the repository root as a project root. There is no flag for
it. A dogfood round runs in a scratch tree or it does not run.
