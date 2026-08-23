---
purpose: build and verify the fog-free trees that main and alpha publish
admits: publication tooling, the single fog list it shares, the channel split, and the index gate
refuses: skill logic, doctrine, anything a published tree needs at runtime
max_file_bytes: 12000
---

# Tools

`dev` is where the work happens. Every published tree is generated from it by
`publish.py`, carrying the skills and nothing else.

```bash
python3 tools/publish.py --out /tmp/published --check
python3 tools/publish.py --out /tmp/alpha --channel alpha --check
python3 tools/check_publication.py /tmp/published
python3 tools/index_gate.py
python3 tools/test_fog.py && python3 tools/test_index_gate.py
```

`fog.py` holds the list once so `publish.py` and `check_publication.py` cannot
disagree about what fog is. It also holds `ALPHA_SKILLS`: a skill named there is
fog on `main` and shipped on `alpha`, `KEEP_ALWAYS` included. That override is
deliberate — `KEEP_ALWAYS` protects a skill's payload from the fog rules, not
from a decision that the skill is not ready to ship. Generating the tree rather than curating it is the
point: a rule that says "remember not to commit the roadmap to main" is a rule
someone forgets on a tired evening.

`index_gate.py` reads the same `ALPHA_SKILLS` and checks the README against it:
what the tooling publishes and what the README advertises come from one list, so
they cannot drift apart in the one place a reader would notice first.

This directory is itself fog. It builds `main`; it does not ship on it.
