---
purpose: build and verify the fog-free tree that main publishes
admits: publication tooling and the single fog list it shares
refuses: skill logic, doctrine, anything a published tree needs at runtime
max_file_bytes: 12000
---

# Tools

`dev` is where the work happens. `main` is generated from it by `publish.py`,
carrying the skill and nothing else.

```bash
python3 tools/publish.py --out /tmp/published --check
python3 tools/check_publication.py /tmp/published
```

`fog.py` holds the list once so `publish.py` and `check_publication.py` cannot
disagree about what fog is. Generating the tree rather than curating it is the
point: a rule that says "remember not to commit the roadmap to main" is a rule
someone forgets on a tired evening.

This directory is itself fog. It builds `main`; it does not ship on it.
