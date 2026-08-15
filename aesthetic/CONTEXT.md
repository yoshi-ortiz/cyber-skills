---
purpose: skill entry point -- everything an agent must know before its first command
admits: SKILL.md, AGENTS.md, and directories that carry their own contract
refuses: doctrine, examples, command reference -- those belong in references/
max_file_bytes: 6500
---

# Skill root

`SKILL.md` is loaded on **every** invocation. Its budget is the whole point of this
contract: it grew to 12,907 bytes (~3,226 tokens) once, because nothing bounded it.

Before adding a paragraph here, ask whether a tool could enforce it instead. Prose
that duplicates tool behaviour is prose that drifts out of sync with the tool --
that is exactly how `companion-contract.md` came to contradict `SKILL.md`.
