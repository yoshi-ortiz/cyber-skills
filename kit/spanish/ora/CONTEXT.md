---
purpose: a voice skill that rewrites replies in the user's own Spanish, on request
admits: SKILL.md, and any reference this skill alone needs
refuses: aesthetic doctrine, design vocabulary, anything from another skill in this package
max_file_bytes: 8000
---

# Ora

One file, one job: restate what the agent has already written, in the variety
of Spanish the user themselves writes. It never decides anything. By default
it covers one reply and stops; `on` holds it for the session, `off` ends that
early. Neither mode is the file's own state — the calling agent tracks it.

It ships in the same package as [aesthetic/](../aesthetic/) and shares nothing
with it. Ora's rules about tone and emoji budget are not design doctrine, and
aesthetic's Golden Rules are not writing advice. An agent that has both loaded
should treat them as two unrelated skills that happen to live in one repository.
