---
purpose: the companion files this harness requires, vendored because they live in no repository of their own
admits: server.cjs, start-server.sh, install.sh, frame-template.html -- the browser surface that carries clicks to the durable ledger
refuses: harness logic, doctrine, anything a project should own
max_file_bytes: 40000
---

# Companion

The harness does not implement a companion; it requires one that satisfies
`references/companion-contract.md`. The stock brainstorming-skill files satisfy
neither the broadcast nor the state-greeting requirement, so the working copies
live here and `install.sh` puts them in place.

A design run treats this directory as read-only: it may run `install.sh` and
`start-server.sh`, never edit them. Fixing a companion defect is a change to the
skill, and changes to the skill follow `AGENTS.md`.

`start-server.sh` cds to this directory and `server.cjs` reads `frame-template.html` from `__dirname`. SKILL.md launches `companion/start-server.sh`, so the template has to live here, not only under brainstorming/scripts/.
