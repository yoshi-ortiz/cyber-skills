---
purpose: the check family router for Monitor-phase reads, and the skills that measure
admits: SKILL.md, and one skill directory per read-only measurement skill
refuses: any write. A finding goes to the family that owns it, never fixed here
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
| [build-context-token-vectors/](build-context-token-vectors/) | Peer embedding and EVoC clustering over the installed corpus |
| [tokens-qa/](tokens-qa/) | Black-box QA over one Shot: what it cost, what it broke |
