---
purpose: skill entry point -- turning fetched sources into a cited OKF bundle the project keeps
admits: SKILL.md, and directories that carry their own contract
refuses: doctrine and command detail, which belong in references/; any knowledge file about a real subject, which belongs in the target project
max_file_bytes: 7250
---

# Knowledge

`SKILL.md` is loaded on every invocation. Everything it does not need before
its first command is a pointer into `references/`.

The output of this skill never lands here. Concept files are written into the
**target project**, under `docs/knowledge/`, because they are facts about that
project's dependencies and have no meaning in this repository. The only OKF
files in this directory are the skill's own two references, which happen to be
written in the format they describe and are checked by the same script.

```bash
python3 knowledge/scripts/okf.py check --root knowledge/references \
    --ignore CONTEXT.md
```

It ships in the same package as [aesthetic/](../aesthetic/) and shares nothing
with it. Aesthetic keeps its own reference bundle in the same format; that is a
shared format, not a shared contract, and neither skill's rules apply to the
other. `aesthetic/references/` predates this skill and is not maintained by it.
