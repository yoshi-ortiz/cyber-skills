---
purpose: skill entry point -- everything an agent must know before its first command
admits: SKILL.md, AGENTS.md, and directories that carry their own contract
refuses: doctrine, examples, command reference -- those belong in references/
max_file_bytes: 7250
---

# Skill root

`SKILL.md` is loaded on **every** invocation. Its byte budget is load-bearing — disclose detail to `references/` via context pointers, not by growing this file.

Before adding a paragraph here, ask whether a tool could enforce it instead.
