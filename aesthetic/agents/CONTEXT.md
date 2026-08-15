---
purpose: per-agent adapter manifests, so all three agents resolve to one skill copy
admits: one manifest per agent runtime
refuses: skill logic of any kind -- a manifest that behaves is a fork
max_file_bytes: 4000
---

# Agents

Two divergent copies of this skill have already shipped contradictory behaviour:
`~/.agents/skills/aesthetic` ran ahead of the iCloud canonical copy for hours, and
the committed copy rendered an invisible star strip while the runtime one did not.

Canonical is iCloud. After editing, rsync to `~/.agents/skills/aesthetic/`, then
commit. Never patch the runtime copy alone.
