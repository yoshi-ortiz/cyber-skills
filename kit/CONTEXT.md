---
purpose: a bootstrap and user-invoked guide to the harness that installs every other skill
admits: SKILL.md, child skill directories that carry their own contract, and any reference this skill alone needs
refuses: aesthetic doctrine, design vocabulary, anything from another skill in this package
max_file_bytes: 8000
---

# Kit

One file, one job: hand an agent the operating manual for the collection that
arms it. It describes another repository, `yoshi-ortiz/harness-core`, and holds
no logic of its own. Nothing here runs; the harness does the running.

Child skills in this family:

| Skill | Role |
| --- | --- |
| [starter-pack/](starter-pack/) | Original name alias for kit |
| [silly/](silly/) | Second names and language aliases |
| [spanish/ora/](spanish/ora/) | Spanish conclusion voice |

Model-invoked so First can call domain bootstrap; explicit Kit commands remain available.

It ships in the same package as [aesthetic/](../first/aesthetic/) and shares nothing
with it.
