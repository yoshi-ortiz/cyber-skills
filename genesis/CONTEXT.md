---
purpose: skill entry point -- the spec-driven build discipline and the file topology it keeps state in
admits: SKILL.md, and directories that carry their own contract
refuses: doctrine and worked contracts, which belong in references/; any state about a real project, which belongs in that project
max_file_bytes: 7250
---

# Genesis

`SKILL.md` is loaded on every invocation and holds the steps only. Each step
that has a contract behind it points into `references/` rather than growing.

User-invoked on purpose. The doctrine is expensive and applies to a decision
someone is making deliberately: starting a project, starting a feature, or
auditing one. Firing it on every coding turn would charge every turn for a
contract most of them do not need.

It writes nothing into this repository. `ROADMAP.md`, `BUGS.md`, `docs/SPEC/`
and the rest are files in the **target project**. This repository has its own
`ROADMAP.md` and `BUGS.md`, and they are Repo-Dev Context for the skills
themselves, not artifacts of this skill running.

Step 3 delegates to [knowledge/](../knowledge/) rather than restating the
format. Two skills that both described OKF would drift, and the one that
drifted would be this one, since it is not the one with the gate.
