---
type: Contract
title: Feature branch and commit
description: Isolate and record each software feature as a reviewable Git change.
status: stable
---

# Feature branch

For each bounded software feature, inspect Git status and the current branch.
Reuse an existing branch that owns this feature; otherwise create a
`codex/<feature>` branch from the agreed base. Preserve unrelated changes and
avoid branching from an unknown or dirty base without accounting for its state.

Implement and verify the Item there. Stage only its files, inspect the staged
diff, and commit with a message naming the feature and resulting behavior.
Keep acceptance pending until the owner accepts the result; a commit records a
verified change, not user approval. Report the branch, commit and proof. Done
when this feature has a reviewable commit on its owning branch, or an exact Git
or verification blocker is recorded. If Git is unavailable, provide the patch
and commit instructions rather than claiming a commit.
