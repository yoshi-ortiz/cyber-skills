---
purpose: a user-invoked guide to the harness that installs every other skill
admits: SKILL.md, and any reference this skill alone needs
refuses: aesthetic doctrine, design vocabulary, anything from another skill in this package
max_file_bytes: 8000
---

# Starter pack

One file, one job: hand an agent the operating manual for the collection that
arms it. It describes another repository, `yoshi-ortiz/harness-core`, and holds
no logic of its own. Nothing here runs; the harness does the running.

User-invoked on purpose. It fires when someone types its name, so it costs no
context on the turns nobody asked for it, which is the whole argument for a
reference skill that is read a few times a month.

It ships in the same package as [aesthetic/](../aesthetic/) and shares nothing
with it.
