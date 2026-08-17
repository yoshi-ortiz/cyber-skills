---
purpose: skill entry point -- everything an agent must know before its first command
admits: SKILL.md, AGENTS.md, and directories that carry their own contract
refuses: doctrine, examples, command reference -- those belong in references/
max_file_bytes: 7250
---

# Skill root

`SKILL.md` is loaded on **every** invocation. Its budget is the whole point of this
contract: it grew to 12,907 bytes (~3,226 tokens) once, because nothing bounded it.

Before adding a paragraph here, ask whether a tool could enforce it instead. Prose
that duplicates tool behaviour is prose that drifts out of sync with the tool --
that is exactly how `companion-contract.md` came to contradict `SKILL.md`.

The budget was 6500 and is now 7250. What bought the extra 750 bytes: `## When
invoked` and `## What a design run may write`, which exist because three
consecutive runs read empty arguments as licence to improvise, and spent their
turns editing this skill's own scripts instead of designing. Neither rule can be
enforced by a tool the run is free to ignore, so both have to be in context on
every invocation. The six-step loop moved to `references/loop.md` to help pay for
them. `## Open the page first` exists because every continue run started with a
doctor dump instead of a page. This is a ceiling, not an allowance: the next
addition displaces something.
