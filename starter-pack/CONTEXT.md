---
purpose: one shipped alias, so the skill's original name keeps working
admits: SKILL.md, and nothing else
refuses: instructions of its own; every word of them belongs to kit/
max_file_bytes: 2000
---

# starter-pack

A stub, in the shape [silly/scripts/alias.py](../silly/scripts/alias.py) writes:
a name, an `alias_of` pointing at the skill that holds the work, and no
content. It ships in the published tree instead of being installed on demand,
which is the one thing that separates it from an alias `/silly` would make.

The rename to `kit/` happened after this name was published. Deleting it would
break every agent that already carries it, and an empty directory costs less
than that.
