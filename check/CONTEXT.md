---
purpose: the check family router for Monitor-phase reads, and the skills that measure
admits: SKILL.md, and one skill directory per measurement or context-index skill
refuses: unscoped product changes; the router remains read-only and child skills declare their writes
max_file_bytes: 8000
---

# check

Skills that read production and progress evidence back into planning. Maps to the
`check` family on the rail.

[SKILL.md](SKILL.md) routes `zoom-out`, `review`, and `graphify`, and names the
gates that answer the ontology question. The measurement skills below carry
their own doctrine.

| Skill | Role |
| --- | --- |
| [tokens-ontology/](tokens-ontology/) | Repository retrieval with pgvector and EVoC exploration |
| [tokens-qa/](tokens-qa/) | Session compass, scoped repairs and evidence-driven RSI reporting |
